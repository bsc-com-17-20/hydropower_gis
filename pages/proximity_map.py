import json
import os
import duckdb
import folium
import streamlit as st
from streamlit_folium import st_folium
from pyproj import Proj, transformer
from proximity import proximity_results

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
m = folium.Map(location=[-13.5, 34], zoom_start=6)

# Prepare coordinates and proximity data
scheme_locations = {}
for feature in hydro_data["features"]:
    coords = feature["geometry"]["coordinates"]
    lon, lat = transformer.transform(input_proj, output_proj, coords[0], coords[1])
    properties = feature["properties"]
    scheme_locations[properties["Scheme_Nam"]] = {
        "lat": lat,
        "lon": lon,
        "status": properties["Status"],
    }

for _, row in proximity_results.iterrows():
    scheme1 = row["scheme1"]
    neighbors = row["nearest_neighbors"]

    # Add marker for the primary scheme
    loc1 = scheme_locations[scheme1]
    popup_info = (
        f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
    )
    folium.Marker(
        location=[loc1["lat"], loc1["lon"]],
        popup=popup_info,
        icon=folium.Icon(color="red" if loc1["status"] == "Proposed" else "blue"),
    ).add_to(m)

    # Add lines to nearest neighbors
    for neighbor in neighbors.split(", "):  # Split by neighbor entries
        try:
            neighbor_name, distance = neighbor.split(": ")
            distance = float(distance.split(" km")[0])
            loc2 = scheme_locations[neighbor_name.split(" (")[0]]  # Extract scheme name

            # Add line for proximity
            folium.PolyLine(
                locations=[[loc1["lat"], loc1["lon"]], [loc2["lat"], loc2["lon"]]],
                color="green" if distance < 50 else "orange",
                weight=2,
                tooltip=f"{scheme1} ↔ {neighbor_name}: {distance} km",
            ).add_to(m)
        except Exception as e:
            print(f"Error processing neighbor {neighbor}: {e}")

# Save the map to an HTML file
m.save("malawi_hydropower_proximity_schemes.html")
st.header("Proximity Map of Hydro Stations in Malawi")
st_folium(m, width=756)
