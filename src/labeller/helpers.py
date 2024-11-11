import dataclasses
import logging
from pathlib import Path
from typing import TypedDict, Union

import pandas as pd

logger = logging.getLogger(__name__)
PathLike = Union[str, Path]


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

    def save(self, dst_path: PathLike) -> None:
        self.df.to_parquet(dst_path)
