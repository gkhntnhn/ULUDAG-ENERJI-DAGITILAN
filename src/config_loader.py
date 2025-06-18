import json
from datetime import datetime, timedelta
import pandas as pd


def load_config(config_path: str, data_df: pd.DataFrame = None) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # EPİAŞ end_date dinamik olarak bugünün bir gün öncesi yapılır
    today = datetime.now().strftime("%Y-%m-%dT00:00:00+03:00")
    if config["epias"]["end_date"] is None:
        config["epias"]["end_date"] = today

    # Solar end_date, start_date'e 10 yıl eklenerek hesaplanır
    solar_start = datetime.strptime(config["solar"]["start_date"], "%Y-%m-%d")
    solar_end = (solar_start.replace(year=solar_start.year + 10)).strftime("%Y-%m-%d")
    config["solar"]["end_date"] = solar_end

    # Calendar tarihleri eğer veri seti verildiyse onun üzerinden hesaplanır
    if data_df is not None and "date" in data_df.columns:
        min_date = pd.to_datetime(data_df["date"].min())
        max_date = min_date + pd.DateOffset(years=10)
        config["calendar"] = {
            "start_date": min_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": max_date.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
    # Eğer h_end_date boşsa bugünden 5 gün öncesi olarak ayarla
    if config["historical_weather"]["h_end_date"] is None:
        h_end = datetime.now() - timedelta(days=5)
        config["historical_weather"]["h_end_date"] = h_end.strftime("%Y-%m-%d")
    
    # Forecast weather tarihleri her gün dinamik olarak ayarlanır
    config["forecast_weather"]["f_start_date"] = datetime.today().strftime("%Y-%m-%d")
    config["forecast_weather"]["f_end_date"] = (datetime.today() + timedelta(days=6)).strftime("%Y-%m-%d")

    return config
