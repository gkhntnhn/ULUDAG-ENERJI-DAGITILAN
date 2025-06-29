# -----------------------------
# Data Preparation Script
# -----------------------------
from src.data_loader import DataLoader
from src.epias_data import EpiasDataProcessor
from src.solar_data import SolarDataProcessor
from src.calendar_data import CalendarDataProcessor
from utils.data_prepare_config import data_prepare_config
from utils.data_prepare_functions import DataPrepareFunctions
import pandas as pd
import warnings
import os

# -----------------------------

# -----------------------------
# Global Configurations
# -----------------------------
warnings.filterwarnings("ignore")
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DataPrepare:
    """
    Class to handle data preparation tasks.
    This class orchestrates the loading, processing, and saving of data.
    """

    def __init__(self, data_path, config_path, historical_path, forecast_path):
        self.data_path = data_path
        self.config_path = config_path
        self.historical_path = historical_path
        self.forecast_path = forecast_path

    def DataPrepareFunction(
        self, data_path, config_path, historical_path, forecast_path
    ):
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
        prepare_functions = DataPrepareFunctions()
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
        pk_path = os.path.join(BASE_DIR, "data", "raw", "2020_2025_pk.parquet")
        epias_df = epias_processor.epias_processor(
            epias_df_raw,
            epias_proc["epias_periods"],
            epias_proc["epias_variables"],
            epias_proc["epias_functions"],
            epias_proc["epias_window"],
            pk_path=pk_path,
            start_date=epias_proc["start_date"],
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
            start_date=config["calendar"]["start_date"],
            end_date=config["calendar"]["end_date"],
        )
        # -----------------------------

        # -----------------------------
        # Weather Data
        # -----------------------------
        weather_df = prepare_functions.generate_multi_location_weather_data(config)
        weighted_weather_df = prepare_functions.weighted_average_weather_data(
            weather_df, config["location_weights"]
        )
        # -----------------------------

        # -----------------------------
        # Prepare Main Data
        # -----------------------------
        df = prepare_functions.main_data_prepare(
            data, epias_df, solar_df, calendar_df, weather_df, weighted_weather_df
        )
        # -----------------------------

        # -----------------------------
        # Process and Save Main Data
        # -----------------------------
        df = prepare_functions.process_save_main_data(
            df, self.historical_path, self.forecast_path
        )
        # -----------------------------

        return df
