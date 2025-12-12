"""
Flight Tracker Application with Kepler.gl
Visualize flight paths with animation using Databricks data
"""

import os
import json
import re
from io import StringIO
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from flask import Flask, jsonify
from dash import Dash, html, dcc, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from databricks import sql
from keplergl import KeplerGl
from databricks_utils import sqlQuery, get_databricks_server_hostname, get_databricks_token, get_databricks_sp_token

# server = Flask(__name__)

# @server.route("/mapbox_token")
# def mapbox_token():
#     # Return token at runtime—never embedded in HTML
#     return jsonify({"token": os.environ["MAPBOX_API_KEY"]})

# Table configuration
# TABLE_NAME = "justinm.geospatial.flights_states"
TABLE_NAME = "justinm.opensky.ingest_flights"

# Initialize Dash app
app = Dash(
    __name__,
    # server=server,
    external_stylesheets=[dbc.themes.DARKLY],
    # suppress_callback_exceptions=True,
    title="Flight Tracker - Animated"
)

# Styles - Dark mode to match Kepler map
CARD_STYLE = {
    "margin": "10px",
    "padding": "15px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.5)",
    "borderRadius": "5px",
    "backgroundColor": "#242730",
    "border": "1px solid #3a3f4b"
}

CONTROL_PANEL_STYLE = {
    **CARD_STYLE,
    "height": "calc(100vh - 80px)",
    "overflowY": "auto",
    "margin": "10px 0 10px 10px"
}

MAP_CONTAINER_STYLE = {
    "height": "calc(100vh - 80px)",
    "margin": "10px 10px 10px 0",
    "borderRadius": "5px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.5)",
    "overflow": "hidden",
    "backgroundColor": "#242730",
    "border": "1px solid #3a3f4b"
}

with open("map.html", "r") as f:
    map_html = f.read()

# Layout
app.layout = dbc.Container(
    fluid=True,
    children=[
        # Header
        dbc.Row([
            dbc.Col([
                html.H2(
                    "✈️ Flight Tracker - Animated",
                    className="text-center",
                    style={
                        "color": "#12939A",
                        "margin": "10px 0",
                        "padding": "10px 0",
                        "textShadow": "0 0 10px rgba(18, 147, 154, 0.5)"
                    }
                ),
            ])
        ]),
        
        # Main content
        dbc.Row([
            # Left sidebar - Filters
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("Filters", style={"color": "#e0e0e0", "margin": "0"})
                    ),
                    dbc.CardBody([
                        # Status indicator
                        html.Div([
                            html.Span("●", id="status-indicator", style={
                                "color": "gray",
                                "fontSize": "20px",
                                "marginRight": "5px"
                            }),
                            html.Span("Ready", id="status-text", style={"color": "#e0e0e0"}),
                        ], className="mb-3"),
                        
                        html.Hr(),
                        
                        # Callsign filter (dropdown)
                        html.Div([
                            dbc.Label("Callsign", html_for="callsign-filter", style={"color": "#e0e0e0"}),
                            dcc.Dropdown(
                                id="callsign-filter",
                                options=[],
                                value=[],  # No default callsign - show all
                                placeholder="Select callsign(s)...",
                                multi=True,
                                className="mb-3 dark-dropdown",
                                style={"backgroundColor": "#2c3039", "color": "#e0e0e0"}
                            ),
                        ]),
                        
                        # Origin country filter (dropdown)
                        html.Div([
                            dbc.Label("Origin Country", html_for="country-filter", style={"color": "#e0e0e0"}),
                            dcc.Dropdown(
                                id="country-filter",
                                options=[],
                                value=["United States"],  # Default to United States
                                placeholder="Select country(ies)...",
                                multi=True,
                                className="mb-3 dark-dropdown",
                                style={"backgroundColor": "#2c3039", "color": "#e0e0e0"}
                            ),
                        ]),
                        
                        # Timestamp range filter
                        html.Div([
                            dbc.Label("Start Date & Time", html_for="start-datetime-filter", style={"color": "#e0e0e0"}),
                            dbc.Input(
                                id="start-datetime-filter",
                                type="datetime-local",
                                value=(datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M'),
                                className="mb-2",
                                style={"backgroundColor": "#2c3039", "color": "#e0e0e0", "border": "1px solid #3a3f4b"}
                            ),
                            dbc.Label("End Date & Time", html_for="end-datetime-filter", style={"color": "#e0e0e0", "marginTop": "10px"}),
                            dbc.Input(
                                id="end-datetime-filter",
                                type="datetime-local",
                                value=datetime.now().strftime('%Y-%m-%dT%H:%M'),
                                className="mb-3",
                                style={"backgroundColor": "#2c3039", "color": "#e0e0e0", "border": "1px solid #3a3f4b"}
                            ),
                        ]),
                        
                        html.Hr(),
                        
                        # Load data button
                        dbc.Button(
                            "Load Flight Data",
                            id="load-button",
                            color="primary",
                            className="w-100 mb-3"
                        ),
                        
                        html.Hr(),
                        
                        # Statistics
                        html.Div([
                            html.H6("Statistics", className="mb-2", style={"color": "#e0e0e0"}),
                            html.Div(id="stats-display", style={"color": "#e0e0e0"})
                        ])
                    ])
                ], style=CONTROL_PANEL_STYLE)
            ], width=3),
            
            # Right side - Kepler.gl Map
            dbc.Col([
                html.Div([
                    html.Iframe(
                        id="kepler-map",
                        srcDoc=map_html,
                        style={"width": "100%", "height": "100%", "border": "none"}
                    )
                ], style=MAP_CONTAINER_STYLE)
            ], width=9, style={"padding": "0"})
        ], style={"height": "calc(100vh - 80px)"}),
        
        # Store for flight data
        dcc.Store(id="flight-data-store"),
        dcc.Store(id="initial-load-complete", data=False),
        
        # Interval to trigger initial load
        dcc.Interval(
            id="initial-load-trigger",
            interval=500,  # 500ms delay
            n_intervals=0,
            max_intervals=1  # Only fire once
        )
    ],
    style={
        "maxWidth": "100%",
        "padding": "0",
        "height": "100vh",
        "overflow": "hidden",
        "backgroundColor": "#1a1d24"
    }
)


# def get_databricks_connection():
#     """
#     Create and return a Databricks SQL connection
#     """
#     if not all([DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN]):
#         raise ValueError(
#             "Databricks credentials not configured. Please set environment variables:\n"
#             "DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN"
#         )
    
#     connection = sql.connect(
#         server_hostname=DATABRICKS_SERVER_HOSTNAME,
#         http_path=DATABRICKS_HTTP_PATH,
#         access_token=DATABRICKS_TOKEN
#     )
#     return connection


def fetch_flight_data(callsigns=None, countries=None, start_date=None, end_date=None):
    """
    Fetch flight data from Databricks table
    
    Args:
        callsigns: List of callsigns to filter
        countries: List of origin countries to filter
        start_date: Start timestamp (datetime or string)
        end_date: End timestamp (datetime or string)
    
    Returns:
        pandas DataFrame with flight data
    """
    try:
        # connection = get_databricks_connection()
        # cursor = connection.cursor()
        
        # Build query with filters
        query = f"""
            SELECT 
                icao24, 
                callsign, 
                origin_country, 
                time_position as last_position, 
                last_contact as timestamp,
                longitude as lon, 
                latitude as lat
                -- geo_altitude as altitude
                -- on_ground as onground, 
                -- velocity as groundspeed, 
                -- true_track as track,
                -- vertical_rate, 
                -- squawk, 
                -- spi, 
                -- category as position_source
            FROM {TABLE_NAME}
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL
        """
        
        # Add filters
        if callsigns:
            callsigns_str = ", ".join([f"'{cs}'" for cs in callsigns])
            query += f" AND callsign IN ({callsigns_str})"
        
        if countries:
            countries_str = ", ".join([f"'{c}'" for c in countries])
            query += f" AND origin_country IN ({countries_str})"
        
        if start_date:
            query += f" AND last_contact >= '{start_date}'"
        
        if end_date:
            query += f" AND last_contact <= '{end_date}'"
        
        query += " ORDER BY last_contact"
        
        print(f"Executing query: {query}")
        
        # Execute query
        # cursor.execute(query)
        
        
        # Fetch results
        # columns = [desc[0] for desc in cursor.description]
        # rows = cursor.fetchall()
        
        # # Close connection
        # cursor.close()
        # connection.close()
        
        df = sqlQuery(query)
        # Create DataFrame
        # df = pd.DataFrame(rows, columns=columns)
        
        if not df.empty:
            # Convert ALL datetime/timestamp columns to string format
            for col in df.columns:
                # Check if column contains datetime-like objects
                if df[col].dtype == 'object':
                    # Check first non-null value
                    sample = df[col].dropna().head(1)
                    if len(sample) > 0:
                        sample_val = sample.iloc[0]
                        # Check if it's a datetime-like object
                        if hasattr(sample_val, 'strftime') or str(type(sample_val)) == "<class 'datetime.datetime'>":
                            try:
                                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                # Also check pandas datetime types
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Clean callsign
            if 'callsign' in df.columns:
                df['callsign'] = df['callsign'].fillna('N/A').str.strip()
        
        print(f"Fetched {len(df)} records")
        return df
        
    except Exception as e:
        print(f"Error fetching flight data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_unique_callsigns():
    """Get unique callsigns from the table for dropdown"""
    try:
        # connection = get_databricks_connection()
        # cursor = connection.cursor()
        
        query = f"""
            SELECT DISTINCT callsign 
            FROM {TABLE_NAME} 
            WHERE callsign IS NOT NULL 
            ORDER BY callsign 
            LIMIT 1000
        """
        
        # cursor.execute(query)
        # callsigns = [row[0].strip() for row in cursor.fetchall() if row[0]]
        
        # cursor.close()
        # connection.close()
        
        df = sqlQuery(query)
        callsigns = df['callsign'].unique()
        
        return [{"label": cs, "value": cs} for cs in callsigns]
        
    except Exception as e:
        print(f"Error fetching callsigns: {e}")
        return []


def get_unique_countries():
    """Get unique origin countries from the table for dropdown"""
    try:
        # connection = get_databricks_connection()
        # cursor = connection.cursor()
        
        query = f"""
            SELECT DISTINCT origin_country 
            FROM {TABLE_NAME} 
            WHERE origin_country IS NOT NULL 
            ORDER BY origin_country
        """
        
        # cursor.execute(query)
        # countries = [row[0] for row in cursor.fetchall() if row[0]]
        
        # cursor.close()
        # connection.close()
        
        df = sqlQuery(query)
        countries = df['origin_country'].unique()
        
        return [{"label": c, "value": c} for c in countries]
        
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []


def create_kepler_map(df):
    """
    Create Kepler.gl map with flight path animation
    
    Args:
        df: pandas DataFrame with flight data (must have lat, lon, timestamp columns)
    
    Returns:
        HTML string of Kepler.gl map
    """
    if df.empty:
        return "<html><body style='background-color: #242730; color: #e0e0e0;'><h3 style='text-align: center; padding: 50px;'>No data to display. Please load data first.</h3></body></html>"
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # CRITICAL: Convert timestamp to string format that Kepler understands
    # This must be done before passing to Kepler.gl
    if 'timestamp' in df.columns:
        # Check if it's already a string
        if df['timestamp'].dtype != 'object' or not isinstance(df['timestamp'].iloc[0], str):
            # Convert pandas timestamps to string
            if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Handle object dtype with Timestamp objects
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert any other timestamp columns
    for col in df.columns:
        if col != 'timestamp' and ('time' in col.lower() or 'date' in col.lower()):
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                elif df[col].dtype == 'object' and len(df[col].dropna()) > 0:
                    sample_val = df[col].dropna().iloc[0]
                    if hasattr(sample_val, 'strftime'):
                        df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass  # If conversion fails, leave as is
    
    # Create Kepler map
    mapbox_api_key = os.environ["MAPBOX_API_KEY"]
    # print("MAPBOX_API_KEY:", mapbox_api_key)
    # print("TOKEN FROM ENV:", repr(os.environ.get("MAPBOX_API_KEY")))
    map_obj = KeplerGl(height=800, mapboxApiAccessToken=mapbox_api_key)
    
    # Add data to map
    map_obj.add_data(data=df, name='flight_paths')
    
    # Configure the map for trip/path visualization with animation
    config = {
        'version': 'v1',
        'config': {
            'visState': {
                'filters': [
                    {
                        'dataId': ['flight_paths'],
                        'id': 'time_filter',
                        'name': ['timestamp'],
                        'type': 'timeRange',
                        'enlarged': True,
                        'plotType': 'histogram',
                        'animationWindow': 'free',
                        'speed': 1
                    }
                ],
                'layers': [
                    {
                        'type': 'trip',
                        'config': {
                            'dataId': 'flight_paths',
                            'label': 'Flight Paths',
                            'color': [18, 147, 154],
                            'columns': {
                                'lat': 'lat',
                                'lng': 'lon',
                                'timestamp': 'timestamp'
                            },
                            'isVisible': True,
                            'visConfig': {
                                'opacity': 0.8,
                                'thickness': 3,
                                'trailLength': 180,
                                'colorRange': {
                                    'name': 'Global Warming',
                                    'type': 'sequential',
                                    'category': 'Uber',
                                    'colors': [
                                        '#5A1846',
                                        '#900C3F',
                                        '#C70039',
                                        '#E3611C',
                                        '#F1920E',
                                        '#FFC300'
                                    ]
                                }
                            }
                        }
                    },
                    {
                        'type': 'point',
                        'config': {
                            'dataId': 'flight_paths',
                            'label': 'Aircraft Points',
                            'color': [255, 203, 153],
                            'columns': {
                                'lat': 'lat',
                                'lng': 'lon',
                                'altitude': 'altitude'
                            },
                            'isVisible': True,
                            'visConfig': {
                                'radius': 5,
                                'opacity': 0.6,
                                'radiusRange': [0, 50],
                                'colorRange': {
                                    'name': 'Global Warming',
                                    'type': 'sequential',
                                    'category': 'Uber',
                                    'colors': [
                                        '#5A1846',
                                        '#900C3F',
                                        '#C70039',
                                        '#E3611C',
                                        '#F1920E',
                                        '#FFC300'
                                    ]
                                },
                                'filled': True
                            }
                        }
                    }
                ],
                'interactionConfig': {
                    'tooltip': {
                        'fieldsToShow': {
                            'flight_paths': [
                                {'name': 'callsign', 'format': None},
                                {'name': 'origin_country', 'format': None},
                                {'name': 'altitude', 'format': None},
                                {'name': 'groundspeed', 'format': None},
                                {'name': 'timestamp', 'format': None}
                            ]
                        },
                        'enabled': True
                    }
                }
            },
            'mapState': {
                'bearing': 0,
                'dragRotate': False,
                'latitude': 38.6274,
                'longitude': -90.1982,
                'pitch': 0,
                'zoom': 4,
                'isSplit': False,
                "isViewportSynced": True,
            },
            'mapStyle': {
                'styleType': 'dark',
                'topLayerGroups': {},
                'visibleLayerGroups': {
                    'label': True,
                    'road': True,
                    'border': False,
                    'building': True,
                    'water': True,
                    'land': True,
                    '3d building': False
                }
            }
        }
    }
    
    # Apply configuration
    map_obj.config = config
    # print("CONFIG:", map_obj.config)
    map_obj.save_to_html(file_name="map.html")
    # After saving map.html, find and replace Mapbox tokens using regex
    new_token = os.environ["MAPBOX_API_KEY"]
    try:
        with open("map.html", "r", encoding="utf-8") as f:
            html_contents = f.read()
        # Use regex to find and replace any token after mapboxApiAccessToken:
        # This matches mapboxApiAccessToken:"<any characters>" or mapboxApiAccessToken:""
        html_contents = re.sub(
            r'mapboxApiAccessToken:"[^"]*"',
            f'mapboxApiAccessToken:"{new_token}"',
            html_contents
        )
        with open("map.html", "w", encoding="utf-8") as f:
            f.write(html_contents)
    except Exception as e:
        print(f"Token replace failed: {e}")

    with open("map.html", "r", encoding="utf-8") as f:
            html_contents = f.read()

    return html_contents
    
    # # Return HTML - decode bytes to string if necessary
    # html_output = map_obj._repr_html_()
    
    # # Check if it's bytes and decode to string
    # if isinstance(html_output, bytes):
    #     html_output = html_output.decode('utf-8')
    
    # # print("HTML OUTPUT:", html_output)
    # return html_output


@app.callback(
    [
        Output("callsign-filter", "options"),
        Output("country-filter", "options"),
        Output("initial-load-complete", "data")
    ],
    [
        Input("load-button", "n_clicks"),
        Input("initial-load-trigger", "n_intervals")
    ],
    State("initial-load-complete", "data")
)
def load_filter_options(n_clicks, n_intervals, initial_load_complete):
    """Load dropdown options on initial page load or button click"""
    ctx = callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Only load once automatically, or when button is clicked
    if trigger_id == "initial-load-trigger" and initial_load_complete:
        raise PreventUpdate
    
    callsigns = get_unique_callsigns()
    countries = get_unique_countries()
    
    return callsigns, countries, True


@app.callback(
    [
        Output("flight-data-store", "data"),
        Output("status-indicator", "style"),
        Output("status-text", "children")
    ],
    [
        Input("load-button", "n_clicks"),
        Input("initial-load-trigger", "n_intervals")
    ],
    [
        State("callsign-filter", "value"),
        State("country-filter", "value"),
        State("start-datetime-filter", "value"),
        State("end-datetime-filter", "value"),
        State("initial-load-complete", "data")
    ]
)
def load_flight_data(n_clicks, n_intervals, callsigns, countries, start_datetime, end_datetime, initial_load_complete):
    """
    Load flight data from Databricks based on filters
    """
    ctx = callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Auto-load on initial trigger with past 6 hours of data
    if trigger_id == "initial-load-trigger":
        if not initial_load_complete:
            # Set time window to past 6 hours for initial load
            current_time = datetime.now()
            six_hours_ago = current_time - timedelta(hours=6)
            start_datetime = six_hours_ago.strftime('%Y-%m-%dT%H:%M')
            end_datetime = current_time.strftime('%Y-%m-%dT%H:%M')
            # Don't filter by callsign - show all
            callsigns = None if not callsigns else callsigns
    elif trigger_id == "load-button":
        if not n_clicks:
            raise PreventUpdate
    else:
        raise PreventUpdate
    
    # Convert datetime-local format to database format
    start_date = None
    end_date = None
    if start_datetime:
        # Convert from 'YYYY-MM-DDTHH:MM' to 'YYYY-MM-DD HH:MM:SS'
        start_date = start_datetime.replace('T', ' ') + ':00'
    if end_datetime:
        # Convert from 'YYYY-MM-DDTHH:MM' to 'YYYY-MM-DD HH:MM:SS'
        end_date = end_datetime.replace('T', ' ') + ':00'
    
    try:
        # Fetch data
        df = fetch_flight_data(
            callsigns=callsigns,
            countries=countries,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return (
                None,
                {"color": "orange", "fontSize": "20px", "marginRight": "5px"},
                "No Data"
            )
        
        # Double-check: Ensure all datetime columns are converted to strings for JSON serialization
        for col in df.columns:
            # Check pandas datetime types
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            # Check for object columns that might contain datetime objects
            elif df[col].dtype == 'object':
                sample = df[col].dropna().head(1)
                if len(sample) > 0:
                    sample_val = sample.iloc[0]
                    if hasattr(sample_val, 'strftime') or 'Timestamp' in str(type(sample_val)):
                        try:
                            df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) and hasattr(x, 'strftime') else str(x) if pd.notna(x) else None)
                        except Exception as e:
                            print(f"Warning: Could not convert column {col}: {e}")
        
        # Convert to JSON for storage
        data_json = df.to_json(date_format='iso', orient='split')
        
        return (
            data_json,
            {"color": "green", "fontSize": "20px", "marginRight": "5px"},
            f"Loaded {len(df)} records"
        )
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return (
            None,
            {"color": "red", "fontSize": "20px", "marginRight": "5px"},
            "Error loading data"
        )


@app.callback(
    [
        Output("kepler-map", "srcDoc"),
        Output("stats-display", "children")
    ],
    Input("flight-data-store", "data")
)
def update_map_and_stats(data_json):
    """
    Update Kepler.gl map and statistics
    """
    if not data_json:
        return (
            "<html><body style='background-color: #242730; color: #e0e0e0;'><h3 style='text-align: center; padding: 50px;'>No data loaded. Click 'Load Data' to begin.</h3></body></html>",
            html.P("No data available")
        )
    
    try:
        # Load data
        df = pd.read_json(StringIO(data_json), orient='split')
        
        if df.empty:
            return (
                "<html><body style='background-color: #242730; color: #e0e0e0;'><h3 style='text-align: center; padding: 50px;'>No flights match the selected filters.</h3></body></html>",
                html.P("No data matches filters")
            )
        
        # Ensure timestamp is a string (in case JSON deserialized it back to datetime)
        if 'timestamp' in df.columns and df['timestamp'].dtype != 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create Kepler map (will do additional timestamp conversion inside)
        kepler_html = create_kepler_map(df)
        
        # Create statistics
        total_flights = df['callsign'].nunique()
        total_records = len(df)
        countries = df['origin_country'].nunique()
        
        # avg_altitude = df['altitude'].mean()
        # avg_speed = df['groundspeed'].mean()
        
        stats = html.Div([
            html.P([html.Strong("Total Flights: "), f"{total_flights}"], style={"color": "#e0e0e0"}),
            html.P([html.Strong("Total Records: "), f"{total_records}"], style={"color": "#e0e0e0"}),
            html.P([html.Strong("Countries: "), f"{countries}"], style={"color": "#e0e0e0"}),
            html.Hr(),
            # html.P([html.Strong("Avg Altitude: "), f"{avg_altitude:.0f} m" if not np.isnan(avg_altitude) else "N/A"], style={"color": "#e0e0e0"}),
            # html.P([html.Strong("Avg Speed: "), f"{avg_speed:.1f} m/s" if not np.isnan(avg_speed) else "N/A"], style={"color": "#e0e0e0"}),
        ], style={"fontSize": "14px", "color": "#e0e0e0"})
        
        # with open("map.html", "r") as f:
        #     kepler_html = f.read()

        return kepler_html, stats
        
    except Exception as e:
        print(f"Error updating map: {e}")
        import traceback
        traceback.print_exc()
        return (
            f"<html><body style='background-color: #242730; color: #e0e0e0;'><h3 style='text-align: center; padding: 50px;'>Error creating map: {str(e)}</h3></body></html>",
            html.P("Error loading data")
        )


# Run the app
if __name__ == "__main__":
    app.run(
        debug=False
    )
