import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_mantine_components as dmc
from src.shared.journal_utils import (
    get_journal_with_details,
    update_journal,
    add_place,
    get_currency_data,
    upload_cover_image,
    delete_cover_image,
    delete_places_outside_date_range,
)
from src.shared.auth_utils import get_user_info
from datetime import datetime, timedelta
from src.pages.journal_detail_page import create_timeline


def journal_edit_layout(journal_id=None, auth_data=None):
    return html.Div(
        [
            dcc.Store(id="journal-edit-store"),
            dcc.Store(id="places-store"),
            dcc.Store(id="page-load-store", data=False),
            dcc.Interval(
                id="journal-load-interval", interval=500, n_intervals=0, max_intervals=5
            ),
            html.Div(
                id="journal-edit-content",
                style={"padding": "2rem"},
                children=[dmc.LoadingOverlay(visible=True)],
            ),
        ]
    )


def register_journal_edit_callbacks(app):
    @app.callback(
        Output("journal-edit-store", "data"),
        Output("places-store", "data"),
        Output("journal-edit-content", "children"),
        Output("journal-load-interval", "disabled"),
        Output("page-load-store", "data"),
        Input("journal-load-interval", "n_intervals"),
        State("url", "pathname"),
        State("auth-store", "data"),
    )
    def load_journal_data(n_intervals, pathname, auth_data):
        parts = pathname.split("/")
        if len(parts) < 4 or not (parts[1] == "journal" and parts[3] == "edit"):
            return (
                no_update,
                no_update,
                "Invalid URL for editing a journal.",
                True,
                False,
            )

        journal_id = parts[2]
        journal = get_journal_with_details(journal_id)

        if not journal:
            if n_intervals >= 4:  # Corresponds to max_intervals=5 (0, 1, 2, 3, 4)
                return (
                    no_update,
                    no_update,
                    html.Div("Journal not found after several attempts."),
                    True,
                )
            return no_update, no_update, no_update, False  # Keep trying

        # If journal is found, disable the interval and render the page
        if journal:
            user_info = get_user_info(auth_data.get("idToken")) if auth_data else None
            if not user_info or user_info.uid != journal.get("user_id"):
                return (
                    no_update,
                    no_update,
                    dmc.Alert(
                        "You are not authorized to edit this journal.", color="red"
                    ),
                    True,
                )

            start_date = journal.get("start_date", "")
            days = journal.get("days", 1)
            nights = journal.get("nights", 0)
            places = journal.get("journalPlaces", [])
            status = journal.get("status", "draft")

            edit_layout = html.Div(
                [
                    dmc.Group(
                        [
                            html.H1(f"Editing: {journal.get('title', 'No Title')}"),
                            dmc.Badge(
                                status.capitalize(),
                                color="blue" if status == "draft" else "green",
                                variant="light",
                                id="journal-status-badge",
                            ),
                        ],
                        justify="space-between",
                    ),
                    dmc.Alert(
                        id="edit-notification",
                        title="Notification",
                        children="",
                        color="green",
                        withCloseButton=True,
                        hide=True,
                    ),
                    dmc.Grid(
                        children=[
                            dmc.GridCol(
                                [
                                    dmc.Text("Cover Image"),
                                    dcc.Upload(
                                        id="upload-image-edit",
                                        children=html.Div(
                                            [
                                                "Drag and Drop or ",
                                                html.A("Select Files"),
                                            ]
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
                                    html.Img(
                                        id="output-image-upload",
                                        src=journal.get(
                                            "cover_image_url",
                                            "https://via.placeholder.com/200x150",
                                        ),
                                        style={"width": "100%", "height": "auto"},
                                    ),
                                    dmc.Group(
                                        [
                                            dmc.Button(
                                                "Delete Cover Image",
                                                id="delete-cover-image-btn",
                                                color="red",
                                                variant="outline",
                                                style={"marginTop": "10px"},
                                            )
                                        ],
                                        justify="center",
                                    ),
                                ],
                                span=4,
                            ),
                            dmc.GridCol(
                                [
                                    dmc.TextInput(
                                        id="journal-title-input",
                                        label="Title",
                                        value=journal.get("title", ""),
                                        required=True,
                                    ),
                                    dmc.Textarea(
                                        id="journal-summary-input",
                                        label="Summary",
                                        value=journal.get("summary", ""),
                                    ),
                                    dmc.Textarea(
                                        id="journal-introduction-input",
                                        label="Introduction",
                                        value=journal.get("introduction", ""),
                                    ),
                                    dmc.DatePickerInput(
                                        id="journal-start-date-picker",
                                        label="Start Date",
                                        value=start_date if start_date else None,
                                        required=True,
                                    ),
                                    dmc.NumberInput(
                                        id="journal-days-input",
                                        label="Days",
                                        value=days,
                                        min=1,
                                        required=True,
                                    ),
                                    dmc.Group(
                                        [
                                            dmc.NumberInput(
                                                id="journal-total-cost-input",
                                                label="Total Cost",
                                                value=journal.get("total_cost"),
                                                min=0,
                                                style={"flex": 1},
                                            ),
                                            dmc.Autocomplete(
                                                id="journal-currency-input",
                                                label="Currency",
                                                data=get_currency_data(),
                                                value=journal.get("currency", "🇲🇾 MYR"),
                                                style={"flex": 1},
                                            ),
                                        ],
                                        grow=True,
                                        style={"margin-top": "1rem"},
                                    ),
                                ],
                                span=8,
                            ),
                        ],
                        gutter="xl",
                    ),
                    html.Hr(style={"margin": "2rem 0"}),
                    dmc.Group(
                        [
                            html.H2("Timeline"),
                            dmc.Button(
                                "Add Place", id="add-place-btn", variant="outline"
                            ),
                        ],
                        justify="space-between",
                    ),
                    html.Div(id="full-timeline-container"),
                    dmc.Modal(
                        id="add-place-modal",
                        title="Add a New Place",
                        zIndex=10000,
                        opened=False,
                        children=[
                            dmc.TextInput(
                                id="place-name-input", label="Place Name", required=True
                            ),
                            dmc.TextInput(
                                id="place-address-input", label="Address", required=True
                            ),
                            dmc.ChipGroup(
                                id="place-date-select", children=[], multiple=True
                            ),
                            dmc.Textarea(
                                id="place-notes-input", label="Notes (Optional)"
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        "Cancel",
                                        id="cancel-place-btn",
                                        color="gray",
                                        variant="outline",
                                    ),
                                    dmc.Button("Save Place", id="save-place-btn"),
                                ],
                                justify="flex-end",
                                style={"marginTop": "1rem"},
                            ),
                        ],
                    ),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Publish" if status == "draft" else "Unpublish",
                                id="toggle-status-btn",
                                color="green" if status == "draft" else "orange",
                            ),
                            dcc.Link(
                                dmc.Button("Cancel", color="gray", variant="outline"),
                                href=f"/journal/{journal_id}/view",
                            ),
                            dmc.Button("Save Changes", id="save-journal-changes-btn"),
                        ],
                        justify="flex-end",
                        style={"marginTop": "1rem"},
                    ),
                ]
            )
            return journal, places, edit_layout, True, True

        return no_update, no_update, no_update, True, False

    @app.callback(
        Output("output-image-upload", "src"),
        Input("upload-image-edit", "contents"),
        State("output-image-upload", "src"),
    )
    def update_output(contents, src):
        if contents is not None:
            return contents
        return src

    @app.callback(
        Output("journal-edit-store", "data", allow_duplicate=True),
        Output("journal-status-badge", "children"),
        Output("toggle-status-btn", "children"),
        Output("toggle-status-btn", "color"),
        Output("edit-notification", "children", allow_duplicate=True),
        Output("edit-notification", "hide", allow_duplicate=True),
        Output("edit-notification", "color", allow_duplicate=True),
        Input("toggle-status-btn", "n_clicks"),
        State("journal-edit-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_journal_status(n_clicks, journal_data):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, True, "green"

        journal_id = journal_data.get("id")
        current_status = journal_data.get("status", "draft")
        new_status = "public" if current_status == "draft" else "draft"

        if update_journal(journal_id, {"status": new_status}):
            journal_data["status"] = new_status  # Update local state
            return (
                journal_data,
                new_status.capitalize(),
                "Publish" if new_status == "draft" else "Unpublish",
                "green" if new_status == "draft" else "orange",
                f"Journal status changed to {new_status}.",
                False,
                "green",
            )
        else:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                "Failed to update journal status.",
                False,
                "red",
            )

    @app.callback(
        [
            Output("edit-notification", "children", allow_duplicate=True),
            Output("edit-notification", "hide", allow_duplicate=True),
            Output("edit-notification", "color", allow_duplicate=True),
            Output("url", "pathname", allow_duplicate=True),
        ],
        [Input("save-journal-changes-btn", "n_clicks")],
        [
            State("journal-edit-store", "data"),
            State("journal-title-input", "value"),
            State("journal-summary-input", "value"),
            State("journal-introduction-input", "value"),
            State("journal-start-date-picker", "value"),
            State("journal-days-input", "value"),
            State("journal-total-cost-input", "value"),
            State("journal-currency-input", "value"),
            State("upload-image-edit", "contents"),
            State("upload-image-edit", "filename"),
        ],
        prevent_initial_call=True,
    )
    def handle_save_journal(
        n_clicks,
        journal_data,
        title,
        summary,
        introduction,
        start_date,
        days,
        total_cost,
        currency,
        image_contents,
        image_filename,
    ):
        if not n_clicks:
            return no_update, True, "green", no_update

        journal_id = journal_data.get("id")

        update_payload = {
            "title": title,
            "summary": summary,
            "introduction": introduction,
            "start_date": start_date,
            "days": days,
            "nights": days - 1 if days > 0 else 0,
            "total_cost": total_cost,
            "currency": currency,
        }

        if image_contents:
            image_url = upload_cover_image(journal_id, image_contents, image_filename)
            if image_url:
                update_payload["cover_image_url"] = image_url
            else:
                return "Failed to upload cover image.", False, "red", no_update

        update_payload = {k: v for k, v in update_payload.items() if v is not None}

        if update_journal(journal_id, update_payload):
            return (
                "Journal updated successfully!",
                False,
                "green",
                f"/journal/{journal_id}/view",
            )
        else:
            return "Failed to update journal.", False, "red", no_update

    @app.callback(
        [
            Output("edit-notification", "children", allow_duplicate=True),
            Output("edit-notification", "hide", allow_duplicate=True),
            Output("edit-notification", "color", allow_duplicate=True),
            Output("url", "pathname", allow_duplicate=True),
        ],
        [Input("delete-cover-image-btn", "n_clicks")],
        [State("journal-edit-store", "data")],
        prevent_initial_call=True,
    )
    def handle_delete_cover_image(n_clicks, journal_data):
        if not n_clicks:
            return no_update, True, "green", no_update

        journal_id = journal_data.get("id")
        if delete_cover_image(journal_id):
            return "Cover image deleted.", False, "blue", f"/journal/{journal_id}/edit"
        else:
            return "Failed to delete cover image.", False, "red", no_update

    @app.callback(
        Output("journal-edit-store", "data", allow_duplicate=True),
        Output("places-store", "data", allow_duplicate=True),
        [
            Input("journal-start-date-picker", "value"),
            Input("journal-days-input", "value"),
        ],
        State("journal-edit-store", "data"),
        prevent_initial_call=True,
    )
    def handle_date_change(start_date, days, journal_data):
        ctx = dash.callback_context
        if not ctx.triggered:
            return no_update, no_update

        if not start_date or not days or not journal_data:
            return no_update, no_update

        initial_start_date = journal_data.get("start_date", "").split("T")[0]
        initial_days = journal_data.get("days", 1)
        new_start_date_str = start_date.split("T")[0]

        if initial_start_date == new_start_date_str and initial_days == days:
            return no_update, no_update

        journal_id = journal_data.get("id")
        start_date_obj = datetime.fromisoformat(start_date.split("T")[0])
        end_date_obj = start_date_obj + timedelta(days=days - 1)
        end_date = end_date_obj.isoformat()

        delete_places_outside_date_range(journal_id, start_date, end_date)

        journal_data["start_date"] = start_date
        journal_data["days"] = days

        fresh_journal = get_journal_with_details(journal_id)
        places = fresh_journal.get("journalPlaces", [])

        return journal_data, places

    @app.callback(
        Output("full-timeline-container", "children"),
        [Input("places-store", "data"), Input("journal-edit-store", "data")],
    )
    def update_full_timeline(places, journal_data):
        start_date = journal_data.get("start_date")
        days = journal_data.get("days")
        if not all([start_date, days]):
            return dmc.Text(
                "Please set a start date and number of days for the journal.",
                c="orange",
            )

        return create_timeline(start_date, days, places)

    @app.callback(
        Output("add-place-modal", "opened"),
        [Input("add-place-btn", "n_clicks"), Input("cancel-place-btn", "n_clicks")],
        [State("add-place-modal", "opened")],
        prevent_initial_call=True,
    )
    def toggle_modal(n_add, n_cancel, is_open):
        if n_add or n_cancel:
            return not is_open
        return is_open

    @app.callback(
        Output("place-date-select", "children"),
        Input("add-place-btn", "n_clicks"),
        State("journal-edit-store", "data"),
        prevent_initial_call=True,
    )
    def populate_date_dropdown(n_clicks, journal_data):
        start_date_str = journal_data.get("start_date")
        days = journal_data.get("days")
        if not start_date_str or not days:
            return []

        start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")

        return [
            dmc.Chip(
                f"Day {i + 1}: {(start_date + timedelta(days=i)).strftime('%B %d')}",
                value=(start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            )
            for i in range(days)
        ]

    @app.callback(
        [
            Output("places-store", "data", allow_duplicate=True),
            Output("add-place-modal", "opened", allow_duplicate=True),
            Output("full-timeline-container", "children", allow_duplicate=True),
        ],
        Input("save-place-btn", "n_clicks"),
        [
            State("journal-edit-store", "data"),
            State("place-name-input", "value"),
            State("place-address-input", "value"),
            State("place-date-select", "value"),
            State("place-notes-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_place(n_clicks, journal_data, name, address, selected_dates, notes):
        if not n_clicks:
            return no_update, no_update, no_update

        journal_id = journal_data.get("id")
        if not name or not address or not selected_dates:
            return no_update, True, no_update

        for place_date in selected_dates:
            place_data = {
                "name": name,
                "address": address,
                "date": place_date,
                "notes": notes,
            }
            add_place(journal_id, place_data)

        fresh_journal = get_journal_with_details(journal_id)
        places = fresh_journal.get("journalPlaces", [])
        start_date = fresh_journal.get("start_date")
        end_date = fresh_journal.get("end_date")

        return places, False, create_timeline(start_date, end_date, places)
