import streamlit as st
import pandas as pd
import numpy as np

st.header("MALAWI HYDROPOWER SCHEMES")

map_data = pd.DataFrame(
    np.random.randn(1000,2)/[50,50] + [-13.5, 34],
    columns=['lat','lon']
)
st.map(map_data)