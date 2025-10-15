import dash
from dash import html, dcc, Input, Output, State
import dash_mantine_components as dmc
from flask import session
from components.header import create_header
from components.sidebar import create_sidebar
from components.auth import update_user_password, sign_in_user

home_layout = dmc.Container(
    [
        # Header
        create_header(),
        dmc.Space(h=20),
        # Main content with sidebar + main area
        dmc.Group(
            [
                # Sidebar
                create_sidebar(),
                # Main content placeholder
                html.Div(id="home_content", className="home-content")
            ],
            align="start"
        )
    ],
    fluid=True
)

def register_home_callbacks(app):
    # Update Password
    @app.callback(
        Output("update_status", "children"),
        Input("update_password_btn", "n_clicks"),
        State("current_password", "value"),
        State("new_password", "value"),
        prevent_initial_call=True
    )
    def update_password(n_clicks, current_password, new_password):
        if "idToken" not in session or "email" not in session:
            return "Not logged in"

        if not current_password or not new_password:
            return "All password fields are required."

        if len(new_password) < 6:
            return "New password must be at least 6 characters"

        # Verify current password by trying to sign in
        verify_resp = sign_in_user(session["email"], current_password)
        if "error" in verify_resp:
            return "Incorrect current password."

        # If verification is successful, update the password
        update_resp = update_user_password(session["idToken"], new_password)

        if "idToken" in update_resp:
            session["idToken"] = update_resp["idToken"]
            return "Password updated successfully!"
        else:
            return "Update failed: " + update_resp.get("error", {}).get("message", "")

    # Logout
    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        Input("logout_btn", "n_clicks"),
        prevent_initial_call=True
    )
    def logout(n_clicks):
        if n_clicks:
            session.clear()
            return '/'
        return dash.no_update

    # Account Settings Collapse
    @app.callback(
        Output("account_settings_collapse", "opened"),
        Input("account_settings_link", "n_clicks"),
        State("account_settings_collapse", "opened"),
        prevent_initial_call=True
    )
    def toggle_account_settings(n_clicks, is_open):
        return not is_open if n_clicks else False

    # Update Password Collapse
    @app.callback(
        Output("update_password_collapse", "opened"),
        Input("update_password_link", "n_clicks"),
        State("update_password_collapse", "opened"),
        prevent_initial_call=True
    )
    def toggle_update_password(n_clicks, is_open):
        return not is_open if n_clicks else False
