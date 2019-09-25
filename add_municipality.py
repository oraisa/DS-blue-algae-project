import pandas as pd
import re
import numpy as np

df = pd.read_csv("thl_data.csv")
df = df[df.Provider != "TIETO PUUTTUU"]
topi = pd.read_excel("topi-2019-09-25.xlsx")

def get_code(row):
    m = re.search("\((\d+)\)", row.Provider)
    if m:
        return m.group(1)
    else:
        print(row.Provider)
        return np.nan

codes = df.apply(get_code, axis=1)
df["Code"] = codes.astype("int")

def get_municipality(row):
    code = row.Code
    places = topi[topi.tunnus == code].kunta
    if places.size > 0:
        return places.mode()[0]
    else: return np.nan

municipalities = df.apply(get_municipality, axis=1)
df["Municipality"] = municipalities
df.dropna(subset=["Municipality"], inplace=True)
df.fillna(0, inplace=True)
checkupsByMunicipality = df.drop("Code", axis=1).groupby("Municipality").sum()
checkupsByMunicipality.to_csv("checkupsByMunicipality.csv")
