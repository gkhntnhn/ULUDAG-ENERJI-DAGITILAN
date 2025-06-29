from DataPrePare import DataPrepare
import pandas as pd
import catboost as cb
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

data_path = os.path.join(BASE_DIR, "data", "raw", "consumption.xlsx")
config_path = os.path.join(BASE_DIR, "data", "raw", "config.json")
historical_path = os.path.join(BASE_DIR, "data", "processed")
forecast_path = os.path.join(BASE_DIR, "data", "processed")

result_path = os.path.join(BASE_DIR, "result")

DP = DataPrepare(data_path, config_path, historical_path, forecast_path)
df = DP.DataPrepareFunction(data_path, config_path, historical_path, forecast_path)

forecast = pd.read_parquet(os.path.join(BASE_DIR, forecast_path, "Forecast_Data.parquet"))

model = cb.CatBoostRegressor()
model.load_model(os.path.join(BASE_DIR, "models","exp_model.cbm"))


result = pd.DataFrame(
    model.predict(forecast.drop(columns=["consumption"])), columns=["consumption"]
).set_index(forecast.index)

now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
now = now.replace(":", "_")
now_day = time.strftime("%Y-%m-%d", time.localtime())


os.makedirs(os.path.join(BASE_DIR, result_path, now_day), exist_ok=True)

if __name__ == "__main__":
    result.to_excel(os.path.join(BASE_DIR, result_path, now_day, f"Forecast_Results_{now}.xlsx"))
    print(f"Forecasting completed and results saved to {now_day}/Forecast_Results_{now}.xlsx")