import pandas as pd
import numpy as np
# Data can be downloaded from
# https://sampo.thl.fi/pivot/prod/fi/avopika/pikarap01/fact_ahil_pikarap01.csv?row=palveluntuottaja-349235L&column=viikko-349531L

raw_df = pd.read_csv("fact_ahil_pikarap01.csv", sep=";")
providers = raw_df.Palveluntuottaja.value_counts().index.sort_values()

weeks_by_provider = (raw_df[raw_df.Palveluntuottaja == key].val for key in providers)
data = np.stack(weeks_by_provider)
week_list = list(raw_df[raw_df.Palveluntuottaja == providers[0]].Viikko)
week_list = map(lambda x: "{}_{}".format(x[1], 2018 if x[0] <= 51 else 2019), enumerate(week_list))
df = pd.DataFrame(data, index=providers, columns=week_list)
df.to_csv("thl_data.csv")
