import pandas as pd 
from functools import reduce

class PrepareFunctions:
    def __init__(self):
        pass

    def prepare_weather_data(self, historical_weather_df, forecast_weather_df):
        weather_df = pd.concat([historical_weather_df, forecast_weather_df], ignore_index=True)
        return weather_df.reset_index(drop=True)
    
    def main_data_prepare(self, data, epias_df, solar_df, calendar_df, weather_df):
        dataframes = [data, epias_df, solar_df, calendar_df, weather_df]
            # Tüm dataframe'lerdeki 'date' sütunlarının timezone'unu kaldır
        for i in range(len(dataframes)):
            if pd.api.types.is_datetime64tz_dtype(dataframes[i]["date"]):
                dataframes[i]["date"] = dataframes[i]["date"].dt.tz_localize(None)
        df  = reduce(lambda left, right: pd.merge(left, right, on='date', how='inner'), dataframes)
        df["date"] = df["date"].dt.strftime('%Y-%m-%d %H:%M')
        df  = df.set_index("date")

        return df.reset_index(drop=True)
    
    def process_save_main_data(self, df,historical_df_path, forecast_df_path):
        cat_cols = df.select_dtypes(exclude="number").columns
        num_cols = df.select_dtypes(include="number").columns

        df[cat_cols] = df[cat_cols].astype('category')
        df[num_cols] = df[num_cols].astype('float')

        bool_cols = df.columns[df.nunique() == 2]
        df[bool_cols] = df[bool_cols].apply(lambda x: x.astype(bool))

        historical_df = df.iloc[:-48,:].copy()
        historical_df.to_parquet(historical_df_path + "Historical_Data.parquet")
        forecast_df = df.iloc[-48:,:].copy()
        forecast_df.to_parquet(forecast_df_path + "Forecast_Data.parquet")
        return df