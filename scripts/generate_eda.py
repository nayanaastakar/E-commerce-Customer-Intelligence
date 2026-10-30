"""Generate exploratory data analysis (EDA) charts from clean transactions and exports.
Saves publication-quality figures in reports/figures/.
"""
import logging
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

log = logging.getLogger("generate_eda")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
FIG_DIR = ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def plot_monthly_sales():
    df = pd.read_csv(EXPORTS / "monthly_sales.csv")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    x = range(len(df))
    ax1.bar(x, df["gross_sales"], label="Gross Sales", color="#2b5c8f", alpha=0.8, width=0.4, align="center")
    ax1.bar(x, df["net_sales"], label="Net Sales", color="#2ca02c", alpha=0.8, width=0.4, align="edge")
    ax1.bar(x, df["returns"], label="Returns", color="#d62728", alpha=0.7, width=-0.2, align="edge")
    
    ax1.set_xlabel("Year-Month", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Sales (£)", fontsize=11, fontweight="bold")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(df["year_month"], rotation=45, ha="right")
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(x, df["mom_growth_pct"], color="#ff7f0e", marker="o", linewidth=2, label="MoM Growth %")
    ax2.set_ylabel("MoM Growth (%)", fontsize=11, fontweight="bold", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")
    ax2.axhline(0, color="gray", linestyle=":", alpha=0.7)

    plt.title("Monthly Sales Trend & Month-over-Month Growth", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    out = FIG_DIR / "monthly_sales_trend.png"
    plt.savefig(out, dpi=300)
    plt.close()
    log.info("Saved %s", out)


def plot_rfm_segments():
    df = pd.read_csv(EXPORTS / "customer_rfm.csv")
    seg_counts = df["segment"].value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#2b5c8f", "#41b6c4", "#7fcdbb", "#c7e9b4", "#fec44f", "#fe9929", "#d95f0e"]
    bars = ax.barh(seg_counts.index, seg_counts.values, color=colors[:len(seg_counts)])
    
    for bar in bars:
        w = bar.get_width()
        pct = 100 * w / len(df)
        ax.text(w + 15, bar.get_y() + bar.get_height() / 2, f"{w:,} ({pct:.1f}%)",
                va="center", ha="left", fontsize=10, fontweight="bold")

    ax.set_xlabel("Number of Customers", fontsize=11, fontweight="bold")
    ax.set_title(f"Customer Distribution by RFM Segment (Total: {len(df):,})", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlim(0, max(seg_counts.values) * 1.2)
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    ax.invert_yaxis()

    plt.tight_layout()
    out = FIG_DIR / "rfm_segment_distribution.png"
    plt.savefig(out, dpi=300)
    plt.close()
    log.info("Saved %s", out)


def plot_cohort_retention():
    df = pd.read_csv(EXPORTS / "cohort_retention_pct.csv").set_index("cohort")
    # numeric age columns
    age_cols = [c for c in df.columns if c.isdigit()]
    matrix = df[age_cols].values

    fig, ax = plt.subplots(figsize=(14, 8))
    cmap = plt.cm.YlGnBu
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0, vmax=50)

    ax.set_xticks(range(len(age_cols)))
    ax.set_xticklabels([f"M+{c}" for c in age_cols], fontsize=10)
    ax.set_yticks(range(len(df.index)))
    ax.set_yticklabels(df.index, fontsize=10)

    for i in range(len(df.index)):
        for j in range(len(age_cols)):
            val = matrix[i, j]
            if not np.isnan(val):
                text_color = "white" if val > 25 else "black"
                ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color=text_color, fontsize=9, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Retention Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Customer Cohort Retention Heatmap (%)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Cohort Month Index (Age)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Cohort Acquisition Month", fontsize=11, fontweight="bold")

    plt.tight_layout()
    out = FIG_DIR / "cohort_retention_heatmap.png"
    plt.savefig(out, dpi=300)
    plt.close()
    log.info("Saved %s", out)


def generate_all():
    log.info("Generating EDA charts...")
    plot_monthly_sales()
    plot_rfm_segments()
    plot_cohort_retention()
    log.info("All EDA charts generated successfully in %s", FIG_DIR)


if __name__ == "__main__":
    generate_all()
