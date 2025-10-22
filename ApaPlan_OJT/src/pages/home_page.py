from dash import html, dcc, Input, Output, State, ALL, callback_context
import dash_mantine_components as dmc
from src.shared.auth_utils import get_user_info
from src.shared.journal_utils import (
    create_journal, get_user_journals, get_journal
)
import json


def create_journal_modal():
    return dmc.Modal(
        id="journal-modal",
        title="Create New Journal",
        zIndex=10000,
        children=[
            dmc.Text("Title *"),
            dmc.TextInput(id="journal-title-input", required=True),
            dmc.Text("Summary *"),
            dmc.Textarea(id="journal-summary-input", required=True),
            dmc.Text("Introduction"),
            dmc.Textarea(id="journal-introduction-input"),
            dmc.Text("Cover Image URL"),
            dmc.TextInput(id="journal-cover-image-input"),
            dmc.Text("Total Cost"),
            dmc.NumberInput(id="journal-total-cost-input", min=0),
            dmc.Text("Currency"),
            dmc.TextInput(id="journal-currency-input", placeholder="e.g., USD, EUR"),
            dmc.Text("Places"),
            dmc.JsonInput(
                id="journal-places-input",
                placeholder='e.g., ["Paris", "Rome"]',
                formatOnBlur=True
            ),
            html.Div([
                dmc.Text("Date Range *"),
                dmc.DatePickerInput(
                    id="journal-date-range-picker",
                    type="range",
                    placeholder="Select date range",
                    dropdownType="modal",
                    modalProps={'zIndex': 10001},
                ),
            ], style={"margin-top": "1rem"}),
            dmc.Group(
                [
                    dmc.Button("Cancel", id="cancel-journal-btn", variant="outline"),
                    dmc.Button("Save", id="save-journal-btn"),
                ],
                justify="flex-end",
                style={"marginTop": "1rem"},
            ),
        ],
    )


def home_layout():
    return html.Div(
        [
            dcc.Store(id='user-info-store', storage_type='session'),
            dcc.Store(id='selected-journal-store', storage_type='session'),
            html.Div(id='home-page-content'),
            dmc.Modal(
                id="journal-details-modal",
                zIndex=10000,
                children=[],
            ),
        ]
    )


def register_home_callbacks(app):
    @app.callback(
        Output('user-info-store', 'data'),
        Input('auth-store', 'data')
    )
    def store_user_info(auth_data):
        print("store_user_info callback triggered.")
        if auth_data and 'idToken' in auth_data:
            print("Auth data found, fetching user info...")
            user_info = get_user_info(auth_data['idToken'])
            print("User info received:", user_info)
            return user_info
        print("Auth data not found or invalid in store_user_info.")
        return None

    @app.callback(
        Output('home-page-content', 'children'),
        Input('user-info-store', 'data')
    )
    def update_home_page_content(user_info):
        if user_info and 'users' in user_info and user_info['users']:
            display_name = user_info['users'][0].get('displayName', 'User')
            return html.Div([
                html.H1(f"Welcome, {display_name}!"),
                create_journal_modal(),
                dmc.Accordion(
                    id="journal-accordion",
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl("All Journals"),
                                dmc.AccordionPanel(
                                    [
                                        html.Div(id="journal-list-container"),
                                        dmc.Button(
                                            "Create a new journal",
                                            id="create-journal-btn",
                                            style={'marginTop': '20px'}
                                        ),
                                    ]
                                ),
                            ],
                            value="journal-list"
                        ),
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl("User Profile"),
                                dmc.AccordionPanel(
                                    dcc.Link(
                                        "Go to your profile page",
                                        href="/profile"
                                    )
                                ),
                            ],
                            value="profile"
                        ),
                    ],
                    value="journal-list"  # Start with the accordion open
                ),
            ])
        return html.Div("Loading...")

    @app.callback(
        Output("journal-modal", "opened"),
        [
            Input("create-journal-btn", "n_clicks"),
            Input("cancel-journal-btn", "n_clicks"),
            Input("save-journal-btn", "n_clicks"),
        ],
        State("journal-modal", "opened"),
        prevent_initial_call=True,
    )
    def toggle_modal(n_create, n_cancel, n_save, opened):
        return not opened

    @app.callback(
        Output("selected-journal-store", "data"),
        Input("save-journal-btn", "n_clicks"),
        [
            State("user-info-store", "data"),
            State("journal-title-input", "value"),
            State("journal-summary-input", "value"),
            State("journal-introduction-input", "value"),
            State("journal-cover-image-input", "value"),
            State("journal-date-range-picker", "value"),
            State("journal-total-cost-input", "value"),
            State("journal-currency-input", "value"),
            State("journal-places-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_new_journal(
        n_clicks, user_info, title, summary, introduction,
        cover_image_url, date_range, total_cost, currency, places
    ):
        if n_clicks and user_info and 'users' in user_info and user_info['users']:
            user_id = user_info['users'][0]['localId']
            start_date, end_date = date_range
            journal_id = create_journal(
                user_id, title, summary, introduction, cover_image_url,
                start_date, end_date, total_cost, currency, json.loads(places)
            )
            return journal_id
        return None

    @app.callback(
        Output("journal-details-modal", "opened"),
        Output("journal-details-modal", "children"),
        Input({'type': 'view-journal-btn', 'index': ALL}, 'n_clicks'),
        State("journal-details-modal", "opened"),
        prevent_initial_call=True,
    )
    def open_details_modal(n_clicks, opened):
        ctx = callback_context
        if not ctx.triggered:
            return opened, []

        button_id_str = (
            ctx.triggered[0]['prop_id'].split('.')[0]
        )
        button_id = json.loads(button_id_str)
        journal_id = button_id['index']
        journal = get_journal(journal_id)

        if not journal:
            return not opened, dmc.Text("Journal not found.")

        modal_content = [
            dmc.Text(journal.get('title', 'No Title'), weight=500, size="lg"),
            dmc.Text(
                f"Created on: "
                f"{journal.get('created_at').strftime('%Y-%m-%d')}",
                size="sm",
                color="gray"
            ),
            dmc.Text(journal.get('summary', ''), style={'marginTop': '1rem'}),
            dmc.Text(
                journal.get('introduction', ''),
                style={'marginTop': '1rem'}
            ),
        ]
        return not opened, modal_content

    @app.callback(
        Output("selected-journal-store", "data", allow_duplicate=True),
        Input({'type': 'view-journal-btn', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def view_journal(n_clicks):
        ctx = callback_context
        if not ctx.triggered:
            return None
        
        button_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
        button_id = json.loads(button_id_str)
        journal_id = button_id['index']
        return journal_id

    @app.callback(
        Output("journal-list-container", "children"),
        [
            Input('user-info-store', 'data'),
            Input("save-journal-btn", "n_clicks"),
        ]
    )
    def display_journals(user_info, save_clicks):
        if not (user_info and 'users' in user_info and user_info['users']):
            print("User info not found or invalid.")
            return html.P("Please log in to see your journals.")

        print("User Info:", user_info)
        user_id = user_info['users'][0]['localId']
        print("Querying journals for user ID:", user_id)
        journals = get_user_journals(user_id)
        print("Journals found:", journals)
        print(f"User ID from auth: {user_id}")
        print(f"Journals retrieved from Firestore: {journals}")

        if not journals:
            return html.P("You haven't created any journals yet.")

        journal_cards = []
        for journal in journals:
            created_at = journal.get('created_at')
            date_str = 'N/A'
            # Ensure created_at is a datetime object before formatting
            if hasattr(created_at, 'strftime'):
                date_str = created_at.strftime('%Y-%m-%d')

            card = dmc.Card(
                children=[
                    dmc.CardSection(
                        dmc.Image(
                            src=journal.get(
                                'cover_image_url',
                                'https://via.placeholder.com/150'
                            ),
                            h=160,
                        )
                    ),
                    dmc.Group(
                        [
                            dmc.Text(
                                journal.get('title', 'No Title'), weight=500
                            ),
                            dmc.Badge(
                                date_str,
                                color="blue",
                                variant="light"
                            ),
                        ],
                        position="apart",
                        mt="md",
                        mb="xs",
                    ),
                    dmc.Button(
                        "View Details",
                        id={
                            'type': 'view-journal-btn',
                            'index': journal.get('id')  # Use .get() for safety
                        },
                        variant="light",
                        color="blue",
                        fullWidth=True,
                        mt="md",
                        radius="md",
                    ),
                ],
                withBorder=True,
                shadow="sm",
                radius="md",
                style={"width": 300, "margin": "1rem"},
            )
            journal_cards.append(card)

        return dmc.Group(journal_cards)
