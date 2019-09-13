import numpy as np
import pandas as pd
import json

class Site:
    def __init__(self, id, area, municipality, water_body):
        self.id = id
        self.area = area
        self.municipality = municipality
        self.water_body = water_body
        self.weeks = {}

    def add_week(self, week, level):
        if week in self.weeks:
            if self.weeks[week] != level:
                print("Conflicted measurement ({} vs {}) for week {} in {} ({})".format(
                    level, self.weeks[week], week, self.area, self.id
                ))
        else:
            self.weeks[week] = level

    def get_dict_record(self):
        dict = self.weeks
        dict["area"] = self.area
        dict["municipality"] = self.municipality
        return dict

results = {}
for year in range(1998, 2019 + 1):
    with open("data{}.json".format(year)) as file:
        data = json.load(file)
        if "warnings" in data:
            print(data["warnings"])
        results.update(data["query"]["results"])

# results = data["query"]["results"]
sites = {}
for result_key in results:
    res = results[result_key]["printouts"]

    # For some reason all the values in the json are in arrays,
    # check that the arrays only have one value each
    if len(res["SiteID"]) != 1:
        print("Id length {} for {}".format(len(res["SiteID"]), res["SiteID"]))
        continue
    if len(res["Kunta"]) != 1:
        print("Kunta length {} for {}".format(len(res["Kunta"]), res["SiteID"][0]))
        continue
    if len(res["Vesistö"]) != 1:
        print("Vesistö length {} for {}".format(len(res["Vesistö"]), res["SiteID"][0]))
        continue
    if len(res["Alue"]) != 1:
        print("Alue length {} for {}".format(len(res["Alue"]), res["SiteID"][0]))
        continue
    if len(res["Levätilanne"]) != 1:
        print("Levätilanne length {} for {}".format(len(res["Levätilanne"]), res["SiteID"][0]))
        continue
    if len(res["Viikko"]) != 1:
        print("Viikko length {} for {}".format(len(res["Viikko"]), res["SiteID"][0]))
        continue

    id = res["SiteID"][0]
    if id not in sites:
        area = res["Alue"][0]["fulltext"]
        municipality = res["Kunta"][0]["fulltext"]
        water_body = res["Vesistö"][0]
        sites[id] = Site(id, area, municipality, water_body)
    sites[id].add_week((res["Vuosi"][0], res["Viikko"][0]), res["Levätilanne"][0])

df = pd.DataFrame.from_dict({id: sites[id].get_dict_record() for id in sites}, orient="index")
columns = df.columns
other_columns = ["area", "municipality"]
columns = list(filter(lambda s: s not in other_columns, columns))
columns.sort()
df = df.reindex(columns=other_columns + columns)
df = df.sort_values(by=["area"])
df.to_csv("data.csv")
