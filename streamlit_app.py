import streamlit as st
import pandas as pd

from inventory_engine import InventoryOptimizer

st.set_page_config(
    page_title="Inventory Optimizer",
    layout="wide"
)

st.title("Inventory Optimization Dashboard")

uploaded_file = st.file_uploader(
    "Upload Inventory Excel",
    type=["xlsx"]
)

if uploaded_file:

    optimizer = InventoryOptimizer()

    result_df, summary = optimizer.optimize(
        uploaded_file
    )

    st.subheader("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total SKUs",
        summary["Total_SKUs"]
    )

    col2.metric(
        "Critical",
        summary["Critical_SKUs"]
    )

    col3.metric(
        "Reorder",
        summary["Reorder_SKUs"]
    )

    col4.metric(
        "Inventory Value",
        f"₹{summary['Total_Inventory_Value']:,.0f}"
    )

    st.subheader("Recommendations")

    st.dataframe(
        result_df,
        use_container_width=True
    )

    excel = result_df.to_csv(
        index=False
    ).encode()

    st.download_button(
        "Download Results",
        excel,
        "inventory_recommendations.csv",
        "text/csv"
    )