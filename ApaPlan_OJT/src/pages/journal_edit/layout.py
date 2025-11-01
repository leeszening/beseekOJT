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
                    "data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' width='200' height='150' viewBox='0 0 200 150' fill='%23ccc'%3e%3crect width='200' height='150'/%3e%3c/svg%3e",
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
            dmc.Group(
                [
                    html.H2("Timeline"),
                ],
                justify="space-between",
            ),
            html.Div(id="full-timeline-container"),
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
            dcc.Store(id="journal-edit-page-loaded", data=True),
            dcc.Store(id="journal-edit-store"),
            dcc.Store(id="page-load-store", data=False),
            dcc.Store(id="timeline-update-store"),
            html.Div(id="script-error-handler-output", style={"display": "none"}),
            html.Div(id="map-error-div", style={"color": "red"}),
            dmc.Modal(
                id="add-place-modal",
                title="Add a Place to Your Journal",
                zIndex=10000,
                children=[
                    dcc.Store(id='modal-context-store'),
                    dmc.MultiSelect(
                        id='day-select-multiselect',
                        label="Select Day(s)",
                        placeholder="You can add this place to multiple days",
                        styles={'dropdown': {'zIndex': 10001}}
                    ),
                    dcc.Store(id='gmaps-place-data-store'),
                    dcc.Interval(id='gmaps-data-poller', interval=200, disabled=True),
                    dmc.TextInput(id='place-autocomplete-input', label="Search for a place"),
                    html.Div(id='map-canvas', style={'height': '300px', 'marginTop': '1rem'}),
                    dmc.Grid(
                        children=[
                            dmc.GridCol(dmc.TextInput(id='place-name-output', label="Place Name", readOnly=True), span=6),
                            dmc.GridCol(dmc.TextInput(id='place-type-output', label="Google Category", readOnly=True), span=6),
                        ],
                        gutter="xl",
                    ),
                    dmc.TextInput(id='place-address-output', label="Address", readOnly=True),
                    dmc.TextInput(id='place-coords-output', label="Coordinates", readOnly=True),
                    dmc.MultiSelect(
                        id='place-type-multiselect',
                        label="Type (Tag)",
                        data=[
                            "Food & Beverages", "Shop", "Accommodation", "Office", "Mall",
                            "Street Stall", "Farmers Market", "Parking", "Petrol Station",
                            "RnR", "Toilet"
                        ],
                        placeholder="Select tags that apply",
                        styles={'dropdown': {'zIndex': 10001}}
                    ),
                    dmc.Textarea(id='place-opening-hours-output', label="Opening Hours", readOnly=True, autosize=True, minRows=2),
                    dmc.CheckboxGroup(
                        id='place-friendliness-checkbox',
                        label="Friendliness",
                        children=[
                            dmc.Checkbox(label="OKU Friendly", value="oku"),
                            dmc.Checkbox(label="Family Friendly", value="family"),
                            dmc.Checkbox(label="Kids Friendly", value="kids"),
                        ],
                    ),
                    dmc.Grid(
                        children=[
                            dmc.GridCol(dmc.TextInput(id='place-phone-output', label="Phone", readOnly=True), span=6),
                            dmc.GridCol(dmc.TextInput(id='place-whatsapp-input', label="WhatsApp"), span=6),
                        ],
                        gutter="xl",
                    ),
                    dmc.TextInput(id='place-website-output', label="Website", readOnly=True),
                    dmc.Accordion(
                        children=[
                            dmc.AccordionItem(
                                [
                                    dmc.AccordionControl("Social Media Links"),
                                    dmc.AccordionPanel(
                                        [
                                            dmc.TextInput(id='social-facebook-input', label="Facebook"),
                                            dmc.TextInput(id='social-instagram-input', label="Instagram"),
                                            dmc.TextInput(id='social-tiktok-input', label="TikTok"),
                                            dmc.TextInput(id='social-youtube-input', label="YouTube"),
                                            dmc.TextInput(id='social-linkedin-input', label="LinkedIn"),
                                        ]
                                    ),
                                ],
                                value="socials"
                            )
                        ]
                    ),
                    dmc.Textarea(id='place-description-textarea', label="Description"),
                    dmc.Group(
                        [
                            dmc.Button("Confirm", id="confirm-add-place-btn"),
                            dmc.Button("Cancel", id="cancel-add-place-btn", color="red"),
                        ],
                        justify="flex-end",
                        style={'marginTop': '1rem'}
                    ),
                ],
            ),
            html.Div(
                id="journal-edit-content",
                style={"padding": "2rem"},
                children=[dmc.LoadingOverlay(visible=True)],
            ),
        ]
    )
