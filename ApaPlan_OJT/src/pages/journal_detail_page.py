from dash import html, dcc, Input, Output, State
import dash_mantine_components as dmc
from src.shared.journal_utils import get_journal_with_details, get_all_user_profiles
from src.shared.auth_utils import get_user_info
from datetime import datetime, timedelta

def create_timeline(start_date_str, days, places=None):
    """Generates a timeline accordion based on the start date and number of days."""
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
    all_user_profiles = get_all_user_profiles()
    if not journal:
        return html.Div("Journal not found.")

    is_author = False
    if auth_data and 'idToken' in auth_data:
        user_info = get_user_info(auth_data['idToken'])
        if user_info and user_info.uid == journal.get('user_id'):
            is_author = True

    start_date = journal.get("start_date", "")
    days = journal.get("days", 1)
    places = journal.get("journalPlaces", [])
    author_id = journal.get("user_id")
    author_profile = all_user_profiles.get(author_id)
    author_name = author_profile.get("display_name", "Anonymous") if author_profile else "Anonymous"
    last_updated = journal.get("updated_at", journal.get("created_at", "Not available"))

    return html.Div([
        dcc.Store(id='journal-detail-store', data=journal),
        dcc.Interval(id='journal-detail-interval', interval=5000, n_intervals=0),
        dcc.Link(dmc.Button("Back to Home", variant="outline"), href="/home"),
        html.H1("Journal Details"),
        html.Img(
            id='journal-cover-image',
            src=journal.get('cover_image_url', 'https://via.placeholder.com/200x150'),
            style={
                'width': '100%',
                'height': 'auto',
                'maxHeight': '300px',
                'objectFit': 'cover',
                'marginBottom': '2rem'
            }
        ),
        dmc.Grid(
            children=[
                dmc.GridCol(
                    [
                        dmc.Text(id='journal-title', children=journal.get('title', 'No Title'), size="xl", fw=700),
                        dmc.Text(id='journal-summary', children=journal.get('summary', ''), size="md", c="gray"),
                        html.Hr(),
                        dmc.Text(id='journal-introduction', children=journal.get('introduction', '')),
                        html.Hr(),
                        dmc.Group(
                            [
                                dmc.Text("Start Date:", fw=500),
                                dmc.Text(
                                    id="journal-start-date",
                                    children=start_date.split("T")[0]
                                    if start_date
                                    else "Not set",
                                ),
                            ]
                        ),
                        dmc.Group(
                            [
                                dmc.Text("Duration:", fw=500),
                                dmc.Text(
                                    id="journal-duration",
                                    children=f"{days} days",
                                ),
                            ]
                        ),
                        dmc.Group([
                            dmc.Text("Total Cost:", fw=500),
                            dmc.Text(id='journal-total-cost', children=f"{journal.get('total_cost', 'N/A')} {journal.get('currency', '')}")
                        ]),
                    ],
                    span=12
                ),
            ],
            gutter="xl",
        ),
        html.Hr(style={"margin": "2rem 0"}),
        html.H2("Timeline"),
        html.Div(
            id="timeline-container", children=create_timeline(start_date, days, places)
        ),
        dmc.Group(
            [
                dcc.Link(
                    dmc.Button("Edit Journal"),
                    href=f"/journal/{journal_id}/edit",
                    id="edit-journal-link",
                )
                if is_author
                else None
            ],
            justify="flex-end",
            style={"marginTop": "1rem"},
        ),
        dmc.Group(
            [
                dmc.Text(f"Last updated by {author_name} on {last_updated}", c="dimmed", size="sm")
            ],
            justify="center",
            style={"marginTop": "2rem"},
        )
    ], style={"padding": "2rem"})

def register_journal_detail_callbacks(app):
    @app.callback(
        Output('journal-detail-store', 'data'),
        Input('journal-detail-interval', 'n_intervals'),
        State('url', 'pathname'),
    )
    def refresh_journal_data(n, pathname):
        journal_id = pathname.split('/')[2]
        if not journal_id:
            return dash.no_update
        
        journal = get_journal_with_details(journal_id)
        return journal

    @app.callback(
        Output('timeline-container', 'children'),
        Output('journal-cover-image', 'src'),
        Output('journal-title', 'children'),
        Output('journal-summary', 'children'),
        Output('journal-introduction', 'children'),
        Output("journal-start-date", "children"),
        Output("journal-duration", "children"),
        Output('journal-total-cost', 'children'),
        Input('journal-detail-store', 'data')
    )
    def update_journal_detail_view(journal):
        if not journal:
            return dash.no_update

        start_date = journal.get("start_date", "")
        days = journal.get("days", 1)
        places = journal.get("journalPlaces", [])

        timeline = create_timeline(start_date, days, places)
        cover_image = journal.get(
            "cover_image_url", "https://via.placeholder.com/200x150"
        )
        title = journal.get("title", "No Title")
        summary = journal.get("summary", "")
        introduction = journal.get("introduction", "")
        start_date_str = start_date.split("T")[0] if start_date else "Not set"
        duration = f"{days} days"
        total_cost = (
            f"{journal.get('total_cost', 'N/A')} {journal.get('currency', '')}"
        )

        return (
            timeline,
            cover_image,
            title,
            summary,
            introduction,
            start_date_str,
            duration,
            total_cost,
        )
