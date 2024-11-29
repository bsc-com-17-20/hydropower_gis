import json
import duckdb
import os
import streamlit as st

st.header("Proximity Analysis of Hydropower Stations in Malawi")

# Connect to an in-memory database
con = duckdb.connect(":memory:")

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


# Load the GeoJSON data
with open("hydro.json", "r") as file:
    hydro_data = json.load(file)

# Create a table with hydropower scheme data
con.execute(
    """
CREATE TABLE hydropower_schemes (
    scheme_name VARCHAR,
    status VARCHAR,
    longitude DOUBLE,
    latitude DOUBLE
)
"""
)

# Insert data from the GeoJSON
for feature in hydro_data["features"]:
    con.execute(
        """
    INSERT INTO hydropower_schemes 
    VALUES (?, ?, ?, ?)
    """,
        (
            feature["properties"]["Scheme_Nam"],
            feature["properties"]["Status"],
            feature["geometry"]["coordinates"][0],
            feature["geometry"]["coordinates"][1],
        ),
    )

# Proximity Analysis using ST_Distance (requires spatial extension)
proximity_query = """
WITH scheme_distances AS (
    SELECT 
        h1.scheme_name AS scheme1,
        h2.scheme_name AS scheme2,
        ST_Distance(
            ST_Point(h1.longitude, h1.latitude), 
            ST_Point(h2.longitude, h2.latitude)
        ) / 1000.0 AS distance_km,
        h1.status AS status1,
        h2.status AS status2
    FROM hydropower_schemes h1
    CROSS JOIN hydropower_schemes h2
    WHERE h1.scheme_name != h2.scheme_name
)

SELECT 
    scheme1,
    status1,
    ROUND(MIN(distance_km), 2) AS min_distance,
    ROUND(AVG(distance_km), 2) AS avg_distance,
    ROUND(MAX(distance_km), 2) AS max_distance,
    GROUP_CONCAT(
        scheme2 || ' (' || status2 || '): ' || ROUND(distance_km, 2) || ' km', 
        ', '
    ) AS nearest_neighbors
FROM scheme_distances
GROUP BY scheme1, status1
ORDER BY min_distance
LIMIT 20
"""

# Status-based Proximity Analysis
status_proximity_query = """
WITH status_distances AS (
    SELECT 
        h1.status AS status1,
        h2.status AS status2,
        ST_Distance(
            ST_Point(h1.longitude, h1.latitude), 
            ST_Point(h2.longitude, h2.latitude)
        ) / 1000.0 AS distance_km
    FROM hydropower_schemes h1
    CROSS JOIN hydropower_schemes h2
    WHERE h1.status != h2.status
)

SELECT 
    status1,
    status2,
    ROUND(MIN(distance_km), 2) AS min_distance,
    ROUND(AVG(distance_km), 2) AS avg_distance,
    ROUND(MAX(distance_km), 2) AS max_distance,
    COUNT(*) AS total_comparisons,
    SUM(CASE WHEN distance_km <= 50 THEN 1 ELSE 0 END) AS schemes_within_50km
FROM status_distances
GROUP BY status1, status2
ORDER BY status1, status2
"""

# Execute and display results
print("Proximity Analysis for Individual Schemes:")
"Proximity Analysis for Individual Schemes:"
proximity_results = con.execute(proximity_query).fetchdf()
print(proximity_results)
proximity_results

print("\n\nStatus-based Proximity Analysis:")
"\n\nStatus-based Proximity Analysis:"
status_proximity_results = con.execute(status_proximity_query).fetchdf()
print(status_proximity_results)
status_proximity_results

# Close the connection
con.close()
