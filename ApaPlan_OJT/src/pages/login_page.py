import dash
from dash import html, dcc, Input, Output, State
import dash_mantine_components as dmc
from flask import session
from components.auth import sign_in_user, create_user, send_password_reset_email

login_layout = dmc.Center(
    dmc.Card(
        [
            html.H2("Login"),
            dmc.TextInput(id="email", placeholder="Email"),
            dmc.PasswordInput(id="password", placeholder="Password"),
            dmc.Button("Login", id="login_btn", fullWidth=True, mt="sm"),
            html.Div(id="login_status", className="login-status"),
            html.Div([
                dmc.Button("Forgot Password?", id="reset_btn", variant="outline", size="xs", mt="sm"),
                html.Span("  "),
                dmc.Button("Don't have an account? Sign up", id="signup_btn", variant="outline", size="xs", mt="sm")
            ]),
            # Signup Modal
            dmc.Modal(
                id="signup_modal",
                title="Sign Up",
                children=[
                    dmc.TextInput(id="signup_email", placeholder="Email"),
                    dmc.PasswordInput(id="signup_password", placeholder="Password", mt="sm"),
                    dmc.Button("Create Account", id="signup_submit", mt="sm"),
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
                    dmc.Button("Send Reset Email", id="reset_submit", mt="sm"),
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
        Output('url', 'pathname'),
        Output("login_status", "children"),
        Input("login_btn", "n_clicks"),
        State("email", "value"),
        State("password", "value"),
        prevent_initial_call=True
    )
    def login(n_clicks, email, password):
        if not email or not password:
            return dash.no_update, "Email and password required"

        resp = sign_in_user(email, password)

        if "idToken" in resp:
            session["idToken"] = resp["idToken"]
            session["email"] = email
            return '/home', ''
        else:
            error_msg = resp.get("error", {}).get("message", "Login failed")
            return dash.no_update, error_msg

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
            return "Email and password required"

        resp = create_user(email, password)

        if "idToken" in resp:
            return "Account created successfully! You can login now."
        else:
            return "Signup failed: " + resp.get("error", {}).get("message", "")

    # Reset Password Submit
    @app.callback(
        Output("reset_status", "children"),
        Input("reset_submit", "n_clicks"),
        State("reset_email", "value"),
        prevent_initial_call=True
    )
    def reset_password(n_clicks, email):
        if not email:
            return "Email required"

        resp = send_password_reset_email(email)

        if "error" in resp:
            return "Reset failed: " + resp["error"].get("message", "")
        else:
            return f"Password reset email sent to {email}!"
