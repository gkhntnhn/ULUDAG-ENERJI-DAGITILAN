import pandas as pd


class DataLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def load_excel(self, sheet_name: str = 0, shift_hours: int = 48) -> pd.DataFrame:
        """
        Excel dosyasını yükler ve date sütununu belirtilen saatte ileri taşır
        
        Args:
            sheet_name: Excel sheet adı veya indeksi
            shift_hours: Date sütununu kaç saat ileri taşıyacak (varsayılan: 48)
            
        Returns:
            pd.DataFrame: İşlenmiş veri
        """
        try:
            # Excel dosyasını oku
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)

            # Date ve time sütunlarını birleştir
            df["date"] = pd.to_datetime(df["date"]) + pd.to_timedelta(
                df["time"], unit="h"
            )

            df = df.sort_values(by="date")
            df = df[["date", "consumption"]].copy()

            min_date = df["date"].min()
            index = pd.date_range(
                start=min_date, periods=(len(df)+shift_hours), freq="H"
            )

            self.result = pd.DataFrame({"date": index})

            self.result = self.result.merge(
                df, how="left", on=["date"]
            )

            return self.result

        except Exception as e:
            raise RuntimeError(f"Excel dosyasi okunamadi veya islenemedi: {e}")
