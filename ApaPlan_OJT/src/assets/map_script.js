// Global variables to hold map, marker, and the autocomplete element instance.
let map;
let marker;
let autocompleteElement;

/**
 * Initializes the map and the classic Google Places Autocomplete.
 * This function is designed to be called when the modal becomes visible.
 */
async function initializeMapComponents() {
    const mapContainer = document.getElementById('add-place-map');
    const autocompleteContainer = document.getElementById('place-autocomplete-container');
    
    if (!mapContainer || !autocompleteContainer) {
        console.error("Map or autocomplete container not found. Bailing out.");
        return;
    }

    // Ensure we have the necessary libraries loaded.
    try {
        const { Map } = await google.maps.importLibrary("maps");
        const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
        const { Autocomplete } = await google.maps.importLibrary("places");

        // 1. Initialize the Map
        map = new Map(mapContainer, {
            center: { lat: 3.1390, lng: 101.6869 }, // Default to Kuala Lumpur
            zoom: 12,
            mapId: window.GOOGLE_MAP_ID,
        });

        // 2. Create a standard input element for autocomplete
        const inputElement = document.createElement('input');
        inputElement.type = 'text';
        inputElement.placeholder = 'E.g., Petronas Twin Towers';
        inputElement.style.width = '100%';
        inputElement.style.padding = '8px';
        
        // Clear any previous elements and append the new input
        autocompleteContainer.innerHTML = '';
        autocompleteContainer.appendChild(inputElement);

        // 3. Create the classic Autocomplete instance
        const autocomplete = new Autocomplete(inputElement, {
            fields: ["name", "formatted_address", "geometry"],
        });

        // 4. Add event listener for when a place is selected
        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();

            if (!place || !place.geometry || !place.geometry.location) {
                console.error("Invalid place object returned:", place);
                return;
            }

            // Center the map on the selected place
            if (place.geometry.viewport) {
                map.fitBounds(place.geometry.viewport);
            } else {
                map.setCenter(place.geometry.location);
                map.setZoom(17);
            }

            // Clear the old marker
            if (marker) {
                marker.map = null;
            }

            // Create and position a new marker
            marker = new AdvancedMarkerElement({
                map: map,
                position: place.geometry.location,
                title: place.name,
            });
            
            // 5. Prepare data and send it to Dash via dcc.Store
            const placeData = {
                name: place.name,
                address: place.formatted_address,
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng(),
            };
            
            // Find the hidden input and set its value
            const hiddenInput = document.getElementById('selected-place-json');
            if (hiddenInput) {
                hiddenInput.value = JSON.stringify(placeData);
                // Manually dispatch an event to trigger Dash callback
                var event = new Event('input', { bubbles: true });
                hiddenInput.dispatchEvent(event);
            }
        });

        // Trigger a resize event to ensure the map renders correctly inside the modal
        setTimeout(() => google.maps.event.trigger(map, 'resize'), 200);

    } catch (error) {
        console.error("Error loading Google Maps libraries:", error);
    }
}

// Assign the function to the window object so it can be called from Dash
window.initializeMapComponents = initializeMapComponents;
