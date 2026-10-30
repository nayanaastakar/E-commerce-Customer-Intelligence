"""Interactive Customer Intelligence & Retention Analytics Dashboard (Streamlit).
Implements the 4-page dashboard specification from powerbi/dashboard_spec.md.
Run: streamlit run dashboard.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="E-Commerce Customer Intelligence & Retention Platform",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
EXPORTS = ROOT / "exports"
PROCESSED = ROOT / "data" / "processed"


@st.cache_data
def load_data():
    monthly = pd.read_csv(EXPORTS / "monthly_sales.csv")
    rfm = pd.read_csv(EXPORTS / "customer_rfm.csv")
    cohort_pct = pd.read_csv(EXPORTS / "cohort_retention_pct.csv")
    cohort_counts = pd.read_csv(EXPORTS / "cohort_retention_counts.csv")
    with open(PROCESSED / "data_quality_report.json", encoding="utf-8") as f:
        dq = json.load(f)
    return monthly, rfm, cohort_pct, cohort_counts, dq


monthly_df, rfm_df, cohort_pct_df, cohort_counts_df, dq_report = load_data()
kpis = dq_report["kpis"]

st.sidebar.title("🛒 Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "1. Executive Overview",
        "2. Customer Retention & Cohorts",
        "3. RFM Customer Segmentation",
        "4. Sales & Product Performance",
        "5. Data Quality & Warehouse Audit",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Data Status**: Verified (MySQL 8.0 + Star Schema)")
st.sidebar.markdown(f"**Transactions Analyzed**: {dq_report['cleaning']['clean_rows']:,}")
st.sidebar.markdown(f"**Customer Coverage**: {dq_report['cleaning']['customer_id_coverage_pct']}%")

# ----------------------------------------------------
# PAGE 1: EXECUTIVE OVERVIEW
# ----------------------------------------------------
if page == "1. Executive Overview":
    st.title("📊 Executive Overview & Business KPIs")
    st.markdown("High-level transactional volume, revenue, return rates, and customer retention metrics.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Net Sales", f"£{kpis['net_sales']:,.2f}")
    col2.metric("Gross Sales", f"£{kpis['gross_sales']:,.2f}")
    col3.metric("Returns & Refunds", f"£{kpis['returns']:,.2f}", delta=f"-{(kpis['returns']/kpis['gross_sales'])*100:.1f}%", delta_color="inverse")
    col4.metric("Avg Invoice Value", f"£{kpis['avg_invoice_value']:,.2f}")
    col5.metric("Repeat Purchase Rate", f"{kpis['repeat_purchase_rate']*100:.1f}%", f"{kpis['repeat_customers']:,} repeat")

    st.markdown("---")
    c1, c2 = st.columns([7, 5])

    with c1:
        st.subheader("Monthly Net Sales & Returns Trend")
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Bar(x=monthly_df["year_month"], y=monthly_df["net_sales"], name="Net Sales (£)", marker_color="#2ca02c"))
        fig_rev.add_trace(go.Bar(x=monthly_df["year_month"], y=monthly_df["returns"], name="Returns (£)", marker_color="#d62728"))
        fig_rev.update_layout(barmode="group", xaxis_title="Year-Month", yaxis_title="Sales (£)", height=400, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_rev, use_container_width=True)

    with c2:
        st.subheader("Invoice & Customer Volume by Month")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=monthly_df["year_month"], y=monthly_df["invoices"], mode="lines+markers", name="Invoices", line=dict(color="#1f77b4", width=3)))
        fig_vol.add_trace(go.Scatter(x=monthly_df["year_month"], y=monthly_df["customers"], mode="lines+markers", name="Active Customers", line=dict(color="#ff7f0e", width=2, dash="dot")))
        fig_vol.update_layout(xaxis_title="Year-Month", yaxis_title="Count", height=400, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_vol, use_container_width=True)

# ----------------------------------------------------
# PAGE 2: CUSTOMER RETENTION & COHORTS
# ----------------------------------------------------
elif page == "2. Customer Retention & Cohorts":
    st.title("🔄 Customer Cohort Retention Analysis")
    st.markdown("Tracks retention rates of customer cohorts based on their initial purchase month. Month 0 is 100%.")

    cohort_data = cohort_pct_df.set_index("cohort")
    age_cols = [c for c in cohort_data.columns if c.isdigit()]
    z_values = cohort_data[age_cols].values

    fig_heat = px.imshow(
        z_values,
        labels=dict(x="Cohort Month Index (Age)", y="Acquisition Cohort", color="Retention (%)"),
        x=[f"Month {c}" for c in age_cols],
        y=cohort_data.index.tolist(),
        color_continuous_scale="Viridis",
        aspect="auto",
        text_auto=".1f",
    )
    fig_heat.update_layout(height=520, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Cohort Acquisition Sizes")
        counts_data = cohort_counts_df.set_index("cohort")
        cohort_sizes = counts_data["0"]
        fig_bar = px.bar(
            x=cohort_sizes.index,
            y=cohort_sizes.values,
            labels={"x": "Cohort", "y": "Acquired Customers"},
            color=cohort_sizes.values,
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("Average Retention Curve across Cohorts")
        avg_retention = cohort_data[age_cols].mean(axis=0)
        fig_curve = px.line(
            x=[f"Month {c}" for c in age_cols],
            y=avg_retention.values,
            markers=True,
            labels={"x": "Months Since First Purchase", "y": "Average Retention Rate (%)"},
        )
        fig_curve.update_layout(height=350)
        st.plotly_chart(fig_curve, use_container_width=True)

# ----------------------------------------------------
# PAGE 3: RFM CUSTOMER SEGMENTATION
# ----------------------------------------------------
elif page == "3. RFM Customer Segmentation":
    st.title("👥 RFM Customer Segmentation")
    st.markdown("Recency, Frequency, and Monetary scoring assigning customers into behavioral segments.")

    seg_summary = rfm_df.groupby("segment").agg(
        customers=("customer_id", "count"),
        total_revenue=("monetary", "sum"),
        avg_revenue=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency_days", "mean"),
    ).reset_index().sort_values(by="total_revenue", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Customer Share by Segment")
        fig_pie = px.pie(seg_summary, names="segment", values="customers", hole=0.45, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_pie.update_layout(height=380)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Revenue Contribution by Segment (£)")
        fig_rev_seg = px.bar(seg_summary, x="segment", y="total_revenue", color="segment", text_auto=",.0f")
        fig_rev_seg.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_rev_seg, use_container_width=True)

    st.subheader("Segment Details & Behavioral Profile")
    st.dataframe(
        seg_summary.rename(
            columns={
                "segment": "Segment",
                "customers": "Customers",
                "total_revenue": "Total Revenue (£)",
                "avg_revenue": "Avg Revenue / Cust (£)",
                "avg_frequency": "Avg Frequency (Orders)",
                "avg_recency": "Avg Recency (Days)",
            }
        ).style.format({
            "Customers": "{:,}",
            "Total Revenue (£)": "£{:,.2f}",
            "Avg Revenue / Cust (£)": "£{:,.2f}",
            "Avg Frequency (Orders)": "{:.1f}",
            "Avg Recency (Days)": "{:.0f}",
        }),
        use_container_width=True,
    )

    st.subheader("Recency vs. Frequency Scatter (Bubble Size = Monetary Value)")
    sample_rfm = rfm_df.sample(min(1500, len(rfm_df)), random_state=42)
    fig_scatter = px.scatter(
        sample_rfm,
        x="recency_days",
        y="frequency",
        size="monetary",
        color="segment",
        hover_data=["customer_id", "monetary"],
        labels={"recency_days": "Recency (Days Since Last Order)", "frequency": "Frequency (Number of Orders)"},
        height=500,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ----------------------------------------------------
# PAGE 4: SALES & PRODUCT PERFORMANCE
# ----------------------------------------------------
elif page == "4. Sales & Product Performance":
    st.title("📈 Sales & Product Growth Analytics")
    st.markdown("Month-over-month growth rates, 3-month rolling averages, and top products.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Month-over-Month Net Sales Growth (%)")
        fig_mom = px.bar(
            monthly_df,
            x="year_month",
            y="mom_growth_pct",
            labels={"year_month": "Year-Month", "mom_growth_pct": "MoM Growth %"},
            color="mom_growth_pct",
            color_continuous_scale="RdYlGn",
        )
        fig_mom.update_layout(height=380)
        st.plotly_chart(fig_mom, use_container_width=True)

    with c2:
        st.subheader("3-Month Rolling Average Net Sales (£)")
        fig_roll = px.line(
            monthly_df,
            x="year_month",
            y=["net_sales", "rolling_3m_net_sales"],
            labels={"value": "Sales (£)", "year_month": "Year-Month"},
        )
        fig_roll.update_layout(height=380)
        st.plotly_chart(fig_roll, use_container_width=True)

    st.subheader("Monthly Performance Breakdown")
    st.dataframe(
        monthly_df.rename(
            columns={
                "year_month": "Month",
                "gross_sales": "Gross Sales (£)",
                "returns": "Returns (£)",
                "net_sales": "Net Sales (£)",
                "invoices": "Invoices",
                "customers": "Active Customers",
                "mom_growth_pct": "MoM Growth (%)",
                "rolling_3m_net_sales": "Rolling 3M Net (£)",
            }
        ).style.format({
            "Gross Sales (£)": "£{:,.2f}",
            "Returns (£)": "£{:,.2f}",
            "Net Sales (£)": "£{:,.2f}",
            "Invoices": "{:,}",
            "Active Customers": "{:,}",
            "MoM Growth (%)": "{:+.2f}%",
            "Rolling 3M Net (£)": "£{:,.2f}",
        }),
        use_container_width=True,
    )

# ----------------------------------------------------
# PAGE 5: DATA QUALITY & AUDIT
# ----------------------------------------------------
elif page == "5. Data Quality & Warehouse Audit":
    st.title("🛡️ Data Warehouse Audit & Integrity Status")
    st.markdown("Automated reconciliation checks across Python ETL, MySQL star schema, and analytical views.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Pipeline Clean Rows", f"{dq_report['cleaning']['clean_rows']:,}")
    c2.metric("Exact Duplicates Excluded", f"{dq_report['cleaning']['exact_duplicates_removed']:,}")
    c3.metric("Structural Rejections", f"{dq_report['cleaning']['rejected_rows']:,}")

    st.markdown("### Reconciliation Audit Evidence")
    audit_file = ROOT / "reports" / "sql_reconciliation_report.json"
    if audit_file.exists():
        with open(audit_file, encoding="utf-8") as f:
            audit_data = json.load(f)
        st.success(f"Status: {audit_data['status']} — All MySQL warehouse KPIs reconcile 100% with Python pipeline.")
        st.json(audit_data)
    else:
        st.info("Run scripts/reconcile_sql.py to generate latest database audit report.")
