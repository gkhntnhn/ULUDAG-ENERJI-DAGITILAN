import requests_cache
from openmeteo_requests import Client
from retry_requests import retry
import pandas as pd
import math

pd.set_option("display.width", 50000)
pd.set_option("display.max_columns", None)


class HistoricalWeatherDataProcessor:
    def __init__(self, lat, lon, start_date, end_date, timezone="Europe/Istanbul"):
        self.lat = lat
        self.lon = lon
        self.start_date = start_date
        self.end_date = end_date
        self.timezone = timezone
        self.session = self._create_session()
        self.client = Client(session=self.session)
        self.weather_mapping = self._weather_mapping()
        self.weather_severity = self._weather_severity()

    def _create_session(self):
        cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
        return retry(cache_session, retries=5, backoff_factor=0.2)

    def _weather_mapping(self):
        return {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Drizzle: Light",
            53: "Drizzle: Moderate",
            55: "Drizzle: Dense intensity",
            56: "Freezing Drizzle: Light",
            57: "Freezing Drizzle: Dense intensity",
            61: "Rain: Slight",
            63: "Rain: Moderate",
            65: "Rain: Heavy intensity",
            66: "Freezing Rain: Light",
            67: "Freezing Rain: Heavy intensity",
            71: "Snow fall: Slight",
            73: "Snow fall: Moderate",
            75: "Snow fall: Heavy intensity",
            77: "Snow grains",
            80: "Rain showers: Slight",
            81: "Rain showers: Moderate",
            82: "Rain showers: Violent",
            85: "Snow showers: Slight",
            86: "Snow showers: Heavy",
            95: "Thunderstorm: Slight or moderate",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }

    def _weather_severity(self):
        return {
            "Clear sky": 0,
            "Mainly clear": 0,
            "Partly cloudy": 1,
            "Overcast": 1,
            "Fog": 2,
            "Depositing rime fog": 2,
            "Drizzle: Light": 3,
            "Drizzle: Moderate": 3,
            "Drizzle: Dense intensity": 3,
            "Freezing Drizzle: Light": 4,
            "Freezing Drizzle: Dense intensity": 4,
            "Rain: Slight": 5,
            "Rain: Moderate": 5,
            "Rain: Heavy intensity": 5,
            "Freezing Rain: Light": 6,
            "Freezing Rain: Heavy intensity": 6,
            "Snow fall: Slight": 7,
            "Snow fall: Moderate": 7,
            "Snow fall: Heavy intensity": 7,
            "Snow grains": 7,
            "Rain showers: Slight": 8,
            "Rain showers: Moderate": 8,
            "Rain showers: Violent": 8,
            "Snow showers: Slight": 9,
            "Snow showers: Heavy": 9,
            "Thunderstorm: Slight or moderate": 10,
            "Thunderstorm with slight hail": 10,
            "Thunderstorm with heavy hail": 10,
        }

    def _wind_direction_category(self, degree):
        if (degree >= 337.5) or (degree < 22.5):
            return "N"
        elif 22.5 <= degree < 67.5:
            return "NE"
        elif 67.5 <= degree < 112.5:
            return "E"
        elif 112.5 <= degree < 157.5:
            return "SE"
        elif 157.5 <= degree < 202.5:
            return "S"
        elif 202.5 <= degree < 247.5:
            return "SW"
        elif 247.5 <= degree < 292.5:
            return "W"
        elif 292.5 <= degree < 337.5:
            return "NW"

    def _calculate_hdd_cdd(self, temp, base_temp=18):
        return max(base_temp - temp, 0), max(temp - base_temp, 0)

    def _wind_chill(self, temp, wind_speed):
        return (
            13.12
            + 0.6215 * temp
            - 11.37 * (wind_speed**0.16)
            + 0.3965 * temp * (wind_speed**0.16)
        )

    def _categorize_features(self, df):
        df["wind_direction_10m"] = df["wind_direction_10m"].apply(
            self._wind_direction_category
        )
        df["temperature_cut"] = pd.qcut(
            df["temperature_2m"].rank(method="first"),
            10,
            labels=[f"temperature_level_{i}" for i in range(1, 11)],
        )
        df["humidity_cut"] = pd.qcut(
            df["relative_humidity_2m"].rank(method="first"),
            10,
            labels=[f"humidity_level_{i}" for i in range(1, 11)],
        )
        df["weather_code"] = df["weather_code"].replace(self.weather_mapping)
        return df

    def fetch(self):
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "apparent_temperature",
                "precipitation",
                "snow_depth",
                "weather_code",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "shortwave_radiation",
            ],
            "timezone": "auto",
        }

        response = self.client.weather_api(url, params=params)[0]
        hourly = response.Hourly()
        dates = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )

        data = {
            "date": dates,
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
            "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
            "dew_point_2m": hourly.Variables(2).ValuesAsNumpy(),
            "apparent_temperature": hourly.Variables(3).ValuesAsNumpy(),
            "precipitation": hourly.Variables(4).ValuesAsNumpy(),
            "snow_depth": hourly.Variables(5).ValuesAsNumpy(),
            "weather_code": hourly.Variables(6).ValuesAsNumpy(),
            "surface_pressure": hourly.Variables(7).ValuesAsNumpy(),
            "wind_speed_10m": hourly.Variables(8).ValuesAsNumpy(),
            "wind_direction_10m": hourly.Variables(9).ValuesAsNumpy(),
            "shortwave_radiation": hourly.Variables(10).ValuesAsNumpy(),
        }

        df = pd.DataFrame(data)
        df["date"] = df["date"].dt.tz_convert(self.timezone)

        df["daily_temp_range"] = df.groupby(df["date"].dt.date)[
            "temperature_2m"
        ].transform(lambda x: x.max() - x.min())
        df = self._categorize_features(df)
        df[["HDD", "CDD"]] = (
            df["temperature_2m"].apply(self._calculate_hdd_cdd).tolist()
        )
        df["precipitation_duration"] = (df["precipitation"] > 0).rolling(24).sum()
        df["wind_chill"] = df.apply(
            lambda row: self._wind_chill(row["temperature_2m"], row["wind_speed_10m"]),
            axis=1,
        )
        df["cumulative_precipitation_24h"] = df["precipitation"].rolling(24).sum()
        df["heat_index"] = df.apply(
            lambda row: row["temperature_2m"]
            if row["temperature_2m"] < 27
            else -42.379
            + 2.04901523 * row["temperature_2m"]
            + 10.14333127 * row["relative_humidity_2m"]
            - 0.22475541 * row["temperature_2m"] * row["relative_humidity_2m"]
            - 6.83783e-3 * row["temperature_2m"] ** 2
            - 5.481717e-2 * row["relative_humidity_2m"] ** 2
            + 1.22874e-3 * row["temperature_2m"] ** 2 * row["relative_humidity_2m"]
            + 8.5282e-4 * row["temperature_2m"] * row["relative_humidity_2m"] ** 2
            - 1.99e-6 * row["temperature_2m"] ** 2 * row["relative_humidity_2m"] ** 2,
            axis=1,
        )
        for lag in [1, 2, 3, 4, 5, 6, 24, 48]:
            df[f"temp_lag_{lag}h"] = df["temperature_2m"].shift(lag)
            df[f"humidity_lag_{lag}h"] = df["relative_humidity_2m"].shift(lag)

        df["weather_severity"] = df["weather_code"].map(self.weather_severity)
        df["weather_change_score"] = df["weather_severity"].diff().abs()
        df["temperature_humidity_cut"] = (
            df["temperature_cut"].astype(str) + "--" + df["humidity_cut"].astype(str)
        )

        return df
