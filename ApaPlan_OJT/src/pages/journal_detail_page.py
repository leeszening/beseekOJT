from dash import (
    html, dcc, Input, Output, State, no_update
)
import dash_mantine_components as dmc
from src.shared.journal_utils import get_journal, update_journal, add_place, get_journal_places, get_place
from src.pages.home_page import get_currency_data
from datetime import datetime, timedelta

def create_timeline(start_date_str, end_date_str, places=None):
    """Generates a timeline accordion based on the date range."""
    try:
        start_date = datetime.strptime(start_date_str.split('T')[0], '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str.split('T')[0], '%Y-%m-%d')
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


def journal_detail_layout(journal_id=None):
    if not journal_id:
        return html.Div("No journal selected.")

    journal = get_journal(journal_id)
    if not journal:
        return html.Div("Journal not found.")

    start_date = journal.get('start_date', '')
    end_date = journal.get('end_date', '')
    places = get_journal_places(journal_id)

    return html.Div([
        dcc.Store(id='journal-detail-store', data=journal),
        dcc.Store(id='places-store', data=places),
        dcc.Store(id='timeline-refresh-signal', data=0),
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
                    [
                        dmc.TextInput(
                            id="journal-title-input",
                            label="Title",
                            value=journal.get('title', ''),
                            required=True
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
                    ],
                    span=8
                ),
            ],
            gutter="xl",
        ),
        dmc.DatePickerInput(
            id="journal-date-range-picker",
            type="range",
            label="Date Range",
            value=[start_date, end_date] if start_date and end_date else None,
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
        dmc.Group(
            [
                dmc.Button("Save Changes", id="save-journal-changes-btn"),
            ],
            justify="flex-end",
            style={"marginTop": "1rem"},
        ),
        html.Hr(style={"margin": "2rem 0"}),
        dmc.Group(
            [
                html.H2("Timeline", style={"flex": 1}),
                dmc.Button("Add Place", id="add-place-btn", variant="outline"),
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
        html.Div(id='full-timeline-container')  # This will be populated by a callback
    ], style={"padding": "2rem"})


def register_journal_detail_callbacks(app):
    @app.callback(
        Output('place-date-select', 'children'),
        Input('journal-date-range-picker', 'value'),
        Input('add-place-btn', 'n_clicks'),
        State('journal-detail-store', 'data'),
        prevent_initial_call=True,
    )
    def populate_date_dropdown(date_range, n_clicks, journal_data):
        start_date_str, end_date_str = None, None

        if date_range:
            start_date_str, end_date_str = date_range
        elif journal_data:
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
        n_clicks, journal_data, name, address, selected_dates,
        notes, current_places
    ):
        if not n_clicks:
            return (
                no_update, True, 'green', no_update, no_update,
                "", "", ""
            )

        journal_id = journal_data.get('id')
        user_id = journal_data.get('user_id')

        name_error = "Place Name is required." if not name else ""
        address_error = "Address is required." if not address else ""
        date_error = "Please select at least one day." if not selected_dates else ""

        if name_error or address_error or date_error:
            return (
                no_update, True, "red", no_update, True,
                name_error, address_error, date_error
            )

        updated_places = list(current_places)
        
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
            place_id = add_place(journal_id, user_id, place_data)
            if place_id:
                new_place = get_place(place_id)
                if new_place:
                    updated_places.append(new_place)
                else:
                    error_message = f"Failed to retrieve new place for {place_date}."
                    return (
                        no_update, True, "red", no_update, True,
                        "", "", error_message
                    )
            else:
                # Handle failure for individual place addition
                error_message = f"Failed to add place for {place_date}."
                return (
                    no_update, True, "red", no_update, True,
                    "", "", error_message
                )

        return (
            "Places added successfully!", False, "green", updated_places,
            False, "", "", ""
        )

    @app.callback(
        [
            Output("update-notification", "children", allow_duplicate=True),
            Output("update-notification", "hide", allow_duplicate=True),
            Output("update-notification", "color", allow_duplicate=True),
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
            return no_update, True, "green"

        journal_id = journal_data.get('id')
        if not journal_id:
            return "Error: Journal ID not found.", False, "red"

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
            return "Journal updated successfully!", False, "green"
        else:
            return "Failed to update journal.", False, "red"


    @app.callback(
        Output('full-timeline-container', 'children'),
        Input('journal-date-range-picker', 'value'),
        Input('places-store', 'data'),
        State('journal-detail-store', 'data')
    )
    def update_full_timeline(date_range, places, journal_data):
        # This callback runs on page load and when dependencies change
        start_date, end_date = (None, None)
        if date_range:
            start_date, end_date = date_range
        else:
            start_date = journal_data.get('start_date')
            end_date = journal_data.get('end_date')

        if not all([start_date, end_date]):
            return dmc.Text(
                "Please set a date range for the journal.", c="orange"
            )

        tba_places = [p for p in places if p.get('date') == 'To be arranged']
        dated_places = [p for p in places if p.get('date') != 'To be arranged']

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
                                                fw=500
                                            ),
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
                                ] if tba_places else [dmc.Text("No places yet.")]
                            )
                        ),
                    ],
                    value="tba"
                )
            ],
            value="tba"  # Keep it open by default
        )

        dated_timeline = create_timeline(start_date, end_date, dated_places)

        return html.Div([
            tba_section,
            html.Hr(style={"margin": "2rem 0"}),
            dated_timeline
        ])
