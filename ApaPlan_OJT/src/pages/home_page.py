from dash import (
    html, dcc, Input, Output, State, ALL, callback_context, no_update
)
import dash_mantine_components as dmc
from src.shared.auth_utils import get_user_info
from src.shared.journal_utils import (
    create_journal, get_user_journals, get_journal
)
import json
import pycountry


def get_currency_data():
    currency_data = []
    for country in pycountry.countries:
        try:
            currency = pycountry.currencies.get(numeric=country.numeric)
            if currency:
                # The 'flag' attribute was removed in pycountry 23.12.11.
                # This is the new recommended way to get the flag emoji.
                flag = "".join(
                    chr(ord(c.lower()) + 127397) for c in country.alpha_2
                )
                currency_data.append(f"{flag} {currency.alpha_3}")
        except (AttributeError, KeyError):
            continue
    return sorted(list(set(currency_data)))


def create_journal_modal():
    return dmc.Modal(
        id="journal-modal",
        title="Create New Journal",
        zIndex=10000,
        children=[
            dcc.Upload(
                id='upload-image',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a Cover Image')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False
            ),
            html.Div(id='output-image-upload', children=[
                html.Img(src='https://via.placeholder.com/200x150', style={'width': '100%', 'height': 'auto'})
            ]),
            dmc.Text("Title *"),
            dmc.TextInput(id="journal-title-input", required=True),
            html.Div([
                dmc.Text("Date Range *"),
                dmc.DatePickerInput(
                    id="journal-date-range-picker",
                    type="range",
                    placeholder="Select date range",
                    dropdownType="modal",
                    modalProps={'zIndex': 10001},
                    required=True
                ),
            ], style={"margin-top": "1rem"}),
            dmc.Accordion(
                children=[
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl("Other Details"),
                            dmc.AccordionPanel(
                                children=[
                                    dmc.Text("Summary"),
                                    dmc.Textarea(id="journal-summary-input"),
                                    dmc.Text("Introduction"),
                                    dmc.Textarea(id="journal-introduction-input"),
                                    dmc.Group(
                                        [
                                            dmc.NumberInput(
                                                id="journal-total-cost-input",
                                                label="Total Cost",
                                                min=0,
                                                style={"flex": 1},
                                            ),
                                            dmc.Autocomplete(
                                                id="journal-currency-input",
                                                label="Currency",
                                                data=get_currency_data(),
                                                value="🇲🇾 MYR",
                                                style={"flex": 1},
                                                styles={"dropdown": {"zIndex": 10001}},
                                            ),
                                        ],
                                        grow=True,
                                        style={"margin-top": "1rem"},
                                    ),
                                ]
                            ),
                        ],
                        value="other-details"
                    )
                ]
            ),
            dmc.Group(
                [
                    dmc.Button(
                        "Cancel", id="cancel-journal-btn", variant="outline"
                    ),
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
            dcc.Store(id='modal-state-store', data={'opened': False}),
            dcc.Store(id='journal-update-trigger-store', storage_type='memory'),
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
                dmc.Button(
                    "Create a new journal",
                    id="create-journal-btn",
                    style={'marginBottom': '20px'}
                ),
                dmc.Accordion(
                    id="journal-accordion",
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl("My Journals"),
                                dmc.AccordionPanel(
                                    html.Div(id="journal-list-container")
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
        Input("create-journal-btn", "n_clicks"),
        Input("cancel-journal-btn", "n_clicks"),
        Input("save-journal-btn", "n_clicks"),
        State("modal-state-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_modal_open_close(n_create, n_cancel, n_save, modal_state):
        ctx = callback_context
        if not ctx.triggered:
            return no_update

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == "create-journal-btn":
            return True
        if trigger_id in ["cancel-journal-btn", "save-journal-btn"]:
            return False
        
        return modal_state.get('opened', False)

    @app.callback(
        Output("journal-title-input", "value"),
        Output("journal-summary-input", "value"),
        Output("journal-introduction-input", "value"),
        Output("journal-date-range-picker", "value"),
        Output("journal-total-cost-input", "value"),
        Output("journal-currency-input", "value"),
        Output("upload-image", "contents", allow_duplicate=True),
        Output('output-image-upload', 'children', allow_duplicate=True),
        Input("journal-modal", "opened"),
        prevent_initial_call=True
    )
    def clear_modal_inputs(opened):
        if not opened:
            return "", "", "", None, None, "🇲🇾 MYR", None, html.Img(src='https://via.placeholder.com/200x150', style={'width': '100%', 'height': 'auto'})
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    @app.callback(
        Output('output-image-upload', 'children', allow_duplicate=True),
        Input('upload-image', 'contents'),
        prevent_initial_call=True
    )
    def update_output(contents):
        if contents is not None:
            return html.Img(src=contents, style={'width': '100%', 'height': 'auto'})
        return html.Img(src='https://via.placeholder.com/200x150', style={'width': '100%', 'height': 'auto'})

    @app.callback(
        Output("journal-update-trigger-store", "data"),
        Output("selected-journal-store", "data"),
        Output("modal-state-store", "data"),
        Output('url', 'href', allow_duplicate=True),
        Output("journal-title-input", "error"),
        Output("journal-date-range-picker", "error"),
        Output("journal-summary-input", "error"),
        Input("save-journal-btn", "n_clicks"),
        [
            State("user-info-store", "data"),
            State("journal-title-input", "value"),
            State("journal-summary-input", "value"),
            State("journal-introduction-input", "value"),
            State("upload-image", "contents"),
            State("journal-date-range-picker", "value"),
            State("journal-total-cost-input", "value"),
            State("journal-currency-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_new_journal(
        n_clicks, user_info, title, summary, introduction,
        cover_image_contents, date_range, total_cost, currency
    ):
        if not n_clicks:
            return (
                no_update, no_update, {'opened': True}, no_update, no_update,
                no_update, no_update
            )

        title_error = "Title is required." if not title else None
        date_range_error = "Date range is required." if not date_range else None
        summary_error = None

        if title_error or date_range_error:
            return (
                no_update, no_update, {'opened': True}, no_update,
                title_error, date_range_error, summary_error,
            )

        if user_info and 'users' in user_info and user_info['users']:
            user_id = user_info['users'][0]['localId']
            start_date, end_date = date_range
            journal_id = create_journal(
                user_id, title, summary, introduction,
                cover_image_contents, start_date, end_date, total_cost,
                currency
            )
            if journal_id:
                # On success, update the trigger store with the new journal ID
                return (
                    journal_id, journal_id, {'opened': False}, no_update,
                    None, None, None
                )
            else:
                # On failure, do not trigger a refresh
                return (
                    no_update, no_update, {'opened': True}, no_update,
                    "Error", "Failed to create journal.", None
                )
        
        # On user error, do not trigger a refresh
        return (
            no_update, no_update, {'opened': True}, no_update, "Error",
            "User not logged in.", None
        )


    @app.callback(
        Output("journal-list-container", "children"),
        [
            Input('user-info-store', 'data'),
            Input('journal-update-trigger-store', 'data'),
        ]
    )
    def display_journals(user_info, trigger_data):
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
            # Use start_date instead of created_at for the badge
            date_str = journal.get('start_date', 'N/A')

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
                                journal.get('title', 'No Title'), fw=500
                            ),
                            dmc.Badge(
                                date_str,
                                color="blue",
                                variant="light"
                            ),
                        ],
                        justify="space-between",
                        mt="md",
                        mb="xs",
                    ),
                    dcc.Link(
                        dmc.Button(
                            "View Details",
                            variant="light",
                            color="blue",
                            fullWidth=True,
                            mt="md",
                            radius="md",
                        ),
                        href=f"/journal/{journal.get('id')}",
                        style={"textDecoration": "none"},
                    ),
                ],
                withBorder=True,
                shadow="sm",
                radius="md",
                style={"width": 300, "margin": "1rem"},
            )
            journal_cards.append(card)

        return dmc.Group(journal_cards)
