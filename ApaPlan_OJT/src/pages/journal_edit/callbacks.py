import dash
from dash import html, dcc, Input, Output, State, no_update, ClientsideFunction
import dash_mantine_components as dmc
from datetime import datetime, timedelta
import logging
import plotly.graph_objects as go
from src.shared.journal_utils import (
    get_journal_with_details,
    update_journal,
    add_place,
    update_place,
    upload_cover_image,
    delete_cover_image,
    delete_places_outside_date_range,
    delete_place,
)
from src.shared.auth_utils import get_user_info
from .layout import create_journal_edit_layout, create_edit_timeline

logging.basicConfig(level=logging.INFO)


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
            if n_intervals >= 4:
                return (
                    no_update,
                    no_update,
                    html.Div("Journal not found after several attempts."),
                    True,
                    False
                )
            return no_update, no_update, no_update, False, False

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
                    False
                )

            places = journal.get("journalPlaces", [])
            edit_layout = create_journal_edit_layout(journal)
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
        journal_id = journal_data.get("id")
        if not all([start_date, days]):
            return dmc.Text(
                "Please set a start date and number of days for the journal.",
                c="orange",
            )

        return create_edit_timeline(start_date, days, places, journal_id)

    @app.callback(
        Output("add-place-modal", "opened"),
        Output("place-to-edit-store", "data"),
        [
            Input({"type": "add-place-day-btn", "date": dash.ALL}, "n_clicks"),
            Input({"type": "edit-place-btn", "place_id": dash.ALL}, "n_clicks"),
            Input("cancel-place-btn", "n_clicks"),
            Input("save-place-btn", "n_clicks"),
        ],
        [State("add-place-modal", "opened")],
        prevent_initial_call=True,
    )
    def toggle_modal(n_add, n_edit, n_cancel, n_save, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return no_update, no_update

        trigger_id_str = ctx.triggered[0]["prop_id"].split(".")[0]

        if "cancel-place-btn" in trigger_id_str or "save-place-btn" in trigger_id_str:
            return False, None

        if any(n is not None for n in n_add) or any(n is not None for n in n_edit):
            import json
            trigger_id = json.loads(trigger_id_str)
            place_id = trigger_id.get("place_id")
            return True, place_id if "edit-place-btn" in trigger_id_str else None

        return no_update, no_update

    @app.callback(
        Output("place-date-select", "children"),
        Output("place-date-select", "value"),
        Output("place-name-input", "value", allow_duplicate=True),
        Output("place-address-input", "value", allow_duplicate=True),
        Output("place-notes-input", "value"),
        Output("add-place-modal", "title"),
        Input("place-to-edit-store", "data"),
        Input({"type": "add-place-day-btn", "date": dash.ALL}, "n_clicks"),
        State("journal-edit-store", "data"),
        State("places-store", "data"),
        prevent_initial_call=True,
    )
    def populate_modal_for_add_or_edit(
        place_id, n_add, journal_data, places_data
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update, no_update

        start_date_str = journal_data.get("start_date")
        days = journal_data.get("days")
        if not start_date_str or not days:
            return [], [], "", "", "", "Add a New Place"

        start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
        date_options = [
            dmc.Chip(
                f"Day {i + 1}: {(start_date + timedelta(days=i)).strftime('%B %d')}",
                value=(start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            )
            for i in range(days)
        ]

        if place_id:  # Editing an existing place
            place = next((p for p in places_data if p["id"] == place_id), None)
            if place:
                return (
                    date_options,
                    [place.get("date", "").split("T")[0]],
                    place.get("name", ""),
                    place.get("address", ""),
                    place.get("notes", ""),
                    "Edit Place",
                )

        # Adding a new place
        trigger_id_str = ctx.triggered[0]["prop_id"].split(".")[0]
        if "add-place-day-btn" in trigger_id_str:
            import json
            date = json.loads(trigger_id_str).get("date")
            return date_options, [date] if date else [], "", "", "", "Add a New Place"

        return date_options, [], "", "", "", "Add a New Place"

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
            State("selected-place-json", "value"),
            State("place-to-edit-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def save_place(
        n_clicks,
        journal_data,
        name,
        address,
        selected_dates,
        notes,
        selected_place_json,
        place_id_to_edit,
    ):
        if not n_clicks:
            return no_update, no_update, no_update

        journal_id = journal_data.get("id")
        if not name or not address or not selected_dates:
            return no_update, True, no_update

        import json
        place_data_from_store = (
            json.loads(selected_place_json) if selected_place_json else {}
        )

        place_payload = {
            "name": name,
            "address": address,
            "date": selected_dates[0] if selected_dates else None,
            "notes": notes,
            "latitude": place_data_from_store.get("lat"),
            "longitude": place_data_from_store.get("lng"),
        }

        if place_id_to_edit:
            update_place(journal_id, place_id_to_edit, place_payload)
        else:
            add_place(journal_id, place_payload)

        fresh_journal = get_journal_with_details(journal_id)
        places = fresh_journal.get("journalPlaces", [])
        start_date = fresh_journal.get("start_date")
        days = fresh_journal.get("days")

        return places, False, create_edit_timeline(start_date, days, places, journal_id)


    app.clientside_callback(
        """
        function(opened) {
            if (opened) {
                // A short delay to ensure the modal is fully rendered before initializing the map
                setTimeout(() => {
                    if (window.initializeMapComponents) {
                        window.initializeMapComponents();
                    }
                }, 200);
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('add-place-modal', 'data-dummy'),
        Input('add-place-modal', 'opened')
    )

    @app.callback(
        Output('place-map', 'figure'),
        [Input('places-store', 'data'),
         Input('selected-place-json', 'value')],
        prevent_initial_call=True
    )
    def update_main_map_with_places(places, selected_place_json):
        import json
        selected_place = json.loads(selected_place_json) if selected_place_json else None

        logging.info(f"Updating map. Existing places: {len(places) if places else 0}")
        logging.info(f"Newly selected place: {selected_place}")
        places = places or []
        
        all_lats = [p['latitude'] for p in places if p.get('latitude') is not None]
        all_lons = [p['longitude'] for p in places if p.get('longitude') is not None]
        all_texts = [p.get('name', 'No Name') for p in places]
        
        # Add the newly selected place for temporary display
        if selected_place and selected_place.get('lat') is not None:
            all_lats.append(selected_place['lat'])
            all_lons.append(selected_place['lng'])
            all_texts.append(selected_place.get('name', 'New Selection'))

        if not all_lats or not all_lons:
            return go.Figure(go.Scattermapbox()).update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )

        fig = go.Figure(go.Scattermapbox(
            lat=all_lats,
            lon=all_lons,
            mode='markers',
            marker=go.scattermapbox.Marker(size=12),
            text=all_texts,
            hoverinfo='text'
        ))

        # Center the map on the last added pin (the new selection)
        center_lat = all_lats[-1]
        center_lon = all_lons[-1]
        zoom = 14 if selected_place else 10

        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        return fig

    @app.callback(
        Output('place-name-input', 'value'),
        Output('place-address-input', 'value'),
        Input('selected-place-json', 'value'),
        prevent_initial_call=True
    )
    def update_form_from_autocomplete(selected_place_json):
        import json
        place_data = json.loads(selected_place_json) if selected_place_json else None
        if place_data:
            return place_data.get('name', ''), place_data.get('address', '')
        return no_update, no_update

    @app.callback(
        Output("journal-summary-input", "value"),
        Input("generate-summary-btn", "n_clicks"),
        [State("places-store", "data"), State("journal-edit-store", "data")],
        prevent_initial_call=True,
    )
    def generate_summary(n_clicks, places, journal_data):
        logging.info("Generate summary callback triggered.")
        if not n_clicks:
            logging.info("No clicks detected, returning no_update.")
            return no_update

        if not places:
            logging.warning("No places found in places-store.")
            return "No places have been added yet."

        logging.info(f"Places data: {places}")
        logging.info(f"Journal data: {journal_data}")

        start_date_str = journal_data.get("start_date")
        if not start_date_str:
            logging.warning("Start date not found in journal_data.")
            return "Please set a start date for the journal first."

        try:
            start_date = datetime.fromisoformat(start_date_str.split("T")[0])
            logging.info(f"Parsed start date: {start_date}")

            places.sort(key=lambda p: p.get('date', ''))
            logging.info("Places sorted by date.")

            places_by_day = {}
            for place in places:
                place_date_str = place.get("date")
                if place_date_str:
                    place_date = datetime.fromisoformat(
                        place_date_str.split("T")[0]
                    )
                    day_number = (place_date - start_date).days + 1
                    if day_number not in places_by_day:
                        places_by_day[day_number] = []
                    places_by_day[day_number].append(
                        place.get("name", "Unnamed Place")
                    )

            logging.info(f"Places grouped by day: {places_by_day}")

            summary_parts = []
            for day in sorted(places_by_day.keys()):
                day_summary = f"Day {day}: {' - '.join(places_by_day[day])}"
                summary_parts.append(day_summary)

            final_summary = ", ".join(summary_parts)
            logging.info(f"Generated summary: {final_summary}")
            return final_summary
        except Exception as e:
            logging.error(f"Error during summary generation: {e}")
            return f"An error occurred: {e}"


    @app.callback(
        Output("places-store", "data", allow_duplicate=True),
        Output("delete-confirm-modal", "opened", allow_duplicate=True),
        Input("confirm-delete-btn", "n_clicks"),
        State("place-to-delete-store", "data"),
        State("journal-edit-store", "data"),
        prevent_initial_call=True,
    )
    def confirm_delete_place(n_clicks, place_id, journal_data):
        if not n_clicks or not place_id:
            return no_update, False

        journal_id = journal_data.get("id")
        if delete_place(journal_id, place_id):
            fresh_journal = get_journal_with_details(journal_id)
            return fresh_journal.get("journalPlaces", []), False

        return no_update, False

    @app.callback(
        Output("delete-confirm-modal", "opened", allow_duplicate=True),
        Output("place-to-delete-store", "data", allow_duplicate=True),
        Input({"type": "delete-place-btn", "place_id": dash.ALL}, "n_clicks"),
        Input("cancel-delete-btn", "n_clicks"),
        State("delete-confirm-modal", "opened"),
        prevent_initial_call=True,
    )
    def toggle_delete_modal(n_delete, n_cancel, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return no_update, no_update

        trigger_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if "cancel-delete-btn" in trigger_id_str:
            return False, no_update

        if any(n_clicks is not None for n_clicks in n_delete):
            import json
            trigger_id = json.loads(trigger_id_str)
            place_id = trigger_id.get("place_id")
            return True, place_id

        return no_update, no_update

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
