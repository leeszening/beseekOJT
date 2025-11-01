import dash
from dash import html, dcc, Input, Output, State, no_update, ClientsideFunction, ALL
import dash_mantine_components as dmc
from datetime import datetime, timedelta
import logging
import plotly.graph_objects as go
from src.shared.journal_utils import (
    get_journal_with_details,
    update_journal,
    upload_cover_image,
    delete_cover_image,
    save_places_to_journal,
    fetch_journal_places,
    fetch_all_journal_places,
)
from src.shared.auth_utils import get_user_info
from src.components.timeline import create_timeline
from .layout import create_journal_edit_layout

logging.basicConfig(level=logging.INFO)


def register_journal_edit_callbacks(app):
    @app.callback(
        Output("journal-edit-store", "data"),
        Output("journal-edit-content", "children"),
        Output("page-load-store", "data"),
        Input("journal-edit-page-loaded", "data"),
        State("url", "pathname"),
        State("auth-store", "data"),
    )
    def load_journal_data(page_loaded, pathname, auth_data):
        if not page_loaded:
            return no_update, no_update, no_update

        parts = pathname.split("/")
        if len(parts) < 4 or not (parts[1] == "journal" and parts[3] == "edit"):
            return (
                no_update,
                "Invalid URL for editing a journal.",
                False,
            )

        journal_id = parts[2]
        journal = get_journal_with_details(journal_id)

        if not journal:
            return (
                no_update,
                html.Div("Journal not found."),
                False,
            )

        user_info = get_user_info(auth_data.get("idToken")) if auth_data else None
        if not user_info or user_info.uid != journal.get("user_id"):
            return (
                no_update,
                dmc.Alert(
                    "You are not authorized to edit this journal.", color="red"
                ),
                False,
            )

        edit_layout = create_journal_edit_layout(journal)
        return journal, edit_layout, True

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
            journal_data["status"] = new_status
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
            image_url = upload_cover_image(
                journal_id, image_contents, image_filename)
            if image_url:
                update_payload["cover_image_url"] = image_url
            else:
                return "Failed to upload cover image.", False, "red", no_update

        update_payload = {k: v for k, v in update_payload.items()
                          if v is not None}

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
        Output("journal-summary-input", "value"),
        Input("generate-summary-btn", "n_clicks"),
        State("journal-edit-store", "data"),
        prevent_initial_call=True,
    )
    def generate_summary(n_clicks, journal_data):
        if not n_clicks:
            return no_update

        journal_id = journal_data.get("id")
        all_places = fetch_all_journal_places(journal_id)

        if not all_places:
            return "No places found to generate a summary."

        # Simple summary based on place names
        place_names = [place.get("name") for place in all_places if place.get("name")]
        
        if not place_names:
            return "No places with names found to generate a summary."

        # Create a simple summary string
        summary = f"This journey includes visits to: {', '.join(sorted(list(set(place_names))))}."
        
        return summary

    @app.callback(
        Output("full-timeline-container", "children"),
        Input("journal-edit-store", "data"),
        Input("journal-start-date-picker", "value"),
        Input("journal-days-input", "value"),
        Input("timeline-update-store", "data"),
    )
    def update_timeline_tabs(journal_data, start_date_str, days, _):
        if not journal_data:
            return dmc.Text("Loading journal data...", c="dimmed")

        journal_id = journal_data.get("id")
        start_date_str = start_date_str or journal_data.get("start_date")
        days = days or journal_data.get("days")

        all_places = fetch_all_journal_places(journal_id)
        
        return create_timeline(start_date_str, days, all_places, is_editable=True)

    app.clientside_callback(
        """
        function(page_loaded) {
            if (page_loaded) {
                const script = document.getElementById('google-maps-script');
                if (script) {
                    script.onerror = function() {
                        const errorDiv = document.getElementById('map-error-div');
                        if (errorDiv) {
                            errorDiv.innerHTML = 'Failed to load Google Maps. Please check your internet connection and API key.';
                        }
                    };
                }
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('script-error-handler-output', 'data-dummy'),
        Input('page-load-store', 'data')
    )

    @app.callback(
        Output("add-place-modal", "opened"),
        Output("modal-context-store", "data"),
        Output("day-select-multiselect", "data"),
        Output("day-select-multiselect", "value"),
        Input({'type': 'add-place-btn', 'date': ALL}, 'n_clicks'),
        State("journal-start-date-picker", "value"),
        State("journal-days-input", "value"),
        prevent_initial_call=True
    )
    def open_add_place_modal(n_clicks, start_date_str, days):
        if not any(n_clicks) or not start_date_str or not days:
            return no_update, no_update, no_update, no_update

        ctx = dash.callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        import ast
        date_str = ast.literal_eval(button_id)['date']

        try:
            start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
        except (ValueError, AttributeError):
            return no_update, no_update, no_update, no_update

        day_options = [
            {
                'label': f"Day {i + 1}",
                'value': (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            }
            for i in range(days)
        ]
        
        return True, {'date': date_str}, day_options, [date_str]

    @app.callback(
        Output("add-place-modal", "opened", allow_duplicate=True),
        Input("cancel-add-place-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_add_place_modal(n_clicks):
        if n_clicks:
            return False
        return no_update

    app.clientside_callback(
        """
        function(opened) {
            if (opened) {
                // Use a short delay to ensure the modal and its contents are fully rendered
                setTimeout(function() {
                    if (window.initAutocomplete) {
                        window.initAutocomplete();
                    }
                }, 100);
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('gmaps-place-data-store', 'id', allow_duplicate=True), # Dummy output
        Input('add-place-modal', 'opened'),
        prevent_initial_call=True
    )

    @app.callback(
        Output('place-name-output', 'value'),
        Output('place-address-output', 'value'),
        Output('place-type-output', 'value'),
        Output('place-coords-output', 'value'),
        Output('place-opening-hours-output', 'value'),
        Output('place-phone-output', 'value'),
        Output('place-website-output', 'value'),
        Output('place-friendliness-checkbox', 'value'),
        Input('gmaps-place-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_place_details_from_store(data):
        if not data:
            return "", "", "", "", "", "", "", []

        import json
        place_data = json.loads(data)

        name = place_data.get('name', '')
        address = place_data.get('address', '')
        types = ", ".join(place_data.get('types', [])).replace('_', ' ').title()
        
        location = place_data.get('location', {})
        coords = f"{location.get('lat', ''):.6f}, {location.get('lng', ''):.6f}" if location else ""
        
        opening_hours = "\n".join(place_data.get('opening_hours', []))
        phone = place_data.get('phone', '')
        website = place_data.get('website', '')
        
        friendliness = []
        if place_data.get('oku_friendly'):
            friendliness.append('oku')
        # Note: Google API does not provide 'family' or 'kids' friendly directly.
        # This would need to be inferred or entered manually. 'oku' is based on
        # 'wheelchair_accessible_entrance'.

        return name, address, types, coords, opening_hours, phone, website, friendliness

    @app.callback(
        Output('gmaps-data-poller', 'disabled'),
        Input('add-place-modal', 'opened')
    )
    def toggle_gmaps_poller(opened):
        return not opened

    app.clientside_callback(
        """
        function(n_intervals) {
            if (window.gmaps_selected_place) {
                const data = window.gmaps_selected_place;
                window.gmaps_selected_place = null; // Clear the global variable
                return data;
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('gmaps-place-data-store', 'data'),
        Input('gmaps-data-poller', 'n_intervals')
    )

    @app.callback(
        Output("add-place-modal", "opened", allow_duplicate=True),
        Output("edit-notification", "children", allow_duplicate=True),
        Output("edit-notification", "hide", allow_duplicate=True),
        Output("edit-notification", "color", allow_duplicate=True),
        Output("confirm-add-place-btn", "loading"),
        Output("timeline-update-store", "data"),
        Input("confirm-add-place-btn", "n_clicks"),
        State("url", "pathname"),
        State("gmaps-place-data-store", "data"),
        State("day-select-multiselect", "value"),
        State("place-description-textarea", "value"),
        State("place-type-multiselect", "value"),
        State("place-friendliness-checkbox", "value"),
        prevent_initial_call=True,
    )
    def handle_confirm_add_place(
        n_clicks,
        pathname,
        gmaps_place_data,
        dates,
        description,
        category,
        friendliness,
    ):
        if not n_clicks:
            return no_update, no_update, True, "green", False, no_update

        journal_id = pathname.split("/")[2]

        if not gmaps_place_data:
            return (
                no_update,
                "No place data found. Please select a place from the search box.",
                False,
                "red",
                False,
                no_update,
            )

        if not dates:
            return (
                no_update,
                "Please select at least one date.",
                False,
                "red",
                False,
                no_update,
            )

        import json
        place_data_base = json.loads(gmaps_place_data)

        # Combine all data into a single dictionary
        place_data_base.update(
            {
                "description": description,
                "category": category,
                "friendliness": friendliness,
            }
        )

        places_to_save = []
        for date in dates:
            place_data = place_data_base.copy()
            place_data["date"] = date
            places_to_save.append(place_data)

        if save_places_to_journal(journal_id, places_to_save):
            return False, "Place(s) added successfully!", False, "green", False, datetime.now().isoformat()
        else:
            return (
                no_update,
                "Failed to save place for one or more dates. Please try again.",
                False,
                "red",
                False,
                no_update,
            )
