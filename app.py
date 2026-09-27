from pathlib import Path
import pandas as pd
import streamlit as st
from analytics import load_transactions, summarize

st.set_page_config(page_title="Spending Insights", layout="wide")
st.title("Spending Insights")
st.caption("Explore transactions locally. The included demo data is synthetic.")
with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload transaction CSV", type="csv")
    st.caption("Columns: date, description, amount; optional category. Positive = income, negative = expense.")
    st.download_button("Download sample CSV", Path(__file__).parent.joinpath("data/sample_transactions.csv").read_bytes(),
                       file_name="sample_transactions.csv", mime="text/csv")
try:
    source = uploaded if uploaded is not None else Path(__file__).parent / "data/sample_transactions.csv"
    data, discarded = load_transactions(source)
except (ValueError, pd.errors.ParserError, UnicodeError, OSError) as exc:
    st.error(f"Could not load CSV: {exc}")
    st.stop()
if discarded:
    st.warning(f"Skipped {discarded} rows with missing or invalid date, description, or amount.")
if data.empty:
    st.info("No valid transactions to analyze.")
    st.stop()
months = sorted(data.month.unique())
selected = st.sidebar.multiselect("Months", months, default=months)
categories = sorted(data.category.unique())
chosen = st.sidebar.multiselect("Categories", categories, default=categories)
filtered = data[data.month.isin(selected) & data.category.isin(chosen)]
if filtered.empty:
    st.info("No transactions match these filters.")
    st.stop()
results = summarize(filtered)
a, b, c = st.columns(3)
a.metric("Income", f"${results['income']:,.2f}")
b.metric("Spending", f"${results['spending']:,.2f}")
c.metric("Net", f"${results['net']:,.2f}")
left, right = st.columns(2)
with left:
    st.subheader("Spending by category")
    st.bar_chart(results["categories"].set_index("category")["spend"])
with right:
    st.subheader("Monthly cash flow")
    st.line_chart(results["monthly"].set_index("month")[["income", "spending", "net"]])
st.subheader("Transactions")
st.dataframe(filtered.drop(columns="month"), use_container_width=True, hide_index=True)
st.download_button("Export filtered transactions", filtered.drop(columns="month").to_csv(index=False),
                   file_name="filtered_transactions.csv", mime="text/csv")
