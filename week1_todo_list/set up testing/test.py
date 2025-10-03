import dash
from dash import html, dcc
import plotly.express as px
import sqlite3

# ---------- SQLite Setup ----------
# Create (or connect to) a database
conn = sqlite3.connect("example.db")
cursor = conn.cursor()

# Create a sample table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT,
    amount INTEGER
)
""")

# Insert sample data if table is empty
cursor.execute("SELECT COUNT(*) FROM sales")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO sales (product, amount) VALUES (?, ?)",
        [("Apples", 10), ("Bananas", 15), ("Cherries", 7)]
    )
    conn.commit()

# Fetch data from SQLite
cursor.execute("SELECT product, amount FROM sales")
rows = cursor.fetchall()
conn.close()

# Convert to dict for Plotly
data = {"Product": [r[0] for r in rows], "Amount": [r[1] for r in rows]}

# ---------- Dash Setup ----------
app = dash.Dash(__name__)

fig = px.bar(data, x="Product", y="Amount", title="Sales Data from SQLite")

app.layout = html.Div(children=[
    html.H1("Dash + SQLite Example"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run(debug=True)
