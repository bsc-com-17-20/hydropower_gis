import os
import duckdb
import folium
import json
from pyproj import Proj, transform
import streamlit as st
from streamlit_folium import st_folium
from proximity import proximity_results, status_proximity_results

# Initialize DuckDB connection
con = duckdb.connect()

# Verify extension files exist
spatial_extension_path = "./duckdb_extensions/spatial.duckdb_extension"
httpfs_extension_path = "./duckdb_extensions/httpfs.duckdb_extension"

# Print full paths and check file existence
print(f"Spatial Extension Full Path: {os.path.abspath(spatial_extension_path)}")
print(f"HTTPFS Extension Full Path: {os.path.abspath(httpfs_extension_path)}")

if not os.path.exists(spatial_extension_path):
    raise FileNotFoundError(f"Spatial extension not found at {spatial_extension_path}")

if not os.path.exists(httpfs_extension_path):
    raise FileNotFoundError(f"HTTPFS extension not found at {httpfs_extension_path}")

# Load spatial extension
con.sql(f"LOAD '{spatial_extension_path}';")
con.sql(f"LOAD '{httpfs_extension_path}';")

# Verify HYDRO file exists
hydro_file = "hydro.json"
if not os.path.exists(hydro_file):
    raise FileNotFoundError(f"HYDRO file not found at {hydro_file}")

# Verify SLN file exists
sln_file = "sln.geojson"
if not os.path.exists(sln_file):
    raise FileNotFoundError(f"HYDRO file not found at {sln_file}")


# Ingest the data from JSON and create a table
hydro_table = con.sql(
    f"CREATE TABLE hydro_malawi AS SELECT * FROM read_json_auto('{hydro_file}')"
)

# Ingest the data from JSON and create a table
sln_table = con.sql(
    f"CREATE TABLE sln_malawi AS SELECT * FROM read_json_auto('{sln_file}')"
)

hydro_query = """
SELECT * FROM hydro_malawi
"""
sln_query = """
SELECT * FROM sln_malawi
"""

hydro_result = con.sql(query=hydro_query).df()
sln_result = con.sql(query=sln_query).df()
st.write(hydro_result)
st.write(sln_result)

# Load the geojson data
with open("hydro.json") as f:
    hydro_data = json.load(f)

# Define the projection of the input coordinates (EPSG:22236)
input_proj = Proj(init="epsg:22236")

# Define the output projection (WGS84)
output_proj = Proj(init="epsg:4326")

# Create a Folium map centered around Malawi
m = folium.Map(location=[-13.5, 34], zoom_start=6)

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

st.header("Malawi Hydropower Scheme")
st_folium(m, width=756)
proximity_results
status_proximity_results

print("Map successfully created!")
con.close()
