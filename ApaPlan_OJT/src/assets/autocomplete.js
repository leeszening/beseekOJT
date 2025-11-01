// This function will be called by a clientside callback when the modal is opened.
function initAutocomplete() {
    // Ensure the Google Maps script has loaded.
    if (!google || !google.maps || !google.maps.places) {
        console.error("Google Maps JavaScript API library not loaded.");
        return;
    }

    const mapCanvas = document.getElementById('map-canvas');
    const autocompleteInput = document.getElementById('place-autocomplete-input');

    // Exit if the necessary elements aren't on the page.
    if (!mapCanvas || !autocompleteInput) {
        console.log("Autocomplete elements not found, skipping initialization.");
        return;
    }

    // Default map options (e.g., center on a neutral location)
    const mapOptions = {
        center: { lat: 20, lng: 0 },
        zoom: 2,
        mapId: window.GOOGLE_MAP_ID // Use the mapId from index.html
    };

    const map = new google.maps.Map(mapCanvas, mapOptions);
    const { AdvancedMarkerElement } = google.maps.marker;

    // --- Autocomplete Initialization ---
    const autocomplete = new google.maps.places.Autocomplete(autocompleteInput, {
        fields: [
            "place_id", "name", "formatted_address", "geometry", "types",
            "opening_hours", "formatted_phone_number", "website", "wheelchair_accessible_entrance"
        ],
        types: ["establishment"]
    });

    autocomplete.bindTo("bounds", map);

    let marker = new AdvancedMarkerElement({
        map: null, // Initially hidden
        position: mapOptions.center,
    });

    // --- Event Listener for Place Selection ---
    autocomplete.addListener("place_changed", () => {
        marker.map = null; // Hide previous marker
        const place = autocomplete.getPlace();

        if (!place.geometry || !place.geometry.location) {
            console.log("No details available for input: '" + place.name + "'");
            return;
        }

        // If the place has a geometry, then present it on a map.
        if (place.geometry.viewport) {
            map.fitBounds(place.geometry.viewport);
        } else {
            map.setCenter(place.geometry.location);
            map.setZoom(17); // Why 17? Because it looks good.
        }

        marker.position = place.geometry.location;
        marker.map = map;

        // --- Store Data in Global Variable ---
        // We store the selected place data in a global variable. A dcc.Interval
        // component will poll this variable and update the dcc.Store in Dash.
        // This is the most robust method to avoid JS scope and timing issues.
        const dataToStore = {
            place_id: place.place_id,
            name: place.name,
            address: place.formatted_address,
            location: {
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            },
            types: place.types,
            opening_hours: place.opening_hours ? place.opening_hours.weekday_text : [],
            phone: place.formatted_phone_number || "",
            website: place.website || "",
            oku_friendly: place.wheelchair_accessible_entrance || false
        };
        window.gmaps_selected_place = JSON.stringify(dataToStore);
    });
}

// Assign the function to the window object so Dash can call it.
window.initAutocomplete = initAutocomplete;
