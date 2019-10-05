import requests
import xml.etree.ElementTree as ET
import pandas as pd
import dateutil.parser
import sys

# Daily average temperature in Celcius
temperature_code = "tday"
# Daily rain sum in mm
rain_code = "rrday"
query_weather = "fmi::observations::weather::daily::timevaluepair"
place = "Tampere"
params = [temperature_code, rain_code]
start_times = ["2019-01-01", "2018-01-01", "2017-10-01"]
end_times = ["2019-10-01", "2018-12-31", "2017-12-31"]

omso_prefix = "{http://inspire.ec.europa.eu/schemas/omso/3.0}"
om_prefix = "{http://www.opengis.net/om/2.0}"
wml2_prefix = "{http://www.opengis.net/waterml/2.0}"

def check_response(response):
    if not response.ok:
        print(response.status_code)
        print(response.text)
        sys.exit()

def get_data_for_period(start_time, end_time):
    weather_response = requests.get("http://opendata.fmi.fi/wfs/fin", params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "storedquery_id": query_weather, "place": place,
        "starttime": start_time, "endtime": end_time,
        "parameters": ",".join(params)
    })
    check_response(weather_response)
    weather_root = ET.fromstring(weather_response.text)

    df = pd.DataFrame()
    for child in weather_root:
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
    return df.groupby("Year, Week").mean()

dfs = [get_data_for_period(start_times[i], end_times[i]) for i in range(len(start_times))]
df = pd.concat(dfs)
df["fi-1-1-tday"].to_csv("temperature_tampere.csv")
