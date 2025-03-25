# Labeller
A simple tool to label timeseries data, built using plotly Dash.

## Installation
```bash
pip install git+https://github.com/gabrielecalvo/labeller.git "plotly<6"
```
NOTE: It currently only works with plotly 5

## Usage
You can create a labeller app using the `create_app` function. 
The function requires a `DataHandler` object, which is used to load and save the data. 
The `DataHandler` object can be created using the `DataHandler.from_df` method, which requires a pandas DataFrame, a destination path, and a `ColumnDefinitions` object.

An example usage in a script is shown below, but it can also be used within a Jupyter notebook.

```python
import pandas as pd
import labeller

data_handler = labeller.DataHandler(
    df=pd.read_parquet("path/to/src_data.parquet"),
    column_definitions=labeller.ColumnDefinitions(
        scatter_x_col="x",
        scatter_y1_col="y1",
        scatter_y2_col="y2",
        timeseries_x_col="timestamp",
        timeseries_y_col="y2",
        label_col="label",
    ),
)

app = labeller.create_app(data_handler=data_handler, dst_path="path/to/output_data.parquet")
app.run_server(debug=True, use_reloader=False)
```
