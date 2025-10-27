from dash import (
    html, dcc, Input, Output, State, no_update, callback_context
)
import dash_mantine_components as dmc
from src.shared.journal_utils import get_journal, update_journal, add_place
from src.shared.auth_utils import get_user_info
from datetime import datetime, timedelta
from src.shared.journal_utils import get_currency_data


def create_timeline(start_date_str, end_date_str, places=None):
    """Generates a timeline accordion based on the date range."""
    try:
        start_date = datetime.strptime(
            start_date_str.split('T')[0], '%Y-%m-%d')
        end_date = datetime.strptime(
            end_date_str.split('T')[0], '%Y-%m-%d')
    except (ValueError, AttributeError):
        return dmc.Text("Invalid date format provided.", c="red")

    delta = end_date - start_date
    days = delta.days + 1

    if days <= 0:
        return dmc.Text("End date must be after start date.", c="red")

    timeline_items = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_str = current_date.strftime('%Y-%m-%d')
        day_label = f"Day {i + 1}: {current_date.strftime('%B %d, %Y')}"

        # Filter places for the current day
        day_places = [
            p for p in (places or [])
            if p.get('date', '').split('T')[0] == day_str
        ]

        # Create the content for the accordion panel
        if day_places:
            panel_content = [
                dmc.Paper(
                    [
                        dmc.Text(place.get('name', 'No name'), fw=500),
                        dmc.Text(place.get('address', 'No address'), size="sm"),
                        dmc.Text(place.get('notes', ''), size="sm", c="dimmed"),
                    ],
                    shadow="xs", p="sm", withBorder=True, mb="sm"
                ) for place in day_places
            ]
        else:
            panel_content = [dmc.Text("No places for this day.")]

        timeline_items.append(
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(day_label),
                    dmc.AccordionPanel(dmc.Stack(children=panel_content)),
                ],
                value=f"day-{i+1}"
            )
        )
    
    return dmc.Accordion(children=timeline_items, chevronPosition="left")


def journal_detail_layout(journal_id=None, auth_data=None, mode='view'):
    if not journal_id:
        return html.Div("No journal selected.")

    journal = get_journal(journal_id)
    if not journal:
        return html.Div("Journal not found.")

    places = journal.get('journalPlaces', [])

    # Determine if the current user is the author
    is_author = False
    if auth_data and 'idToken' in auth_data:
        user_info = get_user_info(auth_data['idToken'])
        if user_info:
            user_id = user_info.uid
            if user_id == journal.get('user_id'):
                is_author = True

    initial_mode = mode

    return html.Div([
        dcc.Store(id='auth-data', data=auth_data),
        dcc.Store(id='redirect-store'),
        dcc.Store(id='update-success-signal', data=None),
        dcc.Store(id='journal-detail-store', data=journal),
        dcc.Store(id='places-store', data=places),
        dcc.Store(id='timeline-refresh-signal', data=0),
        dcc.Store(id='page-mode-store', data={'mode': initial_mode}),
        dmc.Modal(
            id='add-place-modal',
            title="Add a New Place",
            zIndex=10000,
            opened=False,
            children=[
                dmc.TextInput(
                    id="place-name-input", label="Place Name", required=True
                ),
                dmc.Text(id="place-name-error", c="red", size="sm"),
                dmc.TextInput(
                    id="place-address-input", label="Address", required=True
                ),
                dmc.Text(id="place-address-error", c="red", size="sm"),
                dmc.Text("Assign to Day", size="sm", fw=500),
                dmc.ChipGroup(
                    id="place-date-select",
                    children=[],  # Populated by callback
                    multiple=True
                ),
                dmc.Text(id="place-date-error", c="red", size="sm"),
                dmc.Textarea(id="place-notes-input", label="Notes (Optional)"),
                dmc.Group(
                    [
                        dmc.Button(
                            "Cancel", id="cancel-place-btn", color="gray",
                            variant="outline"
                        ),
                        dmc.Button("Save Place", id="save-place-btn"),
                    ],
                    justify="flex-end",
                    style={"marginTop": "1rem"},
                ),
            ]
        ),
        dcc.Link(dmc.Button("Back to Home", variant="outline"), href="/home"),
        html.H1("Journal Details"),
        dmc.Grid(
            children=[
                dmc.GridCol(
                    [
                        dmc.Text("Cover Image"),
                        html.Img(
                            id='journal-cover-image',
                            src=journal.get(
                                'cover_image_url',
                                'https://via.placeholder.com/200x150'
                            ),
                            style={'width': '100%', 'height': 'auto'}
                        ),
                    ],
                    span=4
                ),
                dmc.GridCol(
                    html.Div(id='journal-details-content'),
                    span=8
                ),
            ],
            gutter="xl",
        ),
        html.Hr(style={"margin": "2rem 0"}),
        dmc.Group(
            [
                html.H2("Timeline", style={"flex": 1}),
                html.Div(
                    dmc.Button(
                        "Add Place",
                        id="add-place-btn",
                        variant="outline",
                    ),
                    id='add-place-button-container',
                ),
            ],
            justify="space-between",
            align="center"
        ),
        dmc.Alert(
            id="update-notification",
            title="Notification",
            children="",
            color="green",
            withCloseButton=True,
            hide=True,
        ),
        html.Div(id='full-timeline-container'),  # Populated by callback
        dmc.Group(
            id='action-buttons-group',
            children=[
                dmc.Button(
                    "Edit",
                    id="edit-journal-btn",
                    style={'display': 'block'
                           if is_author and initial_mode == 'view' else 'none'}
                ),
                dmc.Button(
                    "Save Changes",
                    id="save-journal-changes-btn",
                    style={'display': 'block'
                           if is_author and initial_mode == 'edit' else 'none'}
                ),
                dmc.Button(
                    "Cancel",
                    id="cancel-edit-btn",
                    color="gray",
                    variant="outline",
                    style={'display': 'block'
                           if is_author and initial_mode == 'edit' else 'none'}
                ),
            ],
            justify="flex-end",
            style={"marginTop": "1rem"},
        ),
    ], style={"padding": "2rem"})


def register_journal_detail_callbacks(app):
    @app.callback(
        Output('journal-details-content', 'children'),
        Input('page-mode-store', 'data'),
        State('journal-detail-store', 'data')
    )
    def display_journal_details(mode_data, journal):
        mode = mode_data.get('mode', 'view')
        start_date = journal.get('start_date', '')
        end_date = journal.get('end_date', '')

        if mode == 'edit':
            return [
                dmc.TextInput(
                    id="journal-title-input",
                    label="Title",
                    value=journal.get('title', ''),
                    required=True,
                ),
                dmc.Textarea(
                    id="journal-summary-input",
                    label="Summary",
                    value=journal.get('summary', ''),
                ),
                dmc.Textarea(
                    id="journal-introduction-input",
                    label="Introduction",
                    value=journal.get('introduction', ''),
                ),
                dmc.DatePickerInput(
                    id="journal-date-range-picker",
                    type="range",
                    label="Date Range",
                    value=[start_date, end_date]
                    if start_date and end_date else None,
                    required=True
                ),
                dmc.Group(
                    [
                        dmc.NumberInput(
                            id="journal-total-cost-input",
                            label="Total Cost",
                            value=journal.get('total_cost'),
                            min=0,
                            style={"flex": 1},
                        ),
                        dmc.Autocomplete(
                            id="journal-currency-input",
                            label="Currency",
                            data=get_currency_data(),
                            value=journal.get('currency', '🇲🇾 MYR'),
                            style={"flex": 1},
                        ),
                    ],
                    grow=True,
                    style={"margin-top": "1rem"},
                ),
            ]
        else:  # view mode
            start_date = journal.get('start_date', '')
            end_date = journal.get('end_date', '')
            return [
                dmc.Text(journal.get('title', 'No Title'), size="xl", fw=700),
                dmc.Text(journal.get('summary', ''), size="md", c="gray"),
                html.Hr(),
                dmc.Text(journal.get('introduction', '')),
                html.Hr(),
                dmc.Group([
                    dmc.Text("Date Range:", fw=500),
                    dmc.Text(
                        f"{start_date.split('T')[0]} to "
                        f"{end_date.split('T')[0]}"
                        if start_date and end_date else "Not set"
                    )
                ]),
                dmc.Group([
                    dmc.Text("Total Cost:", fw=500),
                    dmc.Text(
                        f"{journal.get('total_cost', 'N/A')} "
                        f"{journal.get('currency', '')}"
                    )
                ]),
            ]

    @app.callback(
        Output('page-mode-store', 'data'),
        Output('action-buttons-group', 'children'),
        Input('edit-journal-btn', 'n_clicks'),
        Input('cancel-edit-btn', 'n_clicks'),
        Input('save-journal-changes-btn', 'n_clicks'),
        State('page-mode-store', 'data'),
        State('auth-data', 'data'),
        State('journal-detail-store', 'data'),
        prevent_initial_call=True
    )
    def toggle_edit_mode(
        edit_clicks, cancel_clicks, save_clicks, mode_data, auth_data, journal
    ):
        ctx = callback_context
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        is_author = False
        if auth_data and 'idToken' in auth_data:
            user_info = get_user_info(auth_data['idToken'])
            if user_info and user_info.uid == journal.get('user_id'):
                is_author = True

        mode = mode_data.get('mode', 'view')

        if button_id == 'edit-journal-btn' and is_author:
            mode = 'edit'
        elif button_id in ['cancel-edit-btn', 'save-journal-changes-btn']:
            mode = 'view'

        action_buttons = [
            dmc.Button(
                "Edit",
                id="edit-journal-btn",
                style={'display': 'block'
                       if is_author and mode == 'view' else 'none'}
            ),
            dmc.Button(
                "Save Changes",
                id="save-journal-changes-btn",
                style={'display': 'block'
                       if is_author and mode == 'edit' else 'none'}
            ),
            dmc.Button(
                "Cancel",
                id="cancel-edit-btn",
                color="gray",
                variant="outline",
                style={'display': 'block'
                       if is_author and mode == 'edit' else 'none'}
            ),
        ]

        return {'mode': mode}, action_buttons

    @app.callback(
        Output('add-place-button-container', 'style'),
        Input('page-mode-store', 'data'),
        State('auth-data', 'data'),
        State('journal-detail-store', 'data')
    )
    def toggle_add_place_button_visibility(mode_data, auth_data, journal):
        mode = mode_data.get('mode', 'view')
        is_author = False
        if auth_data and 'idToken' in auth_data:
            user_info = get_user_info(auth_data['idToken'])
            if user_info and user_info.uid == journal.get('user_id'):
                is_author = True

        if is_author and mode == 'edit':
            return {'display': 'block'}
        return {'display': 'none'}

    @app.callback(
        Output('place-date-select', 'children'),
        Input('add-place-btn', 'n_clicks'),
        State('journal-detail-store', 'data'),
        prevent_initial_call=True,
    )
    def populate_date_dropdown(n_clicks, journal_data):
        start_date_str = journal_data.get('start_date')
        end_date_str = journal_data.get('end_date')

        if not start_date_str or not end_date_str:
            return []

        try:
            start_date = datetime.strptime(
                start_date_str.split('T')[0], '%Y-%m-%d'
            )
            end_date = datetime.strptime(
                end_date_str.split('T')[0], '%Y-%m-%d'
            )
        except (ValueError, AttributeError):
            return []
        
        delta = end_date - start_date
        days = delta.days + 1

        if days <= 0:
            return []

        date_options = [
            dmc.Chip("To be arranged", value="To be arranged")
        ]
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            day_str = current_date.strftime('%Y-%m-%d')
            day_label = f"Day {i + 1}: {current_date.strftime('%B %d')}"
            date_options.append(dmc.Chip(day_label, value=day_str))

        return date_options

    @app.callback(
        Output('add-place-modal', 'opened'),
        Input('add-place-btn', 'n_clicks'),
        Input('cancel-place-btn', 'n_clicks'),
        State('add-place-modal', 'opened'),
        prevent_initial_call=True,
    )
    def toggle_modal_open_close(n_add, n_cancel, is_open):
        from dash import callback_context
        button_id = callback_context.triggered[0]["prop_id"].split(".")[0]
        if button_id == "add-place-btn":
            return not is_open
        if button_id == "cancel-place-btn":
            return False
        return is_open

    @app.callback(
        [
            Output('update-notification', 'children', allow_duplicate=True),
            Output('update-notification', 'hide', allow_duplicate=True),
            Output('update-notification', 'color', allow_duplicate=True),
            Output('places-store', 'data'),
            Output('add-place-modal', 'opened', allow_duplicate=True),
            Output('place-name-error', 'children'),
            Output('place-address-error', 'children'),
            Output('place-date-error', 'children')
        ],
        Input('save-place-btn', 'n_clicks'),
        [
            State('journal-detail-store', 'data'),
            State('place-name-input', 'value'),
            State('place-address-input', 'value'),
            State('place-date-select', 'value'),
            State('place-notes-input', 'value'),
            State('places-store', 'data')
        ],
        prevent_initial_call=True,
    )
    def save_place(
        n_clicks, journal_data, name, address, selected_dates, notes,
        current_places
    ):
        if not n_clicks:
            return no_update, True, 'green', no_update, no_update, "", "", ""

        journal_id = journal_data.get('id')
        name_error = "Place Name is required." if not name else ""
        address_error = "Address is required." if not address else ""
        date_error = "Please select at least one day." \
            if not selected_dates else ""

        if name_error or address_error or date_error:
            return (
                no_update, True, "red", no_update, True, name_error,
                address_error, date_error
            )

        # If 'To be arranged' is selected, treat it as the only selection
        if "To be arranged" in selected_dates:
            dates_to_process = ["To be arranged"]
        else:
            dates_to_process = selected_dates

        for place_date in dates_to_process:
            place_data = {
                'name': name,
                'address': address,
                'date': place_date,
                'notes': notes,
            }
            place_id = add_place(journal_id, place_data)
            if not place_id:
                error_message = f"Failed to add place for {place_date}."
                return (
                    no_update, True, "red", no_update, True,
                    "", "", error_message
                )

        # After successfully adding all places, refetch the journal to get the
        # updated places list
        fresh_journal = get_journal(journal_id)
        updated_places = fresh_journal.get('journalPlaces', []) if \
            fresh_journal else current_places

        return (
            "Places added successfully!", False, "green", updated_places,
            False, "", "", ""
        )

    @app.callback(
        [
            Output("update-notification", "children", allow_duplicate=True),
            Output("update-notification", "hide", allow_duplicate=True),
            Output("update-notification", "color", allow_duplicate=True),
            Output('journal-detail-store', 'data'),
            Output('places-store', 'data', allow_duplicate=True),
        ],
        Input("save-journal-changes-btn", "n_clicks"),
        [
            State("journal-detail-store", "data"),
            State("journal-title-input", "value"),
            State("journal-summary-input", "value"),
            State("journal-introduction-input", "value"),
            State("journal-date-range-picker", "value"),
            State("journal-total-cost-input", "value"),
            State("journal-currency-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_journal_changes(
        n_clicks, journal_data, title, summary, introduction, date_range,
        total_cost, currency
    ):
        if not n_clicks:
            return no_update, True, "green", no_update, no_update

        journal_id = journal_data.get('id')
        if not journal_id:
            msg = "Error: Journal ID not found."
            return msg, False, "red", no_update, no_update

        start_date, end_date = (None, None)
        if date_range:
            start_date, end_date = date_range

        updated_data = {
            'title': title,
            'summary': summary,
            'introduction': introduction,
            'start_date': start_date,
            'end_date': end_date,
            'total_cost': total_cost,
            'currency': currency,
        }

        if update_journal(journal_id, updated_data):
            # Refetch data to ensure UI is in sync
            fresh_journal = get_journal(journal_id)
            if fresh_journal:
                updated_places = fresh_journal.get('journalPlaces', [])
                return (
                    "Journal updated successfully!", False, "green", fresh_journal,
                    updated_places
                )
            else:
                # Handle case where refetch fails
                msg = "Update succeeded, but failed to refetch data."
                return msg, False, "orange", no_update, no_update
        else:
            return "Failed to update journal.", False, "red", no_update, \
                no_update

    @app.callback(
        Output('full-timeline-container', 'children'),
        [Input('places-store', 'data'), Input('journal-detail-store', 'data')]
    )
    def update_full_timeline(places, journal_data):
        # This callback runs on page load and when dependencies change
        start_date = journal_data.get('start_date')
        end_date = journal_data.get('end_date')

        if not all([start_date, end_date]):
            return dmc.Text("Please set a date range for the journal.", c="orange")

        tba_places = [
            p for p in places if p.get('date') == 'To be arranged'
        ]
        dated_places = [
            p for p in places if p.get('date') != 'To be arranged'
        ]

        tba_section = dmc.Accordion(
            chevronPosition="left",
            children=[
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl("To be arranged"),
                        dmc.AccordionPanel(
                            dmc.Stack(
                                children=[
                                    dmc.Paper(
                                        [
                                            dmc.Text(
                                                place.get('name', 'No name'),
                                                fw=500),
                                            dmc.Text(
                                                place.get(
                                                    'address', 'No address'
                                                ), size="sm"),
                                            dmc.Text(
                                                place.get('notes', ''),
                                                size="sm", c="dimmed"),
                                        ],
                                        shadow="xs", p="sm", withBorder=True
                                    ) for place in tba_places
                                ] if tba_places else [
                                    dmc.Text("No places yet.")
                                ]
                            )
                        ),
                    ],
                    value="tba"
                )
            ],
            value="tba"  # Keep it open by default
        )

        dated_timeline = create_timeline(
            start_date, end_date, dated_places
        )

        return html.Div([
            tba_section,
            html.Hr(style={"margin": "2rem 0"}),
            dated_timeline
        ])
