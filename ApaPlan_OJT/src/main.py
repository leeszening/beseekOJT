import os
from dash import Dash, html, dcc, Input, Output
import dash_mantine_components as dmc
from flask import Flask, session
from dotenv import load_dotenv

# Load env variables
load_dotenv()
API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# --- Flask server ---
server = Flask(__name__)
server.secret_key = SECRET_KEY

# --- Dash app ---
app = Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "Firebase Auth Demo"

# --- Import layouts and callbacks ---
from pages.login_page import login_layout, register_login_callbacks
from pages.home_page import home_layout, register_home_callbacks

# --- App Layout ---
app.layout = dmc.MantineProvider(
    html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])
)

# --- Register callbacks ---
register_login_callbacks(app)
register_home_callbacks(app)

# --- URL Router ---
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/home' and 'idToken' in session:
        return home_layout
    else:
        return login_layout

# --- Run app ---
if __name__ == "__main__":
    app.run(debug=True, port=8088)
