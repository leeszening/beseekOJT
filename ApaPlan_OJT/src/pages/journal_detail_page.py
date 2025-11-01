from dash import html, dcc, Input, Output, State
import dash_mantine_components as dmc
from src.shared.journal_utils import get_journal_with_details, get_user_profiles_by_ids, fetch_all_journal_places
from src.shared.auth_utils import get_user_info
from src.components.timeline import create_timeline
from datetime import datetime, timedelta

def journal_detail_layout(journal_id=None, auth_data=None):
    if not journal_id:
        return html.Div("No journal selected.")

    journal = get_journal_with_details(journal_id)
    if not journal:
        return html.Div("Journal not found.")

    author_id = journal.get("user_id")
    if author_id:
        user_profiles = get_user_profiles_by_ids([author_id])
        author_profile = user_profiles.get(author_id)
    else:
        author_profile = None

    is_author = False
    if auth_data and 'idToken' in auth_data:
        user_info = get_user_info(auth_data['idToken'])
        if user_info and user_info.uid == journal.get('user_id'):
            is_author = True

    start_date = journal.get("start_date", "")
    days = journal.get("days", 1)
    places = journal.get("journalPlaces", [])
    author_name = author_profile.get("display_name", "Anonymous") if author_profile else "Anonymous"
    last_updated = journal.get("updated_at", journal.get("created_at", "Not available"))
    status = journal.get("status", "draft")

    return html.Div([
        dcc.Store(id='journal-detail-store', data=journal),
        dcc.Interval(id='journal-detail-interval', interval=5000, n_intervals=0),
        dcc.Link(dmc.Button("Back to Home", variant="outline"), href="/home"),
        dmc.Group(
            [
                html.H1("Journal Details"),
                dmc.Badge(
                    status.capitalize(),
                    color="blue" if status == "draft" else "green",
                    variant="light",
                    id="journal-status-badge",
                ),
            ],
            justify="space-between",
        ),
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
        html.Div(id="timeline-container"),
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

        journal_id = journal.get("id")
        start_date = journal.get("start_date", "")
        days = journal.get("days", 1)
        
        # Fetch all places for the journal
        places = fetch_all_journal_places(journal_id)

        timeline = create_timeline(start_date, days, places, is_editable=False)
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
