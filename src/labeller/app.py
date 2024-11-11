from os import PathLike
from typing import Union

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from labeller.helpers import DataHandler, Selection

DEFAULT_DST_PATH = "labelled_data.parquet"


class IDS:
    SCATTER_1 = "fig-scatter-1"
    SCATTER_2 = "fig-scatter-2"
    TIMESERIES = "fig-timeseries"
    LABEL_INPUT = "input-label"
    TAG_BUTTON = "btn-tag"
    EXPORT_BUTTON = "btn-export"
    MESSAGE = "txt-message"


def _get_cross_selected_indexes(
    initial_selection: list[float],
    selected_scatter_1: Selection,
    selected_scatter_2: Selection,
    selected_timeseries: Selection,
) -> list:
    _selection = set(initial_selection)
    for sel in (selected_scatter_1, selected_scatter_2, selected_timeseries):
        if sel and sel["points"]:
            _selection = _selection.intersection(p["pointIndex"] for p in sel["points"])

    return sorted(_selection)


def _get_figure(df: pd.DataFrame, x_col: str, y_col: str, cross_selected_idxs: list) -> go.Figure:
    fig = px.scatter(df, x=df[x_col], y=df[y_col])

    fig.update_traces(
        selectedpoints=cross_selected_idxs,
        mode="markers",
        unselected={"marker": {"opacity": 0.1, "color": "gray"}},
    )

    fig.update_layout(
        margin={"l": 20, "r": 0, "b": 15, "t": 5},
        dragmode="lasso",
        newselection_mode="gradual",
    )
    return fig


def create_app(data_handler: DataHandler, dst_path: Union[str, "PathLike[str]"] = DEFAULT_DST_PATH) -> dash.Dash:
    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            html.Div(
                [dcc.Graph(id=IDS.SCATTER_1, style={"flex": "1"}), dcc.Graph(id=IDS.SCATTER_2, style={"flex": "1"})],
                style={"display": "flex", "justify-content": "space-around", "width": "100%"},
            ),
            html.Div(
                [dcc.Graph(id=IDS.TIMESERIES, style={"flex": "1"})],
                style={"display": "flex", "justify-content": "space-around", "width": "100%"},
            ),
            html.Div(
                [
                    html.Label("Enter label for selected points:"),
                    dcc.Input(id=IDS.LABEL_INPUT, type="text", placeholder="Enter label..."),
                    html.Button("Tag Selected Points", id=IDS.TAG_BUTTON),
                    html.Div(id=IDS.MESSAGE, style={"text-align": "center", "margin-top": "10px"}),
                ],
                style={"padding": "10px", "text-align": "center"},
            ),
            html.Div(
                [
                    html.Button("Export labelled data", id=IDS.EXPORT_BUTTON),
                ],
                style={"padding": "10px", "text-align": "center"},
            ),
        ]
    )

    @app.callback(
        Output(IDS.SCATTER_1, "figure"),
        Output(IDS.SCATTER_2, "figure"),
        Output(IDS.TIMESERIES, "figure"),
        Input(IDS.SCATTER_1, "selectedData"),
        Input(IDS.SCATTER_2, "selectedData"),
        Input(IDS.TIMESERIES, "selectedData"),
    )
    def cross_select(sel_scatter_1: Selection, sel_scatter_2: Selection, sel_timeseries: Selection) -> list[go.Figure]:
        cross_selected = _get_cross_selected_indexes(
            data_handler.df.index, sel_scatter_1, sel_scatter_2, sel_timeseries
        )
        return [
            _get_figure(
                df=data_handler.df,
                x_col=data_handler.column_definitions.scatter_x_col,
                y_col=data_handler.column_definitions.scatter_y1_col,
                cross_selected_idxs=cross_selected,
            ),
            _get_figure(
                df=data_handler.df,
                x_col=data_handler.column_definitions.scatter_x_col,
                y_col=data_handler.column_definitions.scatter_y2_col,
                cross_selected_idxs=cross_selected,
            ),
            _get_figure(
                df=data_handler.df,
                x_col=data_handler.column_definitions.timeseries_x_col,
                y_col=data_handler.column_definitions.timeseries_y_col,
                cross_selected_idxs=cross_selected,
            ),
        ]

    @app.callback(
        Output(IDS.MESSAGE, "children", allow_duplicate=True),
        Input(IDS.TAG_BUTTON, "n_clicks"),
        State(IDS.SCATTER_1, "selectedData"),
        State(IDS.SCATTER_2, "selectedData"),
        State(IDS.TIMESERIES, "selectedData"),
        State(IDS.LABEL_INPUT, "value"),
        prevent_initial_call=True,
    )
    def tag_selected_points(
        _n_clicks: int, sel_scatter_1: Selection, sel_scatter_2: Selection, sel_timeseries: Selection, label: str
    ) -> str:
        if not label or label.strip() == "":
            return "No label provided."

        cross_selected_indexes = _get_cross_selected_indexes(
            data_handler.df.index, sel_scatter_1, sel_scatter_2, sel_timeseries
        )
        data_handler.df.loc[cross_selected_indexes, data_handler.column_definitions.label_col] = label
        return f"Labeled {len(cross_selected_indexes)} points with '{label}'."

    @app.callback(
        Output(IDS.MESSAGE, "children", allow_duplicate=True),
        Input(IDS.EXPORT_BUTTON, "n_clicks"),
        prevent_initial_call=True,
    )
    def export_data(_n_clicks: int) -> str:
        data_handler.df.to_parquet(dst_path)
        return f"Data exported to {dst_path}"

    return app
