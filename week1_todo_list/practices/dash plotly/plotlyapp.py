# import
import dash
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html
import plotly.express as px
import pandas as pd

# load data
def load_data():
    data = pd.read_csv('assets/healthcare.csv')
    data["Billing Amount"] = pd.to_numeric(data["Billing Amount"], errors='coerce')
    data["Date of Admission"] = pd.to_datetime(data["Date of Admission"], errors='coerce')
    data["YearMonth"] = data["Date of Admission"].dt.to_period("M")
    return data

data = load_data()

# create app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# app layout and design
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.H1("Healthcare Dashboard", className="text-center my-2")], width=12)
    ])
])









if __name__ == '__main__':
    app.run(debug=True, port=8071)