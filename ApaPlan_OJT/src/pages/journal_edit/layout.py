import dash
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
from src.shared.journal_utils import get_currency_data

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def create_initial_map():
    """Creates an initial empty map figure."""
    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=20, lon=0),
            zoom=1
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig


def create_edit_timeline(start_date_str, days, places=None, journal_id=None):
    """Generates a timeline accordion for the edit page with 'Add Place' buttons."""
    from datetime import datetime, timedelta

    try:
        start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
    except (ValueError, AttributeError):
        return dmc.Text("Invalid date format provided.", c="red")

    if not isinstance(days, int) or days <= 0:
        return dmc.Text("Number of days must be a positive integer.", c="red")

    places_by_date = {}
    for p in (places or []):
        place_date = p.get('date', '').split('T')[0]
        if place_date:
            if place_date not in places_by_date:
                places_by_date[place_date] = []
            places_by_date[place_date].append(p)

    timeline_items = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_str = current_date.strftime('%Y-%m-%d')
        day_label = f"Day {i + 1}: {current_date.strftime('%B %d, %Y')}"
        day_places = places_by_date.get(day_str, [])

        panel_content = [
            dmc.Paper(
                dmc.Group(
                    [
                        html.Div(
                            [
                                dmc.Text(place.get('name', 'No name'), fw=500),
                                dmc.Text(place.get('address', 'No address'), size="sm"),
                                dmc.Text(place.get('notes', ''), size="sm", c="dimmed"),
                            ],
                            style={'flex': 1}
                        ),
                        dmc.ActionIcon(
                            DashIconify(icon="radix-icons:trash"),
                            id={"type": "delete-place-btn",
                                "place_id": place.get("id")},
                            color="red",
                            variant="hover",
                        )
                    ],
                    justify="space-between",
                    align="center"
                ),
                shadow="xs", p="sm", withBorder=True, mb="sm"
            ) for place in day_places
        ] if day_places else [dmc.Text("No places for this day.")]

        panel_content.append(
            dmc.Group(
                [
                    dmc.Button(
                        "Add Place",
                        id={"type": "add-place-day-btn", "date": day_str},
                        variant="outline",
                    )
                ],
                justify="flex-end",
                style={"marginTop": "1rem"},
            )
        )

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


def create_add_place_modal():
    """Creates the modal for adding a new place with a map."""
    return dmc.Modal(
        id="add-place-modal",
        title="Add a New Place",
        size="xl",
        zIndex=10000,
        children=[
            html.Div(
                id="map-container",
                style={"height": "400px", "width": "100%", "marginBottom": "20px"}
            ),
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        [
                            dmc.Text("Search for a place", fw=500),
                            # This div will act as a container for the new PlaceAutocompleteElement,
                            # which will be created and appended by our JavaScript.
                            html.Div(id="place-autocomplete-container", style={"width": "100%"}),
                        ],
                        span=8
                    ),
                    dmc.GridCol(
                        [
                            dmc.Text("Select a State", fw=500),
                            dcc.Dropdown(
                                id='state-selector-dropdown',
                                options=[
                                    {'label': 'Johor', 'value': 'Johor'},
                                    {'label': 'Kedah', 'value': 'Kedah'},
                                    {'label': 'Kelantan', 'value': 'Kelantan'},
                                    {'label': 'Malacca', 'value': 'Malacca'},
                                    {'label': 'Negeri Sembilan',
                                     'value': 'Negeri Sembilan'},
                                    {'label': 'Pahang', 'value': 'Pahang'},
                                    {'label': 'Penang', 'value': 'Penang'},
                                    {'label': 'Perak', 'value': 'Perak'},
                                    {'label': 'Perlis', 'value': 'Perlis'},
                                    {'label': 'Sabah', 'value': 'Sabah'},
                                    {'label': 'Sarawak', 'value': 'Sarawak'},
                                    {'label': 'Selangor', 'value': 'Selangor'},
                                    {'label': 'Terengganu', 'value': 'Terengganu'},
                                ],
                                placeholder="Bias search to a state",
                            ),
                        ],
                        span=4
                    ),
                    dmc.GridCol(
                        [
                            dmc.Text("Place Name", fw=500, mt="md"),
                            dcc.Input(id="place-name-input",
                                      style={"width": "100%"}),
                        ],
                        span=12
                    ),
                    dmc.GridCol(
                        [
                            dmc.Text("Address", fw=500, mt="md"),
                            dcc.Input(id="place-address-input",
                                      style={"width": "100%"}),
                        ],
                        span=12
                    ),
                    dmc.GridCol(
                        [
                            dmc.Text("Date", fw=500, mt="md"),
                            dmc.ChipGroup(
                                id="place-date-select", children=[], multiple=True
                            ),
                        ],
                        span=12
                    ),
                    dmc.GridCol(
                        [
                            dmc.Text("Notes", fw=500, mt="md"),
                            dmc.Textarea(
                                id="place-notes-input", label="Notes (Optional)"
                            ),
                        ],
                        span=12
                    ),
                ],
                gutter="md"
            ),
            dmc.Group(
                [
                    dmc.Button("Cancel", id="cancel-place-btn", variant="outline"),
                    dmc.Button("Save Place", id="save-place-btn"),
                ],
                justify="flex-end",
                style={"marginTop": "20px"},
            ),
            # Dummy output for the clientside callback to trigger map setup.
            # This is a common pattern when a callback's primary purpose is to execute JavaScript
            # without directly updating a visible component property.
            html.Div(id="map-clientside-trigger-output", style={"display": "none"}),
        ],
    )


def create_journal_edit_layout(journal):
    start_date = journal.get("start_date", "")
    days = journal.get("days", 1)
    status = journal.get("status", "draft")
    journal_id = journal.get("id")

    return html.Div(
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
            html.Img(
                id="output-image-upload",
                src=journal.get(
                    "cover_image_url",
                    "https://via.placeholder.com/200x150",
                ),
                style={
                    'width': '100%',
                    'height': 'auto',
                    'maxHeight': '300px',
                    'objectFit': 'cover',
                    'marginBottom': '1rem'
                }
            ),
            dmc.Group(
                [
                    dcc.Upload(
                        id="upload-image-edit",
                        children=dmc.Button(
                            "Update Cover Image",
                            variant="outline"
                        ),
                        multiple=False,
                        style_active={
                            'border': '2px solid #007BFF'
                        },
                    ),
                    dmc.Button(
                        "Delete Cover Image",
                        id="delete-cover-image-btn",
                        color="red",
                        variant="outline",
                    )
                ],
                justify="center",
                style={'marginBottom': '2rem'}
            ),
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        [
                            dmc.TextInput(
                                id="journal-title-input",
                                label="Title",
                                value=journal.get("title", ""),
                                required=True,
                            ),
                            dmc.Group(
                                [
                                    dmc.Textarea(
                                        id="journal-summary-input",
                                        label="Summary",
                                        value=journal.get("summary", ""),
                                        style={"flex": 1},
                                    ),
                                    dmc.Button(
                                        "Generate",
                                        id="generate-summary-btn",
                                        variant="outline",
                                        style={"margin-top": "25px"},
                                    ),
                                ],
                                grow=False,
                                align="flex-start",
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
                        span=12,
                    ),
                ],
                gutter="xl",
            ),
            html.Hr(style={"margin": "2rem 0"}),
            html.H2("Location Map"),
            dcc.Graph(
                id='place-map',
                figure=create_initial_map(),
                style={'height': '400px', 'width': '100%', 'marginBottom': '2rem'}
            ),
            dmc.Group(
                [
                    html.H2("Timeline"),
                ],
                justify="space-between",
            ),
            html.Div(id="full-timeline-container"),
            create_add_place_modal(),
            dmc.Modal(
                id="delete-confirm-modal",
                title="Confirm Deletion",
                children=[
                    dmc.Text(
                        "Are you sure you want to delete this place? This action cannot be undone."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Cancel", id="cancel-delete-btn", variant="outline"),
                            dmc.Button(
                                "Confirm", id="confirm-delete-btn", color="red"),
                        ],
                        justify="flex-end",
                        style={"marginTop": "1rem"},
                    ),
                ],
                zIndex=10001,
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


def journal_edit_layout(journal_id=None, auth_data=None):
    return html.Div(
        [
            dcc.Store(id="journal-edit-store"),
            dcc.Store(id="places-store"),
            dcc.Store(id='selected-place-details-store'),  # Renamed for clarity
            dcc.Store(id='place-coordinates-store'),
            dcc.Store(id="page-load-store", data=False),
            dcc.Store(id="place-to-delete-store"),
            # This dummy div is the target for the clientside callback that attaches the error handler.
            html.Div(id="script-error-handler-output", style={"display": "none"}),
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
