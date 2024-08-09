from datetime import datetime
from functools import cache

from meteostat import Point, Hourly

HOME_LAT_LON = 35.935069, 14.491261
SICILY_LAT_LON = 36.7228304, 14.8160372


def get_all_locations():
    return {
        'malta': HOME_LAT_LON,
        'sicily': SICILY_LAT_LON,
    }


@cache
def _get_weather(lat, lon, dt) -> tuple:
    loc = Point(lat, lon, 70)
    dt = datetime(dt.year, dt.month, dt.day, dt.hour)
    try:
        res = Hourly(loc, dt, dt).fetch().iloc[0]
    except IndexError:
        print(f'No weather data for on {dt}@{lat},{lon}')
        return None, None, None, None, None, None, None
    return res.temp, res.dwpt, res.rhum, res.prcp, res.wdir, res.wspd, res.pres


def get_geo_weather(x, lat_lon: tuple[float, float] = None) -> tuple:
    release_dt = x['release_datetime']
    lat, lon = lat_lon or (x['latitude'], x['longitude'])
    return _get_weather(lat, lon, release_dt)
