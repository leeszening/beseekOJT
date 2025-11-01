import dash_mantine_components as dmc
from datetime import datetime, timedelta
import logging

def create_timeline(start_date_str, days, places=None, is_editable=False):
    """
    Generates a tabbed timeline for a journal.
    Can be used in both view-only and editable modes.
    """
    if not start_date_str or not days:
        return dmc.Text("Please provide a start date and number of days.", c="dimmed")

    try:
        start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
    except (ValueError, AttributeError):
        return dmc.Text("Invalid date format.", c="red")

    tabs_list = []
    panels_list = []
    first_date_string = start_date.strftime('%Y-%m-%d')

    # Group places by date for efficient lookup
    places_by_date = {}
    if places:
        for place in places:
            date_str = place.get("date")
            if date_str:
                if date_str not in places_by_date:
                    places_by_date[date_str] = []
                places_by_date[date_str].append(place)

    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_string = current_date.strftime('%Y-%m-%d')
        
        tabs_list.append(dmc.TabsTab(f"Day {i + 1}", value=date_string))
        
        places_for_day = places_by_date.get(date_string, [])
        
        try:
            place_cards = []
            for place in places_for_day:
                card_children = []

                # Display 'name' as a title if it exists
                if place.get('name'):
                    card_children.append(dmc.Text(place.get('name'), fw=500))

                # Define the fields to be displayed in the card
                display_fields = {
                    "address": "Address",
                    "phone": "Phone",
                    "opening_hours": "Opening Hours",
                    "description": "Description",
                    "category": "Type",
                }

                # Display the specified fields if they exist and are not empty
                for field, label in display_fields.items():
                    value = place.get(field)
                    if value:
                        card_children.append(
                            dmc.Text(f"{label}: {value}", size="sm", mt="xs")
                        )

                if is_editable:
                    card_children.append(
                        dmc.Group(
                            [
                                dmc.Button("Edit", id={'type': 'edit-place-btn', 'index': place.get('journal_place_doc_id')}),
                                dmc.Button("Delete", id={'type': 'delete-place-btn', 'index': place.get('journal_place_doc_id')}, color="red"),
                            ],
                            mt="md",
                        )
                    )
                # Create a collapsible accordion for each place
                accordion = dmc.Accordion(
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl(place.get('name', 'No Title')),
                                dmc.AccordionPanel(children=card_children[1:]),  # Exclude the title
                            ],
                            value=place.get('journal_place_doc_id', 'default-value'),
                        )
                    ],
                    mt="sm"
                )
                place_cards.append(accordion)
        except Exception as e:
            logging.error(f"Error rendering place cards for date {date_string}: {e}")
            place_cards = [dmc.Alert("Error loading places for this day.", color="red")]

        panel_children = place_cards
        if is_editable:
            panel_children.append(
                dmc.Button(
                    "Add Place",
                    id={'type': 'add-place-btn', 'date': date_string},
                    mt="sm"
                )
            )
        elif not place_cards:
            panel_children = [dmc.Text("No places recorded for this day.")]

        panels_list.append(
            dmc.TabsPanel(
                children=panel_children,
                value=date_string
            )
        )

    return dmc.Tabs(
        id="journal-timeline-tabs",
        value=first_date_string,
        children=[
            dmc.TabsList(tabs_list),
            *panels_list,
        ],
    )
