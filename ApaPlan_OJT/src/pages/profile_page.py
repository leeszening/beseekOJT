import dash
import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State
from dash.dependencies import ClientsideFunction
from src.components.auth import (
    update_user_password, get_user_profile, update_user_profile, upload_avatar
)
from src.components.pyrebase_auth import sign_in_user
from src.shared.auth_utils import handle_auth_error
import base64


def profile_layout():
    return dmc.Container(
        [
            dcc.Store(id='profile-uid-store'),
            dcc.Store(id='edit-mode-store', data=False),
            dcc.Store(id='modal-trigger-store'),
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                style={"maxWidth": "500px", "margin": "auto"},
                children=[
                    dmc.Group(
                        justify="space-between",
                        children=[
                            dmc.Title("User Profile", order=2),
                            dmc.Button(
                                "Edit",
                                id="edit-profile-icon",
                                variant="subtle",
                            ),
                        ],
                    ),
                    dmc.Space(h=20),
                    # View Mode
                    html.Div(
                        id="profile-view-mode",
                        children=[
                            dmc.Center(
                                dcc.Upload(
                                    id='upload-avatar',
                                    children=html.Div([
                                        dmc.Avatar(
                                            id="user-avatar", size="xl", radius="xl"
                                        )
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '60px',
                                        'lineHeight': '60px',
                                        'borderWidth': '1px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        'margin': '10px'
                                    },
                                    multiple=False
                                )
                            ),
                            dmc.Space(h=20),
                            dmc.Group([
                                dmc.Text("Username:"),
                                dmc.Text(id="username-display")
                            ]),
                            dmc.Group([
                                dmc.Text("Display Name:"),
                                dmc.Text(id="display-name-display")
                            ]),
                            dmc.Group([
                                dmc.Text("Email:"),
                                dmc.Text(id="user-email-display")
                            ]),
                            dmc.Space(h=20),
                            dmc.Button(
                                "Change Password",
                                id="change-password-btn",
                                fullWidth=True
                            ),
                            dmc.Space(h=10),
                            dcc.Link(
                                dmc.Button("Logout", fullWidth=True),
                                href="/logout",
                                style={"textDecoration": "none"}
                            ),
                            dmc.Space(h=10),
                            dcc.Link(
                                dmc.Button("Back to Home", fullWidth=True, variant="outline"),
                                href="/",
                                style={"textDecoration": "none"}
                            ),
                        ],
                    ),
                    # Edit Mode
                    html.Div(
                        id="profile-edit-mode",
                        style={"display": "none"},
                        children=[
                            dmc.TextInput(label="Username", id="username-input"),
                            dmc.TextInput(label="Display Name", id="display-name-input"),
                            dmc.Button("Save Profile", id="save-profile-btn", mt="md"),
                        ],
                    ),
                    dmc.Space(h=20),
                    html.Div(id="profile-status"),
                ],
            ),
            dmc.Modal(
                title="Change Password",
                id="password-modal",
                opened=False,
                zIndex=10000,
                children=[
                    dmc.PasswordInput(
                        label="Current Password",
                        id="current_password",
                        style={"width": "300px"}
                    ),
                    dmc.PasswordInput(
                        label="New Password",
                        id="new_password",
                        style={"width": "300px"}
                    ),
                    dmc.Space(h=20),
                    dmc.Button("Update Password", id="update_password_btn"),
                    dmc.Space(h=20),
                    html.Div(id="update_status")
                ],
            ),
        ],
        fluid=True
    )


def register_profile_callbacks(app):
    @app.callback(
        Output("user-avatar", "src"),
        Output("username-display", "children"),
        Output("display-name-display", "children"),
        Output("user-email-display", "children"),
        Output("username-input", "value"),
        Output("display-name-input", "value"),
        Output("profile-uid-store", "data"),
        Input('auth-store', 'data')
    )
    def load_user_profile(auth_data):
        if not auth_data or "localId" not in auth_data:
            return "", "N/A", "N/A", "N/A", "", "", None

        uid = auth_data["localId"]
        profile_resp = get_user_profile(uid)

        if profile_resp["status"] == "success":
            profile = profile_resp["data"]
            display_name = profile.get("display_name", "")
            if not display_name:
                display_name = profile.get("email", "").split('@')[0]

            avatar_url = profile.get("avatar_url", "")

            return (
                avatar_url,
                profile.get("username", "N/A"),
                display_name,
                profile.get("email", "N/A"),
                profile.get("username", ""),
                display_name,
                uid
            )
        else:
            return "", "N/A", "N/A", "N/A", "", "", None

    @app.callback(
        Output("user-avatar", "src", allow_duplicate=True),
        Output("profile-status", "children", allow_duplicate=True),
        Input("upload-avatar", "contents"),
        State("upload-avatar", "filename"),
        State("profile-uid-store", "data"),
        prevent_initial_call=True
    )
    def handle_avatar_upload(contents, filename, uid):
        if not contents:
            return dash.no_update, dash.no_update

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        upload_resp = upload_avatar(uid, decoded, filename)

        if upload_resp["status"] == "success":
            return upload_resp["data"]["avatar_url"], dmc.Alert(
                "Avatar updated successfully!",
                color="green",
                withCloseButton=True,
                duration=3000
            )
        else:
            error_message = "Failed to update avatar."
            if upload_resp["message"] == "UNSUPPORTED_FILE_TYPE":
                error_message = "Unsupported file type. Please upload a JPG, PNG, or GIF."
            return dash.no_update, dmc.Alert(error_message, color="red")

    @app.callback(
        Output("edit-mode-store", "data"),
        Input("edit-profile-icon", "n_clicks"),
        State("edit-mode-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_edit_mode(n_clicks, in_edit_mode):
        return not in_edit_mode

    @app.callback(
        Output("profile-view-mode", "style"),
        Output("profile-edit-mode", "style"),
        Input("edit-mode-store", "data"),
    )
    def update_profile_visibility(in_edit_mode):
        if in_edit_mode:
            return {"display": "none"}, {"display": "block"}
        else:
            return {"display": "block"}, {"display": "none"}

    @app.callback(
        Output("profile-status", "children"),
        Output("edit-mode-store", "data", allow_duplicate=True),
        Input("save-profile-btn", "n_clicks"),
        State("username-input", "value"),
        State("display-name-input", "value"),
        State("profile-uid-store", "data"),
        prevent_initial_call=True
    )
    def save_user_profile(n_clicks, username, display_name, uid):
        if not uid:
            return dmc.Alert("Please log in first.", color="yellow"), True
        profile_data = {
            "username": username,
            "display_name": display_name,
        }
        update_resp = update_user_profile(uid, profile_data)

        if update_resp["status"] == "success":
            return dmc.Alert(
                "Profile updated successfully!",
                color="green",
                withCloseButton=True,
                duration=3000
            ), False
        else:
            return dmc.Alert("Failed to update profile.", color="red"), True

    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='open_modal'
        ),
        Output('modal-trigger-store', 'data'),
        Input('change-password-btn', 'n_clicks'),
        prevent_initial_call=True
    )

    @app.callback(
        Output("password-modal", "opened"),
        Input("modal-trigger-store", "data"),
        State("password-modal", "opened"),
        prevent_initial_call=True,
    )
    def toggle_password_modal(trigger, is_opened):
        if trigger:
            return not is_opened
        return is_opened

    @app.callback(
        Output("update_status", "children"),
        Output('auth-store', 'data', allow_duplicate=True),
        Output("password-modal", "opened", allow_duplicate=True),
        Input("update_password_btn", "n_clicks"),
        State("current_password", "value"),
        State("new_password", "value"),
        State('auth-store', 'data'),
        prevent_initial_call=True
    )
    def update_password_callback(
        n_clicks, current_password, new_password, auth_data
    ):
        if not auth_data or "email" not in auth_data:
            message = "⚠️ Please log in first."
            alert = dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )
            return alert, dash.no_update, dash.no_update
        if not current_password or not new_password:
            message = "⚠️ Please enter both current and new passwords."
            alert = dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )
            return alert, dash.no_update, dash.no_update
        if len(new_password) < 8:
            message = "🔒 Your new password must be at least 8 characters long."
            alert = dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )
            return alert, dash.no_update, dash.no_update
        if current_password == new_password:
            message = "⚠️ Your new password cannot be the same as your current one."
            alert = dmc.Alert(
                message, title="Error", color="yellow", withCloseButton=True
            )
            return alert, dash.no_update, dash.no_update

        email = auth_data["email"]
        auth_resp = sign_in_user(email, current_password)

        if auth_resp["status"] == "error":
            if "INVALID_LOGIN_CREDENTIALS" in auth_resp["message"]:
                message = "❌ The current password you entered is incorrect."
            else:
                message = handle_auth_error(auth_resp["message"])
            alert = dmc.Alert(
                message, title="Error", color="red", withCloseButton=True
            )
            return alert, dash.no_update, dash.no_update

        uid = auth_resp["data"]["localId"]
        update_resp = update_user_password(uid, new_password)

        if update_resp["status"] == "success":
            message = "✅ Password updated successfully!"
            alert = dmc.Alert(
                message,
                title="Success",
                color="green",
                withCloseButton=True
            )
            return alert, dash.no_update, False
        else:
            message = handle_auth_error(update_resp["message"])
            alert = dmc.Alert(
                message, title="Error", color="red", withCloseButton=True
            )
            return alert, dash.no_update, dash.no_update
