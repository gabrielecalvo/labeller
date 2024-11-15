import dataclasses
import logging
from pathlib import Path
from typing import TypedDict

import pandas as pd

logger = logging.getLogger(__name__)
PathLike = str | Path


class Selection(TypedDict):
    points: list[dict[str, float]]
    range: dict[str, list[float]]


@dataclasses.dataclass
class ColumnDefinitions:
    scatter_x_col: str
    scatter_y1_col: str
    scatter_y2_col: str
    timeseries_x_col: str
    timeseries_y_col: str
    label_col: str = "label"


_SELECTION_IDX_COL = "__selection_idx__"


def _validate_df(df: pd.DataFrame, column_defs: ColumnDefinitions) -> pd.DataFrame:
    if df.empty:
        raise ValueError("DataFrame is empty")

    if not df.index.is_unique:
        raise ValueError("Index must be unique")

    if column_defs.label_col not in df.columns:
        df[column_defs.label_col] = "<none>"

    for col in dataclasses.asdict(column_defs).values():
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found")

    return df


class DataHandler:
    df: pd.DataFrame
    column_definitions: ColumnDefinitions

    def __init__(self, df: pd.DataFrame, column_definitions: ColumnDefinitions):
        self.df = _validate_df(df, column_defs=column_definitions)
        self.column_definitions = column_definitions
        self._mark_selection_idx()

    def _mark_selection_idx(self) -> None:
        for _, sub_df in self.df.groupby(self.column_definitions.label_col):
            self.df.loc[sub_df.index, _SELECTION_IDX_COL] = range(sub_df.shape[0])

    def set_label(self, idxs: list[int], label: str) -> None:
        self.df.loc[idxs, self.column_definitions.label_col] = label
        self._mark_selection_idx()

    def get_selection_idx(self, idx: list[int]) -> pd.Series:
        return self.df.loc[idx, _SELECTION_IDX_COL]

    def save(self, dst_path: PathLike) -> None:
        self.df.to_parquet(dst_path)
