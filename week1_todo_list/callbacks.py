import uuid
import dash_mantine_components as dmc
from dash import ctx, Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from components import get_tasks_layout, get_list_navigation_layout, get_pos_from_index

def register_callbacks(app):
    ##############LIST############
    @app.callback(
        [
        Output("main_task_container", "children"),
        Output("main_list_title", "value"),
        Output("list_navigation_layout", "children"),
        ],
        Input("list_data_memory", "data"),
        Input("current_index_memory", "data"),
    )
    def update_task_container(list_data, current_index):
        """ Updates the list of tasks and list title"""

        print("Entering update_task_container callback")

        # Handle the empty state when no lists are available
        if not current_index or not list_data:
            empty_layout = dmc.Text("Create a new list to get started!", align="center", color="gray")
            list_navigation = get_list_navigation_layout(list_data or [], current_index)
            return empty_layout, "No list selected", list_navigation

        #Get the current list
        i = get_pos_from_index(list_data, current_index)
        if i is None: # Safeguard if index is somehow invalid
            raise PreventUpdate
            
        curr_list = list_data[i]

        # Compute layout
        tasks_layout = get_tasks_layout(curr_list["tasks_list"])
        title_layout = curr_list["title"]
        list_navigation = get_list_navigation_layout(list_data, current_index)

        return tasks_layout, title_layout, list_navigation

    @app.callback(
        Output("current_index_memory", "data", allow_duplicate=True),
        Input({"type": "list_button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def switch_list(n_clicks):
        """ Changes the current displayed list"""
        if not any(n_clicks):
            raise PreventUpdate
        
        list_index = ctx.triggered_id["index"]
        return list_index
        
    @app.callback(
        [
            Output("list_data_memory", "data", allow_duplicate=True),
            Output("current_index_memory", "data"),
        ],
        Input("new_list_button", "n_clicks"),
        State("list_data_memory", "data"),
        prevent_initial_call=True,
    )
    def add_list(n_clicks, list_data):
        """ Add a new list and display it"""
        if not n_clicks:
            raise PreventUpdate

        print("Entering add_list callback")
        
        new_index = uuid.uuid4().hex
        new_list = {
            "index": new_index,
            "title": "New list",
            "tasks_list": [],
        }

        new_list_data = list_data + [new_list]
        return new_list_data, new_index

    @app.callback(
        Output("list_data_memory", "data", allow_duplicate=True),
        Input("main_list_title", "value"),
        State("list_data_memory", "data"),
        State("current_index_memory", "data"),
        prevent_initial_call=True,
    )
    def update_list_title(title, list_data, current_index):
        """ Updates the current list title"""

        i = get_pos_from_index(list_data, current_index)
        list_data[i]["title"] = title
        return list_data

    @app.callback(
        [
            Output("del_list_modal", "opened"),
            Output("last-list-warning-modal", "opened", allow_duplicate=True),
        ],
        Input("del_list_button", "n_clicks"),
        State("list_data_memory", "data"),
        prevent_initial_call=True,
    )
    def delete_modal_open_close(n_clicks, list_data):
        """ Opens the correct modal for list deletion. """
        if not n_clicks:
            raise PreventUpdate

        if len(list_data) <= 1:
            return False, True  # Open warning modal

        return True, False  # Open delete confirmation modal

    @app.callback(
        [
            Output("list_data_memory", "data", allow_duplicate=True),
            Output("current_index_memory", "data", allow_duplicate=True),
            Output("del_list_modal", "opened", allow_duplicate=True),
        ],
        Input("del_list_modal_confirm_button", "n_clicks"),
        State("list_data_memory", "data"),
        State("current_index_memory", "data"),
        prevent_initial_call=True,
    )
    def delete_list(n_clicks, list_data, current_index):
        """ Deletes the current list. """
        if not n_clicks:
            raise PreventUpdate

        i = get_pos_from_index(list_data, current_index)
        if i is None:
            raise PreventUpdate
        
        new_list_data = [elem for elem in list_data if elem["index"] != current_index]
        new_current_index = new_list_data[0]["index"] if len(new_list_data) > 0 else None
        
        return new_list_data, new_current_index, False

    @app.callback(
        Output("last-list-warning-modal", "opened", allow_duplicate=True),
        Input("last-list-warning-modal-close-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_last_list_warning_modal(n_clicks):
        """ Closes the 'last list' warning modal. """
        if not n_clicks:
            raise PreventUpdate
        return False

    ############TASK############
    @app.callback(
        Output("list_data_memory", "data", allow_duplicate=True),
        Input("new_task_button", "n_clicks"),
        State("list_data_memory", "data"),
        State("current_index_memory", "data"),
        prevent_initial_call=True,
    )
    def add_task(n_clicks, list_data, current_index):
        """ Adds a task to the list """
        if not n_clicks:
            raise PreventUpdate

        print("Entering add_task callback")
        
        # Create new task dictionary
        new_index = uuid.uuid4().hex
        new_task = {
            "index": new_index,
            "content": "", 
            "checked": False,
        }
        
        # Add new task to the tasks list in memory
        
        i = get_pos_from_index(list_data, current_index)
        list_data[i]["tasks_list"].append(new_task)

        return list_data

    @app.callback(
        Output("list_data_memory", "data", allow_duplicate=True),
        Input({"type": "task_del", "index": ALL}, "n_clicks"),
        State("list_data_memory", "data"),
        State("current_index_memory", "data"),
        prevent_initial_call=True,
    )
    def remove_task(n_clicks, list_data, current_index):
        """ Remove a task from the list """
        if not any(n_clicks):
            raise PreventUpdate

        print("Entering remove_task callback")
        task_index = ctx.triggered_id["index"]

        # Find and remove the task with matching index
        i = get_pos_from_index(list_data, current_index)
        list_data[i]["tasks_list"] = [
            task for task in list_data[i]["tasks_list"] 
            if task["index"] != task_index
        ]
        
        return list_data

    @app.callback(
        Output("list_data_memory", "data", allow_duplicate=True),
        Input({"type": "task_checked", "index": ALL}, "checked"),
        Input({"type": "task_content", "index": ALL}, "value"),
        State("list_data_memory", "data"),
        State("current_index_memory", "data"),
        prevent_initial_call=True,
    )
    def update_task_checked(checked_values, content_values, list_data, current_index):
        """Updates the checked state of tasks"""
        if not checked_values:
            raise PreventUpdate
        
        print("Entering update_task_checked callback")
        i = get_pos_from_index(list_data, current_index)
        # Find the index position in our list of tasks
        task_index = ctx.triggered_id["index"]
        task_pos = get_pos_from_index(list_data[i]["tasks_list"], task_index)

        task_checked_value = checked_values[task_pos]
        task_content_value = content_values[task_pos]

        # Update the task values in list_data
        list_data[i]["tasks_list"][task_pos]["checked"] = task_checked_value
        list_data[i]["tasks_list"][task_pos]["content"] = task_content_value

        return list_data
