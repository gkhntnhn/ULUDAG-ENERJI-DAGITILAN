import holidays
import pandas as pd
import numpy as np
from feature_engine.datetime import DatetimeFeatures
from feature_engine.creation import CyclicalFeatures
from pytz import timezone
import warnings

pd.set_option("display.width", 50000)
pd.set_option("display.max_columns", None)
warnings.filterwarnings("ignore")


class CalendarDataProcessor:
    def __init__(self):
        """
        CalendarDataProcessor sinifini başlatir.

        Args:
            timezone_str (str): Kullanilacak saat dilimi (varsayilan: 'Europe/Istanbul')
        """

    def process_calendar_data(
        self,
        start_date,
        end_date,
        freq="H",
        features_to_extract=["month", "week", "day_of_week", "weekend", "hour"],
    ):
        """
        Belirtilen tarih araliği için takvim özelliklerini oluşturur.

        Args:
            start_date (str): Başlangiç tarihi
            end_date (str): Bitiş tarihi
            freq (str, optional): Veri frekansi. Varsayilan "H" (saatlik)
            features_to_extract (list, optional): Çikarilacak tarih özellikleri.
                                                   Varsayilan ["month", "week", "day_of_week", "weekend", "hour"]

        Returns:
            pandas.DataFrame: Oluşturulan takvim özellikleri
        """
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        calendar = pd.DataFrame({"date": dates})

        # Tatil günlerini ekle
        tr_holidays = holidays.Turkey(language="tr")
        calendar["Holiday_Flag"] = calendar["date"].apply(
            lambda x: tr_holidays.get(x.strftime("%Y-%m-%d"), "None")
        )

        # Tarih özelliklerini çikar
        calendar = (
            DatetimeFeatures(
                variables=None,
                features_to_extract=features_to_extract,
                drop_original=False,
            )
            .fit(calendar)
            .transform(calendar)
        )

        # Döngüsel özellikleri ekle
        calendar = (
            CyclicalFeatures(
                variables=["date_month", "date_week", "date_day_of_week", "date_hour"],
                drop_original=False,
            )
            .fit(calendar)
            .transform(calendar)
        )

        # Yillik mevsimsel döngüleri ekle
        calendar["Yearly_Sin"] = np.sin(
            2 * np.pi * calendar["date"].dt.dayofyear / 365.25
        )
        calendar["Yearly_Cos"] = np.cos(
            2 * np.pi * calendar["date"].dt.dayofyear / 365.25
        )

        # Çeyrek yili ekle
        calendar["Quarter"] = calendar["date"].dt.quarter

        # Tatil öncesi ve sonrasi günleri işaretle
        calendar["Pre_Holiday"] = (
            calendar["Holiday_Flag"]
            .shift(-24)
            .fillna("None")
            .apply(lambda x: 1 if x != "None" else 0)
        )
        calendar["Post_Holiday"] = (
            calendar["Holiday_Flag"]
            .shift(24)
            .fillna("None")
            .apply(lambda x: 1 if x != "None" else 0)
        )

        # Hafta içi/sonu işaretleri
        calendar["Weekday_Flag"] = calendar["date"].dt.weekday.apply(
            lambda x: 1 if x < 5 else 0
        )
        calendar["Weekend_Flag"] = calendar["date"].dt.weekday.apply(
            lambda x: 1 if x >= 5 else 0
        )

        return calendar
