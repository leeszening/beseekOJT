import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

def get_task(task_dict):
    """ Returns a single task layout """
    text = task_dict["content"]
    checked = task_dict["checked"]
    index = task_dict["index"]

    content = dmc.Grid(
        [
            dmc.GridCol(
                dmc.Checkbox(
                    id={"type": "task_checked", "index": index},
                    checked=checked,
                    mt=2
                ), 
                span="content"
            ),
            dmc.GridCol(
                dmc.Text(
                    dcc.Input(
                        text, 
                        id={"type": "task_content", "index": index},
                        className="shadow-input",
                        debounce=True
                    )
                ), 
                span="auto"
            ),
            dmc.GridCol(
                dmc.ActionIcon(
                    DashIconify(icon="tabler:x", width=20),
                    id={"type": "task_del", "index": index},
                    variant="transparent",
                    color="gray",
                    className="task-del-button"
                ),
                span="content"
            ),
        ],
        className="task-container"
    )

    return content


def get_tasks_layout(tasks_list):
    """ Returns the list of tasks """
    tasks = []
    for task_dict in tasks_list:
        task_layout = get_task(task_dict)
        tasks.append(task_layout)

    return tasks


def get_list_layout():
    """ Returns the list of checkboxes """
    
    content = dmc.Paper(
        [
            dmc.Title(
                dcc.Input(
                    id="main_list_title",
                    className="shadow-input",
                    debounce=True,
                    value=""
                ),
            order=2,
            ),
            
            dmc.Container(
                id="main_task_container",
                px=0,
                mt="md",
                mb="md",
            ),
            dmc.Group(
                [
                    dmc.Button(
                        "Add a new task", 
                        id="new_task_button",
                        #style={"width": "100%"},
                        variant="outline", 
                        color="gray",
                        mt="sm"
                    ),

                    dmc.Button(
                        "... or remove list",
                        id="del_list_button",
                        #style={"width": "100%"},
                        variant="subtle", 
                        color="red",
                        size="xs",
                        mt="sm"

                    )
                ]
            ),
        
            dmc.Modal(
                id="del_list_modal",
                title="Are you sure you want to delete this task list?",
                children=[     
                    dmc.Group(
                        [
                            dmc.Button(
                                "Yes, delete", 
                                id="del_list_modal_confirm_button",
                                color="red"
                            ),
                        ],
                        justify="center",
                    ),
                ],
            ),
        ],
        shadow="sm",
        p="md",
        mt="md",
        radius="sm",
    )

    return content

def get_new_list_button():

    return dmc.Button(
        "New list",
        id="new_list_button",
        style={"width": "100%"},
        color="black",
        mt="md",
        mb="md"
    )

def get_list_navigation_layout(list_data, current_index):
    """ Returns a list of lists titles and progressions """

    items = []

    for list_item in list_data:
        # Compute progression
        progress_value = get_progression(list_item)
        progress_color = "green" if progress_value == 100 else "blue"

        # Build card element
        elem = dmc.Paper(
            html.A(
                [
                    dmc.Title(list_item["title"], order=4, mb="sm"),
                    dmc.Progress(value=progress_value, color=progress_color)
                ],
                id={"type": "list_button", "index": list_item["index"]},
                style={"cursor": "pointer"},
            ),
            p="xs",
            mb="sm",
            withBorder=True,
            className="active" if current_index == list_item["index"] else ""
        )
        items.append(elem)
    return items

def get_progression(list_item):
    """ Computes the progression of a list """
    tasks = list_item["tasks_list"]
    if len(tasks) == 0:
        return 0
    return len([task for task in tasks if task["checked"]]) * 100 / len(tasks)

def get_pos_from_index(dict_list, index):
    """ Retrieves the current position in a list of dicts given an index """
    for i, elem in enumerate(dict_list):
        if elem["index"] == index:
            return i
