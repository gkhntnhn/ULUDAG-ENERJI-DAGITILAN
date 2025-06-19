# -----------------------------
# Data Preparation Script
# -----------------------------
from src.data_loader import DataLoader
from src.epias_data import EpiasDataProcessor
from src.solar_data import SolarDataProcessor
from src.calendar_data import CalendarDataProcessor
from src.historical_weather_data import HistoricalWeatherDataProcessor
from src.forecast_weather_data import ForecastWeatherDataProcessor
from utils.data_prepare_config import data_prepare_config
from utils.data_prepare_functions import DataPrepareFunctions
import pandas as pd
import warnings

# -----------------------------

# -----------------------------
# Global Configurations
# -----------------------------
warnings.filterwarnings("ignore")
# -----------------------------

data_path = r"data\raw\consumption.xlsx"
config_path = r"data\raw\config.json"

def DataPrepare(data_path, config_path):
    """
    Main function to prepare data.
    This function orchestrates the data loading, processing, and saving.
    """
    # -----------------------------
    # Data Loader
    # -----------------------------
    data_loader = DataLoader(file_path=data_path)
    data = data_loader.load_excel()
    # -----------------------------

    # -----------------------------
    # Konfigürasyonu yükle
    # -----------------------------
    config = data_prepare_config(config_path, data_df=data)
    # -----------------------------

    # -----------------------------
    # Epias Data
    # -----------------------------
    epias_cfg = config["epias"]
    epias_processor = EpiasDataProcessor()
    epias_df_raw = epias_processor.create_epias(
        username=epias_cfg["username"],
        password=epias_cfg["password"],
        start_year=epias_cfg["start_year"],
        start_month=epias_cfg["start_month"],
        start_date=epias_cfg["start_date"],
        end_date=epias_cfg["end_date"],
        company_name=epias_cfg["company_name"],
        reading_type=epias_cfg["reading_type"],
    )

    epias_proc = epias_cfg["process"]
    epias_df = epias_processor.epias_processor(
        epias_df_raw,
        epias_proc["epias_periods"],
        epias_proc["epias_variables"],
        epias_proc["epias_functions"],
        epias_proc["epias_window"],
        epias_proc["pk_path"],
        epias_proc["start_date"],
    )
    # -----------------------------

    # -----------------------------
    # Solar Data
    # -----------------------------
    solar_cfg = config["solar"]
    solar_processor = SolarDataProcessor(
        lat=solar_cfg["lat"],
        long=solar_cfg["long"],
        alt=solar_cfg["alt"],
        timezone=solar_cfg["timezone"],
    )

    solar_df = solar_processor.process_data(
        start_date=solar_cfg["start_date"], end_date=solar_cfg["end_date"]
    )
    # -----------------------------

    # -----------------------------
    # Calendar Data
    # -----------------------------
    calendar_processor = CalendarDataProcessor()
    calendar_df = calendar_processor.process_calendar_data(
        start_date=config["calendar"]["start_date"], end_date=config["calendar"]["end_date"]
    )
    # -----------------------------

    # -----------------------------
    # Historical Weather Data
    # -----------------------------
    h_weather_cfg = config["historical_weather"]

    historical_data_processor = HistoricalWeatherDataProcessor(
        lat=h_weather_cfg["lat"],
        lon=h_weather_cfg["long"],
        start_date=h_weather_cfg["h_start_date"],
        end_date=h_weather_cfg["h_end_date"],
        timezone=h_weather_cfg["timezone"],
    )

    historical_weather_df = historical_data_processor.fetch()
    # -----------------------------

    # -----------------------------
    # Forecast Weather Data
    # -----------------------------
    f_weather_cfg = config["forecast_weather"]

    forecast_data_processor = ForecastWeatherDataProcessor(
        lat=f_weather_cfg["lat"],
        lon=f_weather_cfg["long"],
        start_date=f_weather_cfg["f_start_date"],
        end_date=f_weather_cfg["f_end_date"],
        timezone=f_weather_cfg["timezone"],
    )

    forecast_weather_df = forecast_data_processor.fetch()
    # -----------------------------

    # -----------------------------
    # Prepare Weather Data
    # -----------------------------
    prepare_functions = DataPrepareFunctions()
    weather_df = prepare_functions.prepare_weather_data(
        historical_weather_df, forecast_weather_df
    )
    # -----------------------------


    # -----------------------------
    # Prepare Main Data
    # -----------------------------
    df = prepare_functions.main_data_prepare(
        data, epias_df, solar_df, calendar_df, weather_df
    )
    # -----------------------------

    # -----------------------------
    # Process and Save Main Data
    # -----------------------------
    df = prepare_functions.process_save_main_data(
        df, r"data//processed//", r"data//processed//"
    )
    # -----------------------------
    print("Data preparation and saving completed successfully.")

if __name__ == "__main__":
    DataPrepare(data_path, config_path)
    print("Data preparation script executed successfully.")



