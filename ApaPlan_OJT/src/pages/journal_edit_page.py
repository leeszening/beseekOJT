from dash import html, dcc, Input, Output, State, no_update
import dash_mantine_components as dmc
from src.shared.journal_utils import get_journal_with_details, update_journal, add_place, get_currency_data
from src.shared.auth_utils import get_user_info
from datetime import datetime, timedelta
from src.pages.journal_detail_page import create_timeline

def journal_edit_layout(journal_id=None, auth_data=None):
    if not journal_id:
        return html.Div("No journal selected.")

    journal = get_journal_with_details(journal_id)
    if not journal:
        return html.Div("Journal not found.")

    user_info = get_user_info(auth_data.get('idToken')) if auth_data else None
    if not user_info or user_info.uid != journal.get('user_id'):
        return dmc.Alert("You are not authorized to edit this journal.", color="red")

    start_date = journal.get('start_date', '')
    end_date = journal.get('end_date', '')
    places = journal.get('journalPlaces', [])

    return html.Div([
        dcc.Store(id='journal-edit-store', data=journal),
        dcc.Store(id='places-store', data=places),
        html.H1(f"Editing: {journal.get('title', 'No Title')}"),
        dmc.Alert(id="edit-notification", title="Notification", children="", color="green", withCloseButton=True, hide=True),
        dmc.Grid(
            children=[
                dmc.GridCol(
                    [
                        dmc.Text("Cover Image"),
                        html.Img(
                            src=journal.get('cover_image_url', 'https://via.placeholder.com/200x150'),
                            style={'width': '100%', 'height': 'auto'}
                        ),
                    ],
                    span=4
                ),
                dmc.GridCol(
                    [
                        dmc.TextInput(id="journal-title-input", label="Title", value=journal.get('title', ''), required=True),
                        dmc.Textarea(id="journal-summary-input", label="Summary", value=journal.get('summary', '')),
                        dmc.Textarea(id="journal-introduction-input", label="Introduction", value=journal.get('introduction', '')),
                        dmc.DatePickerInput(id="journal-date-range-picker", type="range", label="Date Range", value=[start_date, end_date] if start_date and end_date else None, required=True),
                        dmc.Group(
                            [
                                dmc.NumberInput(id="journal-total-cost-input", label="Total Cost", value=journal.get('total_cost'), min=0, style={"flex": 1}),
                                dmc.Autocomplete(id="journal-currency-input", label="Currency", data=get_currency_data(), value=journal.get('currency', '🇲🇾 MYR'), style={"flex": 1}),
                            ],
                            grow=True,
                            style={"margin-top": "1rem"},
                        ),
                    ],
                    span=8
                ),
            ],
            gutter="xl",
        ),
        html.Hr(style={"margin": "2rem 0"}),
        dmc.Group([html.H2("Timeline"), dmc.Button("Add Place", id="add-place-btn", variant="outline")], justify="space-between"),
        html.Div(id='full-timeline-container'),
        dmc.Modal(
            id='add-place-modal',
            title="Add a New Place",
            zIndex=10000,
            opened=False,
            children=[
                dmc.TextInput(id="place-name-input", label="Place Name", required=True),
                dmc.TextInput(id="place-address-input", label="Address", required=True),
                dmc.ChipGroup(id="place-date-select", children=[], multiple=True),
                dmc.Textarea(id="place-notes-input", label="Notes (Optional)"),
                dmc.Group(
                    [
                        dmc.Button("Cancel", id="cancel-place-btn", color="gray", variant="outline"),
                        dmc.Button("Save Place", id="save-place-btn"),
                    ],
                    justify="flex-end",
                    style={"marginTop": "1rem"},
                ),
            ]
        ),
        dmc.Group(
            [
                dcc.Link(dmc.Button("Cancel", color="gray", variant="outline"), href=f"/journal/{journal_id}/view"),
                dmc.Button("Save Changes", id="save-journal-changes-btn"),
            ],
            justify="flex-end",
            style={"marginTop": "1rem"},
        ),
    ], style={"padding": "2rem"})

def register_journal_edit_callbacks(app):
    @app.callback(
        [
            Output("edit-notification", "children"),
            Output("edit-notification", "hide"),
            Output("edit-notification", "color"),
            Output('url', 'pathname', allow_duplicate=True)
        ],
        Input("save-journal-changes-btn", "n_clicks"),
        [
            State("journal-edit-store", "data"),
            State("journal-title-input", "value"),
            State("journal-summary-input", "value"),
            State("journal-introduction-input", "value"),
            State("journal-date-range-picker", "value"),
            State("journal-total-cost-input", "value"),
            State("journal-currency-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_journal_changes(n_clicks, journal_data, title, summary, introduction, date_range, total_cost, currency):
        if not n_clicks:
            return no_update, True, "green", no_update

        journal_id = journal_data.get('id')
        if not journal_id:
            return "Error: Journal ID not found.", False, "red", no_update

        start_date, end_date = (None, None)
        if date_range:
            start_date, end_date = date_range

        updated_data = {
            'title': title, 'summary': summary, 'introduction': introduction,
            'start_date': start_date, 'end_date': end_date,
            'total_cost': total_cost, 'currency': currency,
        }
        update_payload = {k: v for k, v in updated_data.items() if v is not None}

        if update_journal(journal_id, update_payload):
            return "Journal updated successfully!", False, "green", f"/journal/{journal_id}/view"
        else:
            return "Failed to update journal.", False, "red", no_update

    @app.callback(
        Output('full-timeline-container', 'children'),
        [Input('places-store', 'data'), Input('journal-edit-store', 'data')]
    )
    def update_full_timeline(places, journal_data):
        start_date = journal_data.get('start_date')
        end_date = journal_data.get('end_date')
        if not all([start_date, end_date]):
            return dmc.Text("Please set a date range for the journal.", c="orange")
        return create_timeline(start_date, end_date, places)

    @app.callback(
        Output('add-place-modal', 'opened'),
        [Input('add-place-btn', 'n_clicks'), Input('cancel-place-btn', 'n_clicks')],
        [State('add-place-modal', 'opened')],
        prevent_initial_call=True,
    )
    def toggle_modal(n_add, n_cancel, is_open):
        if n_add or n_cancel:
            return not is_open
        return is_open

    @app.callback(
        Output('place-date-select', 'children'),
        Input('add-place-btn', 'n_clicks'),
        State('journal-edit-store', 'data'),
        prevent_initial_call=True,
    )
    def populate_date_dropdown(n_clicks, journal_data):
        start_date_str = journal_data.get('start_date')
        end_date_str = journal_data.get('end_date')
        if not start_date_str or not end_date_str:
            return []
        
        start_date = datetime.strptime(start_date_str.split('T')[0], '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str.split('T')[0], '%Y-%m-%d')
        delta = end_date - start_date
        
        return [
            dmc.Chip(f"Day {i + 1}: {(start_date + timedelta(days=i)).strftime('%B %d')}", value=(start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
            for i in range(delta.days + 1)
        ]

    @app.callback(
        [
            Output('places-store', 'data', allow_duplicate=True),
            Output('add-place-modal', 'opened', allow_duplicate=True),
            Output('full-timeline-container', 'children', allow_duplicate=True)
        ],
        Input('save-place-btn', 'n_clicks'),
        [
            State('journal-edit-store', 'data'),
            State('place-name-input', 'value'),
            State('place-address-input', 'value'),
            State('place-date-select', 'value'),
            State('place-notes-input', 'value'),
        ],
        prevent_initial_call=True,
    )
    def save_place(n_clicks, journal_data, name, address, selected_dates, notes):
        if not n_clicks:
            return no_update, no_update, no_update

        journal_id = journal_data.get('id')
        if not name or not address or not selected_dates:
            return no_update, True, no_update

        for place_date in selected_dates:
            place_data = {'name': name, 'address': address, 'date': place_date, 'notes': notes}
            add_place(journal_id, place_data)

        fresh_journal = get_journal_with_details(journal_id)
        places = fresh_journal.get('journalPlaces', [])
        start_date = fresh_journal.get('start_date')
        end_date = fresh_journal.get('end_date')
        
        return places, False, create_timeline(start_date, end_date, places)
