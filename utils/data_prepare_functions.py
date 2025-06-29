import pandas as pd
from functools import reduce
from src.historical_weather_data import HistoricalWeatherDataProcessor
from src.forecast_weather_data import ForecastWeatherDataProcessor
import time 
import os


class DataPrepareFunctions:
    def __init__(self):
        self.current_time = time.strftime("%Y_%m_%d %H_%M_%S", time.localtime())
        self.current_day = time.strftime("%Y_%m_%d", time.localtime())
        pass

    def prepare_weather_data(self, historical_weather_df, forecast_weather_df):
        weather_df = pd.concat(
            [historical_weather_df, forecast_weather_df], ignore_index=True
        )
        return weather_df.reset_index(drop=True)

    def main_data_prepare(
        self, data, consumption, epias_df, solar_df, calendar_df, weather_df, weighted_weather_df
    ):
        dataframes = [
            data,
            consumption,
            epias_df,
            solar_df,
            calendar_df,
            weather_df,
            weighted_weather_df,
        ]
        # Tüm dataframe'lerdeki 'date' sütunlarının timezone'unu kaldır
        for i in range(len(dataframes)):
            if pd.api.types.is_datetime64tz_dtype(dataframes[i]["date"]):
                dataframes[i]["date"] = dataframes[i]["date"].dt.tz_localize(None)
        df = reduce(
            lambda left, right: pd.merge(left, right, on="date", how="inner"),
            dataframes,
        )
        df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M")
        df = df.set_index("date")

        return df

    def process_save_main_data(self, df, historical_df_path, forecast_df_path):

        day_folder = os.path.join(historical_df_path, self.current_day)

        # Create directories if they do not exist
        os.makedirs(day_folder, exist_ok=True)

        historical_df_path = os.path.join(day_folder, "Historical_Data")
        forecast_df_path = os.path.join(day_folder, "Forecast_Data")

        os.makedirs(historical_df_path, exist_ok=True)
        os.makedirs(forecast_df_path, exist_ok=True)

        cat_cols = df.select_dtypes(exclude="number").columns
        num_cols = df.select_dtypes(include="number").columns

        df[cat_cols] = df[cat_cols].astype("category")
        df[num_cols] = df[num_cols].astype("float")

        bool_cols = df.columns[df.nunique() == 2]
        df[bool_cols] = df[bool_cols].apply(lambda x: x.astype(bool))

        historical_df = df.iloc[:-48, :].copy()
        historical_df.to_parquet(historical_df_path + "/Historical_Data_" + self.current_time + ".parquet")
        forecast_df = df.iloc[-48:, :].copy()
        forecast_df.to_parquet(forecast_df_path + "/Forecast_Data_" + self.current_time + ".parquet")
        forecast_df_result_path = forecast_df_path + "/Forecast_Data_" + self.current_time + ".parquet"
        return df,forecast_df_result_path

    def generate_multi_location_weather_data(self, config):
        weather_dfs = []

        for location_name, coords in config["locations"].items():
            # --- Historical ---
            h_weather_cfg = config["historical_weather"]
            historical_data_processor = HistoricalWeatherDataProcessor(
                lat=coords["lat"],
                lon=coords["long"],
                start_date=h_weather_cfg["h_start_date"],
                end_date=h_weather_cfg["h_end_date"],
                timezone=h_weather_cfg["timezone"],
            )
            historical_df = historical_data_processor.fetch()

            # --- Forecast ---
            f_weather_cfg = config["forecast_weather"]
            forecast_data_processor = ForecastWeatherDataProcessor(
                lat=coords["lat"],
                lon=coords["long"],
                start_date=f_weather_cfg["f_start_date"],
                end_date=f_weather_cfg["f_end_date"],
                timezone=f_weather_cfg["timezone"],
            )
            forecast_df = forecast_data_processor.fetch()

            # --- Merge both & rename ---
            merged_weather = self.prepare_weather_data(historical_df, forecast_df)

            renamed_weather = merged_weather.rename(
                columns={
                    col: f"{col}_{location_name}" if col != "date" else col
                    for col in merged_weather.columns
                }
            )

            weather_dfs.append(renamed_weather)

        # --- Merge all on 'date'
        weather_df_final = weather_dfs[0]
        for df in weather_dfs[1:]:
            weather_df_final = pd.merge(weather_df_final, df, on="date", how="outer")

        return weather_df_final.reset_index(drop=True)

    def weighted_average_weather_data(self, weather_df, location_weights):
        weather_df = weather_df.copy()

        # Ortak zaman indeksini al (zaten tüm lokasyonlarda ortak)
        base_df = pd.DataFrame({"date": weather_df["date"]})

        # Sadece sayısal sütunlar
        numeric_cols = [
            col
            for col in weather_df.columns
            if col != "date" and pd.api.types.is_numeric_dtype(weather_df[col])
        ]

        # Her bir ölçüm (örneğin temperature_2m) için
        for base_col in set(c.rsplit("_", 1)[0] for c in numeric_cols):
            # İlgili şehirli tüm kolonları bul
            cols_for_feature = [
                col for col in numeric_cols if col.startswith(base_col + "_")
            ]

            # Ağırlık vektörünü oluştur
            weights = [location_weights.get(col.rsplit("_", 1)[-1], 0) for col in cols_for_feature]
            feature_matrix = weather_df[cols_for_feature].values

            # Ağırlıklı ortalamayı vektörize şekilde hesapla
            weighted_sum = (feature_matrix * weights).sum(axis=1)

            # Yeni isimle ekle
            base_df[base_col + "_mixed"] = weighted_sum

        return base_df
