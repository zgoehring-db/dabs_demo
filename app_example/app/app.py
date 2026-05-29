"""Minimal Streamlit hello-world for the Databricks Apps half of the DABs demo.

Shows:
- the workspace user the app is running as (Databricks injects identity
  headers — we surface one to make the demo feel real)
- a tiny sample dataframe

Anything more elaborate would distract from the bundle/deploy story.
"""

import os

import pandas as pd
import streamlit as st

st.set_page_config(page_title="DABs demo — hello app", page_icon="👋")

st.title("Hello from Databricks Apps 👋")
st.write(
    "This app was deployed via a Databricks Asset Bundle. The bundle config "
    "lives one folder up in `databricks.yml`."
)

user = os.environ.get("DATABRICKS_APP_USERNAME") or os.environ.get("USER", "unknown")
st.metric("Running as", user)

st.subheader("Sample data")
st.dataframe(
    pd.DataFrame(
        {
            "fruit": ["apple", "banana", "cherry", "date"],
            "count": [12, 7, 19, 3],
        }
    ),
    use_container_width=True,
)

st.caption("Edit app/app.py and redeploy with `databricks bundle deploy`.")
