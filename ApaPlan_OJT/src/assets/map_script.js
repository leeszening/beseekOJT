// Global variables to hold the map and marker instances.
let map;
let marker;
// The autocomplete element is now managed within the setup function.
let autocompleteElement;

/**
 * This function is called if the Google Maps API script fails to load.
 * It provides a clear error message in the console for debugging.
 */
function onGoogleApiError() {
    console.error(
        "Google Maps API failed to load. Please check your API key and Google Cloud project settings."
    );
}

/**
 * Main entry point, called by the Google Maps API script once it's loaded.
 */
async function onGoogleApiLoad() {
    console.log("Google Maps API loaded successfully.");

    // We need to load the 'places' library specifically for the new element.
    const { Place } = await google.maps.importLibrary("places");

    // Define the function that will be called by our Dash clientside callback.
    window.setupMapInModal = function() {
        const mapContainer = document.getElementById('map-container');
        if (!mapContainer) {
            console.error("Map container not found in the DOM.");
            return;
        }

        // --- Initialize the Map (only once) ---
        if (!map) {
            map = new google.maps.Map(mapContainer, {
                center: { lat: 3.1390, lng: 101.6869 }, // Default to Kuala Lumpur
                zoom: 12,
                mapId: "YOUR_MAP_ID" // Recommended for the new element
            });
            console.log("Google Map initialized.");

            // --- Add Listener for Map Clicks ---
            map.addListener('click', (mapsMouseEvent) => {
                const clickedLatLng = mapsMouseEvent.latLng;
                
                // Move the marker to the clicked location
                marker.setPosition(clickedLatLng);
                marker.setVisible(true);
                map.panTo(clickedLatLng);

                // --- Send Data to Dash via dcc.Store ---
                const selectedPlaceStore = document.getElementById('selected-place-details-store');
                if (selectedPlaceStore) {
                    const placeData = {
                        // We don't have address info without geocoding
                        name: `Location at ${clickedLatLng.lat().toFixed(4)}, ${clickedLatLng.lng().toFixed(4)}`,
                        formatted_address: "Address not available from map click",
                        lat: clickedLatLng.lat(),
                        lng: clickedLatLng.lng(),
                    };
                    window.Dash.setProps(selectedPlaceStore.id, { data: placeData });
                }
            });
        }

        // --- Initialize the Marker (only once) ---
        if (!marker) {
            marker = new google.maps.Marker({
                map: map,
                anchorPoint: new google.maps.Point(0, -29),
            });
            console.log("Marker initialized.");
        }

        // --- Initialize Autocomplete Element (only once) ---
        const autocompleteContainer = document.getElementById('place-autocomplete-container');
        if (autocompleteContainer && !autocompleteElement) {
            // Create the new PlaceAutocompleteElement
            autocompleteElement = document.createElement('gmp-place-autocomplete');
            autocompleteElement.setAttribute('placeholder', 'E.g., Petronas Twin Towers');
            autocompleteElement.style.width = '100%';

            // Append it to our container div
            autocompleteContainer.appendChild(autocompleteElement);
            console.log("PlaceAutocompleteElement created and appended.");

            // --- Add Listener for Place Selection ---
            autocompleteElement.addEventListener('gmp-placeselect', (event) => {
                const place = event.place;
                if (!place) {
                    console.warn("No place selected or details available.");
                    return;
                }
                
                // The new element provides geometry and other details directly.
                if (!place.geometry || !place.geometry.location) {
                    console.warn("No details available for input: '" + place.displayName + "'");
                    return;
                }

                marker.setVisible(false);

                if (place.viewport) {
                    map.fitBounds(place.viewport);
                } else {
                    map.setCenter(place.geometry.location);
                    map.setZoom(17);
                }
                marker.setPosition(place.geometry.location);
                marker.setVisible(true);

                // --- Send Data to Dash via dcc.Store ---
                const selectedPlaceStore = document.getElementById('selected-place-details-store');
                if (selectedPlaceStore) {
                    const placeData = {
                        name: place.displayName,
                        formatted_address: place.formattedAddress,
                        lat: place.geometry.location.lat(),
                        lng: place.geometry.location.lng(),
                    };
                    // Use Dash's setProps to update the store's data prop
                    window.Dash.setProps(selectedPlaceStore.id, { data: placeData });
                }
            });
        }

        // --- Handle Map Rendering in Modal ---
        setTimeout(() => {
            google.maps.event.trigger(map, 'resize');
            if (marker && marker.getPosition()) {
                map.setCenter(marker.getPosition());
            } else {
                map.setCenter({ lat: 3.1390, lng: 101.6869 });
            }
        }, 200);
    };
}

// --- Clientside Callback for State Dropdown ---
// NOTE: The new PlaceAutocompleteElement does not support the old 'setBounds' method.
// Location biasing must be handled differently, often by setting a 'locationBias'
// property. This simplified example focuses on the core functionality.
// A more advanced implementation might involve re-creating the element on state change.
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = {
    update_autocomplete_bias: function(state_value) {
        if (autocompleteElement && state_value) {
            console.log(`State selected: ${state_value}. Location biasing with the new PlaceAutocompleteElement requires a different approach and is not implemented in this version.`);
        }
        return window.dash_clientside.no_update;
    }
};
