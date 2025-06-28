from DataPrePare import DataPrepare
import pandas as pd
import catboost as cb


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

if __name__ == "__main__":
    result.to_excel(base + result_path + "Forecast_Results.xlsx")
    print("Forecasting completed and results saved to Forecast_Results.xlsx")