import folium
import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="Malawi Hydropower Map", layout="wide")

st.sidebar.title("Proximity filter")

st.header("MALAWI HYDROPOWER SCHEMES")
st.title("Malawi Hydropower Schemes Map")

# Load hydropower data
with open("hydro.json") as f:
    hydro_data = json.load(f)

# Create a Folium map
m = folium.Map(location=[-13.5, 34], zoom_start=6)

# Prepare data for DataFrame
data = []
for feature in hydro_data["features"]:
    coords = feature["geometry"]["coordinates"]
    properties = feature["properties"]
    folium.Marker(
        location=[coords[1], coords[0]],  # Note: coordinates are [longitude, latitude]
        popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
        icon=folium.Icon(color="blue"),
    ).add_to(m)
    data.append({
        "Scheme Name": properties['Scheme_Nam'],
        "Status": properties['Status'],
        "Latitude": coords[1],
        "Longitude": coords[0],
    })
# Convert data to DataFrame
df = pd.DataFrame(data)

# Render Folium map in Streamlit
st.components.v1.html(m._repr_html_(), height=600)

# Display DataFrame
st.subheader("Hydropower Scheme Coordinates")
st.dataframe(df)