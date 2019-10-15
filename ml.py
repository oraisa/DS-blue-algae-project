import pandas as pd
import numpy as np
import re
import datetime
import itertools
import sklearn.linear_model
import sklearn.svm
import sklearn.ensemble
import sklearn.preprocessing
import sklearn.pipeline
import sklearn.model_selection

visits = pd.read_csv("visits.csv")
algae = pd.read_csv("algae.csv")
temps = pd.read_csv("temperature.csv").set_index("Municipality")
rains = pd.read_csv("rains.csv").set_index("Municipality")
aqs = pd.read_csv("airquality.csv").set_index("Municipality")

population2018 = pd.read_csv("population2018.csv")
population2018.rename(columns={"Alue 2019": "Municipality"}, inplace=True)
population2018.drop(["Tiedot"], axis=1, inplace=True)
population2018.set_index("Municipality", inplace=True)
population2019 = pd.read_csv("population2019.csv")
population2019.rename(columns={"Alue": "Municipality", "Yhteensä Yhteensä Väkiluku": "2019"}, inplace=True)
population2019.drop(["Kuukausi"], axis=1, inplace=True)
population2019.set_index("Municipality", inplace=True)
population = pd.concat([population2018, population2019], axis=1, sort=True)
# temp_tampere = pd.read_csv("temperature_tampere.csv", header=None, names=["Time", "Temperature"])
# temp_tampere.set_index("Time", inplace=True)
# aq_tampere = pd.read_csv("airquality_tampere.csv", header=None, names=["Time", "Air Quality"])
# aq_tampere.set_index("Time", inplace=True)

def columns_rename_visits(col):
    match = re.match("(\d*)_(\d*)", col)
    if match:
        week = int(match.group(1))
        year = int(match.group(2))
        return (year, week)
    else:
        return col

def columns_rename_algae(col):
    match = re.match("\((\d*), (\d*)\)", col)
    if match:
        year = int(match.group(1))
        week = int(match.group(2))
        return (year, week)
    else:
        return col

visits.rename(inplace=True, columns=columns_rename_visits)
algae.rename(inplace=True, columns=columns_rename_algae)
visits.rename(inplace=True, columns={"Municipality": "municipality"})
visits.set_index("municipality", inplace=True)
algae.set_index("municipality", inplace=True)
# not_na_algae = algae[algae.apply(lambda row: row.isna().sum() <= 0, axis=1)]
# algae.fillna(0, inplace=True)

def underflow_year_week(year, week):
    if week <= 0:
        return (year - 1, 52 + week)
    else:
        return (year, week)

def get_data_week_and_two_previous(year_week, municipality, dataset):
    year = year_week[0]
    week = year_week[1]
    return [
        dataset.loc[municipality][underflow_year_week(year, w)]
        if underflow_year_week(year, w) in dataset.columns else 0
        for w in range(week, week - 4, -1)
    ]

algae_places = ["Oulu", "Tampere", "Naantali", "Vaasa", "Raahe", "Lahti"]
places = ["Oulu", "Tampere", "Naantali", "Vaasa", "Raahe", "Lahti", "Helsinki", "Espoo"]
iter = [
    get_data_week_and_two_previous(col, place, algae)
    + get_data_week_and_two_previous(col, place, temps)
    + get_data_week_and_two_previous(col, place, rains)
    + get_data_week_and_two_previous(col, place, aqs)
    # + [visits.loc[place].mean()]
    + [visits.loc[place][col] / population.loc[place][str(col[0])]]
    for col in visits.columns
    for place in algae_places
]
# iter = [
#     get_data_week_and_two_previous(col, temp_tampere)
#     + get_data_week_and_two_previous(col, aq_tampere)
#     + [algae.loc["Tampere"][col]]
#     for col in algae.columns
# ]
data = np.stack(iter)
features = data.shape[1]
X = data[:, 0:features - 1]
y = data[:, features - 1:features].reshape(data.shape[0])
X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y, random_state=44888776)

scaler = sklearn.preprocessing.StandardScaler()

lm = sklearn.linear_model.LinearRegression()
lm_pipe = sklearn.pipeline.Pipeline([("Scale", scaler), ("Model", lm)])
lm_pipe.fit(X_train, y_train)

forest = sklearn.ensemble.RandomForestRegressor(n_estimators=100, max_depth=3, random_state=4324)
forest_pipe = sklearn.pipeline.Pipeline([("Scale", scaler), ("Model", forest)])
forest_pipe.fit(X_train, y_train)

svm = sklearn.svm.SVR()
svm_pipe = sklearn.pipeline.Pipeline([("Scale", scaler), ("Model", svm)])
svm_pipe.fit(X_train, y_train)

print("Lm score: {}, {}".format(lm_pipe.score(X_train, y_train), lm_pipe.score(X_test, y_test)))
print("Forest score: {}, {}".format(forest_pipe.score(X_train, y_train), forest_pipe.score(X_test, y_test)))
print("SVM score: {}, {}".format(svm_pipe.score(X_train, y_train), svm_pipe.score(X_test, y_test)))
