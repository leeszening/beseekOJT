import uuid
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify
from components import get_new_list_button, get_list_layout

# Simplified to just one list
sample_list_data = [
    {
    "index": uuid.uuid4().hex,
    "title": "My Tasks",
    "tasks_list": [
        {
            "index": uuid.uuid4().hex,
            "content": "Task A", 
            "checked": True,
        },
        {
            "index": uuid.uuid4().hex,
            "content": "Task B", 
            "checked": False,
        },
        {
            "index": uuid.uuid4().hex,
            "content": "Task C", 
            "checked": False,
        },
    ],
    },
    {
        "index": uuid.uuid4().hex,
        "title": "Personal",
        "tasks_list": [],
    }  
]

layout = dmc.MantineProvider(
    [
        dmc.Container(
            dmc.Grid(
                [
                    dmc.GridCol(
                        [
                            get_new_list_button(),
                            dmc.Container(
                                id="list_navigation_layout",
                                px=0,
                            )
                        ],
                        span=4,
                    ),
                    dmc.GridCol(
                        get_list_layout(),
                        span="auto",
                        ml="xl",
                    ),
                ], 
                gutter="md",
            ),
            size=600,
        ),
        html.Footer(
            "© developed by SzeNing 2025",
            style={
                "textAlign": "center",
                "padding": "10px",
                "marginTop": "40px",
                "color": "#666",
                "fontSize": "14px",
                "borderTop": "1px solid #ddd",
            },
        ),

        #The stored data in localStorage
        dcc.Store("list_data_memory", data=sample_list_data, storage_type="local"),
        dcc.Store("current_index_memory", data=sample_list_data[0]["index"], storage_type="local"),

        dmc.Modal(
            title="Action Prevented!",
            id="last-list-warning-modal",
            zIndex=10000,
            children=[
                dmc.Group(
                    [
                        DashIconify(icon="tabler:alert-circle", width=30, color="red"),
                        dmc.Text("You must have at least one list."),
                    ]
                ),
                dmc.Group(
                    [
                        dmc.Button("Okay", id="last-list-warning-modal-close-button", color="red"),
                    ],
                    justify="flex-end",
                    mt="md",
                ),
            ],
        ),
    ]
)
