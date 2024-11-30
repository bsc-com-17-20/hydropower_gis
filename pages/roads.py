import duckdb
import geopandas as gpd
import json
import folium

# Connect to DuckDB
con = duckdb.connect()

# Load GeoJSON into a GeoDataFrame
gdf = gpd.read_file("hotosm_mwi_roads_lines_geojson.geojson")

# Alternatively, if you want to extract specific columns:
con.sql(
    """
CREATE TABLE roads AS 
SELECT 
    properties->>'osm_id' AS osm_id,
    properties->>'highway' AS highway,
    properties->>'surface' AS surface,
    ST_LineString(geometry) AS geom
FROM gdf
"""
)

places = con.execute("SELECT * roads").fetchall()

# Create a Folium map centered around Malawi
m = folium.Map(location=[-13.5, 34], zoom_start=6)

# Query the roads from DuckDB
roads_query = """
SELECT osm_id, highway, ST_AsText(geom) AS geom_text FROM roads;
"""
roads_df = con.sql(roads_query).df()

# Add each road as a PolyLine on the map
for _, row in roads_df.iterrows():
    # Convert WKT to coordinates for Folium
    coords = row["geom_text"].replace("LINESTRING(", "").replace(")", "").split(",")
    coords = [
        (float(coord.split()[1]), float(coord.split()[0])) for coord in coords
    ]  # Convert to (lat, lon)

    folium.PolyLine(locations=coords, color="blue", weight=2).add_to(m)

# Save the map to an HTML file
map_path = "malawi_roads_map.html"
m.save(map_path)

print(f"Map successfully created at {map_path}")

# Close DuckDB connection
con.close()
