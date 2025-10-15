from dash import html
import dash_mantine_components as dmc

def create_sidebar():
    return dmc.Box(
        [
            dmc.Stack(
                [
                    dmc.Button("Account Settings", id="account_settings_link", variant="outline"),
                    dmc.Collapse(
                        id="account_settings_collapse",
                        children=dmc.Stack(
                            [
                                dmc.Button("Update Password", id="update_password_link", variant="subtle"),
                                dmc.Collapse(
                                    id="update_password_collapse",
                                    children=dmc.Stack(
                                        [
                                            dmc.PasswordInput(id="current_password", placeholder="Current password", mt="sm"),
                                            dmc.PasswordInput(id="new_password", placeholder="New password", mt="sm"),
                                            dmc.Button("Change Password", id="update_password_btn", mt="sm"),
                                            html.Div(id="update_status", className="update-status")
                                        ],
                                        mt="sm"
                                    )
                                ),
                                dmc.Button("Logout", id="logout_btn", mt="sm"),
                            ],
                            mt="sm"
                        )
                    )
                ]
            )
        ],
        id="sidebar",
        className="sidebar"
    )
