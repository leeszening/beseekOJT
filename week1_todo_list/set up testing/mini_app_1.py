import dash
from dash import html, dcc, Input, Output

app= dash.Dash(__name__)

app.layout= html.Div([
    html.H3("Mini App 1 — Echo"),
    dcc.Input(id="my-input", type="text", placeholder="Type something..."),
    html.Div(id="my-output")
])

@app.callback(
    Output("my-output", "children"),
    Input("my-input", "value")
)
def update_text(value):
    if not value:
        return "Type above 👆"
    return f"You typed: {value}"

if __name__ == "__main__":
    app.run(debug=True, port=8050)

# cd copy_path_to_your_terminal
# source venv/bin/activate (confirm port=8051)
# python minimal_dash_apps.py
