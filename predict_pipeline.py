import os
import glob
import shutil
import pandas as pd
import catboost as cb
from src.DataPrePare import DataPrepare

class ForecastPipeline:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.BASE_DIR, "utils", "config.json")
        # Flat directories with underscores
        self.historical_path = os.path.join(self.BASE_DIR, "data", "historical_data")
        self.forecast_path = os.path.join(self.BASE_DIR, "data", "forecast_data")
        self.model_path = os.path.join(self.BASE_DIR, "models", "exp_model.cbm")
        # Ensure directories exist (create if missing, do nothing if present)
        os.makedirs(self.historical_path, exist_ok=True)
        os.makedirs(self.forecast_path, exist_ok=True)
        # Initialize DataPrepare with new paths
        self.DP = DataPrepare(
            None, self.config_path, self.historical_path, self.forecast_path
        )

    def run(self, input_path: str, timestamp: str) -> pd.DataFrame:
        # Prepare data; returns DataFrame and raw forecast parquet path
        df, forecast_parquet = self.DP.DataPrepareFunction(
            input_path,
            self.config_path,
            self.historical_path,
            self.forecast_path,
        )

        # Move and rename forecast parquet to flat forecast_data folder
        forecast_target = os.path.join(self.forecast_path, f"{timestamp}_forecast_data.parquet")
        os.replace(forecast_parquet, forecast_target)

        # Handle nested historical parquet if present
        nested = glob.glob(os.path.join(self.historical_path, "*", "Historical_Data", "*.parquet"))
        if nested:
            orig_hist = nested[0]
            hist_target = os.path.join(self.historical_path, f"{timestamp}_historical_data.parquet")
            os.replace(orig_hist, hist_target)
            # Clean up nested folder
            nested_date_dir = os.path.dirname(os.path.dirname(orig_hist))
            shutil.rmtree(nested_date_dir, ignore_errors=True)
        else:
            # Fallback: write df to parquet
            hist_target = os.path.join(self.historical_path, f"{timestamp}_historical_data.parquet")
            df.to_parquet(hist_target)

        # Load forecast data and predict
        forecast_df = pd.read_parquet(forecast_target)
        model = cb.CatBoostRegressor()
        model.load_model(self.model_path)
        features = forecast_df.drop(columns=['consumption'], errors='ignore')
        predictions = model.predict(features)
        output_df = pd.DataFrame(predictions, columns=['Predicted_Consumption'], index=forecast_df.index)
        return output_df

if __name__ == '__main__':
    import sys
    from datetime import datetime
    import pytz

    if len(sys.argv) < 2:
        print("Usage: python predict_pipeline.py <input_path>")
        exit(1)

    tz = pytz.timezone('Europe/Istanbul')
    timestamp = datetime.now(tz).strftime('%d_%m_%Y_%H_%M')
    pipeline = ForecastPipeline()
    df = pipeline.run(sys.argv[1], timestamp)
    # Include index in Excel
    df.to_excel(f"{timestamp}_output.xlsx")
    print("Forecasting completed.")
