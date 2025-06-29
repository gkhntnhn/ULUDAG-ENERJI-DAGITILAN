import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import reduce
import time
from sklearn.pipeline import Pipeline
from feature_engine.timeseries.forecasting import (
    LagFeatures,
    WindowFeatures,
    ExpandingWindowFeatures,
)

pd.set_option("display.width", 50000)
pd.set_option("display.max_columns", None)

class EpiasDataProcessor:
    def __init__(self):
        self.tgt_code = None

    def get_tgt_code(self, username, password):
        tgt_url = "https://giris.epias.com.tr/cas/v1/tickets"
        ıd_pass = {"username": username, "password": password}
        tgt_body = {"username": ıd_pass["username"], "password": ıd_pass["password"]}
        tgt_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
        }
        tgt_response = requests.post(tgt_url, data=tgt_body, headers=tgt_headers)
        self.tgt_code = tgt_response.text
        return self.tgt_code

    def calculate_quarters(
        self, start_year, start_month, end_year=None, end_month=None
    ):
        start_date = datetime(start_year, start_month, 1)
        if not end_year or not end_month:
            now = datetime.now()
            current_quarter_start = (now.month - 1) // 3 * 3 + 1
            end_date = (
                datetime(now.year, current_quarter_start, 1)
                + relativedelta(months=3)
                - timedelta(seconds=1)
            )
        else:
            end_date = (
                datetime(end_year, end_month, 1)
                + relativedelta(months=1)
                - timedelta(seconds=1)
            )

        quarters_start = []
        quarters_end = []

        current_date = start_date
        while current_date < end_date:
            quarter_start = current_date
            quarter_end = quarter_start + relativedelta(months=3) - timedelta(seconds=1)

            quarter_start_str = quarter_start.strftime("%Y-%m-%dT%H:%M:%S+03:00")
            quarter_end_str = quarter_end.strftime("%Y-%m-%dT%H:%M:%S+03:00")

            quarters_start.append(quarter_start_str)
            quarters_end.append(quarter_end_str)

            current_date += relativedelta(months=3)
        return quarters_start, quarters_end

    def get_kgup_data(
        self, start_year, start_month, end_year=None, end_month=None, tgt_code=None
    ):
        quarters_start, quarters_end = self.calculate_quarters(
            start_year, start_month, end_year, end_month
        )
        kgup = pd.DataFrame(columns=["date", "toplam"])
        for i in range(len(quarters_start)):
            kgup_url = "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/dpp"
            kgup_headers = {"Content-Type": "application/json", "TGT": tgt_code}
            kgup_body = {
                "startDate": quarters_start[i],
                "endDate": quarters_end[i],
                "region": "TR1",
            }
            kgup_response = requests.post(
                kgup_url, json=kgup_body, headers=kgup_headers
            )
            kgup_cache = pd.DataFrame(json.loads(kgup_response.content)["items"])[
                ["date", "toplam"]
            ]
            kgup = pd.concat([kgup, kgup_cache], ignore_index=True)
        kgup.columns = ["date", "KGUP"]
        kgup["date"] = pd.to_datetime(kgup["date"]).dt.strftime("%Y-%m-%d %H:%M")
        return kgup

    def split_dates_into_years(self, start_date, end_date):
        periods = []
        current_start = pd.to_datetime(start_date).tz_localize(None)
        end_date = pd.to_datetime(end_date).tz_localize(None)

        while current_start < end_date:
            current_end = min(
                current_start + pd.DateOffset(years=1) - timedelta(days=1), end_date
            )
            periods.append(
                (
                    current_start.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
                    current_end.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
                )
            )
            current_start = current_end + timedelta(days=1)

        return periods

    def get_gercek_tuketim_data_by_year(self, start_date, end_date, tgt_code=None):
        gt_url = "https://seffaflik.epias.com.tr/electricity-service/v1/consumption/data/realtime-consumption"
        gt_headers = {"Content-Type": "application/json", "TGT": tgt_code}

        all_data = pd.DataFrame()
        periods = self.split_dates_into_years(start_date, end_date)

        for period_start, period_end in periods:
            gt_body = {
                "startDate": period_start,
                "endDate": period_end,
            }
            gt_response = requests.post(gt_url, json=gt_body, headers=gt_headers)
            period_data = pd.DataFrame(json.loads(gt_response.content)["items"])[
                ["date", "consumption"]
            ]
            period_data.columns = ["date", "GercekTuketim"]
            period_data["date"] = pd.to_datetime(period_data["date"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            all_data = pd.concat([all_data, period_data], ignore_index=True)

        return all_data

    def get_gop_alis_data_by_year(self, start_date, end_date, tgt_code=None):
        gop_url = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/clearing-quantity"
        gop_headers = {"Content-Type": "application/json", "TGT": tgt_code}

        all_data = pd.DataFrame()
        periods = self.split_dates_into_years(start_date, end_date)

        for period_start, period_end in periods:
            gop_body = {
                "startDate": period_start,
                "endDate": period_end,
            }
            gop_response = requests.post(gop_url, json=gop_body, headers=gop_headers)
            period_data = pd.DataFrame(json.loads(gop_response.content)["items"])[
                ["date", "matchedBids"]
            ]
            period_data.columns = ["date", "GopAlis"]
            period_data["date"] = pd.to_datetime(period_data["date"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            all_data = pd.concat([all_data, period_data], ignore_index=True)

        return all_data

    def get_ia_alis_data_by_year(self, start_date, end_date, tgt_code=None):
        ia_url = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/bilateral-contracts/data/bilateral-contracts-bid-quantity"
        ia_headers = {"Content-Type": "application/json", "TGT": tgt_code}

        all_data = pd.DataFrame()
        periods = self.split_dates_into_years(start_date, end_date)

        for period_start, period_end in periods:
            ia_body = {
                "startDate": period_start,
                "endDate": period_end,
            }
            ia_response = requests.post(ia_url, json=ia_body, headers=ia_headers)
            period_data = pd.DataFrame(json.loads(ia_response.content)["items"])[
                ["date", "quantity"]
            ]
            period_data.columns = ["date", "IaAlis"]
            period_data["date"] = pd.to_datetime(period_data["date"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            all_data = pd.concat([all_data, period_data], ignore_index=True)

        return all_data

    def get_yuk_tahmin_data_by_year(self, start_date, end_date, tgt_code=None):
        yuk_tahmin_url = "https://seffaflik.epias.com.tr/electricity-service/v1/consumption/data/load-estimation-plan"
        yuk_tahmin_headers = {"Content-Type": "application/json", "TGT": tgt_code}

        all_data = pd.DataFrame()
        periods = self.split_dates_into_years(start_date, end_date)

        for period_start, period_end in periods:
            yuk_tahmin_body = {
                "startDate": period_start,
                "endDate": period_end,
            }
            yuk_tahmin_response = requests.post(
                yuk_tahmin_url, json=yuk_tahmin_body, headers=yuk_tahmin_headers
            )
            period_data = pd.DataFrame(
                json.loads(yuk_tahmin_response.content)["items"]
            )[["date", "lep"]]
            period_data.columns = ["date", "YukTahmin"]
            period_data["date"] = pd.to_datetime(period_data["date"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            all_data = pd.concat([all_data, period_data], ignore_index=True)

        return all_data

    def create_epias(
        self,
        username,
        password,
        start_year,
        start_month,
        start_date,
        end_date,
        company_name,
        reading_type,
    ):
        def current_time_str():
            return datetime.now().strftime("[%d.%m.%Y %H:%M]")

        print(f"İşlem Başladı. {current_time_str()}")

        TGT_code = self.get_tgt_code(username, password)
        time.sleep(5)
        kgup_data = self.get_kgup_data(start_year, start_month, tgt_code=TGT_code)
        time.sleep(25)  # To avoid rate limiting

        gercek_tuketim_data = self.get_gercek_tuketim_data_by_year(
            start_date, end_date, tgt_code=TGT_code
        )
        time.sleep(25)
        gop_alis_data = self.get_gop_alis_data_by_year(
            start_date, end_date, tgt_code=TGT_code
        )
        time.sleep(25)
        ia_alis_data = self.get_ia_alis_data_by_year(
            start_date, end_date, tgt_code=TGT_code
        )
        time.sleep(25)
        yuk_tahmin_alis_data = self.get_yuk_tahmin_data_by_year(
            start_date, end_date, tgt_code=TGT_code
        )
        dfs = [
            kgup_data,
            gercek_tuketim_data,
            gop_alis_data,
            ia_alis_data,
            yuk_tahmin_alis_data,
        ]
        epias_df = reduce(
            lambda left, right: pd.merge(left, right, on="date", how="inner"), dfs
        )
        print(f"İşlem tamamlandı. {current_time_str()}")
        return epias_df

    def epias_processor(
        self, data, periods, variables, functions, window, pk_path, start_date
    ):
        epias = data.copy()
        date = pd.DataFrame(
            {
                "date": pd.date_range(
                    start=start_date, periods=len(epias) + 48, freq="H"
                ).strftime("%Y-%m-%d %H:%M")
            }
        )
        epias = pd.merge(date, epias, on="date", how="outer")

        lag_transformer = LagFeatures(
            variables=variables, periods=periods, missing_values="ignore"
        )
        window_transformer = WindowFeatures(
            variables=variables,
            window=window,
            functions=functions,
            missing_values="ignore",
        )
        expanding_transformer = ExpandingWindowFeatures(
            variables=variables, functions=functions, missing_values="ignore"
        )
        pipeline = Pipeline(
            [
                ("lag", lag_transformer),
                ("window", window_transformer),
                ("expanding", expanding_transformer),
            ]
        )
        epias = pipeline.fit_transform(epias)
        epias.drop(variables, axis=1, inplace=True)
        pk = pd.read_parquet(pk_path)
        epias = reduce(
            lambda left, right: pd.merge(left, right, on="date", how="inner"),
            [epias, pk],
        )
        epias["date"] = pd.to_datetime(epias["date"])
        return epias
