import json
import os
import geopandas as gpd
import folium
from pyproj import Proj, transformer
import streamlit as st
from streamlit_folium import st_folium
from branca.colormap import LinearColormap
from proximity import proximity_results, buffer_proximity_results
import networkx as nx
import time
import shapely.wkt

# Verify HYDRO file exists
hydro_file = "hydro.json"
if not os.path.exists(hydro_file):
    raise FileNotFoundError(f"HYDRO file not found at {hydro_file}")

print("Load data")
start = time.time()
# Load the data
gdf = gpd.read_file("hotosm_mwi_roads_lines_geojson.geojson")
# Load the geojson data
with open("hydro.json") as f:
    hydro_data = json.load(f)
end = time.time()
print(end - start)
print("Data Loaded")

# Define the projection of the input coordinates (EPSG:22236)
input_proj = Proj(init="epsg:22236")

# Define the output projection (WGS84)
output_proj = Proj(init="epsg:4326")

# Filter out roads of type 'path'
# filtered_gdf = gdf[gdf["highway"] != "path"]
print("Filter data")
start = time.time()
major_roads = gdf[gdf["highway"].isin(["primary", "secondary", "tertiary"])]
end = time.time()
print(end - start)
print("Data filtered")

# Create a network graph
G = nx.Graph()
for idx, road in major_roads.iterrows():
    coords = road.geometry.coords
    for i in range(len(coords) - 1):
        G.add_edge(tuple(coords[i]), tuple(coords[i + 1]))

# Network metrics
st.header("Network Metrics")
"Total nodes:", G.number_of_nodes()
"Total edges:", G.number_of_edges()
"Network density:", nx.density(G)

# Basic network statistics
st.header("Basic Netwrok Statistics")
"Total road segments:", len(major_roads)
"Road type distribution:", major_roads["highway"].value_counts()

# Calculate road segment lengths
# st.header("Road Segment length")
# gdf["length"] = gdf.geometry.length

# Average road segment length
# "Average road segment length:", gdf["length"].mean()
# "Total road network length:", gdf["length"].sum()

# Surface type distribution
# surface_counts = gdf["surface"].value_counts()
# "Road surface distribution:", surface_counts

# Read the GeoJSON file
# gdf = gpd.read_file("hotosm_mwi_roads_lines_geojson.geojson")

# Convert to WGS 84 if not already (just to be sure)
# gdf = gdf.to_crs(epsg=4326)

# Create a map centered on the mean coordinates
# center_lat = gdf.geometry.centroid.y.mean()
# center_lon = gdf.geometry.centroid.x.mean()
# road_map = folium.Map(location=[center_lat, center_lon], zoom_start=10)
road_map = folium.Map(location=[-13.5, 34], zoom_start=10)

# Create a color mapping for road types
# road_types = gdf["highway"].unique()
# color_dict = {
#     "tertiary": "blue",
#     "path": "green",
#     # Add more road types as needed
# }


def add_hydro_stations_to_map(road_map, hydro_data):
    for feature in hydro_data["features"]:
        coords = feature["geometry"]["coordinates"]
        lon, lat = transformer.transform(input_proj, output_proj, coords[0], coords[1])
        properties = feature["properties"]
        if properties["Status"] == "Proposed":
            folium.Marker(
                location=[lat, lon],  # Note: coordinates are [longitude, latitude]
                popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
                icon=folium.Icon(color="red"),
            ).add_to(road_map)
            continue
        folium.Marker(
            location=[lat, lon],  # Note: coordinates are [longitude, latitude]
            popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
            icon=folium.Icon(color="blue"),
        ).add_to(road_map)
    return road_map


def add_proximity_results(m):
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
        # popup_info = (
        #     f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
        # )
        # folium.Marker(
        #     location=[loc1["lat"], loc1["lon"]],
        #     popup=popup_info,
        #     icon=folium.Icon(color="red" if loc1["status"] == "Proposed" else "blue"),
        # ).add_to(m)

        # Add lines to nearest neighbors
        for neighbor in neighbors.split(", "):  # Split by neighbor entries
            try:
                neighbor_name, distance = neighbor.split(": ")
                distance = float(distance.split(" km")[0])
                loc2 = scheme_locations[
                    neighbor_name.split(" (")[0]
                ]  # Extract scheme name

                # Add line for proximity
                folium.PolyLine(
                    locations=[[loc1["lat"], loc1["lon"]], [loc2["lat"], loc2["lon"]]],
                    color="green" if distance < 50 else "orange",
                    weight=2,
                    tooltip=f"{scheme1} ↔ {neighbor_name}: {distance} km",
                ).add_to(m)
            except Exception as e:
                print(f"Error processing neighbor {neighbor}: {e}")
    return m


def add_buffer_results(m, buffer_results):
    # Dictionary to store scheme locations
    scheme_locations = {}

    # Populate scheme locations from hydro_data
    for feature in hydro_data["features"]:
        coords = feature["geometry"]["coordinates"]
        lon, lat = transformer.transform(input_proj, output_proj, coords[0], coords[1])
        properties = feature["properties"]
        scheme_name = properties["Scheme_Nam"]
        scheme_locations[scheme_name] = {
            "lat": lat,
            "lon": lon,
            "status": properties["Status"],
        }

    # Process buffer query results
    for _, row in buffer_results.iterrows():
        scheme_name = row["scheme_name"]

        # Retrieve scheme location
        if scheme_name in scheme_locations:
            loc = scheme_locations[scheme_name]

            # Create a marker for the scheme
            marker_color = "red" if loc["status"] == "Proposed" else "blue"
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=f"Scheme: {scheme_name}<br>Status: {loc['status']}",
                icon=folium.Icon(color=marker_color),
            ).add_to(m)

            # Parse and add buffer geometry
            try:
                # Assuming ST_AsText returns WKT format
                buffer_wkt = row["buffer_geometry"]

                # Convert WKT to GeoJSON for Folium
                buffer_geom = shapely.wkt.loads(buffer_wkt)

                buffer_geojson = {
                    "type": "Feature",
                    "geometry": json.loads(json.dumps(buffer_geom.__geo_interface__)),
                    "properties": {},
                }

                # Create a GeoJSON feature for the buffer
                folium.GeoJson(
                    buffer_geojson.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor": "green",
                        "color": "green",
                        "weight": 2,
                        "fillOpacity": 0.1,
                    },
                    tooltip=f"10km Buffer for {scheme_name}",
                ).add_to(m)

            except Exception as e:
                print(f"Error processing buffer for {scheme_name}: {e}")

    return m


# Function to add roads to the map
def add_roads_to_map(road_map, gdf, color_dict):
    print("Roads")
    start = time.time()
    count = 0
    for idx, road in gdf.iterrows():
        # Extract coordinates
        coords = list(road.geometry.coords)

        # Choose color based on highway type
        road_type = road["highway"]
        color = color_dict.get(road_type, "red")  # Default to red if type not in dict
        count += 1
        # Add the road segment to the map
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in coords],
            color=color,
            weight=2,
            opacity=0.7,
            popup=f"Road Type: {road_type}, OSM ID: {road['osm_id']}",
        ).add_to(road_map)
    end = time.time()
    print(end - start)
    print("Roads loaded")
    print(count)
    return road_map


color_dict = {
    "primary": "#FF4500",  # Orange Red
    "secondary": "#FFD700",  # Gold
    "tertiary": "#1E90FF",  # Dodger Blue
}

st.header("Road")
# Add roads to the map
with st.spinner("Cooking..."):
    road_map = add_roads_to_map(road_map, major_roads, color_dict)
    road_map = add_hydro_stations_to_map(road_map, hydro_data)
    road_map = add_proximity_results(road_map)
    road_map = add_buffer_results(road_map, buffer_proximity_results)
    st_folium(road_map, width=756)

# Add a legend (optional)
legend_html = """
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 120px; height: 90px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white;
     ">
     &nbsp; Road Types <br>
     &nbsp; <i class="fa fa-road" style="color:blue"></i> Tertiary <br>
     &nbsp; <i class="fa fa-road" style="color:green"></i> Path
     </div>
     """
road_map.get_root().html.add_child(folium.Element(legend_html))

# Save the map
road_map.save("malawi_road_network.html")
