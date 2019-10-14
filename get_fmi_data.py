import requests
import xml.etree.ElementTree as ET
import pandas as pd
import dateutil.parser
import sys
import datetime
import ratelimit
import itertools

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

@ratelimit.sleep_and_retry
@ratelimit.limits(calls=600, period=300)
def make_request(params):
    @ratelimit.limits(calls=20000, period=60*60*24)
    def request_wrapper():
        return requests.get("http://opendata.fmi.fi/wfs/fin", params=params)
    return request_wrapper()

def get_data_for_period(params):
    airquality_response = make_request(params)
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

def get_aq_params(period, place):
    query_airquality = "urban::observations::airquality::hourly::timevaluepair"
    start_time, end_time = period
    return {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "starttime": start_time, "endtime": end_time,
        "storedquery_id": query_airquality, "place": place
    }

def get_weather_params(start_time, end_time, place):
    # Daily average temperature in Celcius
    temperature_code = "tday"
    # Daily rain sum in mm
    rain_code = "rrday"
    params = [temperature_code, rain_code]
    query_weather = "fmi::observations::weather::daily::timevaluepair"
    return {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "storedquery_id": query_weather, "place": place,
        "starttime": start_time, "endtime": end_time,
        "parameters": ",".join(params)
    }

def get_aq_data_for_place(place):
    dfs = [get_data_for_period(get_aq_params(period, place)) for period in generate_start_ends()]
    df = pd.concat(dfs)
    df = df.groupby("Year, Week").mean()
    return pd.DataFrame(df["fi-1-1-AQINDEX_PT1H_avg"]).transpose().assign(Municipality=place)

start_times = ["2019-01-01", "2018-01-01", "2017-10-01"]
end_times = ["2019-10-01", "2018-12-31", "2017-12-31"]
def get_weather_data_for_place(place):
    dfs = [get_data_for_period(get_weather_params(start_times[i], end_times[i], place)) for i in range(len(start_times))]
    df = pd.concat(dfs)
    df = df.groupby("Year, Week").mean()
    return (
        pd.DataFrame(df["fi-1-1-tday"]).transpose().assign(Municipality=place),
        pd.DataFrame(df["fi-1-1-rrday"]).transpose().assign(Municipality=place)
    )

places = ["Oulu", "Tampere", "Naantali", "Vaasa", "Raahe", "Lahti", "Helsinki", "Espoo"]
weather_calls = len(places) * len(start_times)
aq_calls = len(list(generate_start_ends())) * len(places)
print("Making {}/20000 calls".format(aq_calls + weather_calls))

dfs = [get_aq_data_for_place(place) for place in places]
aq_df = pd.concat(dfs).set_index("Municipality")
aq_df.to_csv("airquality.csv")

dfs = [get_weather_data_for_place(place) for place in places]
dftuple = [pd.concat(dflist) for dflist in zip(*dfs)]
temp_df = dftuple[0].set_index("Municipality")
temp_df.to_csv("temperature.csv")
rain_df = dftuple[1].set_index("Municipality")
rain_df.to_csv("rains.csv")
