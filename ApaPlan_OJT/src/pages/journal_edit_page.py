from .journal_edit.layout import journal_edit_layout
from .journal_edit.callbacks import register_journal_edit_callbacks

# The layout function is imported from the layout module
# and can be used directly in the main app router.
# Example:
# @app.server.route('/journal/<journal_id>/edit')
# def edit_journal_route(journal_id):
#     return journal_edit_layout(journal_id)

# The callbacks are registered with the Dash app instance.
# This should be done in your main app file (e.g., main.py).
# Example:
# from src.pages.journal_edit_page import register_journal_edit_callbacks
# register_journal_edit_callbacks(app)
