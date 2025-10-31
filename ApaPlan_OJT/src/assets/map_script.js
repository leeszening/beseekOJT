// Global variables to hold the map, marker, and autocomplete instances.
let map;
let marker;
let autocompleteElement;
let isGoogleMapsApiLoaded = false; // Flag to track if the API script has been loaded

/**
 * Dynamically loads the Google Maps script by fetching the API key from the backend.
 */
function loadGoogleMapsScript() {
    // Fetch the API key from our new backend endpoint
    fetch('/api/maps-key')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            const apiKey = data.apiKey;

            // Create a new script element
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=initializeMapComponents`;
            script.async = true;
            script.defer = true;
            script.onerror = onGoogleApiError; // Handle script loading errors

            // Append the script to the document head, which triggers the script to load
            document.head.appendChild(script);
        })
        .catch(error => {
            console.error('Failed to fetch Google Maps API key:', error);
            onGoogleApiError(); // Call the error handler
        });
}

/**
 * This function is called if the Google Maps API script fails to load.
 */
function onGoogleApiError() {
    console.error(
        "Google Maps API failed to load. Check the backend for API key configuration and network for connectivity."
    );
    // Optionally, disable map-related UI elements here
}

/**
 * This function is now the main entry point, called by the dynamically loaded Google Maps script.
 */
window.initializeMapComponents = async function() {
    console.log("Google Maps API loaded successfully via dynamic script.");
    isGoogleMapsApiLoaded = true;

    // We need to load the 'places' library specifically for the new element.
    const { Place } = await google.maps.importLibrary("places");

    // The setupMapInModal function might have been called before the API was ready.
    // If the map container is already in the DOM, we can proceed with setup.
    if (document.getElementById('map-container')) {
        setupMapAndAutocomplete();
    }
};

/**
 * A new function to encapsulate the map and autocomplete setup logic.
 * This will be called by initializeMapComponents or setupMapInModal.
 */
function setupMapAndAutocomplete() {
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
            mapId: "YOUR_MAP_ID" // Replace with your actual Map ID if you have one
        });
        console.log("Google Map initialized.");

        // --- Add Listener for Map Clicks ---
        map.addListener('click', (mapsMouseEvent) => {
            const clickedLatLng = mapsMouseEvent.latLng;
            if (marker) {
                marker.setPosition(clickedLatLng);
                marker.setVisible(true);
            }
            map.panTo(clickedLatLng);

            // --- Send Data to Dash via dcc.Store ---
            const selectedPlaceStore = document.getElementById('selected-place-details-store');
            if (selectedPlaceStore) {
                const placeData = {
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
        autocompleteElement = document.createElement('gmp-place-autocomplete');
        autocompleteElement.setAttribute('placeholder', 'E.g., Petronas Twin Towers');
        autocompleteElement.style.width = '100%';
        autocompleteContainer.innerHTML = ''; // Clear container before appending
        autocompleteContainer.appendChild(autocompleteElement);
        console.log("PlaceAutocompleteElement created and appended.");

        // --- Add Listener for Place Selection ---
        autocompleteElement.addEventListener('gmp-placeselect', (event) => {
            const place = event.place;
            if (!place || !place.geometry || !place.geometry.location) {
                console.warn("Selected place has no geometry.");
                return;
            }

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
                window.Dash.setProps(selectedPlaceStore.id, { data: placeData });
            }
        });
    }

    // --- Handle Map Rendering in Modal ---
    // This ensures the map resizes correctly when the modal opens.
    setTimeout(() => {
        google.maps.event.trigger(map, 'resize');
        if (marker && marker.getPosition()) {
            map.setCenter(marker.getPosition());
        } else {
            map.setCenter({ lat: 3.1390, lng: 101.6869 });
        }
    }, 200);
}


/**
 * This is the primary function called by the Dash clientside callback.
 * It now orchestrates the loading of the API and the setup of the map.
 */
window.setupMapInModal = function() {
    if (isGoogleMapsApiLoaded) {
        // If the API is already loaded, just set up the map components.
        setupMapAndAutocomplete();
    } else {
        // If the API is not loaded, start the loading process.
        // The callback (`initializeMapComponents`) will handle the setup once the script is ready.
        loadGoogleMapsScript();
    }
};

// --- Clientside Callback for State Dropdown ---
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = {
    update_autocomplete_bias: function(state_value) {
        if (autocompleteElement && state_value) {
            console.log(`State selected: ${state_value}. Location biasing with the new PlaceAutocompleteElement requires a different approach.`);
        }
        return window.dash_clientside.no_update;
    }
};
