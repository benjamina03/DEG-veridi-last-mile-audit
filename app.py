"""Veridi Logistics: Last Mile Delivery Auditor (Streamlit dashboard).

Reads the slim CSVs written by the notebook into ./dashboard_data (relative path),
so the raw Olist files never need to be in the repo.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Last Mile Delivery Auditor", page_icon="📦", layout="wide")

DATA_DIR = Path(__file__).parent / "dashboard_data"

# colours (validated categorical slots: blue, orange, violet)
BLUE, ORANGE, VIOLET = "#2a78d6", "#eb6834", "#6250d6"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
CLASS_ORDER = ["On Time", "Late", "Super Late"]
CLASS_COLORS = {"On Time": BLUE, "Late": ORANGE, "Super Late": VIOLET}


# ---------------------------------------------------------------- data
@st.cache_data
def load_data():
    orders = pd.read_csv(
        DATA_DIR / "orders_slim.csv",
        parse_dates=["purchase_date", "delivered_date", "estimated_date"],
    )
    orders["is_late"] = orders["is_late"].astype(bool)
    orders["is_super_late"] = orders["is_super_late"].astype(bool)
    distance = pd.read_csv(DATA_DIR / "state_summary.csv")[["customer_state", "distance_from_sp_km"]]
    categories = pd.read_csv(DATA_DIR / "category_summary.csv")
    return orders, distance, categories


def style(fig, height=420, legend=False):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=100 if legend else 60, b=10),
        font=dict(color=INK),
        title=dict(y=0.98, yanchor="top"),
        title_font=dict(size=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def state_stats(df, distance):
    out = (
        df.groupby("customer_state")
        .agg(
            orders=("order_id", "count"),
            late_orders=("is_late", "sum"),
            super_late_orders=("is_super_late", "sum"),
            avg_review=("review_score", "mean"),
            median_promised_days=("promised_days", "median"),
            median_actual_days=("actual_days", "median"),
        )
        .reset_index()
    )
    out["late_pct"] = out["late_orders"] / out["orders"] * 100
    out["super_late_pct"] = out["super_late_orders"] / out["orders"] * 100
    out["padding_days"] = out["median_promised_days"] - out["median_actual_days"]
    region_map = df.drop_duplicates("customer_state").set_index("customer_state")["region"]
    out["region"] = out["customer_state"].map(region_map)
    return out.merge(distance, on="customer_state", how="left")


orders, distance, categories = load_data()
overall_late_pct = orders["is_late"].mean() * 100  # all data, used by the category tab

# ---------------------------------------------------------------- sidebar filters
st.sidebar.header("Filters")

regions_all = sorted(orders["region"].dropna().unique())
sel_regions = st.sidebar.multiselect("Region", regions_all, default=regions_all)

states_all = sorted(orders.loc[orders["region"].isin(sel_regions), "customer_state"].unique())
sel_states = st.sidebar.multiselect("State", states_all, default=states_all)

dmin, dmax = orders["purchase_date"].min().date(), orders["purchase_date"].max().date()
date_range = st.sidebar.date_input("Purchase date", value=(dmin, dmax), min_value=dmin, max_value=dmax)
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Pick an end date to apply the date filter.")
    st.stop()

mask = (
    orders["customer_state"].isin(sel_states)
    & (orders["purchase_date"].dt.date >= date_range[0])
    & (orders["purchase_date"].dt.date <= date_range[1])
)
df = orders[mask]

st.sidebar.caption(
    "Only delivered orders with a known delivery date are included. "
    "Canceled, unavailable and in-transit orders were excluded in the notebook."
)

# ---------------------------------------------------------------- header + KPIs
st.title("📦 Last Mile Delivery Auditor")
st.caption("Veridi Logistics | Olist Brazilian e-commerce data | Are we failing specific regions, or is this nationwide?")

if df.empty:
    st.warning("No orders match the current filters.")
    st.stop()

late_pct = df["is_late"].mean() * 100
super_late_pct = df["is_super_late"].mean() * 100
avg_review = df["review_score"].mean()
median_diff = df["Days_Difference"].median()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Delivered orders", f"{len(df):,}")
k2.metric("Late (any)", f"{late_pct:.1f}%")
k3.metric("Super late (>5 days)", f"{super_late_pct:.1f}%")
k4.metric("Avg review score", f"{avg_review:.2f}")
k5.metric("Median days early", f"{median_diff:.0f}")

tab_est, tab_geo, tab_sent, tab_cat, tab_lead, tab_about = st.tabs(
    ["Estimates", "Where (states)", "Sentiment", "Categories", "Promised vs actual", "About"]
)

# ---------------------------------------------------------------- tab: estimates
with tab_est:
    st.subheader("Are the delivery estimates wrong?")
    st.write(
        "`Days_Difference` = estimated delivery date minus actual delivery date. "
        "Positive means the order arrived early, negative means late."
    )
    plot_diff = df["Days_Difference"].clip(-30, 60)
    fig = px.histogram(plot_diff, nbins=90, color_discrete_sequence=[BLUE])
    fig.update_traces(hovertemplate="Days_Difference %{x}<br>Orders %{y:,}<extra></extra>")
    fig.add_vline(x=0, line_dash="dash", line_color=ORANGE,
                  annotation_text="Estimated date", annotation_position="top right")
    fig.update_layout(showlegend=False, title="Estimated minus actual delivery date (clipped to -30 / +60 days)",
                      xaxis_title="Days (right of the line = early, left = late)", yaxis_title="Orders")
    st.plotly_chart(style(fig))

    share = (
        df["delivery_class"].value_counts(normalize=True).reindex(CLASS_ORDER).fillna(0) * 100
    ).reset_index()
    share.columns = ["Delivery class", "% of orders"]
    counts = df["delivery_class"].value_counts().reindex(CLASS_ORDER).fillna(0).astype(int).values
    share["Orders"] = counts
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(share.style.format({"% of orders": "{:.2f}", "Orders": "{:,}"}), hide_index=True)
    with c2:
        st.write(
            "**On Time** = delivered on or before the estimate. **Late** = 1-5 days after. "
            "**Super Late** = more than 5 days after."
        )

# ---------------------------------------------------------------- tab: states
with tab_geo:
    st.subheader("Late deliveries by customer state")
    ss = state_stats(df, distance)
    min_orders = st.slider("Hide states with fewer orders than", 0, 500, 0, step=10,
                           help="Small states have noisy percentages. Order counts are shown on hover and in the table.")
    ss_plot = ss[ss["orders"] >= min_orders].sort_values("late_pct")
    ss_plot = ss_plot.assign(
        vs_national=np.where(ss_plot["late_pct"] > late_pct, "Above filtered average", "At or below average")
    )
    fig = px.bar(
        ss_plot, x="late_pct", y="customer_state", orientation="h", color="vs_national",
        color_discrete_map={"Above filtered average": ORANGE, "At or below average": BLUE},
        category_orders={"customer_state": ss_plot["customer_state"].tolist()},
        custom_data=["orders", "super_late_pct", "avg_review"],
        text=ss_plot["late_pct"].map(lambda v: f"{v:.1f}%"),
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Late: %{x:.2f}%<br>Super late: %{customdata[1]:.2f}%"
                      "<br>Orders: %{customdata[0]:,}<br>Avg review: %{customdata[2]:.2f}<extra></extra>",
    )
    fig.add_vline(x=late_pct, line_dash="dash", line_color=INK, line_width=1)
    fig.update_layout(title=f"% of delivered orders that arrived late (dashed line = average, {late_pct:.1f}%)",
                      xaxis_title="% late", yaxis_title=None, legend_title_text=None)
    st.plotly_chart(style(fig, height=max(420, 22 * len(ss_plot) + 160), legend=True))

    st.subheader("By region and distance")
    reg = (
        df.groupby("region")
        .agg(orders=("order_id", "count"), late_pct=("is_late", lambda s: s.mean() * 100),
             super_late_pct=("is_super_late", lambda s: s.mean() * 100),
             avg_review=("review_score", "mean"))
        .sort_values("late_pct", ascending=False)
        .reset_index()
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        st.dataframe(
            reg.style.format({"orders": "{:,}", "late_pct": "{:.2f}", "super_late_pct": "{:.2f}", "avg_review": "{:.2f}"}),
            hide_index=True,
        )
        valid = ss.dropna(subset=["distance_from_sp_km"])
        if len(valid) >= 3:
            rho = valid["distance_from_sp_km"].rank().corr(valid["late_pct"].rank())
            st.caption(f"Spearman correlation between distance from Sao Paulo and late %: **{rho:.2f}** "
                       f"({len(valid)} states). Values near 0 mean distance alone does not explain the pattern.")
    with c2:
        fig = px.scatter(
            ss, x="distance_from_sp_km", y="late_pct", size="orders", text="customer_state",
            color_discrete_sequence=[BLUE], size_max=40,
            custom_data=["region", "orders"],
        )
        fig.update_traces(
            textposition="top center",
            hovertemplate="<b>%{text}</b> (%{customdata[0]})<br>Distance: %{x:,.0f} km<br>Late: %{y:.2f}%"
                          "<br>Orders: %{customdata[1]:,}<extra></extra>",
            marker=dict(line=dict(color="#fcfcfb", width=2), opacity=0.8),
        )
        fig.update_layout(title="Late % vs distance from Sao Paulo (bubble = orders)",
                          xaxis_title="Straight-line distance to state capital (km)", yaxis_title="% late",
                          showlegend=False)
        st.plotly_chart(style(fig, height=380))
    st.caption("Sao Paulo is used as the assumed distribution hub (largest seller base); this is an assumption, not in the data.")

    with st.expander("State table"):
        show = ss.sort_values("late_pct", ascending=False)[
            ["customer_state", "orders", "late_pct", "super_late_pct", "avg_review", "distance_from_sp_km"]
        ]
        st.dataframe(
            show.style.format({"orders": "{:,}", "late_pct": "{:.2f}", "super_late_pct": "{:.2f}",
                               "avg_review": "{:.2f}", "distance_from_sp_km": "{:,.0f}"}),
            hide_index=True,
        )

# ---------------------------------------------------------------- tab: sentiment
with tab_sent:
    st.subheader("Do late deliveries cause bad reviews?")
    rev = df.dropna(subset=["review_score"])
    cls = (
        rev.groupby("delivery_class")
        .agg(reviewed=("review_score", "size"), avg_review=("review_score", "mean"),
             pct_1_star=("review_score", lambda s: (s == 1).mean() * 100))
        .reindex(CLASS_ORDER)
        .reset_index()
    )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(cls, x="delivery_class", y="avg_review", color="delivery_class",
                     color_discrete_map=CLASS_COLORS, text=cls["avg_review"].map(lambda v: f"{v:.2f}"),
                     custom_data=["reviewed"])
        fig.update_traces(textposition="outside",
                          hovertemplate="%{x}<br>Avg review %{y:.2f}<br>Reviews %{customdata[0]:,}<extra></extra>")
        fig.update_layout(title="Average review score by delivery outcome", xaxis_title=None,
                          yaxis_title="Average score (1-5)", yaxis_range=[0, 5], showlegend=False)
        st.plotly_chart(style(fig, height=380))
    with c2:
        fig = px.bar(cls, x="delivery_class", y="pct_1_star", color="delivery_class",
                     color_discrete_map=CLASS_COLORS, text=cls["pct_1_star"].map(lambda v: f"{v:.1f}%"))
        fig.update_traces(textposition="outside",
                          hovertemplate="%{x}<br>1-star share %{y:.1f}%<extra></extra>")
        fig.update_layout(title="Share of reviews that are 1 star", xaxis_title=None,
                          yaxis_title="% of reviews", yaxis_range=[0, 100], showlegend=False)
        st.plotly_chart(style(fig, height=380))

    by_days = (
        rev.groupby("Days_Difference").agg(avg_review=("review_score", "mean"), n=("review_score", "size")).reset_index()
    )
    by_days = by_days[(by_days["n"] >= 30) & by_days["Days_Difference"].between(-30, 30)]
    fig = go.Figure(go.Scatter(
        x=by_days["Days_Difference"], y=by_days["avg_review"], mode="lines+markers",
        line=dict(color=BLUE, width=2), marker=dict(size=6, line=dict(color="#fcfcfb", width=1)),
        customdata=by_days["n"],
        hovertemplate="Days_Difference %{x}<br>Avg review %{y:.2f}<br>Reviews %{customdata:,}<extra></extra>",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color=ORANGE, annotation_text="Estimated date")
    fig.update_layout(title="Average review score vs delivery delay (days with 30+ reviews only)",
                      xaxis_title="Days_Difference (negative = days late, positive = days early)",
                      yaxis_title="Average review score", yaxis_range=[1, 5], showlegend=False)
    st.plotly_chart(style(fig, height=400))

    on_time = rev.loc[~rev["is_late"], "review_score"].mean()
    late = rev.loc[rev["is_late"], "review_score"].mean()
    m1, m2, m3 = st.columns(3)
    m1.metric("Avg review: on time", f"{on_time:.2f}")
    m2.metric("Avg review: late (Late + Super Late)", f"{late:.2f}" if not np.isnan(late) else "n/a")
    if not np.isnan(late):
        m3.metric("Gap", f"{on_time - late:.2f} points")

    one_star = rev[rev["review_score"] == 1]
    if len(one_star):
        st.caption(
            f"Late orders make up {rev['is_late'].mean() * 100:.1f}% of reviewed orders but "
            f"{one_star['is_late'].mean() * 100:.1f}% of all 1-star reviews in this selection. "
            "Lateness explains a large share of bad reviews, not all of them."
        )

# ---------------------------------------------------------------- tab: categories
with tab_cat:
    st.subheader("Product categories (English)")
    st.caption("Category figures use all delivered orders and ignore the sidebar filters. "
               "An order with items from two categories counts once in each.")
    c1, c2 = st.columns(2)
    min_cat = c1.slider("Minimum orders per category", 50, 2000, 200, step=50)
    top_n = c2.slider("Categories to show", 5, 30, 15)
    cat = categories[categories["orders"] >= min_cat].sort_values("late_pct", ascending=False).head(top_n)
    cat = cat.sort_values("late_pct")
    fig = px.bar(cat, x="late_pct", y="category_en", orientation="h", color_discrete_sequence=[BLUE],
                 custom_data=["orders", "avg_review"], text=cat["late_pct"].map(lambda v: f"{v:.1f}%"))
    fig.update_traces(textposition="outside",
                      hovertemplate="<b>%{y}</b><br>Late: %{x:.2f}%<br>Orders: %{customdata[0]:,}"
                                    "<br>Avg review: %{customdata[1]:.2f}<extra></extra>")
    fig.add_vline(x=overall_late_pct, line_dash="dash", line_color=ORANGE, line_width=1.5)
    fig.update_layout(title=f"Categories with the highest late rate (dashed line = all orders, {overall_late_pct:.1f}%)",
                      xaxis_title="% late", yaxis_title=None, showlegend=False)
    st.plotly_chart(style(fig, height=max(380, 26 * len(cat) + 120)))

    st.markdown("**Is furniture harder to ship than electronics?**")
    fe = categories[categories["category_en"].str.contains("furniture|electronics", case=False, regex=True)]
    st.dataframe(
        fe.sort_values("orders", ascending=False)[["category_en", "orders", "late_pct", "avg_days_diff", "avg_review"]]
        .style.format({"orders": "{:,}", "late_pct": "{:.2f}", "avg_days_diff": "{:.1f}", "avg_review": "{:.2f}"}),
        hide_index=True,
    )

# ---------------------------------------------------------------- tab: promised vs actual
with tab_lead:
    st.subheader("Candidate's choice: promised vs actual delivery time")
    st.write(
        "For each state, the median days we **promised** (estimate minus purchase date) next to the median days "
        "it **actually took** (delivery minus purchase date). A large gap means padded estimates; a small gap "
        "means little safety buffer, so late deliveries are more likely."
    )
    lead = state_stats(df, distance)
    sort_by = st.radio("Sort states by", ["Promised days", "Padding (promised - actual)", "Late %"], horizontal=True)
    key = {"Promised days": "median_promised_days", "Padding (promised - actual)": "padding_days", "Late %": "late_pct"}[sort_by]
    lead = lead.sort_values(key, ascending=False)

    fig = go.Figure()
    fig.add_bar(x=lead["customer_state"], y=lead["median_promised_days"], name="Median promised",
                marker_color=BLUE, customdata=lead[["orders", "late_pct"]],
                hovertemplate="<b>%{x}</b><br>Promised: %{y:.0f} days<br>Orders: %{customdata[0]:,}"
                              "<br>Late: %{customdata[1]:.2f}%<extra></extra>")
    fig.add_bar(x=lead["customer_state"], y=lead["median_actual_days"], name="Median actual",
                marker_color=ORANGE, customdata=lead[["orders", "late_pct"]],
                hovertemplate="<b>%{x}</b><br>Actual: %{y:.0f} days<br>Orders: %{customdata[0]:,}"
                              "<br>Late: %{customdata[1]:.2f}%<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08,
                      title="Promised vs actual delivery time by state", yaxis_title="Days from purchase",
                      xaxis_title=None)
    st.plotly_chart(style(fig, height=440, legend=True))

    st.dataframe(
        lead[["customer_state", "orders", "median_promised_days", "median_actual_days", "padding_days", "late_pct"]]
        .style.format({"orders": "{:,}", "median_promised_days": "{:.0f}", "median_actual_days": "{:.0f}",
                       "padding_days": "{:.0f}", "late_pct": "{:.2f}"}),
        hide_index=True,
    )
    st.caption("States with few orders (for example under 100) can show extreme percentages; check the order count.")

# ---------------------------------------------------------------- tab: about
with tab_about:
    st.subheader("Method and definitions")
    st.markdown(
        """
- **Data:** Olist Brazilian e-commerce dataset (orders, customers, reviews, order items, products, category translation).
- **Master table:** one row per order. Repeat reviews were reduced to the latest review per order before joining, so no order is duplicated.
- **Days_Difference:** estimated delivery date minus actual delivery date, compared as calendar dates.
- **Classes:** On Time (0 or more days early), Late (1-5 days late), Super Late (more than 5 days late).
- **Excluded:** orders that were never delivered or have no delivery date.
- **Reviews:** averages use only orders that were reviewed.
- **Distance:** straight-line distance from Sao Paulo to each state capital, used as a proxy for remoteness.
        """
    )
