import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_mantine_components as dmc
from flask import Flask
from dotenv import load_dotenv

# Import layouts and callbacks
from src.pages.login_page import login_layout, register_login_callbacks
from src.pages.home_page import home_layout, register_home_callbacks
from src.pages.profile_page import profile_layout, register_profile_callbacks

# Load env variables
load_dotenv()
API_KEY = os.getenv("FIREBASE_WEB_API_KEY")


# --- Flask server ---
server = Flask(__name__)


# --- Dash app ---
app = Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "ApaPlan"


# --- App Layout ---
app.layout = dmc.MantineProvider(
    html.Div([
        dcc.Store(id='auth-store', storage_type='session'),
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])
)

# --- Register callbacks ---
register_login_callbacks(app)
register_home_callbacks(app)
register_profile_callbacks(app)


# --- Logout an user ---
@app.callback(
    Output('auth-store', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def logout(pathname):
    if pathname == '/logout':
        return None
    return dash.no_update


# --- URL Router ---
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('auth-store', 'data')
)
def display_page(pathname, auth_data):
    if auth_data and 'idToken' in auth_data:
        if pathname == '/profile':
            return profile_layout()
        elif pathname == '/home':
            return home_layout()
        else:
            return home_layout()  # Or a 404 page
    else:
        # Hide header and sidebar for login page
        return login_layout


# --- Redirect logic ---
@app.callback(
    Output('url', 'pathname'),
    Input('auth-store', 'data'),
    State('url', 'pathname')
)
def redirect_logic(auth_data, current_pathname):
    is_authenticated = auth_data and 'idToken' in auth_data

    # If user is authenticated and on the login page, redirect to home
    if is_authenticated and current_pathname == '/':
        return '/home'

    # If user is not authenticated and not on the login page, redirect to login
    if not is_authenticated and current_pathname != '/':
        return '/'

    # No change otherwise
    return dash.no_update


# --- Run app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
