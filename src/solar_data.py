import pandas as pd
import pvlib
import numpy as np
from functools import reduce


class SolarDataProcessor:
    def __init__(self, lat, long, alt, timezone="Europe/Istanbul"):
        """
        Initialize the solar data processor with location parameters.

        Args:
            lat (float): Latitude in degrees
            long (float): Longitude in degrees
            alt (float): Altitude in meters
            timezone (str): Timezone string, default is 'Europe/Istanbul'
        """
        self.lat = lat
        self.long = long
        self.alt = alt
        self.timezone = timezone
        self.location = pvlib.location.Location(lat, long, timezone, alt)

    def process_data(self, start_date, end_date):
        """
        Process solar data for the given date range.

        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: Processed solar data with additional features
        """
        # Create hourly time range
        times = pd.date_range(start_date, end_date, freq="h", tz=self.timezone)

        # Get clear-sky data
        clear_sky = self.location.get_clearsky(times)
        solar_position_data = self.location.get_solarposition(times)

        # Calculate radian values for solar angles
        solar_position_data["apparent_zenith_radian"] = np.radians(
            solar_position_data["apparent_zenith"]
        )
        solar_position_data["azimuth_radian"] = np.radians(
            solar_position_data["azimuth"]
        )

        # Calculate sunrise and sunset times
        solar_position_data["sunrise"] = solar_position_data["apparent_zenith"].apply(
            lambda x: x < 90
        )
        solar_position_data["sunset"] = solar_position_data["apparent_zenith"].apply(
            lambda x: x >= 90
        )

        # Calculate daylight duration
        solar_position_data["daylight"] = solar_position_data["sunrise"].astype(
            int
        ) - solar_position_data["sunset"].astype(int)
        solar_position_data["daylight_hours"] = solar_position_data["daylight"].cumsum()

        # Merge clear-sky and solar position data
        clear_sky.reset_index(inplace=True)
        solar_position_data.reset_index(inplace=True)
        dfs = [clear_sky, solar_position_data]
        solar_data = reduce(
            lambda left, right: pd.merge(left, right, on="index", how="inner"), dfs
        )
        solar_data.rename(columns={"index": "date"}, inplace=True)

        return self._add_features(solar_data)

    def _add_features(self, solar_data):
        """
        Add additional features to the solar data.

        Args:
            solar_data (pd.DataFrame): Base solar data

        Returns:
            pd.DataFrame: Enhanced solar data with additional features
        """
        # Determine daylight hours (0: night, 1: day)
        solar_data["is_day"] = solar_data["apparent_zenith"] < 90

        # Calculate cumulative radiation (daily)
        solar_data["cumulative_ghi"] = solar_data["ghi"].cumsum()

        # Create categories based on sun angle (morning, noon, evening)
        solar_data["sun_position"] = pd.cut(
            solar_data["apparent_zenith"],
            bins=[0, 30, 60, 90, 180],
            labels=["Morning", "Midday", "Afternoon", "Night"],
            right=False,
        )

        # Categorize azimuth angle (directions)
        solar_data["azimuth_direction"] = pd.cut(
            solar_data["azimuth"],
            bins=[0, 22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5, 360],
            labels=[
                "North",
                "North-East",
                "East",
                "South-East",
                "South",
                "South-West",
                "West",
                "North-West",
                "North",
            ],
            include_lowest=True,
            right=False,
            ordered=False,
        )

        # Categorize elevation angle
        solar_data["elevation_category"] = pd.cut(
            solar_data["elevation"],
            bins=[-90, 0, 30, 60, 90],
            labels=["Night", "Low", "Medium", "High"],
            include_lowest=True,
        )

        # Categorize equation of time
        solar_data["equation_of_time_category"] = pd.cut(
            solar_data["equation_of_time"],
            bins=[-float("inf"), -1, 1, float("inf")],
            labels=["Negative", "Neutral", "Positive"],
            include_lowest=True,
        )

        # Add rolling and expanding features
        solar_data["ghi_rolling_12h"] = solar_data["ghi"].rolling(window=12).mean()
        solar_data["daily_daylight_hours"] = solar_data.groupby(
            solar_data["date"].dt.date
        )["is_day"].transform("sum")
        solar_data["dni_rolling_12h"] = solar_data["dni"].rolling(window=12).mean()
        solar_data["dhi_rolling_12h"] = solar_data["dhi"].rolling(window=12).mean()

        return solar_data
