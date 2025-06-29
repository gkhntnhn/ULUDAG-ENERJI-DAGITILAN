from src.DataPrePare import DataPrepare
import pandas as pd
import catboost as cb
import time
import os


class ForecastPipeline:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.data_path = os.path.join(self.BASE_DIR, "input", "consumption.xlsx")
        self.config_path = os.path.join(self.BASE_DIR, "utils", "config.json")
        self.historical_path = os.path.join(self.BASE_DIR, "data")
        self.forecast_path = os.path.join(self.BASE_DIR, "data")
        self.input_path = os.path.join(self.BASE_DIR, "input")
        self.output_path = os.path.join(self.BASE_DIR, "output")

        self.current_time = None
        self.current_day = None

        #self.current_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        #self.current_day = time.strftime("%Y_%m_%d", time.localtime())

        # DataPrepare instance
        self.DP = DataPrepare(
            self.data_path, self.config_path, self.historical_path, self.forecast_path
        )

    def run(self):
        # Prepare data
        df, forecast_df_result_path = self.DP.DataPrepareFunction(
            self.data_path,
            self.config_path,
            self.historical_path,
            self.forecast_path,
        )

        # Load forecast data
        forecast = pd.read_parquet(forecast_df_result_path)
        # Load model
        model = cb.CatBoostRegressor()
        model.load_model(os.path.join(self.BASE_DIR, "models", "exp_model.cbm"))

        # Predict
        output = pd.DataFrame(
            model.predict(forecast.drop(columns=["consumption"])),
            columns=["consumption"],
        ).set_index(forecast.index)

        # Save results
        day_folder = os.path.join(self.output_path, self.current_day)
        os.makedirs(day_folder, exist_ok=True)

        file_path = os.path.join(
            day_folder, f"Forecast_Results_{self.current_time}.xlsx"
        )
        output.to_excel(file_path)

        print(f"Forecasting completed and results saved to {file_path}")


if __name__ == "__main__":
    pipeline = ForecastPipeline()
    pipeline.run()