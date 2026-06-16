import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

file_path ="data/original_Jan2026_do_not_touch.xlsx" #source
corrections_path ="data/updated_duplicate_rows.xlsx" #corrected duplicates

df = pd.read_excel(file_path, sheet_name="Daten", dtype=object) #load data into a dataframe (df)
df_corrections = pd.read_excel(corrections_path, dtype=object) #load corrections

########DROPPING duplicates & merging researcher corrected data###################

df = df[~df['Pat.Nr'].duplicated(keep=False)] #delete duplicates of Pat.Nr
df = pd.concat([df, df_corrections], ignore_index=True) #append corrected duplicate entries

########CLEANING##########

df.dropna(how='all', inplace=True) #ignore fully empty rows
df.rename(columns={'Pat.Nr': 'patnr'}, inplace=True)
df.columns = df.columns.str.lower() #everything lowercase
df.replace('', np.nan, inplace=True) #replace blanks with missing (NaN)

#replace , with .
cols_with_comma = ['hd', 'ffbh1', 'ffbh2', 'basfi1', 'basfi2', 'basdai1', 'basdai2',
                          'sdai1', 'sdai2', 'dapsa1', 'dapsa2', 'sledai1', 'sledai2',
                          'das281', 'das282']
for col in cols_with_comma:
    df[col] = df[col].astype(str).str.replace(',', '.', regex=False) #cast as string and replace
    df[col] = df[col].replace('nan', np.nan)

#correct minor data-entry errors
df['hd'] = df['hd'].astype(str).str.replace('LL40.5', 'L40.5', regex=False) \
                                .str.replace(r'L40\.$', 'L40', regex=True) \
                                .str.replace(r'\bM5\b', 'M05', regex=True)
df.loc[df['hd'] == 'M15.9', 'hd'] = 'M06'

# patient with sdai baseline inconsistent with patient-reported scores (sdai1=2.3, sdai2=19.8)
# excluded from test score analysis only
df.loc[(df['sdai1'] == '2.3') & (df['sdai2'] == '19.8'), ['sdai1', 'sdai2']] = np.nan


#fix accidental datetime coded entries that should be decimals
# basfi2: '2026-03-09 00:00:00', -> 9.3
# sdai2:'2026-02-09 00:00:00' -> 9.2
# dapsa1:'2026-05-30 00:00:00'-> 30.5 and '1900-01-17 07:12:00 ->16.1'

def fix_datetime(val):
    if not isinstance(val, str):
        return val
    try:
        dt = datetime.strptime(val.strip(), '%Y-%m-%d %H:%M:%S')
        day = dt.day
        month = dt.month
        if dt.hour > 0 or dt.minute > 0:
            day = day - 1  # heuristic: time component caused Excel to round up by one day
            # confirmed affected value: dapsa1 '1900-01-17 07:12:00' -> 16.1
        return float(f"{day}.{month}")
    except ValueError:
        return val

for col in ['basfi2', 'sdai2', 'dapsa1']:
    df[col] = df[col].apply(fix_datetime)

########CASTING TYPES##########

df['patnr'] = df['patnr'].astype(int)
df['alter'] = df['alter'].astype(int)
df['geschlecht'] = df['geschlecht'].astype(str)
df[['vas1p', 'vas1a', 'vas2p', 'vas2a']] = df[['vas1p', 'vas1a', 'vas2p', 'vas2a']].astype(int)
df[['ffbh1', 'ffbh2', 'basfi1', 'basfi2', 'basdai1', 'basdai2', 'sdai1', 'sdai2', 'dapsa1', 'dapsa2',
    'sledai1', 'sledai2', 'das281', 'das282']] = df[['ffbh1', 'ffbh2', 'basfi1', 'basfi2', 'basdai1',
    'basdai2', 'sdai1', 'sdai2', 'dapsa1', 'dapsa2', 'sledai1', 'sledai2', 'das281', 'das282']].astype(float)


########## WRITE TO SQLITE #########

con = sqlite3.connect("data/rheuma_konf_2026.db") # connection object stored as con
df.to_sql("ingest", con, if_exists="replace", index=False) #df transformed to ingest
con.close()
