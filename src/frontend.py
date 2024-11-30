from streamlit_folium import folium_static
import folium
import streamlit as st
import json
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Malawi Hydropower Map", layout="wide", page_icon=":water_wave:", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Improved Header Styling */
    .css-1aumxhk {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Sidebar Styling */
    .css-1ynqkn9 {
        background-color: #e6eaf4;
        border-radius: 10px;
        padding: 15px;
    }
    
    /* Title Styling */
    .css-1ukqq1l {
        color: #2c3e50;
        font-weight: bold;
    }
            
    /* Filter Elements */
    .stMultiSelect, .stTextInput {
        background-color: rgba(255,255,255,0.1);
        border-radius: 10px;
        color: white;
    }
    
    /* Download Button Styling */
    .stDownloadButton > button {
        background-color: #3498db;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background-color: #2980b9;
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* DataFrame Styling */
    .dataframe {
        background-color: #f8fafc;
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)


# Page Title with Gradient Effect
st.markdown("""
    <h1 style='text-align: center; 
               color: #2c3e50; 
               background: linear-gradient(to right, #3498db, #2ecc71);
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;
               padding: 10px;'>
    Malawi Hydropower Schemes
    </h1>
""", unsafe_allow_html=True)

st.markdown("## Explore Hydropower Locations Across Malawi", unsafe_allow_html=True)

# Load hydropower data
with open("hydro.json") as f:
    hydro_data = json.load(f)

# Prepare data for DataFrame
data = []
for feature in hydro_data["features"]:
    coords = feature["geometry"]["coordinates"]
    properties = feature["properties"]
    data.append({
        "Scheme Name": properties['Scheme_Nam'],
        "Status": properties['Status'],
        "Longitude": coords[0],
        "Latitude": coords[1],
    })
# Convert data to DataFrame
df = pd.DataFrame(data)

st.sidebar.title("🔍 Hydropower Scheme Filters")
status_filter = st.sidebar.multiselect(
    "filter by status", options = df["Status"].unique(),default = df["Status"].unique(), help= "select hydropower scheme status to display"
)
name_search = st.sidebar.text_input("Search by scheme name", placeholder="Enter scheme name ...")

# filter data base on user input

filtered_df = df[
    (df["Status"].isin(status_filter))&
    (df["Scheme Name"].str.contains(name_search,case = False, na = False))
]

st.sidebar.download_button(
     label=" 📥 Download Filtered Data",
     data = filtered_df.to_csv(index=False),
     file_name="filtered_hydropower_data.csv",
     mime = "text/csv",
    help="Download the current filtered dataset"
)

# Statistics Display
# List-style metrics in the sidebar
st.sidebar.metric("Total Schemes", len(df))
st.sidebar.metric("Filtered Schemes", len(filtered_df))
st.sidebar.metric("Unique Statuses", df["Status"].nunique())

m = folium.Map(location=[-13.5, 34], zoom_start=6,  tiles="CartoDB positron" )

status_colors = { 'Operational': 'green','Under Construction': 'orange', 'Planned': 'blue','Decommissioned': 'red'
}
for _, row in filtered_df.iterrows():
     status = row['Status']
     color = status_colors.get(status, 'gray')

     folium.Marker(
        location=[row['Latitude'], row['Longitude']],  
        popup=f"Scheme Name: {properties['Scheme_Nam']}<br>Status: {properties['Status']}",
        icon=folium.Icon(color="color"),
    ).add_to(m)
      
folium_static = m.save("map.html")
# Render Folium map in Streamlit
st.components.v1.html(m._repr_html_(), height=600)

# Display DataFrame
st.subheader("📍Hydropower Scheme Coordinates")
st.dataframe(filtered_df, use_container_width=True, hide_index=True,)







# Create a new DataFrame with the count of each status
status_counts = filtered_df['Status'].value_counts().reset_index()
status_counts.columns = ['Status', 'Count']

# Create a pie chart
fig_pie = px.pie(status_counts, names='Status', values='Count')
fig_pie.update_layout(title='Distribution of Scheme Statuses')

# Convert the list to a DataFrame
data_df = pd.DataFrame(data)

# Rename the columns
data_df.columns = ['Scheme Name', 'Status', 'Existing', 'Proposed']

# Melt the DataFrame
data_melted = pd.melt(data_df, id_vars=['Scheme Name', 'Status'], value_vars=['Existing', 'Proposed'])

# Create a bar chart with two categories
fig_bar = px.bar(data_melted, x='Scheme Name', y='value', color='variable', barmode='group')
fig_bar.update_layout(title='Existing vs Proposed Values', xaxis_title='Scheme Name', yaxis_title='Value')

# Create a line chart
fig_line = px.line(data_melted, x='Scheme Name', y='value', color='variable')
fig_line.update_layout(title='Trend of Existing and Proposed Values', xaxis_title='Scheme Name', yaxis_title='Value')

# Display the charts
st.subheader("Scheme Status Distribution")
st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Existing vs Proposed Values")
col1, col2 = st.columns(2)
col1.plotly_chart(fig_bar, use_container_width=True)
col2.plotly_chart(fig_line, use_container_width=True)