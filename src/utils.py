import pandas as pd

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

###### GROUPS & VARIABLES

#build aggregate diagnose gruppen
hauptgruppen = ['L40', 'M05', 'M06', 'M45']

def build_diagnose_gruppe(df):
    df['hd_basis'] = df['hd'].str.split('.').str[0] #create Basisdiagnose column
    df['diagnose_gruppe'] = df['hd_basis'].apply(   #For each value x in the split series
        lambda x: x if x in hauptgruppen else 'Sonstige'    #if it's in hauptgruppen keep it as is, otherwise replace with 'Sonstige'.
    )
    return df

# Core score pairs — used across analysis and regression files
score_pairs = [
    ('vas1a', 'vas2a', 'vasa'),
    ('vas1p', 'vas2p', 'vasp'),
    ('ffbh1', 'ffbh2', 'ffbh'),
    ('norm1', 'norm2', 'norm')
]

score_labels = {
    'vas1a': 'VAS-A',
    'vas1p': 'VAS-P',
    'ffbh1': 'FFbH',
    'norm1': 'Aktivität'
}
