import pandas as pd


class DataLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def load_excel(self, sheet_name: str = 0) -> pd.DataFrame:
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)

            df["Date"] = pd.to_datetime(df["Date"]) + pd.to_timedelta(
                df["Time"], unit="h"
            )

            self.df = df[["Date", "Consumption"]].copy()
            return self.df

        except Exception as e:
            raise RuntimeError(f"Excel dosyasi okunamadi veya islenemedi: {e}")
