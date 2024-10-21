const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config(); // Load .env file

const app = express();
const port = process.env.PORT || 3000;

// Enable CORS for all origins (you can restrict this to specific domains)
app.use(cors());

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Endpoint to provide the Google Maps API Key
app.get('/api/google-api-key', (req, res) => {
    const apiKey = process.env.GOOGLE_MAPS_API_KEY;
    res.json({ apiKey });
});

// Serve the homepage (index.html) from the 'public' directory
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});