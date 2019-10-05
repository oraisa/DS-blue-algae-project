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
temp_tampere = pd.read_csv("temperature_tampere.csv", header=None, names=["Time", "Temperature"])
temp_tampere.set_index("Time", inplace=True)
aq_tampere = pd.read_csv("airquality_tampere.csv", header=None, names=["Time", "Air Quality"])
aq_tampere.set_index("Time", inplace=True)

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
# visits = visits[algae.columns]
visits.set_index("municipality", inplace=True)
algae.set_index("municipality", inplace=True)
algae.fillna(0, inplace=True)

def underflow_year_week(year, week):
    if week <= 0:
        return (year - 1, 52 + week)
    else:
        return (year, week)
def get_data_week_and_two_previous(year_week, dataset):
    year, week = year_week
    return [dataset.loc[str(underflow_year_week(year, w))].values[0] for w in range(week, week - 5, -1)]

def get_algae_week_and_two_previous(year_week, municipality):
    def is_column_in_algae(year, week):
        if year == 2018: return 23 <= week <= 39
        else: return 23 <= week <= 37
    year = year_week[0]
    week = year_week[1]
    return [algae.loc[municipality][(year, w)] if is_column_in_algae(year, w) else 0 for w in range(week, week - 5, -1)]

# iter = [
#     get_algae_week_and_two_previous(col, "Tampere")
#     + get_data_week_and_two_previous(col, temp_tampere)
#     + get_data_week_and_two_previous(col, aq_tampere)
#     + [visits.loc["Tampere"][col]]
#     for col in visits.columns
# ]
iter = [
    get_data_week_and_two_previous(col, temp_tampere)
    + get_data_week_and_two_previous(col, aq_tampere)
    + [algae.loc["Tampere"][col]]
    for col in algae.columns
]
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
