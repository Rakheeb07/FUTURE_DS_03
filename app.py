import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="Funnel Dashboard", layout="wide")

# -------------------------
# LOAD DATA
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv", sep="\t")
    df.columns = df.columns.str.strip().str.lower()

    df['event_time'] = df['event_time'].astype(str).str.replace(" UTC", "")
    df['event_time'] = pd.to_datetime(df['event_time'], errors='coerce')

    df['category_code'] = df['category_code'].fillna("unknown")
    df['brand'] = df['brand'].fillna("unknown")

    return df

df = load_data()

# -------------------------
# SIDEBAR FILTERS
# -------------------------
st.sidebar.title("Filters")

brand_filter = st.sidebar.multiselect(
    "Brand", df['brand'].unique(), default=df['brand'].unique()[:5]
)

category_filter = st.sidebar.multiselect(
    "Category", df['category_code'].unique(), default=df['category_code'].unique()[:5]
)

df = df[
    (df['brand'].isin(brand_filter)) &
    (df['category_code'].isin(category_filter))
]

# -------------------------
# FUNNEL STAGE
# -------------------------
stage_map = {
    "view": "Visitor",
    "cart": "Cart",
    "purchase": "Customer"
}
df['funnel_stage'] = df['event_type'].map(stage_map).fillna("Other")

# -------------------------
# KPI CALCULATIONS
# -------------------------
total_visitors  = df[df['event_type']=='view']['user_session'].nunique()
total_cart      = df[df['event_type']=='cart']['user_session'].nunique()
total_customers = df[df['event_type']=='purchase']['user_session'].nunique()

conversion_rate = (total_customers / total_visitors * 100) if total_visitors else 0

# -------------------------
# TITLE
# -------------------------
st.title("Marketing Funnel & Conversion Performance Dashboard")

# -------------------------
# KPI SECTION
# -------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Visitors", total_visitors)
col2.metric("Cart Users", total_cart)
col3.metric("Customers", total_customers)
col4.metric("Conversion Rate (%)", f"{conversion_rate:.2f}")

st.markdown("---")

# =========================================================
# ✅ VISUAL 1 → FUNNEL (Drop-off)
# =========================================================
st.subheader("Where are users dropping off in the funnel?")

fig_funnel = go.Figure(go.Funnel(
    y=["Visitors", "Cart", "Customers"],
    x=[total_visitors, total_cart, total_customers],
    textinfo="value+percent initial"
))

st.plotly_chart(fig_funnel, use_container_width=True)

# =========================================================
# ✅ VISUAL 2 → QUALITY CHANNELS
# =========================================================
st.subheader("Which channels bring high-quality leads?")

brand_df = df[df['event_type']=='purchase'] \
    .groupby('brand')['user_session'].nunique() \
    .reset_index(name='customers') \
    .sort_values(by='customers', ascending=False)

fig_bar = px.bar(
    brand_df.head(10),
    x='brand',
    y='customers',
    color='customers',
    color_continuous_scale='Oranges'
)

st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# ✅ VISUAL 3 → IMPROVE CONVERSION
# =========================================================
st.subheader("How can conversion rates be improved?")

purchase_df = df[df['event_type']=='purchase']

fig_scatter = px.scatter(
    purchase_df,
    x='price',
    y='user_id',
    color='category_code',
    title="High price vs low conversion pattern"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# ✅ VISUAL 4 → STAGE OPTIMIZATION
# =========================================================
st.subheader("Which stages need optimization?")

stage_df = df.groupby(['category_code','funnel_stage']) \
    .size().reset_index(name='count')

fig_stack = px.bar(
    stage_df,
    x='category_code',
    y='count',
    color='funnel_stage',
    barmode='group'
)

st.plotly_chart(fig_stack, use_container_width=True)

# =========================================================
# ✅ VISUAL 5 → LEAD DISTRIBUTION (FIXED)
# =========================================================
st.subheader("Lead distribution across categories")

cart_df = df[df['event_type']=='cart']

if cart_df.empty:
    st.warning("No cart data available for selected filters")
else:
    donut_df = cart_df['category_code'].value_counts().reset_index()
    donut_df.columns = ['category_code','count']

    # Take top 8 categories only (important)
    donut_df = donut_df.head(8)

    fig_donut = px.pie(
        donut_df,
        names='category_code',
        values='count',
        hole=0.5
    )

    st.plotly_chart(fig_donut, use_container_width=True)
# -------------------------
# INSIGHTS
# -------------------------
st.markdown("### Key Insights")

st.markdown("""
• Significant drop-off occurs between Visitor and Cart stage  
• Certain brands generate higher conversions indicating better lead quality  
• Higher priced products show lower conversion rates  
• Some categories require optimization across funnel stages  
""")