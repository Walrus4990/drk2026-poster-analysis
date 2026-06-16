import pandas as pd
import sqlite3
from scipy import stats
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd

########## LOAD CLEAN DATASET ########################

con = sqlite3.connect("data/rheuma_konf_2026.db")
df = pd.read_sql("SELECT * FROM reshaped", con)
freq_df = pd.read_sql("SELECT * FROM test_score_frequencies", con)
long_df = pd.read_sql("SELECT * FROM long", con)
con.close()


#################### MAKING SIGNIFICANCE PRETTY ##############


def significance_stars(p):
    if pd.isna(p):
        return ''
    elif p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return ''

def format_coef(coef, p):
    if pd.isna(coef):
        return ''
    stars = significance_stars(p)
    return f"{coef}{stars}"




########## AGE & GENDER ########################

alter_df = df.groupby("geschlecht")["alter"].agg(
    Durchschnittsalter="mean",
    StdAbw="std",
    N="count"
).reset_index()


# Separate dfs (or series) for the age values by gender
male_ages = df.loc[df["geschlecht"] == "m", "alter"]
female_ages = df.loc[df["geschlecht"] == "w", "alter"]

# Two-sample independent t-test
t_stat, p_value = stats.ttest_ind(male_ages, female_ages, equal_var=False)  # Welch's t-test

alter_df["t_Stat"] = None
alter_df["p_Wert"] = None

alter_total_row = pd.DataFrame({
    "geschlecht": ["insgesamt"],
    "Durchschnittsalter": [df["alter"].mean()],
    "StdAbw": [df["alter"].std()],
    "N": [df["alter"].count()],
    "t_Stat": [t_stat],
    "p_Wert": [p_value],
    'sig': significance_stars(p_value)
})

alter_df = pd.concat([alter_df, alter_total_row], ignore_index=True)
alter_df[['Durchschnittsalter', 'StdAbw']] = alter_df[['Durchschnittsalter', 'StdAbw']].round(2)


########## DIAGNOSE ########################

df['hd_basis'] = df['hd'].str.split('.').str[0] #create Basisdiagnose column snce used a lot throughout


diagnose_df = df.groupby(df["hd_basis"]).agg(
    insgesamt=("hd", "count"),
    m=("geschlecht", lambda x: (x == "m").sum()),
    w=("geschlecht", lambda x: (x == "w").sum())
).reset_index().rename(columns={"hd_basis": "Diagnose"})

diagnose_total_row = pd.DataFrame({
    "Diagnose": ["insgesamt"],
    "insgesamt": [diagnose_df["insgesamt"].sum()],
    "m": [diagnose_df["m"].sum()],
    "w": [diagnose_df["w"].sum()]
})

diagnose_df = pd.concat([diagnose_df, diagnose_total_row], ignore_index=True)

#add sonstige
#For each value x in the split series
#if it's in hauptgruppen keep it as is, otherwise replace with 'Sonstige'.

hauptgruppen = ['L40', 'M05', 'M06', 'M45']

df['diagnose_gruppe'] = df['hd_basis'].apply(
    lambda x: x if x in hauptgruppen else 'Sonstige'
)

diagnose_agg_df = pd.crosstab(
    df['geschlecht'],
    df['diagnose_gruppe'],
    margins=True,
    normalize='index'
).round(2) * 100
diagnose_agg_df.columns = [str(col) + ' (%)' for col in diagnose_agg_df.columns]


############### RESPONSE TO TREATMENT TESTS ######################

score_labels = {
    'vas1a': 'VAS-A',
    'vas1p': 'VAS-P',
    'ffbh1': 'FFbH',
    'norm1': 'Aktivität'
}

pairs=[
    ('vas1a', 'vas2a'),
    ('vas1p', 'vas2p'),
    ('ffbh1', 'ffbh2'),
    ('norm1', 'norm2')
]

groups = [
    ('insgesamt', df),
    ('m', df[df["geschlecht"] == "m"]),
    ('w', df[df["geschlecht"] == "w"])
]


results = []
for group_name, group_df in groups:         # repeat loop for all, men and women
    for xante, xpost in pairs:
        data = group_df[[xante, xpost]].dropna()  # drop missing, only include valid pairs
        t_stat, p_val = stats.ttest_rel(data[xante], data[xpost])
        results.append({
            'Gruppe': group_name,
            'Test_Score': score_labels[xante],
            'vorher_Durchschnitt': round(data[xante].mean(), 2),
            'nachher_Durchschnitt': round(data[xpost].mean(), 2),
            'N': len(data),
            't_Stat': round(t_stat, 4),
            'p_Wert': round(p_val, 4),
            'sig': significance_stars(p_val)
        })

verlauf_df = pd.DataFrame(results)

#sort by test & w, m, total
group_order = {'insgesamt': 2, 'm': 1, 'w': 0}
verlauf_df['group_order'] = verlauf_df['Gruppe'].map(group_order)
verlauf_df = verlauf_df.sort_values(['Test_Score', 'group_order']).drop(columns='group_order')


############### NORMALISED SCORES FOR PLOTTING ######################

norm_score_labels = {
    'vas_norm1a': 'VAS-A',
    'vas_norm1p': 'VAS-P',
    'ffbh_norm1': 'FFbH',
    'norm1':      'Aktivität'
}

norm_pairs = [
    ('vas_norm1a', 'vas_norm2a'),
    ('vas_norm1p', 'vas_norm2p'),
    ('ffbh_norm1', 'ffbh_norm2'),
    ('norm1',      'norm2')
]

norm_results = []
for group_name, group_df in groups:
    for xante, xpost in norm_pairs:
        data = group_df[[xante, xpost]].dropna()
        norm_results.append({
            'Gruppe': group_name,
            'Test_Score': norm_score_labels[xante],
            'vorher_Durchschnitt': round(data[xante].mean(), 2),
            'nachher_Durchschnitt': round(data[xpost].mean(), 2),
            'N': len(data)
        })

verlauf_norm_df = pd.DataFrame(norm_results)
verlauf_norm_df['group_order'] = verlauf_norm_df['Gruppe'].map(group_order)
verlauf_norm_df = verlauf_norm_df.sort_values(['Test_Score', 'group_order']).drop(columns='group_order')


############### DIFFERENCE MEN AND WOMEN ######################


#create difference
for xante, xpost in pairs:
    df[xante + '_diff'] = df[xpost] - df[xante]

#define groups for loop
triplets = [
    ('vas1a', 'vas2a', 'vas1a_diff'),
    ('vas1p', 'vas2p', 'vas1p_diff'),
    ('ffbh1', 'ffbh2', 'ffbh1_diff'),
    ('norm1', 'norm2', 'norm1_diff')
]

zeitpunkt = [('vorher', 0), ('nachher', 1), ('diff', 2)]

m_w_results = []
for xante, xpost, col_diff in triplets:
    for label, idx in zeitpunkt:
        col = [xante, xpost, col_diff][idx]
        m_data = df[df["geschlecht"] == "m"][col].dropna()
        w_data = df[df["geschlecht"] == "w"][col].dropna()
        t_stat, p_val = stats.ttest_ind(m_data, w_data, equal_var=False)  # Welch's t-test
        m_w_results.append({
            'Test_Score': score_labels[xante],
            'Zeitpunkt': label,
            'm_Durchschnitt': round(m_data.mean(), 2),
            'm_N': len(m_data),
            'w_Durchschnitt': round(w_data.mean(), 2),
            'w_N': len(w_data),
            't_Stat': round(t_stat, 4),
            'p_Wert': round(p_val, 4),
            'sig': significance_stars(p_val)
        })

m_w_unterschied_df = pd.DataFrame(m_w_results)
print(m_w_unterschied_df)

############### DIFFERENCE DIAGNOSE (ANOVA) ######################

anova_triplets = [
    ('vas1a', 'vas2a', 'vas1a_diff'),
    ('vas1p', 'vas2p', 'vas1p_diff'),
    ('ffbh1', 'ffbh2', 'ffbh1_diff')
]

anova_results = []
for xante, xpost, diff_col in anova_triplets:
    for label, col in [('vorher', xante), ('nachher', xpost), ('diff', diff_col)]:
        groups_anova = [group_data.dropna()
                        for _, group_data in df.groupby('diagnose_gruppe')[col]] #drop missing pairs
        f_stat, p_val = stats.f_oneway(*groups_anova)
        anova_results.append({
            'Test_Score': score_labels[xante],
            'Zeitpunkt': label,
            'F_Stat': round(f_stat, 4),
            'p_Wert': round(p_val, 4),
            'sig': significance_stars(p_val),
            'N': df[col].notna().sum()
        })

anova_df = pd.DataFrame(anova_results)


tukey_results = []
for xante, xpost, diff_col in anova_triplets:
    for label, col in [('vorher', xante), ('nachher', xpost), ('diff', diff_col)]:
        data = df[['diagnose_gruppe', col]].dropna()
        tukey = pairwise_tukeyhsd(data[col], data['diagnose_gruppe'])
        rows = tukey.summary().data[1:]
        for row in rows:
            tukey_results.append({
                'Test_Score': score_labels[xante],
                'Zeitpunkt': label,
                'Gruppe_1': row[0],
                'Gruppe_2': row[1],
                'Mittelwert_Diff': round(float(row[2]), 4),
                'p_Wert': round(float(row[3]), 4),
                'sig': significance_stars(float(row[3]))
            })

tukey_df = pd.DataFrame(tukey_results).sort_values(by=['Gruppe_1', 'p_Wert'], ascending=True)
print(tukey_df)

########## TESTSCORE FREQUENZ ########################

freq_df = freq_df.set_index('index')
selected_counts = df['selected_test_score'].value_counts()
freq_df['analysiert'] = selected_counts
freq_df = freq_df.fillna(0).astype(int)
freq_df = freq_df.reset_index().rename(columns={
    'index': 'Test_Score',
    'n_valid_pairs': 'insgesamt'
})

test_score_labels = {
    'sdai': 'SDAI',
    'dapsa': 'DAPSA',
    'basdai': 'BASDAI',
    'basfi': 'BASFI',
    'sledai': 'SLEDAI',
    'das28': 'DAS28'
}

freq_df['Test_Score'] = freq_df['Test_Score'].map(test_score_labels)

########## REGRESSION ANALYSIS ########################

#score_value — the outcome, what we're trying to explain - voreher as default
#zeitpunkt — fixed effect for time (vorher/nachher)
#geschlecht — fixed effect for sex - w as default
#zeitpunkt * geschlecht — interaction and both main effects
#alter — age as a covariate
#diagnose  - as a co/variate
#groups=data["patnr"] — identifies which rows belong to the same patient



long_df = long_df.merge(
    df[['patnr', 'diagnose_gruppe']],
    on='patnr',
    how='left'
)

base_covariates = {
    'zeitpunkt':   "C(zeitpunkt, Treatment('vorher'))[T.nachher]",
    'geschlecht':  "C(geschlecht, Treatment('w'))[T.m]",
    'interaktion': "C(zeitpunkt, Treatment('vorher'))[T.nachher]:C(geschlecht, Treatment('w'))[T.m]",
    'alter':       'alter',
}

diagnose_covariates = {
    g: f"C(diagnose_gruppe, Treatment('Sonstige'))[T.{g}]" for g in hauptgruppen
}

def build_model(diagnose_cov=True): #function that takes a boolean to switch between models
    model = """score_value ~
        C(zeitpunkt, Treatment('vorher')) *
        C(geschlecht, Treatment('w')) +
        alter"""
    if diagnose_cov: #if True (i.e. not norm)
        model += " + C(diagnose_gruppe, Treatment('Sonstige'))"
        covariates = base_covariates | diagnose_covariates #combine base & diagnose covariates to one dictionary
    else:
        model
        covariates = base_covariates
    return model, covariates

model_results = []
for score in long_df['score_type'].unique(): #for every unique score (i.e. ffbh)
    data = long_df[long_df['score_type'] == score].copy() # copy the data for the specific test score
    model, covariates = build_model(diagnose_cov=score != 'norm') #build model and select co-variates depending on eth value of score
    result = smf.mixedlm(model, data=data, groups=data["patnr"]).fit(reml=True) #run the model, patnr  is the grouping var in the model

    row = {'score_type': score}
    for key, value in covariates.items():
        row[key] = format_coef(round(result.params.get(value, np.nan), 4), result.pvalues.get(value, np.nan))
    row['N'] = len(data) // 2
    model_results.append(row)


model_df = pd.DataFrame(model_results)
footnote = pd.DataFrame([{'score_type': '* p<0.05, ** p<0.01, *** p<0.001'}])
model_df = pd.concat([model_df, footnote], ignore_index=True)

#exporting to SQL to look at table
con = sqlite3.connect("data/rheuma_konf_2026.db")
model_df.to_sql("model", con, if_exists="replace", index=False)
con.close()

########## EXPORT TO EXCEL ########################

with pd.ExcelWriter("outputs/Ergebnisse.xlsx", engine="openpyxl", mode='w') as writer:
    alter_df.to_excel(writer, sheet_name="Alter", index=False)
    diagnose_df.to_excel(writer, sheet_name="Diagnose", index=False)
    diagnose_agg_df.to_excel(writer,sheet_name="Diagnose Zusammenfassung", index=True)
    verlauf_df.to_excel(writer, sheet_name="Verlauf", index=False)
    verlauf_norm_df.to_excel(writer, sheet_name="Verlauf Normalisiert", index=False)
    m_w_unterschied_df.to_excel(writer, sheet_name="Geschlechtervergleich", index=False)
    freq_df.to_excel(writer, sheet_name="Scoreverteilung", index=False)
    model_df.to_excel(writer, sheet_name="Multivariate Regressionsanalyse", index=False)

    # ANOVA and Tukey on same sheet
    anova_df.to_excel(writer, sheet_name="ANOVA Diagnose", index=False, startrow=5)
    ws = writer.sheets["ANOVA Diagnose"]  # sheet now exists
    ws.cell(row=1, column=1).value = ("Hinweis:")
    ws.cell(row=2, column=1).value = (
        "Die ANOVA prüft, ob sich die Diagnosegruppen insgesamt unterscheiden."
    )
    ws.cell(row=3, column=1).value = (
        "Der Tukey-Test zeigt anschließend, welche Gruppen sich paarweise voneinander unterscheiden.."
    )
    ws.cell(row=5, column=1).value = "------ANOVA-------"
    tukey_start = 5 + len(anova_df) + 3
    ws.cell(row=tukey_start, column=1).value = "------ Tukey Post-hoc -------"
    tukey_df.to_excel(writer, sheet_name="ANOVA Diagnose", index=False, startrow=tukey_start)
