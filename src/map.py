import folium
import json

def create_map():
# Load the geojson data
    with open("hydro.json") as f:
        hydro_data = json.load(f)

    # Create a Folium map centered around Malawi
    m = folium.Map(location=[-13.5, 34], zoom_start=6)

    # Add markers for each hydropower scheme
    for feature in hydro_data["features"]:
        coords = feature["geometry"]["coordinates"]
        properties = feature["properties"]
        folium.Marker(
            location=[coords[1], coords[0]],  # Note: coordinates are [longitude, latitude]
            popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
            icon=folium.Icon(color="blue"),
        ).add_to(m)

    # Save the map to an HTML file
    m.save("malawi_hydropower_schemes.html")

   
    print("Map successfully created!")
