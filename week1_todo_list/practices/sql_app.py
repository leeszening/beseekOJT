import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import sqlite3
import pandas as pd

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_data():
    conn = sqlite3.connect("data.db")
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    return df

def add_task(name, status):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (name, status) VALUES (?, ?)", (name, status))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def update_task(task_id, new_status):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
    conn.commit()
    conn.close()


# --- Dash App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
init_db()

app.layout = dbc.Container([
    html.H2("📋 Dash + SQLite CRUD Demo", className="mt-3"),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="task-name", placeholder="Enter task name...", type="text"),
        ], width=5),
        dbc.Col([
            dbc.Select(
                id="task-status",
                options=[
                    {"label": "Pending", "value": "Pending"},
                    {"label": "In Progress", "value": "In Progress"},
                    {"label": "Done", "value": "Done"},
                ],
                value="Pending",
            )
        ], width=3),
        dbc.Col([
            dbc.Button("Add Task", id="add-btn", color="primary", className="w-100")
        ], width=2),
    ], className="mb-3"),

    dbc.Alert(id="feedback", color="success", is_open=False),

    html.Hr(),
    dbc.Button("🔄 Refresh Table", id="refresh-btn", color="secondary", className="mb-3"),
    html.Div(id="task-table"),
])


# --- Callbacks ---
@app.callback(
    Output("feedback", "children"),
    Output("feedback", "is_open"),
    Input("add-btn", "n_clicks"),
    State("task-name", "value"),
    State("task-status", "value"),
    prevent_initial_call=True
)
def add_task_callback(n_clicks, name, status):
    if not name:
        return "Task name cannot be empty!", True
    add_task(name, status)
    return f"✅ Added task: {name}", True


@app.callback(
    Output("task-table", "children"),
    Input("refresh-btn", "n_clicks"),
    prevent_initial_call=True
)
def refresh_table(_):
    df = get_data()
    if df.empty:
        return html.P("No tasks yet.")
    
    rows = []
    for _, row in df.iterrows():
        rows.append(
            html.Tr([
                html.Td(row["id"]),
                html.Td(row["name"]),
                html.Td(row["status"]),
                html.Td(
                    dbc.ButtonGroup([
                        dbc.Button("Delete", id={"type": "delete-btn", "index": row["id"]}, color="danger", size="sm"),
                        dbc.Button("Mark Done", id={"type": "done-btn", "index": row["id"]}, color="success", size="sm"),
                    ])
                )
            ])
        )
    table = dbc.Table(
        [html.Thead(html.Tr([html.Th("ID"), html.Th("Task"), html.Th("Status"), html.Th("Actions")])),
         html.Tbody(rows)],
        bordered=True, striped=True, hover=True
    )
    return table


# --- Pattern-Matching Callbacks (for dynamic buttons) ---
from dash.dependencies import MATCH, ALL

@app.callback(
    Output("task-table", "children", allow_duplicate=True),
    Input({"type": "delete-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def handle_delete(delete_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    task_id = eval(triggered_id)["index"]
    delete_task(task_id)
    return refresh_table(None)


@app.callback(
    Output("task-table", "children", allow_duplicate=True),
    Input({"type": "done-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def handle_done(done_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    task_id = eval(triggered_id)["index"]
    update_task(task_id, "Done")
    return refresh_table(None)


if __name__ == "__main__":
    app.run(debug=True, port=8070)
