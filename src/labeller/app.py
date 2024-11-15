from os import PathLike
from typing import Union

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, Patch, State, dcc, html

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
    selected_scatter_1: Selection,
    selected_scatter_2: Selection,
    selected_timeseries: Selection,
) -> set | None:
    _selection: set[int] | None = None
    for sel in (selected_scatter_1, selected_scatter_2, selected_timeseries):
        if sel and sel["points"]:
            _sel_points = set(p["customdata"][0] for p in sel["points"])  # type: ignore
            _selection = _sel_points if _selection is None else _selection.intersection(_sel_points)

    return _selection


def _get_figure(
    df: pd.DataFrame, x_col: str, y_col: str, color_col: str, cross_selected_idxs: pd.Series | None
) -> go.Figure | Patch:
    # inspired by https://community.plotly.com/t/selectedpoint-highlights-data-points-for-each-category-instead-of-from-the-dataset-as-a-whole/58697/2

    if cross_selected_idxs is None:
        fig = px.scatter(df, x=df[x_col], y=df[y_col], color=df[color_col], custom_data=[df.index])

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

    patched_fig = Patch()
    for i_trace, (_, sub_df) in enumerate(df.groupby(color_col)):
        patched_fig.data[i_trace]["selectedpoints"] = cross_selected_idxs.filter(sub_df.index).values
    return patched_fig


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
        cross_selected = _get_cross_selected_indexes(sel_scatter_1, sel_scatter_2, sel_timeseries)
        cross_selected_idxs = data_handler.get_selection_idx(sorted(cross_selected)) if cross_selected else None
        _common = {
            "df": data_handler.df,
            "color_col": data_handler.column_definitions.label_col,
            "cross_selected_idxs": cross_selected_idxs,
        }

        return [
            _get_figure(
                x_col=data_handler.column_definitions.scatter_x_col,
                y_col=data_handler.column_definitions.scatter_y1_col,
                **_common,
            ),
            _get_figure(
                x_col=data_handler.column_definitions.scatter_x_col,
                y_col=data_handler.column_definitions.scatter_y2_col,
                **_common,
            ),
            _get_figure(
                x_col=data_handler.column_definitions.timeseries_x_col,
                y_col=data_handler.column_definitions.timeseries_y_col,
                **_common,
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

        cross_selected_indexes = _get_cross_selected_indexes(sel_scatter_1, sel_scatter_2, sel_timeseries)
        if not cross_selected_indexes:
            return "No points selected."

        data_handler.set_label(idxs=list(cross_selected_indexes), label=label)
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
