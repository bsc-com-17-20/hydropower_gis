import os
import folium
import json
from pyproj import Proj, transform
import streamlit as st
from streamlit_folium import st_folium
from proximity import proximity_results, status_proximity_results

# Verify HYDRO file exists
hydro_file = "hydro.json"
if not os.path.exists(hydro_file):
    raise FileNotFoundError(f"HYDRO file not found at {hydro_file}")

# Load the geojson data
with open("hydro.json") as f:
    hydro_data = json.load(f)

# Define the projection of the input coordinates (EPSG:22236)
input_proj = Proj(init="epsg:22236")

# Define the output projection (WGS84)
output_proj = Proj(init="epsg:4326")

# Create a Folium map centered around Malawi
m = folium.Map(location=[-13.5, 34], zoom_start=7)

# Add markers for each hydropower scheme
for feature in hydro_data["features"]:
    coords = feature["geometry"]["coordinates"]
    lon, lat = transform(input_proj, output_proj, coords[0], coords[1])
    properties = feature["properties"]
    if properties["Status"] == "Proposed":
        folium.Marker(
            location=[lat, lon],  # Note: coordinates are [longitude, latitude]
            popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
            icon=folium.Icon(color="red"),
        ).add_to(m)
        continue
    folium.Marker(
        location=[lat, lon],  # Note: coordinates are [longitude, latitude]
        popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
        icon=folium.Icon(color="blue"),
    ).add_to(m)

# Save the map to an HTML file
m.save("malawi_hydropower_schemes.html")

st.header("Malawi Hydro Power Scheme")
st_folium(m, width=756)
proximity_results
status_proximity_results

print("Map successfully created!")
