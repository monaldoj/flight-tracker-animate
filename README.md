# ✈️ Flight Tracker - Kepler.gl Animation

An interactive flight tracking application built with Plotly Dash and Kepler.gl, featuring animated flight path visualization using Databricks data.

![Flight Tracker Demo](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Dash](https://img.shields.io/badge/dash-2.14+-orange)

## 🌟 Features

* **Kepler.gl Visualization**: Beautiful, interactive map with native animation capabilities
* **Animated Flight Paths**: Trip layer visualization with time-based animation showing aircraft movement over time
* **Databricks Integration**: Pulls data directly from Databricks table `justinm.geospatial.flights_states`
* **Simple Filtering**:
  - Callsign dropdown (multi-select)
  - Origin country dropdown (multi-select)
  - Timestamp range picker
* **Real-time Statistics**:
  - Total flights count
  - Total data records
  - Number of countries
  - Average altitude and speed
* **Interactive Map Features**:
  - Zoom, pan, and rotate
  - Tooltip on hover showing flight details
  - Time range filter with histogram
  - Animation controls (play/pause, speed adjustment)
  - Trail length adjustment

## 🏗️ Architecture

The application is built using:

* **Frontend**: Dash (Python web framework) with Bootstrap components
* **Maps**: Kepler.gl for interactive 3D mapping and animation
* **Data Source**: Databricks table via Databricks SQL Connector
* **Data Processing**: Pandas and NumPy
* **Visualization**: Trip layer for animated flight paths

## 📋 Prerequisites

* Python 3.8+
* Databricks workspace with access to the flight data table
* Databricks SQL Warehouse
* Personal Access Token for Databricks

## 🚀 Installation & Setup

### Local Development

1. **Clone the repository**:
```bash
git clone <repository-url>
cd flight-tracker-animate
```

2. **Install dependencies**:
```bash
cd app
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your Databricks credentials:
```bash
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=your-databricks-token
PORT=8050
HOST=0.0.0.0
```

4. **Export environment variables**:
```bash
export $(cat .env | xargs)
```

5. **Run the application**:
```bash
python app.py
```

6. **Open your browser** and navigate to:
```
http://localhost:8050
```

## 🎮 Usage

### Application Workflow

1. **Load Data**: Click the "Load Data" button to populate the callsign and country dropdowns
2. **Select Filters** (optional):
   - Choose one or more callsigns from the dropdown
   - Choose one or more countries from the dropdown
   - Select a date range using the timestamp picker
3. **Load Filtered Data**: Click "Load Data" again with your selected filters
4. **Apply Additional Filters**: Use "Apply Filters" to further refine the data without reloading from Databricks
5. **Animate**: Use Kepler.gl's built-in animation controls to play the flight movements over time

### Map Controls

* **Animation**:
  - Click the play button in the time filter to start animation
  - Adjust animation speed with the speed slider
  - Drag the time range to focus on specific time periods
* **View**:
  - Mouse wheel to zoom
  - Click and drag to pan
  - Right-click and drag to rotate (if enabled)
* **Layers**:
  - Toggle trip layer and point layer visibility
  - Adjust trail length, thickness, and opacity
  - Change color schemes
* **Tooltip**: Hover over any flight path or point to see:
  - Callsign
  - Origin country
  - Altitude
  - Ground speed
  - Timestamp

## 📊 Data Schema

The application reads from table `justinm.geospatial.flights_states` with the following columns:

| Column          | Type      | Description                               |
|-----------------|-----------|-------------------------------------------|
| icao24          | string    | Unique aircraft identifier                |
| callsign        | string    | Aircraft callsign/flight number           |
| origin_country  | string    | Country of registration                   |
| last_position   | timestamp | Last position update time                 |
| timestamp       | timestamp | Data record timestamp                     |
| longitude       | double    | Current longitude                         |
| latitude        | double    | Current latitude                          |
| altitude        | double    | Barometric altitude in meters             |
| onground        | boolean   | On ground status                          |
| groundspeed     | double    | Ground speed in m/s                       |
| track           | double    | True track/heading in degrees             |
| vertical_rate   | double    | Vertical speed in m/s                     |
| squawk          | string    | Squawk code                               |
| spi             | boolean   | Special position indicator                |
| position_source | int       | Position data source                      |

## 🔧 Configuration

### Environment Variables

| Variable                      | Description                      | Required |
|-------------------------------|----------------------------------|----------|
| DATABRICKS_SERVER_HOSTNAME    | Databricks workspace hostname    | Yes      |
| DATABRICKS_HTTP_PATH          | SQL warehouse HTTP path          | Yes      |
| DATABRICKS_TOKEN              | Personal access token            | Yes      |
| PORT                          | Application port                 | No (default: 8050) |
| HOST                          | Application host                 | No (default: 0.0.0.0) |

### Kepler.gl Configuration

The application uses a pre-configured Kepler.gl setup with:

* **Trip Layer**: Animates flight paths over time
  - Color: Blue-to-orange gradient (Global Warming palette)
  - Trail length: 180 seconds
  - Thickness: 3 pixels
  
* **Point Layer**: Shows individual aircraft positions
  - Color: Altitude-based gradient
  - Radius: 5 pixels
  - Opacity: 0.6

* **Time Filter**: Enables animation
  - Type: Time range
  - Animation window: Free
  - Default speed: 1x

You can customize these settings in the `create_kepler_map()` function in `app.py`.

## 🗂️ Project Structure

```
flight-tracker-animate/
├── app/
│   ├── app.py              # Main application file
│   ├── requirements.txt    # Python dependencies
│   └── app.yml             # Databricks app configuration
├── .env.example            # Example environment variables
├── README.md               # Main documentation (this file)
└── ... (other config files)
```

## 🔒 Security & Best Practices

* Never commit credentials or tokens to version control
* Use environment variables for all sensitive configuration
* Use Databricks secrets for production deployments
* Limit SQL warehouse access appropriately
* Monitor query costs and data transfer

## 🚀 Performance Optimization

The app includes several performance optimizations:

1. **Lazy Loading**: Data is only loaded when requested
2. **Client-side Filtering**: Apply filters without re-querying Databricks
3. **Efficient SQL Queries**: Uses column projection and WHERE clauses
4. **Limited Dropdown Options**: Limits callsign dropdown to 1000 entries

For even better performance:

1. **Use date filters**: Always specify a date range to limit data volume
2. **Filter by callsign or country**: Reduces the dataset size
3. **Close animation when not needed**: Reduces rendering load
4. **Use appropriate SQL warehouse size**: Balance cost vs. query speed

## 🐛 Troubleshooting

### Common Issues

**No data showing on map**:
* Click "Load Data" button first
* Check Databricks credentials are correct
* Verify table exists and has data
* Check network connectivity to Databricks

**"Error loading data" message**:
* Verify Databricks SQL Warehouse is running
* Check token has not expired
* Verify HTTP path is correct
* Review console logs for detailed error messages

**Dropdown options not loading**:
* Ensure you clicked "Load Data" button
* Check SQL warehouse permissions
* Verify table name is correct
* Look for errors in browser console

**Animation not working**:
* Ensure data has been loaded
* Check that timestamp column has valid dates
* Verify time filter is enabled in Kepler.gl
* Try clicking the play button in the time range filter

**Kepler.gl map not displaying**:
* Check browser console for errors
* Verify pandas DataFrame has required columns (lat, lon, timestamp)
* Try reloading the page
* Check if data is empty

## 📦 Dependencies

Key Python packages:

* `dash>=2.14.0` - Web framework
* `dash-bootstrap-components>=1.5.0` - UI components
* `pandas>=2.0.0` - Data manipulation
* `numpy>=1.24.0` - Numerical operations
* `plotly>=5.17.0` - Plotting library
* `keplergl>=0.3.2` - Map visualization
* `databricks-sql-connector>=3.0.0` - Databricks SQL connection
* `databricks-sdk>=0.12.0` - Databricks SDK

## 📝 Example Queries

The application generates queries like:

```sql
-- Load all data (with limits)
SELECT icao24, callsign, origin_country, last_position, timestamp,
       longitude as lon, latitude as lat, altitude, onground, groundspeed, 
       track, vertical_rate, squawk, spi, position_source
FROM justinm.geospatial.flights_states
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
ORDER BY timestamp

-- Filter by callsign
WHERE callsign IN ('AAL3074', 'UAL123')

-- Filter by country
WHERE origin_country IN ('United States', 'United Kingdom')

-- Filter by date range
WHERE timestamp >= '2024-01-01' AND timestamp <= '2024-01-31'
```

## 🙏 Acknowledgments

* [Kepler.gl](https://kepler.gl/) by Uber for amazing geospatial visualization
* [Plotly Dash](https://dash.plotly.com/) for the web framework
* [Databricks](https://databricks.com/) for data platform

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues and questions:
* Check the [Kepler.gl documentation](https://docs.kepler.gl/)
* Review [Dash documentation](https://dash.plotly.com/)
* Check [Databricks SQL documentation](https://docs.databricks.com/sql/)

---

**Built with ❤️ using Databricks, Dash, and Kepler.gl**
