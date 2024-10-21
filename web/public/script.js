let map, drawingManager;
let isDrawing = false;

async function getGoogleApiKey() {
    try {
        const response = await axios.get('/api/google-api-key');
        return response.data.apiKey;
    } catch (error) {
        console.error("Error fetching API key: ", error);
        alert("Error fetching Google API key.");
        return null;
    }
}

async function initMap() {
    const apiKey = await getGoogleApiKey();

    if (!apiKey) {
        console.error("Failed to fetch Google API key.");
        return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=drawing&callback=onMapLoad`;
    script.async = true;
    script.defer = true;
    script.onerror = function() {
        console.error("Failed to load Google Maps script.");
        alert("Failed to load Google Maps script.");
    };
    document.head.appendChild(script);
}

function onMapLoad() {
    console.log('Map loaded successfully');
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 8,
        center: { lat: 31.0461, lng: 34.8516 }
    });

    drawingManager = new google.maps.drawing.DrawingManager({
        drawingMode: null,
        drawingControl: false,
        polygonOptions: {
            editable: true,
            draggable: true
        }
    });

    drawingManager.setMap(map);

    google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
        if (event.type === 'polygon') {
            event.overlay.setOptions({
                editable: false,
                draggable: false
            });

            // Use Overpass API to get streets and cities
            getStreetsFromOverpass(event.overlay);
        }
    });
}

function toggleDrawing() {
    isDrawing = !isDrawing;
    drawingManager.setOptions({
        drawingMode: isDrawing ? google.maps.drawing.OverlayType.POLYGON : null
    });
    drawingManager.setMap(map);
}

function getStreetsFromOverpass(polygon) {
    // Extract coordinates from polygon
    const coords = [];
    polygon.getPath().forEach(function(latlng) {
        coords.push(`${latlng.lat()} ${latlng.lng()}`);
    });
    // Close the polygon by repeating the first point
    coords.push(coords[0]);

    // Construct the Overpass QL query
    const query = `
        [out:json];
        // Get administrative boundaries (cities) within the polygon
        (
          relation["boundary"="administrative"]["admin_level"~"^(6|7|8)$"](poly:"${coords.join(' ')}");
        )->.cities;
        // Get ways (streets) within the polygon
        (
          way["highway"](poly:"${coords.join(' ')}");
        )->.streets;
        // Associate streets with cities
        .streets out body;
        rel(pivot.streets)->.streetRelations;
        .cities out body;
        .streetRelations out body;
    `;

    // Make the request to Overpass API
    axios.post('https://overpass-api.de/api/interpreter', `data=${encodeURIComponent(query)}`)
        .then(response => {
            processOverpassData(response.data);
        })
        .catch(error => {
            console.error('Overpass API request failed:', error);
            alert('An error occurred while fetching street data.');
            updateAreaInformation([]);
        });
}

function processOverpassData(data) {
    const elements = data.elements;
    const streets = {};
    const wayIdToCity = {};
    const cityNames = {};

    // Extract city names
    elements.forEach(element => {
        if (element.type === 'relation' && element.tags && element.tags.name && element.tags.boundary === 'administrative') {
            cityNames[element.id] = element.tags.name;
        }
    });

    // Map ways (streets) to cities
    elements.forEach(element => {
        if (element.type === 'way' && element.tags && element.tags.name) {
            let cityName = 'Unknown';

            // Find the relation (city) that the way belongs to
            const relations = elements.filter(rel => rel.type === 'relation' && rel.members && rel.members.some(member => member.type === 'way' && member.ref === element.id));

            if (relations.length > 0) {
                const cityRelation = relations.find(rel => cityNames[rel.id]);
                if (cityRelation) {
                    cityName = cityNames[cityRelation.id];
                }
            }

            if (!streets[cityName]) {
                streets[cityName] = [];
            }
            streets[cityName].push(element.tags.name);
        }
    });

    // Remove duplicate street names
    for (const city in streets) {
        streets[city] = [...new Set(streets[city])];
    }

    // Prepare data for updating area information
    const areaData = Object.keys(streets).map(city => ({
        name: city,
        streets: streets[city]
    }));

    updateAreaInformation(areaData);
}

function updateAreaInformation(data) {
    console.log('Updating area information:', data);
    if (!Array.isArray(data)) {
        console.error('Data is not an array:', data);
        alert('An error occurred: Data is not in the expected format.');
        return;
    }
    const tbody = document.querySelector('#areaData tbody');
    tbody.innerHTML = '';
    data.forEach(city => {
        console.log('City data:', city);
        const row = tbody.insertRow();
        const cellCity = row.insertCell(0);
        const cellStreets = row.insertCell(1);
        cellCity.textContent = city.name;
        if (Array.isArray(city.streets)) {
            cellStreets.textContent = city.streets.length > 0 ? city.streets.join(', ') : 'No streets found';
        } else {
            console.error('Streets data is not an array for city:', city.name, city.streets);
            cellStreets.textContent = 'No streets found';
        }
    });

    if (data.length === 0) {
        const row = tbody.insertRow();
        const cell = row.insertCell(0);
        cell.colSpan = 2;
        cell.textContent = 'No cities or streets found in the selected area.';
    }

    window.areaData = data;
}

function downloadCSV() {
    const data = window.areaData || [];
    if (data.length === 0) {
        alert('No data available to download.');
        return;
    }

    const csvRows = [];
    csvRows.push('City,Street');

    data.forEach(city => {
        if (city.streets.length > 0) {
            city.streets.forEach(street => {
                csvRows.push(`"${city.name}","${street}"`);
            });
        } else {
            csvRows.push(`"${city.name}","No streets found"`);
        }
    });

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'area_data.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Global error handler
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Global error handler:', message, 'at', source, ':', lineno, colno);
    alert('An error occurred: ' + message);
};

initMap();
