import dash
from app import app, server
from layout import layout
from callbacks import register_callbacks

dash._dash_renderer._set_react_version("18.2.0")

# Set the layout of the app
app.layout = layout

# Register the callbacks
register_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8059, host='0.0.0.0')
