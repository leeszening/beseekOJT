from dash import html
import dash_mantine_components as dmc

def create_header():
    return dmc.Box(
        dmc.Group(
            [
                dmc.Burger(id="burger", opened=False, size="sm"),
                html.H3("Home Page")
            ],
            justify="space-between",
            align="center"
        ),
        className="header"
    )
