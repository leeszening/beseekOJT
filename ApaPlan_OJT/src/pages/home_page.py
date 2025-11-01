from dash import html, dcc, Input, Output, State, ALL, callback_context, no_update
import dash_mantine_components as dmc
from src.shared.auth_utils import get_user_info
from src.shared.journal_utils import (
    create_journal,
    get_user_journals,
    get_all_journals,
    get_user_profiles_by_ids,
    get_journal,
    delete_journal,
    upload_cover_image,
)
import json
import logging


def create_journal_modal():
    return dmc.Modal(
        id="journal-modal",
        title="Create New Journal",
        zIndex=10000,
        children=[
            dcc.Upload(
                id="upload-image",
                children=html.Div(
                    ["Drag and Drop or ", html.A("Select a Cover Image")]
                ),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px 0",
                },
                multiple=False,
            ),
            html.Div(
                id="output-image-upload",
                children=[
                    html.Img(
                        src="https://via.placeholder.com/200x150",
                        style={"width": "100%", "height": "auto"},
                    )
                ],
            ),
            dmc.Text("Title *"),
            dmc.TextInput(id="journal-title-input", required=True),
            html.Div(
                [
                    dmc.Text("Start Date *"),
                    dmc.DatePickerInput(
                        id="journal-start-date-picker",
                        placeholder="Select a start date",
                        dropdownType="modal",
                        modalProps={"zIndex": 10001},
                        required=True,
                    ),
                    dmc.Text("Days"),
                    dmc.NumberInput(
                        id="journal-days-input",
                        value=1,
                        min=1,
                        required=True,
                    ),
                ],
                style={"margin-top": "1rem"},
            ),
            dmc.Group(
                [
                    dmc.Button("Cancel", id="cancel-journal-btn", variant="outline"),
                    dmc.Button("Save", id="save-journal-btn"),
                ],
                justify="flex-end",
                style={"marginTop": "1rem"},
            ),
        ],
    )


def home_layout():
    return html.Div(
        [
            dcc.Store(id="user-info-store", storage_type="session"),
            dcc.Store(id="selected-journal-store", storage_type="session"),
            dcc.Store(id="modal-state-store", data={"opened": False}),
            dcc.Store(id="journal-update-trigger-store", storage_type="memory"),
            dcc.Store(id="journal-to-delete-store", storage_type="session"),
            html.Div(id="home-page-content"),
            dmc.Modal(
                id="journal-details-modal",
                zIndex=10000,
                children=[],
            ),
            dmc.Modal(
                id="delete-confirm-modal",
                title="Confirm Deletion",
                opened=False,
                zIndex=10001,
                children=[
                    dmc.Text(
                        "Are you sure you want to delete this journal? "
                        "This action cannot be undone."
                    ),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Cancel", id="cancel-delete-btn", variant="outline"
                            ),
                            dmc.Button("Delete", id="confirm-delete-btn", color="red"),
                        ],
                        justify="flex-end",
                        style={"marginTop": "1rem"},
                    ),
                ],
            ),
        ]
    )


def register_home_callbacks(app):
    @app.callback(Output("user-info-store", "data"), Input("auth-store", "data"))
    def store_user_info(auth_data):
        if auth_data and "idToken" in auth_data:
            user_info = get_user_info(auth_data["idToken"])
            if user_info:
                return {
                    "uid": user_info.uid,
                    "display_name": user_info.display_name,
                    "email": user_info.email,
                }
        return None

    @app.callback(
        Output("home-page-content", "children"), Input("user-info-store", "data")
    )
    def update_home_page_content(user_info):
        if user_info:
            display_name = user_info.get("display_name", "User")
            return html.Div(
                [
                    html.H1(f"Welcome, {display_name}!"),
                    create_journal_modal(),
                    dmc.Button(
                        "Create a new journal",
                        id="create-journal-btn",
                        style={"marginBottom": "20px"},
                    ),
                    dmc.Accordion(
                        id="journal-accordion",
                        children=[
                            dmc.AccordionItem(
                                [
                                    dmc.AccordionControl("My Journals"),
                                    dmc.AccordionPanel(
                                        html.Div(id="journal-list-container")
                                    ),
                                ],
                                value="my-journal-list",
                            ),
                            dmc.AccordionItem(
                                [
                                    dmc.AccordionControl("Discover All Journals"),
                                    dmc.AccordionPanel(
                                        html.Div(id="all-journal-list-container")
                                    ),
                                ],
                                value="all-journal-list",
                            ),
                            dmc.AccordionItem(
                                [
                                    dmc.AccordionControl("User Profile"),
                                    dmc.AccordionPanel(
                                        dcc.Link(
                                            "Go to your profile page", href="/profile"
                                        )
                                    ),
                                ],
                                value="profile",
                            ),
                        ],
                        value="my-journal-list",  # Start with the accordion open
                    ),
                ]
            )
        return html.Div("Loading...")

    @app.callback(
        Output("journal-modal", "opened"),
        Input("create-journal-btn", "n_clicks"),
        Input("cancel-journal-btn", "n_clicks"),
        Input("save-journal-btn", "n_clicks"),
        State("modal-state-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_modal_open_close(n_create, n_cancel, n_save, modal_state):
        ctx = callback_context
        if not ctx.triggered:
            return no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "create-journal-btn":
            return True
        if trigger_id in ["cancel-journal-btn", "save-journal-btn"]:
            return False

        return modal_state.get("opened", False)

    @app.callback(
        [
            Output("journal-title-input", "value"),
            Output("journal-start-date-picker", "value"),
            Output("journal-days-input", "value"),
            Output("upload-image", "contents", allow_duplicate=True),
            Output("output-image-upload", "children", allow_duplicate=True),
        ],
        Input("journal-modal", "opened"),
        prevent_initial_call=True,
    )
    def clear_modal_inputs(opened):
        if not opened:
            return (
                "",
                None,
                1,
                None,
                html.Img(
                    src="https://via.placeholder.com/200x150",
                    style={"width": "100%", "height": "auto"},
                ),
            )
        return no_update, no_update, no_update, no_update, no_update

    @app.callback(
        Output("output-image-upload", "children", allow_duplicate=True),
        Input("upload-image", "contents"),
        prevent_initial_call=True,
    )
    def update_output(contents):
        if contents is not None:
            return html.Img(src=contents, style={"width": "100%", "height": "auto"})
        return html.Img(
            src="https://via.placeholder.com/200x150",
            style={"width": "100%", "height": "auto"},
        )

    @app.callback(
        [
            Output("journal-update-trigger-store", "data"),
            Output("selected-journal-store", "data"),
            Output("modal-state-store", "data"),
            Output("url", "pathname", allow_duplicate=True),
            Output("journal-title-input", "error"),
            Output("journal-start-date-picker", "error"),
        ],
        Input("save-journal-btn", "n_clicks"),
        [
            State("user-info-store", "data"),
            State("journal-title-input", "value"),
            State("upload-image", "contents"),
            State("upload-image", "filename"),
            State("journal-start-date-picker", "value"),
            State("journal-days-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_new_journal(
        n_clicks,
        user_info,
        title,
        cover_image_contents,
        cover_image_filename,
        start_date,
        days,
    ):
        if not n_clicks:
            return (
                no_update,
                no_update,
                {"opened": True},
                no_update,
                no_update,
                no_update,
            )

        title_error = "Title is required." if not title else None
        start_date_error = "Start date is required." if not start_date else None

        if title_error or start_date_error:
            return (
                no_update,
                no_update,
                {"opened": True},
                no_update,
                title_error,
                start_date_error,
            )

        if user_info:
            user_id = user_info["uid"]
            # Create journal without the image first
            journal_id = create_journal(
                user_id=user_id,
                title=title,
                description=None,
                privacy=None,
                cover_image_url=None,
                start_date=start_date,
                days=days,
                places=None,
                journal_entries=None,
            )

            if journal_id:
                # If there's a cover image, upload it
                if cover_image_contents:
                    upload_cover_image(
                        journal_id, cover_image_contents, cover_image_filename
                    )

                # On success, redirect to the new journal's page
                return (
                    journal_id,
                    journal_id,
                    {"opened": False},
                    f"/journal/{journal_id}/edit",
                    None,
                    None,
                )
            else:
                # On failure, do not trigger a refresh
                return (
                    no_update,
                    no_update,
                    {"opened": True},
                    no_update,
                    "Error",
                    "Failed to create journal.",
                )

        # On user error, do not trigger a refresh
        return (
            no_update,
            no_update,
            {"opened": True},
            no_update,
            "Error",
            "User not logged in.",
        )

    @app.callback(
        Output("journal-list-container", "children"),
        [
            Input("user-info-store", "data"),
            Input("journal-update-trigger-store", "data"),
        ],
    )
    def display_journals(user_info, trigger_data):
        if not user_info:
            return html.P("Please log in to see your journals.")

        user_id = user_info["uid"]
        journals = get_user_journals(user_id)

        if not journals:
            return html.P("You haven't created any journals yet.")

        author_ids = [journal.get("user_id") for journal in journals]
        user_profiles = get_user_profiles_by_ids(author_ids)

        journal_cards = []
        for journal in journals:
            # Use duration instead of start_date for the badge
            duration_str = f"{journal.get('days', 1)} Days"
            author_id = journal.get("user_id")
            author_profile = user_profiles.get(author_id)
            author_avatar = (
                author_profile.get("avatar_url") if author_profile else None
            )
            display_name = (
                author_profile.get("display_name")
                if author_profile
                else "Anonymous"
            )

            if author_avatar:
                avatar_component = dmc.Avatar(src=author_avatar, radius="xl")
            else:
                initials = "".join(
                    [name[0] for name in display_name.split()]
                ).upper()
                if len(initials) > 2:
                    initials = initials[:2]
                avatar_component = dmc.Avatar(
                    children=initials, radius="xl", color="blue"
                )

            status = journal.get("status", "draft")
            card = dmc.Card(
                children=[
                    dmc.CardSection(
                        dmc.Image(
                            src=journal.get(
                                "cover_image_url", "https://via.placeholder.com/150"
                            ),
                            h=160,
                        )
                    ),
                    dmc.Group(
                        [
                            dmc.Group(
                                [
                                    avatar_component,
                                    dmc.Text(
                                        journal.get("title", "No Title"), fw=500
                                    ),
                                ],
                            ),
                            dmc.Badge(
                                status.capitalize(),
                                color="blue" if status == "draft" else "green",
                                variant="light",
                            ),
                        ],
                        justify="space-between",
                        mt="md",
                        mb="xs",
                    ),
                    dmc.Text(
                        journal.get("summary", "No summary available."),
                        size="sm",
                        c="dimmed",
                        lineClamp=2,
                        mt="sm",
                    ),
                    dmc.Group(
                        [
                            dcc.Link(
                                dmc.Button(
                                    "View Details", variant="light", color="blue"
                                ),
                                href=f"/journal/{journal.get('id')}/view",
                                style={"textDecoration": "none", "flex": 1},
                            ),
                            dmc.Button(
                                "Delete",
                                id={
                                    "type": "delete-journal-btn",
                                    "index": journal.get("id"),
                                },
                                variant="light",
                                color="red",
                            ),
                        ],
                        grow=True,
                        mt="md",
                    ),
                ],
                withBorder=True,
                shadow="sm",
                radius="md",
                style={"width": 300, "margin": "1rem"},
            )
            journal_cards.append(card)

        return dmc.Group(journal_cards)

    @app.callback(
        Output("all-journal-list-container", "children"),
        [
            Input("user-info-store", "data"),
            Input("journal-update-trigger-store", "data"),
        ],
    )
    def display_all_journals(user_info, trigger_data):
        if not user_info:
            return html.P("Please log in to see journals.")

        user_id = user_info["uid"]
        journals = get_all_journals()

        if not journals:
            return html.P("No journals have been created yet.")

        author_ids = [journal.get("user_id") for journal in journals]
        user_profiles = get_user_profiles_by_ids(author_ids)

        journal_cards = []
        for journal in journals:
            duration_str = f"{journal.get('days', 1)} Days"
            author_id = journal.get("user_id")
            author_profile = user_profiles.get(author_id)
            author_avatar = (
                author_profile.get("avatar_url") if author_profile else None
            )
            display_name = (
                author_profile.get("display_name")
                if author_profile
                else "Anonymous"
            )

            if author_avatar:
                avatar_component = dmc.Avatar(src=author_avatar, radius="xl")
            else:
                initials = "".join(
                    [name[0] for name in display_name.split()]
                ).upper()
                if len(initials) > 2:
                    initials = initials[:2]
                avatar_component = dmc.Avatar(
                    children=initials, radius="xl", color="blue"
                )

            action_buttons = [
                dcc.Link(
                    dmc.Button("View Details", variant="light", color="blue"),
                    href=f"/journal/{journal.get('id')}/view",
                    style={"textDecoration": "none", "flex": 1},
                )
            ]

            if journal.get("user_id") == user_id:
                action_buttons.append(
                    dmc.Button(
                        "Delete",
                        id={
                            "type": "delete-journal-btn",
                            "index": journal.get("id"),
                        },
                        variant="light",
                        color="red",
                    )
                )

            duration_str = f"{journal.get('days', 1)} Days"
            card = dmc.Card(
                children=[
                    dmc.CardSection(
                        dmc.Image(
                            src=journal.get(
                                "cover_image_url", "https://via.placeholder.com/150"
                            ),
                            h=160,
                        )
                    ),
                    dmc.Group(
                        [
                            dmc.Group(
                                [
                                    avatar_component,
                                    dmc.Text(
                                        journal.get("title", "No Title"), fw=500
                                    ),
                                ],
                            ),
                            dmc.Badge(duration_str, color="blue", variant="light"),
                        ],
                        justify="space-between",
                        mt="md",
                        mb="xs",
                    ),
                    dmc.Text(
                        journal.get("summary", "No summary available."),
                        size="sm",
                        c="dimmed",
                        lineClamp=2,
                        mt="sm",
                    ),
                    dmc.Group(
                        action_buttons,
                        grow=True,
                        mt="md",
                    ),
                ],
                withBorder=True,
                shadow="sm",
                radius="md",
                style={"width": 300, "margin": "1rem"},
            )
            journal_cards.append(card)

        return dmc.Group(journal_cards)

    @app.callback(
        [
            Output("delete-confirm-modal", "opened"),
            Output("journal-to-delete-store", "data"),
        ],
        [
            Input({"type": "delete-journal-btn", "index": ALL}, "n_clicks"),
            Input("cancel-delete-btn", "n_clicks"),
            Input("confirm-delete-btn", "n_clicks"),
        ],
        State("journal-to-delete-store", "data"),
        prevent_initial_call=True,
    )
    def handle_delete_modal(delete_clicks, n_cancel, n_confirm, journal_to_delete):
        ctx = callback_context
        if not ctx.triggered or not any(ctx.triggered):
            return no_update, no_update

        # Check if any of the delete buttons were actually clicked
        delete_button_clicked = False
        for trigger in ctx.triggered:
            if (
                "delete-journal-btn" in trigger["prop_id"]
                and trigger.get("value") is not None
            ):
                delete_button_clicked = True
                trigger_id = trigger["prop_id"]
                break

        if delete_button_clicked:
            journal_id = json.loads(trigger_id.split(".")[0])["index"]
            return True, journal_id

        # Handle cancel and confirm buttons
        trigger_id_str = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id_str in ["cancel-delete-btn", "confirm-delete-btn"]:
            return False, None

        return no_update, no_update

    @app.callback(
        Output("journal-update-trigger-store", "data", allow_duplicate=True),
        Input("confirm-delete-btn", "n_clicks"),
        State("journal-to-delete-store", "data"),
        prevent_initial_call=True,
    )
    def process_journal_deletion(n_clicks, journal_id):
        if not n_clicks or not journal_id:
            return no_update

        if delete_journal(journal_id):
            # Trigger a refresh of the journal list
            return {"source": "delete", "status": "success", "journal_id": journal_id}

        return no_update
