#!/usr/bin/env python3
"""
Test Databricks Connection Script
Verifies that your Databricks credentials are configured correctly
and that you can access the flights_states table.
"""

import os
import sys
from databricks import sql

# Configuration
TABLE_NAME = "justinm.geospatial.flights_states"

def test_connection():
    """Test Databricks connection and table access"""
    
    print("=" * 60)
    print("Databricks Connection Test")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("1. Checking environment variables...")
    
    hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
    http_path = os.getenv("DATABRICKS_HTTP_PATH")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not hostname:
        print("❌ DATABRICKS_SERVER_HOSTNAME not set")
        return False
    else:
        print(f"✅ DATABRICKS_SERVER_HOSTNAME: {hostname}")
    
    if not http_path:
        print("❌ DATABRICKS_HTTP_PATH not set")
        return False
    else:
        print(f"✅ DATABRICKS_HTTP_PATH: {http_path}")
    
    if not token:
        print("❌ DATABRICKS_TOKEN not set")
        return False
    else:
        # Show only first and last 4 characters of token
        masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
        print(f"✅ DATABRICKS_TOKEN: {masked_token}")
    
    print()
    
    # Test connection
    print("2. Testing connection to Databricks...")
    
    try:
        connection = sql.connect(
            server_hostname=hostname,
            http_path=http_path,
            access_token=token
        )
        print("✅ Successfully connected to Databricks")
    except Exception as e:
        print(f"❌ Failed to connect to Databricks")
        print(f"   Error: {str(e)}")
        return False
    
    print()
    
    # Test table access
    print(f"3. Testing access to table: {TABLE_NAME}")
    
    try:
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute(f"DESCRIBE TABLE {TABLE_NAME}")
        print(f"✅ Table {TABLE_NAME} exists")
        
        # Get column info
        columns = cursor.fetchall()
        print(f"   Columns: {len(columns)}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        count = cursor.fetchone()[0]
        print(f"✅ Total records: {count:,}")
        
        # Get sample data
        cursor.execute(f"""
            SELECT callsign, origin_country, timestamp, latitude, longitude, altitude 
            FROM {TABLE_NAME} 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            LIMIT 5
        """)
        
        print()
        print("Sample data:")
        print("-" * 60)
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                callsign, country, timestamp, lat, lon, alt = row
                print(f"  {callsign:10} | {country:20} | {timestamp}")
        else:
            print("  No data found")
        
        print("-" * 60)
        
        # Get date range
        cursor.execute(f"""
            SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date
            FROM {TABLE_NAME}
        """)
        
        min_date, max_date = cursor.fetchone()
        print()
        print(f"✅ Date range: {min_date} to {max_date}")
        
        # Get unique callsigns count
        cursor.execute(f"""
            SELECT COUNT(DISTINCT callsign) as unique_callsigns
            FROM {TABLE_NAME}
            WHERE callsign IS NOT NULL
        """)
        
        unique_callsigns = cursor.fetchone()[0]
        print(f"✅ Unique callsigns: {unique_callsigns:,}")
        
        # Get unique countries count
        cursor.execute(f"""
            SELECT COUNT(DISTINCT origin_country) as unique_countries
            FROM {TABLE_NAME}
            WHERE origin_country IS NOT NULL
        """)
        
        unique_countries = cursor.fetchone()[0]
        print(f"✅ Unique countries: {unique_countries}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Failed to access table")
        print(f"   Error: {str(e)}")
        connection.close()
        return False
    
    print()
    
    # Close connection
    connection.close()
    print("✅ Connection closed successfully")
    
    print()
    print("=" * 60)
    print("✅ All tests passed! You're ready to run the application.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: python app/app.py")
    print("  2. Open: http://localhost:8050")
    print("  3. Click 'Load Data' to start")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

