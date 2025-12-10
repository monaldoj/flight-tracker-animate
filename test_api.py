#!/usr/bin/env python3
"""
Simple test script to verify pyopensky REST API connection
Usage: python test_api.py
"""

from pyopensky.rest import REST
import pandas as pd

def test_states():
    """Test fetching current aircraft states"""
    print("🚀 Testing OpenSky Network REST API...")
    print("=" * 60)
    
    # Initialize REST API
    api = REST()
    
    print("\n📡 Fetching current aircraft states...")
    print("This may take a few seconds...")
    
    try:
        # Fetch all current aircraft states
        states = api.states()
        
        if states is None or states.empty:
            print("❌ No aircraft data received")
            return
        
        print(f"\n✅ Successfully fetched data for {len(states)} aircraft!")
        print("\n📊 DataFrame Info:")
        print(f"   Columns: {list(states.columns)}")
        print(f"   Shape: {states.shape}")
        
        # Show sample data
        print("\n🔍 Sample Aircraft (first 5):")
        print("-" * 60)
        
        # Select interesting columns
        display_cols = ['icao24', 'callsign', 'origin_country', 'latitude', 
                       'longitude', 'altitude', 'groundspeed', 'onground']
        
        # Filter columns that exist
        available_cols = [col for col in display_cols if col in states.columns]
        
        sample = states[available_cols].head(5)
        print(sample.to_string(index=False))
        
        # Statistics
        print("\n📈 Statistics:")
        print("-" * 60)
        total = len(states)
        on_ground = len(states[states['onground'] == True])
        in_flight = total - on_ground
        countries = states['origin_country'].nunique()
        
        print(f"   Total Aircraft: {total}")
        print(f"   In Flight: {in_flight}")
        print(f"   On Ground: {on_ground}")
        print(f"   Countries: {countries}")
        
        if 'altitude' in states.columns:
            avg_alt = states[states['onground'] == False]['altitude'].mean()
            print(f"   Avg Altitude (in flight): {avg_alt:.0f} meters")
        
        if 'groundspeed' in states.columns:
            avg_vel = states[states['onground'] == False]['groundspeed'].mean()
            print(f"   Avg Ground Speed (in flight): {avg_vel:.1f} m/s")
        
        print("\n✅ API test successful!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_states_with_bounds():
    """Test fetching aircraft states within specific bounds"""
    print("\n\n🌍 Testing with Bounding Box (Europe)...")
    print("=" * 60)
    
    api = REST()
    
    # Bounding box for Europe (approximately)
    # Format: (min_latitude, max_latitude, min_longitude, max_longitude)
    europe_bounds = (35.0, 60.0, -10.0, 30.0)
    
    print(f"\n📍 Bounds: {europe_bounds}")
    print("   (min_lat, max_lat, min_lon, max_lon)")
    
    try:
        states = api.states(bounds=europe_bounds)
        
        if states is None or states.empty:
            print("❌ No aircraft data received for this region")
            return
        
        print(f"\n✅ Found {len(states)} aircraft in Europe!")
        
        # Show top 5 countries
        print("\n🌐 Top Countries:")
        country_counts = states['origin_country'].value_counts().head(5)
        for country, count in country_counts.items():
            print(f"   {country}: {count} aircraft")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  OpenSky Network REST API Test")
    print("  Using pyopensky library")
    print("=" * 60)
    
    # Test 1: Fetch all states
    test_states()
    
    # Test 2: Fetch states with bounds
    test_states_with_bounds()
    
    print("\n" + "=" * 60)
    print("📚 For more info:")
    print("   OpenSky API: https://opensky-network.org/apidoc/rest.html")
    print("   pyopensky docs: https://mode-s.org/pyopensky/rest.html")
    print("=" * 60)
    print("\n")

