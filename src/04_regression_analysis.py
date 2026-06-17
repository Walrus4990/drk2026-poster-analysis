import pandas as pd
import numpy as np
import sqlite3
import statsmodels.formula.api as smf

from utils import significance_stars, format_coef, hauptgruppen, build_diagnose_gruppe, score_pairs

##fetch data

con = sqlite3.connect("data/rheuma_konf_2026.db")
df = pd.read_sql("SELECT * FROM reshaped", con)
long_df = pd.read_sql("SELECT * FROM long", con)
con.close()

## add diagnose_gruppen column

df = build_diagnose_gruppe(df)

########## REGRESSION ANALYSIS - FULL MODEL  ########################
# Initial model specification:

#Dependent variable:
#score_value — the outcome, what we're trying to explain - vorher as default

#Independent variables:
#zeitpunkt — fixed effect for time (vorher/nachher)
#geschlecht — fixed effect for sex - w as default
#zeitpunkt * geschlecht — interaction and both main effects
#alter — age as a covariate
#diagnose_gruppe  - as a co/variate - Sonstige set as reference

#Random effect:
#groups=data["patnr"] — identifies which rows belong to the same patient

###data

long_df = long_df.merge(
    df[['patnr', 'diagnose_gruppe']],
    on='patnr',
    how='left'
)

###covariate

base_covariates = {
    'zeitpunkt':  "C(zeitpunkt, Treatment('vorher'))[T.nachher]",
    'geschlecht': "C(geschlecht, Treatment('w'))[T.m]",
    'alter':      'alter',
}

diagnose_covariates = {
    g: f"C(diagnose_gruppe, Treatment('Sonstige'))[T.{g}]" for g in hauptgruppen
}

all_covariates = base_covariates | diagnose_covariates


########## TESTING THE FULL MODEL  ########################

######## TEST1: Do we need the interaction term?

# Test: AIC comparison - interaction term (zeitpunkt x geschlecht)
# Compare full model (with interaction) vs base model (without interaction)
# fitted with ML not REML for valid AIC comparison across fixed effects structures

base = """score_value ~
    C(zeitpunkt, Treatment('vorher')) +
    C(geschlecht, Treatment('w')) +
    alter +
    C(diagnose_gruppe, Treatment('Sonstige'))"""

interaction = " + C(zeitpunkt, Treatment('vorher')):C(geschlecht, Treatment('w'))"

full = base + interaction

aic_results = []
for score in long_df['score_type'].unique():
    data = long_df[long_df['score_type'] == score].copy()

    model_full = smf.mixedlm(full, data=data, groups=data["patnr"]).fit(reml=False)
    model_reduced = smf.mixedlm(base, data=data, groups=data["patnr"]).fit(reml=False)

    aic_results.append({
        'Score': score,
        'AIC_Interaktion': round(model_full.aic, 2),
        'AIC_Ohne_Interaktion': round(model_reduced.aic, 2),
        'AIC_Differenz': round(model_full.aic - model_reduced.aic, 2),
        'Interaktion': 'Ja' if model_full.aic < model_reduced.aic - 2 else 'Nein'
    })

aic_df = pd.DataFrame(aic_results)
# print(aic_df)

#CONCLUSION: interaction term almost always below 2, one case 2.8 -> makes no meaningful difference drop


###### TEST 2: Does diagnose_gruppe confound the norm model?

# Model A: norm without diagnosis
# Model B: norm with diagnosis (= base model from Test 1)
# Compare coefficients and standard errors — >10% change in coef = confounding

norm_data = long_df[long_df['score_type'] == 'norm'].copy()

model_norm_without = """score_value ~
    C(zeitpunkt, Treatment('vorher')) +
    C(geschlecht, Treatment('w')) +
    alter"""

result_without = smf.mixedlm(model_norm_without, data=norm_data, groups=norm_data["patnr"]).fit(reml=True)
result_with = smf.mixedlm(base, data=norm_data, groups=norm_data["patnr"]).fit(reml=True)

compare_params = [
    ("C(zeitpunkt, Treatment('vorher'))[T.nachher]", 'Zeitpunkt'),
    ("C(geschlecht, Treatment('w'))[T.m]", 'Geschlecht'),
    ('alter', 'Alter')
]

comparison_results = []
for param, label in compare_params:
    coef_without = result_without.params.get(param, np.nan)
    coef_with = result_with.params.get(param, np.nan)
    se_without = result_without.bse.get(param, np.nan)
    se_with = result_with.bse.get(param, np.nan)
    pct_change_coef = abs((coef_with - coef_without) / coef_without) * 100 if coef_without != 0 else np.nan
    pct_change_se = abs((se_with - se_without) / se_without) * 100 if se_without != 0 else np.nan
    comparison_results.append({
        'Parameter': label,
        'Koeffizient_Ohne_Diagnose': round(coef_without, 4),
        'Koeffizient_Mit_Diagnose': round(coef_with, 4),
        'Änderung_Koeffizient_%': round(pct_change_coef, 1),
        'SE_Ohne_Diagnose': round(se_without, 4),
        'SE_Mit_Diagnose': round(se_with, 4),
        'Änderung_SE_%': round(pct_change_se, 1),
        'Konfundierung': 'Ja' if pct_change_coef > 10 else 'Nein'
    })

comparison_df = pd.DataFrame(comparison_results)
# print(comparison_df.to_string(index=False))

# CONCLUSION: zeitpunkt unaffected, alter and geschlecht change >10% with stable SE
# → diagnosis is a confounder for norm, include diagnose_gruppe in all models


########## REGRESSION ANALYSIS - FINAL MODEL  ########################
# 1. interaction dropped (Test 1)
# 2. diagnose_gruppe included for all scores including norm (Test 2)
# final model formula = base (defined in Test 1)

model_results = []
for score in long_df['score_type'].unique():
    data = long_df[long_df['score_type'] == score].copy()
    result = smf.mixedlm(base, data=data, groups=data["patnr"]).fit(reml=True)

    row = {'score_type': score}
    for key, value in all_covariates.items():
        row[key] = format_coef(round(result.params.get(value, np.nan), 4),
                               result.pvalues.get(value, np.nan))
    row['N'] = len(data) // 2
    model_results.append(row)

##### EXPORT

model_df = pd.DataFrame(model_results)
model_df = model_df.fillna('').replace('nan', '')
footnote = pd.DataFrame([{'score_type': '* p<0.05, ** p<0.01, *** p<0.001'}])
model_df = pd.concat([model_df, footnote], ignore_index=True).fillna('')

# export to SQL
con = sqlite3.connect("data/rheuma_konf_2026.db")
model_df.to_sql("model", con, if_exists="replace", index=False)
con.close()

########## EXPORT TO EXCEL ########################

with pd.ExcelWriter("outputs/Ergebnisse.xlsx", engine="openpyxl", mode='a', if_sheet_exists='replace') as writer:
    model_df.to_excel(writer, sheet_name="Multivariate Regressionsanalyse", index=False)

    aic_df.to_excel(writer, sheet_name="Modelldiagnostik", index=False, startrow=1)
    ws = writer.sheets["Modelldiagnostik"]
    ws.cell(row=1, column=1).value = "--- Interaktionsterm Zeitpunkt x Geschlecht ---"

    diag_start = len(aic_df) + 5
    comparison_df.to_excel(writer, sheet_name="Modelldiagnostik", index=False, startrow=diag_start + 1)
    ws.cell(row=diag_start, column=1).value = "--- Konfundierung Norm und Diagnosegruppe ---"


########## EXPORT TO MARKDOWN ########################

with open("outputs/Regressionsanalyse.md", "w") as f:
    f.write("## Multivariate Regressionsanalyse\n\n")
    f.write(model_df.to_markdown(index=False))

    # f.write("\n\n---\n\n")
    # f.write("## Brauchen wir einen Interaktionsterm Zeitpunkt x Geschlecht?\n\n")
    # f.write(aic_df.to_markdown(index=False))
    # f.write(
    #     "\n\n**Schlussfolgerung:** Der Interaktionsterm verbessert den Modellfit bei nur einem Score um mehr als 2 AIC-Punkte,"
    #         "und dort nur um 2,8. Der Interaktionsterm wird aus dem finalen Modell ausgeschlossen.\n"
    # )

    # f.write("\n\n---\n\n")
    # f.write("## Sind die Diagnosegruppen-Koeffizienten im Norm-Modell konfundiert?\n\n")
    # f.write(comparison_df.to_markdown(index=False))
    # f.write(
    #     "\n\n**Schlussfolgerung:** Der Behandlungseffektkoeffizient (Zeitpunkt) bleibt stabil. "
    #     "Geschlecht- und Alterkoeffizienten ändern sich um mehr als 10% bei stabilem Standardfehler. "
    #     "Die Diagnosezugehörigkeit kovariiert mit anderen Prädiktoren im Modell. "
    #     "Um Konfundierung zu vermeiden und die Effekte der einzelnen Prädiktoren isoliert schätzen zu können, "
    #     "wird die Diagnose in allen Modellen berücksichtigt.\n"
    # )
