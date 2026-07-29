"""
app.py
------
Business Income & Spending Dashboard (Streamlit)

Flow:
  1. Sidebar: choose data source, year, department filter.
  2. Main: KPI cards + Yearly trend chart + Month-wise chart for the selected year.
  3. Select a month -> Department-wise Income/Spending breakdown for that month.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from modules.data_loader import load_data
from modules.aggregations import (
    yearly_summary,
    monthly_summary,
    department_summary,
    kpi_totals,
    MONTH_ORDER,
)
from modules.charts import (
    yearly_trend_chart,
    monthly_chart,
    department_chart,
    department_spending_share_pie,
)

CURRENCY = "₹"  # change to "$" or any symbol you prefer

st.set_page_config(page_title="Business Dashboard", page_icon="📊", layout="wide")

st.title("📊 Business Income & Spending Dashboard")

# ---------------------------------------------------------------------
# Sidebar — data source & filters
# ---------------------------------------------------------------------
st.sidebar.header("Data & Filters")

uploaded_file = st.sidebar.file_uploader(
    "Upload your transactions file (CSV/Excel)", type=["csv", "xlsx", "xls"]
)

data_source = uploaded_file if uploaded_file is not None else "data/transactions.csv"

try:
    df = load_data(data_source)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

if df.empty:
    st.warning("No data found.")
    st.stop()

available_years = sorted(df["year"].unique())
selected_year = st.sidebar.selectbox(
    "Select Year", available_years, index=len(available_years) - 1
)

available_departments = sorted(df["department"].unique())
selected_departments = st.sidebar.multiselect(
    "Filter Departments (optional)", available_departments, default=available_departments
)

df_filtered = df[df["department"].isin(selected_departments)]

# ---------------------------------------------------------------------
# KPI cards for the selected year
# ---------------------------------------------------------------------
kpis = kpi_totals(df_filtered, selected_year)

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"{CURRENCY}{kpis['income']:,.0f}")
col2.metric("Total Spending", f"{CURRENCY}{kpis['spending']:,.0f}")
col3.metric(
    "Net Profit / Loss",
    f"{CURRENCY}{kpis['net']:,.0f}",
    delta=f"{'Profit' if kpis['net'] >= 0 else 'Loss'}",
)

st.divider()

# ---------------------------------------------------------------------
# Yearly trend (always visible, independent of month selection)
# ---------------------------------------------------------------------
yearly_df = yearly_summary(df_filtered)
st.plotly_chart(yearly_trend_chart(yearly_df), use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# Month-wise chart for the selected year
# ---------------------------------------------------------------------
monthly_df = monthly_summary(df_filtered, selected_year)
st.plotly_chart(monthly_chart(monthly_df, selected_year), use_container_width=True)

# ---------------------------------------------------------------------
# Month selector -> Department-wise drill-down
# ---------------------------------------------------------------------
st.subheader("🔍 Drill Down: Department-wise Details")

selected_month_name = st.selectbox("Select a Month", MONTH_ORDER)
selected_month_num = MONTH_ORDER.index(selected_month_name) + 1

dept_df = department_summary(df_filtered, selected_year, selected_month_num)

if dept_df.empty:
    st.info(f"No transactions found for {selected_month_name} {selected_year}.")
else:
    chart_col, pie_col = st.columns([2, 1])
    with chart_col:
        st.plotly_chart(
            department_chart(dept_df, selected_year, selected_month_name),
            use_container_width=True,
        )
    with pie_col:
        st.plotly_chart(
            department_spending_share_pie(dept_df, selected_year, selected_month_name),
            use_container_width=True,
        )

    st.markdown(f"**Department Details — {selected_month_name} {selected_year}**")
    display_df = dept_df.copy()
    for col in ["Income", "Spending", "Net"]:
        display_df[col] = display_df[col].map(lambda x: f"{CURRENCY}{x:,.0f}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_bytes = dept_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download this month's department data (CSV)",
        data=csv_bytes,
        file_name=f"department_summary_{selected_year}_{selected_month_num:02d}.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Tip: Upload your own transactions file from the sidebar. "
    "Required columns: date, department, type (Income/Spending), amount."
)
