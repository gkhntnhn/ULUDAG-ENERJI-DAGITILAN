import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt


class ModelTrainFunctions:
    def __init__(self):
        pass

    def get_data(self, data_path: str) -> pd.DataFrame:
        historical_data = pd.read_parquet(data_path + "/Historical_Data.parquet")
        forecast_data = pd.read_parquet(data_path + "/Forecast_Data.parquet")
        historical_data.index = pd.to_datetime(historical_data.index)
        forecast_data.index = pd.to_datetime(forecast_data.index)
        return historical_data, forecast_data

    def get_tscv_splits(self, dates, n_splits, test_size):
        """
        TimeSeriesSplit kullanarak her split'in başlangıç ve bitiş tarihlerini döndürür.
        """
        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
        splits_info = []
        dates = pd.to_datetime(dates)

        if isinstance(dates, pd.DatetimeIndex):
            dates = pd.Series(dates)

        for i, (train_index, test_index) in enumerate(tscv.split(dates)):
            split_info = {
                "name": f"Split {i + 1}",
                "train_period": (
                    dates.iloc[train_index[0]],
                    dates.iloc[train_index[-1]],
                ),
                "val_period": (dates.iloc[test_index[0]], dates.iloc[test_index[-1]]),
            }
            splits_info.append(split_info)

        return splits_info

    def plot_splits(self, splits_info, data, colors=None):
        if colors is None:
            colors = {
                "train": "#2E86C1",  # Koyu mavi
                "val": "#E67E22",  # Turuncu
            }

        plt.rcParams["figure.facecolor"] = "white"
        plt.rcParams["axes.facecolor"] = "white"
        plt.rcParams["font.family"] = "sans-serif"

        fig, axes = plt.subplots(len(splits_info), 1, figsize=(12, 6), sharex=True)
        fig.patch.set_facecolor("white")

        for i, split in enumerate(splits_info):
            train_data = data[split["train_period"][0] : split["train_period"][1]]
            val_data = data[split["val_period"][0] : split["val_period"][1]]

            axes[i].plot(
                train_data.index,
                train_data.values,
                label="Train",
                color=colors["train"],
                alpha=0.8,
                linewidth=1,
            )
            axes[i].plot(
                val_data.index,
                val_data.values,
                label="Validation",
                color=colors["val"],
                alpha=0.8,
                linestyle="--",
                linewidth=1,
            )

            title = (
                f"{split['name'].capitalize()}: Train ({split['train_period'][0]}-{split['train_period'][1]}), "
                f"Val ({split['val_period'][0]}-{split['val_period'][1]}), "
            )

            axes[i].set_title(title, fontsize=8, pad=2, fontweight="bold")

            legend = axes[i].legend(
                loc="upper left", fontsize=7, bbox_to_anchor=(1.01, 1), borderaxespad=0
            )
            legend.get_frame().set_alpha(0.9)
            legend.get_frame().set_facecolor("white")
            legend.get_frame().set_edgecolor("#CCCCCC")
            plt.setp(legend.get_texts(), fontweight="bold")

            axes[i].grid(True, linestyle="--", alpha=0.4, color="#CCCCCC")
            axes[i].spines["top"].set_visible(False)
            axes[i].spines["right"].set_visible(False)
            axes[i].spines["left"].set_color("#CCCCCC")
            axes[i].spines["bottom"].set_color("#CCCCCC")

            axes[i].yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: format(int(x), ","))
            )

            axes[i].tick_params(axis="both", colors="#666666", labelsize=7)
            plt.setp(axes[i].get_xticklabels(), fontweight="bold")
            plt.setp(axes[i].get_yticklabels(), fontweight="bold")

            axes[i].margins(x=0.01)

        plt.xlabel("Time", fontsize=9, labelpad=5, color="#333333", fontweight="bold")
        plt.xticks(rotation=45, fontsize=7, ha="right")

        fig.text(
            0.02,
            0.5,
            "Consumption",
            va="center",
            rotation="vertical",
            fontsize=9,
            color="#333333",
            fontweight="bold",
        )

        plt.suptitle(
            "Train and Validation Periods",
            fontsize=10,
            y=0.98,
            color="#333333",
            fontweight="bold",
        )

        plt.tight_layout(rect=[0.03, 0.03, 0.92, 0.95])
        plt.show()

    def print_splits_info(self, splits_info):
        for split in splits_info:
            print(f"{split['name']}:")
            print(
                f"  Train: {split['train_period'][0].date()} --> {split['train_period'][1].date()}"
            )
            print(
                f"  Val:  {split['val_period'][0].date()} --> {split['val_period'][1].date()}"
            )
            print("-" * 40)

    def calculate_mape(self, y_true, y_pred):
        mape_df = pd.DataFrame(
            {"Gerçek": y_true, "Tahmin": y_pred, "Abs": abs(y_true - y_pred)}
        )
        return mape_df, round(mape_df["Abs"].sum() / mape_df["Gerçek"].sum() * 100, 2)

    def all_splits_mape_analysis(self, model_performance):
        fig, (ax_hour, ax_weekday, ax_month) = plt.subplots(1, 3, figsize=(20, 5))
        fig.suptitle("MAPE Analysis Across Splits", fontsize=16)

        def mape_analysis(df, ax_hour, ax_weekday, ax_month, split_name):
            result = df.copy()
            result["hour"] = result.index.hour
            hourly_mape = result.groupby("hour").apply(
                lambda x: (x["Abs"].sum() / x["Gerçek"].sum()) * 100
            )
            result["weekday"] = result.index.weekday
            weekday_mape = result.groupby("weekday").apply(
                lambda x: (x["Abs"].sum() / x["Gerçek"].sum()) * 100
            )
            result["month"] = result.index.month
            monthly_mape = result.groupby("month").apply(
                lambda x: (x["Abs"].sum() / x["Gerçek"].sum()) * 100
            )
            monthly_mape = monthly_mape.reindex(range(1, 13), fill_value=0)
            ax_hour.plot(hourly_mape.index, hourly_mape, label=split_name)
            weekdays = [
                "Pazartesi",
                "Salı",
                "Çarşamba",
                "Perşembe",
                "Cuma",
                "Cumartesi",
                "Pazar",
            ]
            ax_weekday.plot(weekdays, weekday_mape, label=split_name)
            months = [
                "Ocak",
                "Şubat",
                "Mart",
                "Nisan",
                "Mayıs",
                "Haziran",
                "Temmuz",
                "Ağustos",
                "Eylül",
                "Ekim",
                "Kasım",
                "Aralık",
            ]
            ax_month.plot(months, monthly_mape, label=split_name)

        split_names = [col for col in model_performance.keys() if "Split" in col]
        for split in split_names:
            test_df = model_performance[split]["val_df"]
            mape_analysis(test_df, ax_hour, ax_weekday, ax_month, split)
        ax_hour.set_title("Günün Saatlerine Göre Ortalama MAPE")
        ax_hour.set_xlabel("Saatler")
        ax_hour.set_ylabel("MAPE (%)")
        ax_hour.legend()
        ax_weekday.set_title("Haftanın Günlerine Göre Ortalama MAPE")
        ax_weekday.set_xlabel("Haftanın Günleri")
        ax_weekday.set_ylabel("MAPE (%)")
        ax_weekday.legend()
        ax_month.set_title("Aylara Göre Ortalama MAPE")
        ax_month.set_xlabel("Aylar")
        ax_month.set_ylabel("MAPE (%)")
        ax_month.legend()
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()

    def all_splits_mape_analysis_v2(self, model_performance):
        split_names = [col for col in model_performance.keys() if "Split" in col]
        num_splits = len(split_names)
        fig, axs = plt.subplots(
            num_splits, 3, figsize=(15, 4 * num_splits), sharey="col"
        )
        fig.suptitle("MAPE Analysis Across Splits", fontsize=16)

        # İç içe MAPE analiz fonksiyonu
        def mape_analysis(df, ax_hour, ax_weekday, ax_month):
            result = df.copy()

            # Günün saatine göre MAPE hesabı
            result["hour"] = result.index.hour
            hourly_mape = result.groupby("hour").apply(
                lambda x: (x["Abs"].sum() / x["Gerçek"].sum()) * 100
            )

            # Haftanın günlerine göre MAPE hesabı
            result["weekday"] = result.index.weekday
            weekday_mape = result.groupby("weekday").apply(
                lambda x: (x["Abs"].sum() / x["Gerçek"].sum()) * 100
            )

            # Aylara göre MAPE hesabı ve eksik ayları sıfırlarla doldurma
            result["month"] = result.index.month
            monthly_mape = result.groupby("month").apply(
                lambda x: (x["Abs"].sum() / x["Gerçek"].sum()) * 100
            )
            monthly_mape = monthly_mape.reindex(range(1, 13), fill_value=0)

            # Saatlik, Haftalık ve Aylık MAPE grafikleri
            ax_hour.bar(hourly_mape.index, hourly_mape)
            ax_weekday.bar(
                [
                    "Pazartesi",
                    "Salı",
                    "Çarşamba",
                    "Perşembe",
                    "Cuma",
                    "Cumartesi",
                    "Pazar",
                ],
                weekday_mape,
            )
            ax_month.bar(
                [
                    "Ocak",
                    "Şubat",
                    "Mart",
                    "Nisan",
                    "Mayıs",
                    "Haziran",
                    "Temmuz",
                    "Ağustos",
                    "Eylül",
                    "Ekim",
                    "Kasım",
                    "Aralık",
                ],
                monthly_mape,
            )

        # Her split için MAPE analizini yap
        split_names = [col for col in model_performance.keys() if "Split" in col]
        for idx, split in enumerate(split_names):
            test_df = model_performance[split]["val_df"]
            ax_hour, ax_weekday, ax_month = axs[idx, 0], axs[idx, 1], axs[idx, 2]

            mape_analysis(test_df, ax_hour, ax_weekday, ax_month)

            # Split başlıkları
            ax_hour.set_title(f"{split} - Günün Saatlerine Göre MAPE")
            ax_weekday.set_title(f"{split} - Haftanın Günlerine Göre MAPE")
            ax_month.set_title(f"{split} - Aylara Göre MAPE")

        # Ortak eksen başlıkları
        for ax in axs[:, 0]:
            ax.set_ylabel("MAPE (%)")

        # Genel başlık ve düzenlemeler
        fig.tight_layout(rect=[0, 0, 1, 0.96])  # Başlık için üst boşluk ekliyoruz
        plt.show()
