import pandas as pd
import numpy as np
import sqlite3

con = sqlite3.connect("data/rheuma_konf_2026.db")
df = pd.read_sql("SELECT * FROM ingest", con)
con.close()

################ TEST SCORE AGGREGATION ##########################
# Different disease activity indices (SDAI, BASDAI, DAPSA etc.) are used
# depending on diagnosis. To analyse treatment response across the full cohort,
# each patient is assigned their primary test (most frequently used in the cohort),
# scores are normalised to 0-1 per test scale, allowing pooled analysis.

test_scores = ['basfi', 'basdai', 'sdai', 'dapsa', 'sledai', 'das28']

#which test score is the most frequently used

freq = {}
for test_score in test_scores:
    col1 = test_score + '1'
    col2 = test_score + '2'
    if col1 in df.columns and col2 in df.columns:
        valid_pair = df[[col1, col2]].dropna().shape[0]  # count valid pairs only. dropna drops incomplete pairs, .shape looks at teh matrix shape and uses the row count as frequency fro how many tests there are
        freq[test_score] = valid_pair                     #matches the test_score with number of valid pairs

freq_df = pd.DataFrame.from_dict(freq, orient='index', columns=['n_valid_pairs']) \
                      .sort_values('n_valid_pairs', ascending=False)


# derive priority order from frequency - most frequent test_score gets highest priority
# note das28
priority_order = freq_df.index.tolist()



# select primary test_score for those patients with more than one test

def select_primary_test_score(test_score_list):
    if not isinstance(test_score_list, list): # the parametre isn't a list,e.g. it's pd.NA bcse no valid pairs
        return pd.NA
    for test_score in priority_order:
        if test_score in test_score_list:
            return test_score       #return test score adn stop
    return pd.NA      #no matching test_score found - should not occur given get_tests_for_patients logic



# builds a list of test score names if the patient has both ex ante and ex post values

def get_test_scores_for_patient(row):
    patient_test_scores = []
    for test_score in test_scores:
        col1 = test_score + '1'
        col2 = test_score + '2'
        if col1 in df.columns and col2 in df.columns:
            if pd.notna(row[col1]) and pd.notna(row[col2]): #checks if the specific cells are full (not empty), if two values per test_score exit
                patient_test_scores.append(test_score)
    return patient_test_scores if patient_test_scores else pd.NA


# for each patient, build a list of valid test scores (get_test_scores_for_patient)
# then assign the highest frequency one as selected_test_score (select_primary_test_score)
# axis=1 means apply the function row by row
df['selected_test_score'] = df.apply(get_test_scores_for_patient, axis=1).apply(select_primary_test_score)

##Note: 55 patienst have no test score at all out of (basfi', 'basdai', 'sdai', 'dapsa', 'sledai', 'das28')


# get the values for the selected test - fct takes a row and returns an array of two values

def get_iteration_values(row):
    sel_test_score = row['selected_test_score']    #this selects the test-score name from eth correct columns
    if pd.isna(sel_test_score):                    # checks if patient has a test score or is in the <NA> group
        return pd.Series([np.nan, np.nan], dtype=float)
    col1 = sel_test_score + '1'                     #adds a 1 to the test_score name (i.e. sdai1)
    col2 = sel_test_score + '2'
    return pd.Series([float(row[col1]), float(row[col2])], dtype=float)        #fetsches the values under test_score name1 (i.e. sdai1) and creates an array with two values

df[['iteration1', 'iteration2']] = df.apply(get_iteration_values, axis=1) #adds the array under columns iteration1 and iteration2


################ TEST SCORE NORMALISATION ##########################

for test_score in df['selected_test_score'].dropna().unique(): #for every unique test_score name in teh column that isn't missing
    mask = df['selected_test_score'] == test_score  #creates mask column that assigns True to a row that has the selected tes score in it
    values = pd.concat([                #stacks two columns in one long series
        df.loc[mask, 'iteration1'],     #mask basically is a condition & means 'the test_score in row is the test score we are looping with
        df.loc[mask, 'iteration2']
    ])
    min_val = values.min()
    max_val = values.max()
    range_val = max_val - min_val if max_val != min_val else 1  # avoid division by zero
    df.loc[mask, 'norm1'] = (df.loc[mask, 'iteration1'] - min_val) / range_val
    df.loc[mask, 'norm2'] = (df.loc[mask, 'iteration2'] - min_val) / range_val

# invert FFbH so higher = worse (same direction as VAS and Aktivität)
df['ffbh1_inv'] = 100 - df['ffbh1']
df['ffbh2_inv'] = 100 - df['ffbh2']

# normalise VAS-A, VAS-P, FFbH (inverted) to 0-1
for col1, col2 in [('vas1a', 'vas2a'), ('vas1p', 'vas2p'), ('ffbh1_inv', 'ffbh2_inv')]:
    values = pd.concat([df[col1], df[col2]]).dropna()
    min_val = values.min()
    max_val = values.max()
    range_val = max_val - min_val if max_val != min_val else 1
    df[col1.replace('1', '_norm1').replace('_inv', '')] = (df[col1] - min_val) / range_val
    df[col2.replace('2', '_norm2').replace('_inv', '')] = (df[col2] - min_val) / range_val

############ RESHAPING ADDITIONAL TABLE LONG FOR REGRESSION ANALYSIS ###################

pairs=[
    ('vas1a', 'vas2a'),
    ('vas1p', 'vas2p'),
    ('ffbh1', 'ffbh2'),
    ('norm1', 'norm2')
]

long_rows = []
for xante, xpost in pairs:
    for _, row in df.iterrows():
        if pd.notna(row[xante]) and pd.notna(row[xpost]):
            long_rows.append({
                'patnr': row['patnr'],
                'geschlecht': row['geschlecht'],
                'alter': row['alter'],
                'score_type': xante.replace('1', ''),
                'zeitpunkt': 'vorher',
                'score_value': row[xante]
            })
            long_rows.append({
                'patnr': row['patnr'],
                'geschlecht': row['geschlecht'],
                'alter': row['alter'],
                'score_type': xante.replace('1', ''),
                'zeitpunkt': 'nachher',
                'score_value': row[xpost]
            })

long_df = pd.DataFrame(long_rows)

############ EXPORTING SQLITE TABLES ###################

con = sqlite3.connect("data/rheuma_konf_2026.db")
df.to_sql("reshaped", con, if_exists="replace", index=False)
freq_df.to_sql("test_score_frequencies", con, if_exists="replace", index=True)
long_df.to_sql("long", con, if_exists="replace", index=False)
con.close()
