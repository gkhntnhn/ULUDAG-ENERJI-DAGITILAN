from src.epias_data import EpiasDataProcessor
from src.solar_data import SolarDataProcessor
from src.calendar_data import CalendarDataProcessor
import pandas as pd
import warnings

warnings.filterwarnings("ignore")
pd.set_option("display.width", 500000)
pd.set_option("display.max_columns", None)

# Epias Data Processing
epias_start_date = "2020-01-01T00:00:00+03:00"
epias_end_date = (pd.Timestamp.today() - pd.Timedelta(days=1)).strftime(
    "%Y-%m-%dT%H:%M:%S+03:00"
)
epias_inputs = {
    "username": "gkhntnhntsdln@gmail.com",
    "password": "9537514682Aa*",
    "start_year": 2020,
    "start_month": 1,
    "start_date": epias_start_date,
    "end_date": epias_end_date,
    "company_name": "ULUDAĞ ELEKTRİK DAĞITIM A.Ş.(ED)",
    "reading_type": "Tek Zamanlı",
}
epias_processor = EpiasDataProcessor()
epias_df_raw = epias_processor.create_epias(
    username=epias_inputs.get("username"),
    password=epias_inputs.get("password"),
    start_year=epias_inputs.get("start_year"),
    start_month=epias_inputs.get("start_month"),
    start_date=epias_inputs.get("start_date"),
    end_date=epias_inputs.get("end_date"),
    company_name=epias_inputs.get("company_name"),
    reading_type=epias_inputs.get("reading_type"),
)

epias_processes_inputs = {
    "epias_periods": [48, 168],
    "epias_variables": ["KGUP", "GercekTuketim", "GopAlis", "IaAlis", "YukTahmin"],
    "epias_functions": ["mean"],
    "epias_window": [48, 168],
    "pk_path": r"data\raw\2020_2025_pk.parquet",
    "start_date": epias_start_date,
}
epias_df = epias_processor.epias_processor(
    epias_df_raw,
    epias_processes_inputs.get("epias_periods"),
    epias_processes_inputs.get("epias_variables"),
    epias_processes_inputs.get("epias_functions"),
    epias_processes_inputs.get("epias_window"),
    epias_processes_inputs.get("pk_path"),
    epias_processes_inputs.get("start_date"),
)


# Solar Data Processing
solar_start_date = "2020-01-01"
solar_end_date = (pd.Timestamp(solar_start_date) + pd.DateOffset(years=10)).strftime(
    "%Y-%m-%d"
)

solar_data_inputs = {
    "start_date": solar_start_date,
    "end_date": solar_end_date,
    "lat": 40.19683112867639,
    "long": 29.049976280652263,
    "alt": 150,
    "timezone": "Europe/Istanbul",
}
solar_processor = SolarDataProcessor(
    lat=solar_data_inputs.get("lat"),
    long=solar_data_inputs.get("long"),
    alt=solar_data_inputs.get("alt"),
    timezone=solar_data_inputs.get("timezone"),
)

solar_df = solar_processor.process_data(
    start_date=solar_data_inputs.get("start_date"),
    end_date=solar_data_inputs.get("end_date"),
)


