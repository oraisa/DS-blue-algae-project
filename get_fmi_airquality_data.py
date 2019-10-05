import requests
import xml.etree.ElementTree as ET
import pandas as pd
import dateutil.parser
import sys
import datetime

query_airquality = "fmi::observations::airquality::hourly::timevaluepair"
place = "Tampere"

omso_prefix = "{http://inspire.ec.europa.eu/schemas/omso/3.0}"
om_prefix = "{http://www.opengis.net/om/2.0}"
wml2_prefix = "{http://www.opengis.net/waterml/2.0}"

def generate_start_ends():
    current = datetime.date(year=2017, month=10, day=1)
    cap = datetime.date(year=2019, month=10, day=1)
    while current < cap:
        next = current + datetime.timedelta(days=4)
        if next > cap: next = cap
        yield (current, next)
        current = next + datetime.timedelta(days=1)

def check_response(response):
    if not response.ok:
        print(response.status_code)
        print(response.text)
        sys.exit()

def get_data_for_period(period):
    start_time, end_time = period
    airquality_response = requests.get("http://opendata.fmi.fi/wfs/fin", params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "starttime": start_time, "endtime": end_time,
        "storedquery_id": query_airquality, "place": place
    })
    check_response(airquality_response)
    airquality_root = ET.fromstring(airquality_response.text)

    df = pd.DataFrame()
    for child in airquality_root:
        child = child.find(omso_prefix + "PointTimeSeriesObservation")

        feature_child = child.find(om_prefix + "featureOfInterest")
        feature_code = feature_child[0].get("{http://www.opengis.net/gml/3.2}id")

        result_child = child.find(om_prefix + "result").find(wml2_prefix + "MeasurementTimeseries")
        results = result_child.findall(wml2_prefix + "point")
        results = map(lambda result: result.find(wml2_prefix + "MeasurementTVP"), results)
        res_dict = {
            dateutil.parser.isoparse(measurement.find(wml2_prefix + "time").text):
            float(measurement.find(wml2_prefix + "value").text)
            for measurement in results
        }
        res_series = pd.Series(res_dict)
        df[feature_code] = res_series

    df["Year, Week"] = df.index.map(lambda dt: (dt.year, dt.isocalendar()[1]))
    return df

dfs = [get_data_for_period(period) for period in generate_start_ends()]
df = pd.concat(dfs)
df = df.groupby("Year, Week").mean()
df["fi-1-1-AQINDEX_PT1H_avg"].to_csv("airquality_tampere.csv")
