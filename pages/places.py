import json
import os
import duckdb
import folium
from streamlit_folium import st_folium

# Verify HYDRO file exists
places_file = "mlwplaces_point.json"
if not os.path.exists(places_file):
    raise FileNotFoundError(f"PLaces file not found at {places_file}")

# Load the geojson data
with open("mlwplaces_point.json") as f:
    places_data = json.load(f)

# Connect to an in-memory DuckDB database
con = duckdb.connect(":memory:")

# Create a table from the GeoJSON data
con.execute(
    """
CREATE TABLE IF NOT EXISTS malawi_places (
    fid INTEGER,
    NAME VARCHAR,
    ADMIN1 VARCHAR,
    COUNTRY VARCHAR,
    CNTRY_FIPS VARCHAR,
    TYPE INTEGER,
    CLASS INTEGER,
    LONGITUDE DOUBLE,
    LATITUDE DOUBLE,
    ID DOUBLE
)
"""
)

# Insert data into the table
for feature in places_data["features"]:
    props = feature["properties"]
    con.execute(
        """
    INSERT INTO malawi_places VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            props["fid"],
            props["NAME"],
            props["ADMIN1"],
            props["COUNTRY"],
            props["CNTRY_FIPS"],
            props["TYPE"],
            props["CLASS"],
            props["LONGITUDE"],
            props["LATITUDE"],
            props["ID"],
        ),
    )

# Query the data to verify
print("Places in Malawi:")
places = con.execute(
    "SELECT NAME, LONGITUDE, LATITUDE, CLASS FROM malawi_places"
).fetchall()
for place in places:
    print(f"{place[0]}: Lon {place[1]}, Lat {place[2]}, Class {place[3]}")

# Create a Folium map centered on Malawi
m = folium.Map(location=[-13.9826, 33.773762], zoom_start=7)

# Add markers for each place
for place in places:
    # Determine marker color based on class
    color = "red" if place[3] == 1 else "blue" if place[3] <= 3 else "green"

    folium.Marker(
        location=[place[2], place[1]],  # [latitude, longitude]
        popup=place[0],
        tooltip=place[0],
        icon=folium.Icon(color=color),
    ).add_to(m)

# Save the map
m.save("malawi_places_map.html")
print("Map saved as malawi_places_map.html")
st_folium(m, width=756)
