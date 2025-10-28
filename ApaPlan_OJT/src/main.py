import os
import sys
import logging

# Add the project root to the Python path before any other imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import firebase_admin
from firebase_admin import credentials, firestore
import firebase_config

# --- Firebase Admin SDK Initialization ---
# This is the robust, centralized initialization pattern.
logging.basicConfig(level=logging.INFO)
try:
    # Check if the app is already initialized to prevent errors on hot reloads
    firebase_admin.get_app()
    logging.info("Firebase app already exists.")
except ValueError:
    logging.info("Firebase app does not exist. Initializing now...")

    # Get storage bucket from environment variables.
    # Make sure dotenv is loaded before this, which happens in firebase_config.py
    storage_bucket = os.getenv("STORAGE_BUCKET")
    if not storage_bucket:
        logging.warning("STORAGE_BUCKET environment variable not set. Storage features may not work.")
        firebase_options = {}
    else:
        # Ensure the bucket name is clean and doesn't contain prefixes
        if "gs://" in storage_bucket:
            storage_bucket = storage_bucket.split("gs://")[1]
        firebase_options = {'storageBucket': storage_bucket}

    # When running in a Google Cloud environment (like Cloud Run),
    # initialize_app() with no arguments will automatically use
    # the service account associated with the revision.
    if 'K_SERVICE' in os.environ:
        firebase_admin.initialize_app(options=firebase_options)
        logging.info("Firebase app initialized successfully using Application Default Credentials.")
    else:
        # Local or Docker development
        # Assumes a serviceAccountKey.json file is in your project root directory
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, firebase_options)
        logging.info("Firebase app initialized successfully using local credentials.")

# Now that the app is initialized, we can get the firestore client
# and assign it to the placeholder in our config module.
firebase_config.db = firestore.client()
# --- End of Firebase Initialization ---


# --- NOW you can safely import your other modules that use firebase ---
import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_mantine_components as dmc
from flask import Flask
from dotenv import load_dotenv

from src.pages.login_page import login_layout, register_login_callbacks
from src.pages.home_page import home_layout, register_home_callbacks
from src.pages.profile_page import profile_layout, register_profile_callbacks
from src.pages.journal_detail_page import journal_detail_layout, register_journal_detail_callbacks
from src.pages.journal_edit_page import journal_edit_layout, register_journal_edit_callbacks

# Load env variables for client-side (pyrebase)
load_dotenv()


# --- Flask server ---
server = Flask(__name__)


# --- Dash app ---
app = Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "ApaPlan"


# --- App Layout ---
app.layout = dmc.MantineProvider(
    children=[
        dcc.Store(id='auth-store', storage_type='session'),
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
    ]
)

# --- Register callbacks ---
register_login_callbacks(app)
register_home_callbacks(app)
register_profile_callbacks(app)
register_journal_detail_callbacks(app)
register_journal_edit_callbacks(app)


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
        elif pathname and pathname.startswith('/journal/'):
            parts = pathname.split('/')
            if len(parts) == 4 and parts[3] == 'edit':
                journal_id = parts[2]
                return journal_edit_layout(journal_id, auth_data)
            elif len(parts) == 4 and parts[3] == 'view':
                journal_id = parts[2]
                return journal_detail_layout(journal_id, auth_data)
            elif len(parts) == 3: # Default to view
                journal_id = parts[2]
                return journal_detail_layout(journal_id, auth_data)
        else:
            return home_layout()  # Or a 404 page
    else:
        # Hide header and sidebar for login page
        return login_layout()


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
