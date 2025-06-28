from DataPrePare import DataPrepare
import pandas as pd
import catboost as cb
import time
import os

base = r"C:/Users/pc/Desktop/ULUDAG-ENERJI-DAGITILAN/"
data_path = r"data/raw/consumption.xlsx"
config_path = r"data/raw/config.json"
historical_path = r"data/processed/"
forecast_path = r"data/processed/"

result_path = r"result/"

DP = DataPrepare(data_path, config_path, historical_path, forecast_path)
df = DP.DataPrepareFunction(data_path, config_path, historical_path, forecast_path)

forecast = pd.read_parquet(base + forecast_path + "Forecast_Data.parquet")

model = cb.CatBoostRegressor()
model.load_model(base + "models/exp_model.cbm")


result = pd.DataFrame(
    model.predict(forecast.drop(columns=["consumption"])), columns=["consumption"]
).set_index(forecast.index)

now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
now = now.replace(":", "_")
now_day = time.strftime("%Y-%m-%d", time.localtime())


os.makedirs(base + result_path + now_day, exist_ok=True)

if __name__ == "__main__":
    result.to_excel(base + result_path + now_day + f"/Forecast_Results_{now}.xlsx")
    print(f"Forecasting completed and results saved to {now_day}/Forecast_Results_{now}.xlsx")