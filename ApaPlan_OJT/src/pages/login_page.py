import dash
from dash import html, Input, Output, State
import dash_mantine_components as dmc
from src.components.pyrebase_auth import (
    sign_in_user,
    send_password_reset_email_pyrebase,
)
from src.components.auth import create_user
from src.shared.auth_utils import handle_auth_error


def login_layout():
    return dmc.Center(
        dmc.Card(
            [
                html.H2("Login"),
                dmc.TextInput(id="email", placeholder="Email"),
                dmc.PasswordInput(id="password", placeholder="Password"),
                dmc.Button("Login", id="login_btn", fullWidth=True, mt="sm"),
                html.Div(id="login_status", className="login-status"),
                html.Div(
                    [
                        dmc.Button(
                            "Forgot Password?",
                            id="reset_btn",
                            variant="outline",
                            size="xs",
                            mt="sm",
                        ),
                        html.Span("  "),
                        dmc.Button(
                            "Don't have an account? Sign up",
                            id="signup_btn",
                            variant="outline",
                            size="xs",
                            mt="sm",
                        ),
                    ]
                ),
                # Signup Modal
                dmc.Modal(
                    id="signup_modal",
                    title="Sign Up",
                    children=[
                        dmc.TextInput(id="signup_email", placeholder="Email"),
                        dmc.PasswordInput(
                            id="signup_password",
                            placeholder="Password",
                            mt="sm"
                        ),
                        dmc.Button(
                            "Create Account",
                            id="signup_submit",
                            mt="sm"
                        ),
                        html.Div(id="signup_status", className="login-status")
                    ],
                    centered=True
                ),
                # Reset Password Modal
                dmc.Modal(
                    id="reset_modal",
                    title="Reset Password",
                    children=[
                        dmc.TextInput(id="reset_email", placeholder="Email"),
                        dmc.Button(
                            "Send Reset Email",
                            id="reset_submit",
                            mt="sm"
                        ),
                        html.Div(id="reset_status", className="login-status")
                    ],
                    centered=True
                )
            ],
            className="login-card"
        )
    )


def register_login_callbacks(app):
    # Login
    @app.callback(
        Output('auth-store', 'data'),
        Output("login_status", "children"),
        Input("login_btn", "n_clicks"),
        State("email", "value"),
        State("password", "value"),
        prevent_initial_call=True
    )
    def login(n_clicks, email, password):
        if not email or not password:
            message = "⚠️ Email and password are required."
            alert = dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )
            return dash.no_update, alert

        resp = sign_in_user(email, password)

        if resp["status"] == "success":
            auth_data = {
                "idToken": resp["data"]["idToken"],
                "email": email,
                "localId": resp["data"]["localId"]
            }
            return auth_data, ''
        else:
            message = handle_auth_error(resp["message"])
            alert = dmc.Alert(
                message, title="Error", color="red", withCloseButton=True
            )
            return dash.no_update, alert

    # Signup Modal Open
    @app.callback(
        Output("signup_modal", "opened"),
        Input("signup_btn", "n_clicks"),
        prevent_initial_call=True
    )
    def open_signup(n_clicks):
        return True if n_clicks else False

    # Reset Modal Open
    @app.callback(
        Output("reset_modal", "opened"),
        Input("reset_btn", "n_clicks"),
        prevent_initial_call=True
    )
    def open_reset(n_clicks):
        return True if n_clicks else False

    # Signup Submit
    @app.callback(
        Output("signup_status", "children"),
        Input("signup_submit", "n_clicks"),
        State("signup_email", "value"),
        State("signup_password", "value"),
        prevent_initial_call=True
    )
    def signup(n_clicks, email, password):
        if not email or not password:
            message = "⚠️ Email and password are required."
            return dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )
        if len(password) < 8:
            message = "🔑 Your password must be at least 8 characters long."
            return dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )

        resp = create_user(email, password)

        if resp["status"] == "success":
            message = "✅ Account created successfully! You can now log in."
            return dmc.Alert(
                message, title="Success", color="green", withCloseButton=True
            )
        else:
            message = handle_auth_error(resp["message"])
            return dmc.Alert(
                message, title="Error", color="red", withCloseButton=True
            )

    # Reset Password Submit
    @app.callback(
        Output("reset_status", "children"),
        Input("reset_submit", "n_clicks"),
        State("reset_email", "value"),
        prevent_initial_call=True
    )
    def reset_password(n_clicks, email):
        if not email:
            message = "⚠️ Email is required."
            return dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )

        resp = send_password_reset_email_pyrebase(email)

        if resp["status"] == "success":
            message = f"✅ Password reset email sent to {email}!"
            return dmc.Alert(
                message, title="Success", color="green", withCloseButton=True
            )
        else:
            message = handle_auth_error(resp["message"])
            return dmc.Alert(
                message, title="Error", color="red", withCloseButton=True
            )

    # Reset signup modal on close
    @app.callback(
        Output("signup_email", "value"),
        Output("signup_password", "value"),
        Output("signup_status", "children", allow_duplicate=True),
        Input("signup_modal", "opened"),
        prevent_initial_call=True,
    )
    def reset_signup_fields(opened):
        if not opened:
            return "", "", ""
        return dash.no_update, dash.no_update, dash.no_update

    # Reset password modal on close
    @app.callback(
        Output("reset_email", "value"),
        Output("reset_status", "children", allow_duplicate=True),
        Input("reset_modal", "opened"),
        prevent_initial_call=True,
    )
    def reset_reset_fields(opened):
        if not opened:
            return "", ""
        return dash.no_update, dash.no_update
