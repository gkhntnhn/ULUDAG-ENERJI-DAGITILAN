import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt


class ModelTrainFunctions:
    def __init__(self):
        pass
    def get_data(self, data_path: str) -> pd.DataFrame:
        historical_data = pd.read_parquet(data_path+"/Historical_Data.parquet")
        forecast_data = pd.read_parquet(data_path+"/Forecast_Data.parquet")
        historical_data.index = pd.to_datetime(historical_data.index)
        forecast_data.index = pd.to_datetime(forecast_data.index)
        return historical_data, forecast_data

    def get_tscv_splits(self, dates, n_splits, test_size):
        """
        Generate time series cross-validation splits.

        Parameters:
        - dates: pd.DatetimeIndex or pd.Series of dates.
        - n_splits: Number of splits for cross-validation.
        - test_size: Size of the test set for each split.
        """
        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
        splits_info = []
        dates = pd.to_datetime(dates)
        if isinstance(dates, pd.DatetimeIndex):
            dates = pd.Series(dates)

        for i, (train_index, test_index) in enumerate(tscv.split(dates)):
            split_info = {
                'name': f"Split {i + 1}",
                'train_period': (dates.iloc[train_index[0]], dates.iloc[train_index[-1]]),
                'val_period': (dates.iloc[test_index[0]], dates.iloc[test_index[-1]])
            }
            splits_info.append(split_info)

        return splits_info
    
    def plot_splits(self, splits_info, data, colors=None):

        if colors is None:
            colors = {
                'train': '#2E86C1',    # Koyu mavi
                'val': '#E67E22',      # Turuncu
            }

        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['font.family'] = 'sans-serif'

        fig, axes = plt.subplots(len(splits_info), 1, figsize=(12, 6), sharex=True)
        fig.patch.set_facecolor('white')

        for i, split in enumerate(splits_info):
            train_data = data[split['train_period'][0]:split['train_period'][1]]
            val_data = data[split['val_period'][0]:split['val_period'][1]]

            axes[i].plot(train_data.index, train_data.values, label="Train",
                        color=colors['train'], alpha=0.8, linewidth=1)
            axes[i].plot(val_data.index, val_data.values, label="Validation",
                        color=colors['val'], alpha=0.8, linestyle='--', linewidth=1)

            title = f"{split['name'].capitalize()}: Train ({split['train_period'][0]}-{split['train_period'][1]}), " \
                    f"Val ({split['val_period'][0]}-{split['val_period'][1]}), "

            axes[i].set_title(title, fontsize=8, pad=2, fontweight='bold')

            legend = axes[i].legend(loc='upper left', fontsize=7,
                                    bbox_to_anchor=(1.01, 1), borderaxespad=0)
            legend.get_frame().set_alpha(0.9)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_edgecolor('#CCCCCC')
            plt.setp(legend.get_texts(), fontweight='bold') 

            axes[i].grid(True, linestyle='--', alpha=0.4, color='#CCCCCC')
            axes[i].spines['top'].set_visible(False)
            axes[i].spines['right'].set_visible(False)
            axes[i].spines['left'].set_color('#CCCCCC')
            axes[i].spines['bottom'].set_color('#CCCCCC')

            axes[i].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

            axes[i].tick_params(axis='both', colors='#666666', labelsize=7)
            plt.setp(axes[i].get_xticklabels(), fontweight='bold') 
            plt.setp(axes[i].get_yticklabels(), fontweight='bold')

            axes[i].margins(x=0.01)

        plt.xlabel('Time', fontsize=9, labelpad=5, color='#333333', fontweight='bold')
        plt.xticks(rotation=45, fontsize=7, ha='right')

        fig.text(0.02, 0.5, 'Consumption', va='center', rotation='vertical',
                fontsize=9, color='#333333', fontweight='bold')

        plt.suptitle('Train and Validation Periods',
                    fontsize=10, y=0.98, color='#333333', fontweight='bold')

        plt.tight_layout(rect=[0.03, 0.03, 0.92, 0.95])
        plt.show()

    def print_splits_info(self, splits_info):

        for split in splits_info:
            print(f"{split['name']}:")
            print(f"  Train: {split['train_period'][0].date()} --> {split['train_period'][1].date()}")
            print(f"  Val:  {split['val_period'][0].date()} --> {split['val_period'][1].date()}")
            print("-" * 40)
    
    def calculate_mape(self, y_true, y_pred):
        mape_df = pd.DataFrame({
            "Gerçek": y_true,
            "Tahmin": y_pred,
            "Abs": abs(y_true - y_pred)
        })
        return mape_df, round(mape_df["Abs"].sum() / mape_df["Gerçek"].sum() * 100, 2)