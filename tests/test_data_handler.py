import pandas as pd
import pytest

from labeller import ColumnDefinitions, DataHandler


class TestDataHandler:
    valid_df = pd.DataFrame(
        {
            "scatter_x_col": [1, 2],
            "scatter_y1_col": [3, 4],
            "scatter_y2_col": [5, 6],
            "timeseries_x_col": [7, 8],
            "timeseries_y_col": [9, 10],
            "label_col": ["a", "b"],
        },
        index=[1, 2],
    )

    @pytest.mark.parametrize(
        "invalid_df, msg",
        [
            (valid_df.iloc[:0], "DataFrame is empty"),
            (valid_df.set_axis([1, 1], axis=0), "Index must be unique"),
            (valid_df.drop(columns=["scatter_x_col"]), "Column 'scatter_x_col' not found"),
            (valid_df.drop(columns=["scatter_y1_col"]), "Column 'scatter_y1_col' not found"),
            (valid_df.drop(columns=["scatter_y2_col"]), "Column 'scatter_y2_col' not found"),
            (valid_df.drop(columns=["timeseries_x_col"]), "Column 'timeseries_x_col' not found"),
            (valid_df.drop(columns=["timeseries_y_col"]), "Column 'timeseries_y_col' not found"),
        ],
    )
    def test_validation(self, invalid_df, msg):
        with pytest.raises(ValueError, match=msg):
            DataHandler(
                invalid_df,
                ColumnDefinitions(
                    scatter_x_col="scatter_x_col",
                    scatter_y1_col="scatter_y1_col",
                    scatter_y2_col="scatter_y2_col",
                    timeseries_x_col="timeseries_x_col",
                    timeseries_y_col="timeseries_y_col",
                ),
            )
