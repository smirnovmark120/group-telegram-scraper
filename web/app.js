// Ensure that Leaflet map is initialized after the DOM is ready
document.addEventListener("DOMContentLoaded", function() {
    // Initialize the map
    const map = L.map('map').setView([32.0853, 34.7818], 13);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    // Create a layer group to store drawn shapes
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Enable drawing of freeform polygons (no rectangles, circles, etc.)
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        },
        draw: {
            polygon: true,  // Only allow polygon drawing
            polyline: false,
            rectangle: false,
            circle: false,
            marker: false,
            circlemarker: false
        }
    });
    map.addControl(drawControl);

    // Event listener: Triggered when a new shape is drawn
    map.on('draw:created', (e) => {
        drawnItems.clearLayers();  // Clear any previous drawings
        drawnItems.addLayer(e.layer);  // Add the newly drawn shape to the map
        updateData();  // Fetch the updated data for the selected area
    });

    // Function to fetch data from Overpass API and display it in the table
    async function updateData() {
        const areas = drawnItems.getLayers();
        if (areas.length === 0) {
            document.getElementById('output').textContent = 'No area selected';
            return;
        }

        const area = areas[0];
        const bounds = area.getBounds();  // Get the bounding box of the drawn area
        const query = `
            [out:json];
            (
                way["highway"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
                relation["boundary"="administrative"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
                node["amenity"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
                way["building"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
            );
            out body;
            >;
            out skel qt;
        `;

        try {
            // Make request to Overpass API
            const response = await axios.get('https://overpass-api.de/api/interpreter', {
                params: { data: query }
            });

            // Process the data
            const streets = await Promise.all(
                response.data.elements
                    .filter(e => e.type === 'way' && e.tags && e.tags.highway)
                    .map(async e => {
                        // Ensure geometry exists and contains at least one point
                        if (e.geometry && e.geometry.length > 0) {
                            const latLng = e.geometry[0];  // Get first point of the way
                            const cityName = await getCityFromCoordinates(latLng.lat, latLng.lon);  // Get city from Nominatim
                            return {
                                name: e.tags.name || 'N/A',
                                name_en: e.tags['name:en'] || 'N/A',
                                name_ar: e.tags['name:ar'] || 'N/A',
                                name_he: e.tags['name:he'] || 'N/A',
                                city: cityName
                            };
                        } else {
                            // If no geometry, return placeholder data
                            return {
                                name: e.tags.name || 'N/A',
                                name_en: e.tags['name:en'] || 'N/A',
                                name_ar: e.tags['name:ar'] || 'N/A',
                                name_he: e.tags['name:he'] || 'N/A',
                                city: 'N/A'
                            };
                        }
                    })
            );

            const areas = response.data.elements.filter(e => e.type === 'relation' && e.tags).map(e => ({
                name: e.tags.name || 'N/A',
                name_en: e.tags['name:en'] || 'N/A',
                name_ar: e.tags['name:ar'] || 'N/A',
                name_he: e.tags['name:he'] || 'N/A',
                type: e.tags.admin_level === '8' ? 'Neighborhood' : e.tags.admin_level === '6' ? 'City' : 'Area'
            }));

            const amenities = response.data.elements.filter(e => e.type === 'node' && e.tags && e.tags.amenity).map(e => ({
                type: e.tags.amenity || 'N/A',
                name: e.tags.name || 'N/A',
                name_en: e.tags['name:en'] || 'N/A',
                name_ar: e.tags['name:ar'] || 'N/A',
                name_he: e.tags['name:he'] || 'N/A'
            }));

            const buildings = response.data.elements.filter(e => e.type === 'way' && e.tags && e.tags.building).length;

            const result = {
                streets,
                areas,
                amenities,
                buildingCount: buildings
            };

            // Display the data as a table in the sidebar
            document.getElementById('output').innerHTML = generateTable(result);
            // Store the JSON for the "Copy JSON" button
            document.getElementById('jsonData').textContent = JSON.stringify(result, null, 2);

        } catch (error) {
            console.error('Error fetching data:', error);
            document.getElementById('output').textContent = 'Error fetching data';
        }
    }

    // Function to find the city for a street
    function findCityName(elements, wayId) {
        const cityRelation = elements.find(e => e.type === 'relation' && e.members.some(m => m.type === 'way' && m.ref === wayId) && e.tags && e.tags.admin_level === '6');
        return cityRelation ? cityRelation.tags.name_en || 'N/A' : 'N/A';
    }

    // Fetch city name using Nominatim's reverse-geocoding
    async function getCityFromCoordinates(lat, lon) {
        try {
            const response = await axios.get('https://nominatim.openstreetmap.org/reverse', {
                params: {
                    lat: lat,
                    lon: lon,
                    format: 'json',
                    addressdetails: 1
                }
            });
            return response.data.address.city || response.data.address.town || response.data.address.village || 'N/A';
        } catch (error) {
            console.error('Error fetching city from Nominatim:', error);
            return 'N/A';
        }
    }

    // Function to generate an HTML table from the result data
    function generateTable(data) {
        let table = `
            <table class="table-auto w-full text-left border-collapse mb-4">
                <thead>
                    <tr class="bg-gray-100">
                        <th class="border px-6 py-3 text-sm">Type</th>
                        <th class="border px-6 py-3 text-sm">Name (EN)</th>
                        <th class="border px-6 py-3 text-sm">Name (AR)</th>
                        <th class="border px-6 py-3 text-sm">Name (HE)</th>
                        <th class="border px-6 py-3 text-sm">City</th>
                    </tr>
                </thead>
                <tbody>
        `;
    
        // Add rows for streets
        data.streets.forEach(street => {
            table += `
                <tr>
                    <td class="border px-6 py-2">Street</td>
                    <td class="border px-6 py-2">${street.name_en}</td>
                    <td class="border px-6 py-2">${street.name_ar}</td>
                    <td class="border px-6 py-2">${street.name_he}</td>
                    <td class="border px-6 py-2">${street.city}</td>
                </tr>
            `;
        });
    
        table += '</tbody></table>';
    
        // Add the total number of streets and the "Copy JSON" button at the bottom
        table += `
            <div class="mt-4 flex justify-between items-center">
                <p class="text-lg">Total Streets: ${data.streets.length}</p>
                <button onclick="copyJSON()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">Copy JSON</button>
            </div>
            <pre id="jsonData" class="hidden"></pre>  <!-- Hidden JSON for copying -->
        `;
    
        return table;
    }

    // Function to copy JSON data to the clipboard
    function copyJSON() {
        const jsonData = document.getElementById('jsonData').textContent;
        navigator.clipboard.writeText(jsonData).then(() => {
            alert('JSON copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    }
});