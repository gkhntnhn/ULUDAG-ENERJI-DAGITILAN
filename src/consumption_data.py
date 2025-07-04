import pandas as pd
from sklearn.pipeline import Pipeline
from feature_engine.timeseries.forecasting import (
    LagFeatures,
    WindowFeatures,
    ExpandingWindowFeatures,
)

pd.set_option("display.width", 50000)
pd.set_option("display.max_columns", None)


class ConsumptionDataProcessor:
    def __init__(self, variables: list, lags: list, functions: list):
        self.variables = variables
        self.lags = lags
        self.functions = functions
        self.pipeline = self._build_pipeline()

    def _build_pipeline(self):
        return Pipeline(
            [
                (
                    "lag",
                    LagFeatures(
                        variables=self.variables,
                        periods=self.lags,
                        missing_values="ignore",
                    ),
                ),
                (
                    "window",
                    WindowFeatures(
                        variables=self.variables,
                        window=self.lags,
                        functions=self.functions,
                        min_periods=1,
                        missing_values="ignore",
                    ),
                ),
                (
                    "expanding",
                    ExpandingWindowFeatures(
                        variables=self.variables,
                        functions=self.functions,
                        missing_values="ignore",
                    ),
                ),
            ]
        )

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        df = self.pipeline.fit_transform(df)

        df.drop(columns=["consumption"], inplace=True, errors="ignore")
        return df.reset_index()
