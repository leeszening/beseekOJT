from dash import html, dcc, Input, Output, State
import dash_mantine_components as dmc
from src.shared.journal_utils import get_journal_with_details
from src.shared.auth_utils import get_user_info
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
                [
                    dmc.Text(place.get('name', 'No name'), fw=500),
                    dmc.Text(place.get('address', 'No address'), size="sm"),
                    dmc.Text(place.get('notes', ''), size="sm", c="dimmed"),
                ],
                shadow="xs", p="sm", withBorder=True, mb="sm"
            ) for place in day_places
        ] if day_places else [dmc.Text("No places for this day.")]

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

def journal_detail_layout(journal_id=None, auth_data=None):
    if not journal_id:
        return html.Div("No journal selected.")

    journal = get_journal_with_details(journal_id)
    if not journal:
        return html.Div("Journal not found.")

    is_author = False
    if auth_data and 'idToken' in auth_data:
        user_info = get_user_info(auth_data['idToken'])
        if user_info and user_info.uid == journal.get('user_id'):
            is_author = True

    start_date = journal.get('start_date', '')
    end_date = journal.get('end_date', '')
    places = journal.get('journalPlaces', [])

    return html.Div([
        dcc.Link(dmc.Button("Back to Home", variant="outline"), href="/home"),
        html.H1("Journal Details"),
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
                        dmc.Text(journal.get('title', 'No Title'), size="xl", fw=700),
                        dmc.Text(journal.get('summary', ''), size="md", c="gray"),
                        html.Hr(),
                        dmc.Text(journal.get('introduction', '')),
                        html.Hr(),
                        dmc.Group([
                            dmc.Text("Date Range:", fw=500),
                            dmc.Text(f"{start_date.split('T')[0]} to {end_date.split('T')[0]}" if start_date and end_date else "Not set")
                        ]),
                        dmc.Group([
                            dmc.Text("Total Cost:", fw=500),
                            dmc.Text(f"{journal.get('total_cost', 'N/A')} {journal.get('currency', '')}")
                        ]),
                    ],
                    span=8
                ),
            ],
            gutter="xl",
        ),
        html.Hr(style={"margin": "2rem 0"}),
        html.H2("Timeline"),
        create_timeline(start_date, end_date, places),
        dmc.Group(
            [
                dcc.Link(
                    dmc.Button("Edit Journal"),
                    href=f"/journal/{journal_id}/edit"
                ) if is_author else None
            ],
            justify="flex-end",
            style={"marginTop": "1rem"},
        ),
    ], style={"padding": "2rem"})

def register_journal_detail_callbacks(app):
    pass
