"""
NASSAU CANDY DISTRIBUTOR - INTERACTIVE STREAMLIT DASHBOARD
===========================================================
This is the main Streamlit application for the shipping route efficiency analysis.
 
Run with: streamlit run streamlit_dashboard.py
"""
 
from gettext import install

import plotly
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Nassau Candy - Route Efficiency Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    "<h1 style='text-align: center;'>Nassau Candy - Route Efficiency Dashboard</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h2 style='text-align: center;'>Nassau Candy Distributor</h2>",
    unsafe_allow_html=True
)

st.markdown(
    "<h3 style='text-align: center;'>Factory-to-Customer Shipping Route Efficiency Analysis</h3>",
    unsafe_allow_html=True
)

st.markdown("---")
# ============================================================================
# LOAD DATA (CACHED FOR PERFORMANCE)
# ============================================================================
@st.cache_data
def load_data():
    # Load the processed data (ensure this file exists from your data processing step)
    df = pd.read_csv('data/nassau_candy_distributor_cleaned.csv', parse_dates=['Order Date', 'Ship Date'])
    return df
data = load_data()

@st.cache_data
def load_metrics():
    """Load aggregated metrics"""
    route_metrics = pd.read_csv('metrics/mode_metrics.csv')
    regional_metrics = pd.read_csv('metrics/regional_metrics.csv')
    state_metrics = pd.read_csv('metrics/state_metrics.csv')
    mode_metrics = pd.read_csv('metrics/mode_metrics.csv')
    factory_metrics = pd.read_csv('metrics/factory_metrics.csv')

    with open('summary_stats.txt', 'r') as f:
        summary_stats = f.read()

    return route_metrics, regional_metrics, state_metrics, mode_metrics, factory_metrics
route_metrics, regional_metrics, state_metrics, mode_metrics, factory_metrics = load_metrics()


# Load all data
df = load_data()
route_metrics, regional_metrics, state_metrics, mode_metrics, factory_metrics = load_metrics()
# ============================================================================
# SIDEBAR - FILTERS
# ============================================================================
st.sidebar.title("Filters")
st.sidebar.markdown("---")
 
# Date Range Filter
date_min = df['Order Date'].min().date()
date_max = df['Order Date'].max().date()
 
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)
 
 # Convert to datetime for filtering
date_start = pd.to_datetime(date_range[0])
date_end = pd.to_datetime(date_range[1])
 
# Region Filter
regions = st.sidebar.multiselect(
    "Select Region(s)",
    options=sorted(df['Region'].unique()),
    default=sorted(df['Region'].unique()),
    help="Choose regions to analyze"
)
 
# State Filter
states = st.sidebar.multiselect(
    "Select State(s)",
    options=sorted(df['State/Province'].unique()),
    default=None,
    help="Leave empty for all states"
)
 
# Factory Filter
factories = st.sidebar.multiselect(
    "Select Factory(ies)",
    options=sorted(df['Factory'].dropna().unique()),
    default=sorted(df['Factory'].dropna().unique()),
    help="Choose factories"
)
 
# Ship Mode Filter
ship_modes = st.sidebar.multiselect(
    "Select Shipping Mode(s)",
    options=sorted(df['Ship Mode'].unique()),
    default=sorted(df['Ship Mode'].unique()),
    help="Choose shipping methods"
)
 
# Lead Time Threshold Slider
lead_time_threshold = st.sidebar.slider(
    "Lead Time Threshold (days)",
    min_value=int(df['Lead Time'].min()),
    max_value=int(df['Lead Time'].max()),
    value=int(df['Lead Time'].quantile(0.75)),
    help="Benchmark for on-time delivery"
)
 
st.sidebar.markdown("---")
 
# Apply all filters
filtered_df = df[
    (df['Order Date'] >= date_start) &
    (df['Order Date'] <= date_end) &
    (df['Region'].isin(regions)) &
    (df['Factory'].isin(factories)) &
    (df['Ship Mode'].isin(ship_modes))
]

# Apply state filter if selected
if states:
    filtered_df = filtered_df[filtered_df['State/Province'].isin(states)]
 
st.sidebar.info(f"Showing {len(filtered_df):,} orders out of {len(df):,} total")


# ============================================================================
# KPI CARDS
# ============================================================================
st.subheader("Key Performance Indicators (KPIs)")
 
col1, col2, col3, col4, col5 = st.columns(5)
 
with col1:
    avg_lead_time = filtered_df['Lead Time'].mean()
    st.metric(
        "Avg Lead Time",
        f"{avg_lead_time:.1f} days",
        help="Average shipping duration"
    )
 
with col2:
    total_orders = len(filtered_df)
    st.metric(
        "Total Orders",
        f"{total_orders:,}",
        help="Number of shipments"
    )
 
with col3:
    on_time = (filtered_df['Lead Time'] <= lead_time_threshold).sum()
    on_time_pct = (on_time / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric(
        "On-Time %",
        f"{on_time_pct:.1f}%",
        help=f"Orders ≤ {lead_time_threshold} days"
    )
 
with col4:
    total_revenue = filtered_df['Sales'].sum()
    st.metric(
        "Total Revenue",
        f"${total_revenue:,.0f}",
        help="Total sales value"
    )
 
with col5:
    routes_count = filtered_df['Route'].nunique()
    st.metric(
        "Routes Analyzed",
        f"{routes_count}",
        help="Unique routes"
    )
 
st.markdown("---")

# ============================================================================
# TAB STRUCTURE
# ============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Route Efficiency",
    "Geographic Map",
    "Ship Mode Analysis",
    "Route Drill-Down",
    "Advanced Analytics"
])


# ============================================================================
# TAB 1: ROUTE EFFICIENCY
# ============================================================================
with tab1:
    st.header("Route Efficiency Overview")
    
    col1, col2 = st.columns(2)
    
    # Top 10 Routes
    with col1:
        st.subheader("Top 10 Most Efficient Routes")
        
        # Get top routes from filtered data
        top_routes = filtered_df.groupby('Route').agg({
            'Lead Time': ['mean', 'std', 'count'],
            'Sales': 'sum'
        }).round(2)
        top_routes.columns = ['Avg Lead Time', 'Std Dev', 'Volume', 'Total Sales']
        top_routes = top_routes.sort_values('Avg Lead Time').head(10)
        
        # Calculate efficiency score
        min_lt = top_routes['Avg Lead Time'].min()
        max_lt = filtered_df.groupby('Route')['Lead Time'].mean().max()
        top_routes['Efficiency'] = 100 - ((top_routes['Avg Lead Time'] - min_lt) / (max_lt - min_lt) * 100)
        top_routes['Efficiency'] = top_routes['Efficiency'].round(1)
        
        st.dataframe(
            top_routes[['Avg Lead Time', 'Std Dev', 'Volume', 'Efficiency']],
            use_container_width=True,
            height=400
        )
    
    # Bottom 10 Routes
    with col2:
        st.subheader("Bottom 10 Least Efficient Routes")
        
        bottom_routes = filtered_df.groupby('Route').agg({
            'Lead Time': ['mean', 'std', 'count'],
            'Sales': 'sum'
        }).round(2)
        bottom_routes.columns = ['Avg Lead Time', 'Std Dev', 'Volume', 'Total Sales']
        bottom_routes = bottom_routes.sort_values('Avg Lead Time', ascending=False).head(10)
        
        # Calculate efficiency score
        min_lt = filtered_df.groupby('Route')['Lead Time'].mean().min()
        max_lt = bottom_routes['Avg Lead Time'].max()
        bottom_routes['Efficiency'] = 100 - ((bottom_routes['Avg Lead Time'] - min_lt) / (max_lt - min_lt) * 100)
        bottom_routes['Efficiency'] = bottom_routes['Efficiency'].round(1)
        
        st.dataframe(
            bottom_routes[['Avg Lead Time', 'Std Dev', 'Volume', 'Efficiency']],
            use_container_width=True,
            height=400
        )
    
    # Lead Time Distribution
    st.subheader("Lead Time Distribution")
    
    fig_dist = px.histogram(
        filtered_df,
        x='Lead Time',
        nbins=40,
        title="Distribution of Shipping Lead Times",
        labels={'Lead Time': 'Lead Time (days)', 'count': 'Number of Orders'},
        color_discrete_sequence=['#636EFA'],
        hover_data={'Lead Time': ':.1f'}
    )
    
    fig_dist.add_vline(
        x=filtered_df['Lead Time'].mean(),
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {filtered_df['Lead Time'].mean():.1f}",
        annotation_position="top right"
    )
    
    fig_dist.update_layout(showlegend=False, hovermode='x unified')
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Route Performance Chart
    st.subheader("Route Performance Rankings")
    
    route_perf = filtered_df.groupby('Route')['Lead Time'].agg(['mean', 'count']).reset_index()
    route_perf = route_perf[route_perf['count'] >= 3].sort_values('mean').head(15)  # Only routes with 3+ orders
    
    fig_route = px.bar(
        route_perf,
        x='mean',
        y='Route',
        orientation='h',
        title="Top 15 Routes by Average Lead Time",
        labels={'mean': 'Average Lead Time (days)', 'Route': 'Route'},
        color='mean',
        color_continuous_scale='RdYlGn_r',
        hover_data={'count': True, 'mean': ':.2f'}
    )
    
    fig_route.update_layout(yaxis={'categoryorder': 'total ascending'}, hovermode='y unified')
    st.plotly_chart(fig_route, use_container_width=True)

# ============================================================================
# TAB 2: GEOGRAPHIC MAP
# ============================================================================
# Bottleneck Analysis
with tab2:
    st.header("Geographic Shipping Analysis")

    col1, col2 = st.columns(2)

with col1:
    bottleneck = filtered_df.groupby('Region').agg({
        'Lead Time': 'mean',
        'Order ID': 'count'
    }).reset_index()
    bottleneck.columns = ['Region', 'Avg Lead Time', 'Volume']

    # Safe normalization — avoids 0/0 when all values are identical
    def safe_norm(series):
        rng = series.max() - series.min()
        return (series - series.min()) / rng if rng > 0 else pd.Series([0.5] * len(series), index=series.index)

    bottleneck['LT_norm']  = safe_norm(bottleneck['Avg Lead Time'])
    bottleneck['Vol_norm'] = safe_norm(bottleneck['Volume'])
    bottleneck['Bottleneck Score'] = (bottleneck['LT_norm'] * 0.6 + bottleneck['Vol_norm'] * 0.4) * 100

    # Drop any remaining NaNs so plotly never receives them in the size array
    bottleneck = bottleneck.dropna(subset=['Bottleneck Score']).sort_values('Bottleneck Score', ascending=False)

    # Guard: need at least one row to plot
    if bottleneck.empty:
        st.info("Not enough data to compute bottleneck scores.")
    else:
        fig_bottleneck = px.scatter(
            bottleneck,
            x='Avg Lead Time',
            y='Volume',
            size='Bottleneck Score',
            color='Bottleneck Score',
            hover_name='Region',
            color_continuous_scale='Reds',
            title="Regional Bottleneck Analysis",
            labels={'Avg Lead Time': 'Average Lead Time (days)', 'Volume': 'Order Volume'}
        )
        st.plotly_chart(fig_bottleneck, use_container_width=True)

with col2:
    st.subheader("Bottleneck Ranking")

    if not bottleneck.empty:
        display_cols = bottleneck[['Region', 'Avg Lead Time', 'Volume', 'Bottleneck Score']].copy()
        display_cols['Avg Lead Time']    = display_cols['Avg Lead Time'].round(2)
        display_cols['Bottleneck Score'] = display_cols['Bottleneck Score'].round(1)
        st.dataframe(display_cols, use_container_width=True, height=300)
    else:
        st.info("No bottleneck data available for the current filters.")

# ============================================================================
# TAB 3: SHIP MODE ANALYSIS
# ============================================================================
with tab3:
    st.header("Shipping Method Comparison")
    
    col1, col2 = st.columns(2)
    
    # Lead Time Comparison
    with col1:
        st.subheader("Average Lead Time by Method")
        
        mode_lead = filtered_df.groupby('Ship Mode')['Lead Time'].agg(['mean', 'median', 'std', 'count']).reset_index()
        mode_lead.columns = ['Ship Mode', 'Mean', 'Median', 'Std Dev', 'Count']
        
        fig_mode_lead = px.bar(
            mode_lead,
            x='Ship Mode',
            y='Mean',
            error_y='Std Dev',
            color='Mean',
            color_continuous_scale='Viridis',
            hover_data={'Mean': ':.2f', 'Median': ':.2f', 'Count': True},
            title="Lead Time by Shipping Method"
        )
        
        st.plotly_chart(fig_mode_lead, use_container_width=True)
    
    # Order Distribution
    with col2:
        st.subheader("Order Distribution by Method")
        
        mode_dist = filtered_df['Ship Mode'].value_counts().reset_index()
        mode_dist.columns = ['Ship Mode', 'Count']
        
        fig_mode_dist = px.pie(
            mode_dist,
            values='Count',
            names='Ship Mode',
            title="Percentage of Orders by Method",
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        st.plotly_chart(fig_mode_dist, use_container_width=True)
    
    # Detailed Comparison
    st.subheader("Detailed Shipping Method Metrics")
    
    mode_detailed = filtered_df.groupby('Ship Mode').agg({
        'Lead Time': ['mean', 'median', 'std', 'min', 'max', 'count'],
        'Sales': ['sum', 'mean'],
        'Cost': 'sum',
        'Gross Profit': 'sum'
    }).round(2)
    
    mode_detailed.columns = ['Avg LT', 'Median LT', 'Std Dev', 'Min LT', 'Max LT', 'Orders',
                            'Total Sales', 'Avg Sale', 'Total Cost', 'Total Profit']
    
    # Calculate on-time percentage
    for mode in mode_detailed.index:
        mode_data = filtered_df[filtered_df['Ship Mode'] == mode]
        on_time_pct = (mode_data['Lead Time'] <= lead_time_threshold).sum() / len(mode_data) * 100
        mode_detailed.loc[mode, 'On-Time %'] = round(on_time_pct, 1)
    
    st.dataframe(mode_detailed, use_container_width=True)
 
# ============================================================================
# TAB 4: ROUTE DRILL-DOWN
# ============================================================================
with tab4:
    st.header("Route Drill-Down Analysis")
    
    col1, col2 = st.columns(2)
    
    # State Selector
    with col1:
        selected_state = st.selectbox(
            "Select a State to Analyze",
            options=sorted(filtered_df['State/Province'].unique()),
            help="Choose a state to see detailed shipping information"
        )
    
    # Factory Selector
    with col2:
        selected_factory = st.selectbox(
            "Filter by Factory (Optional)",
            options=['All'] + sorted(filtered_df['Factory'].dropna().unique())
        )
    
    # Get data for selected state
    state_data = filtered_df[filtered_df['State/Province'] == selected_state]
    
    if selected_factory != 'All':
        state_data = state_data[state_data['Factory'] == selected_factory]
    
    # Metrics for selected state
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Orders",
            len(state_data),
            help=f"Orders to {selected_state}"
        )
    
    with col2:
        st.metric(
            "Avg Lead Time",
            f"{state_data['Lead Time'].mean():.1f} days",
            help="Average shipping duration"
        )
    
    with col3:
        on_time_state = (state_data['Lead Time'] <= lead_time_threshold).sum() / len(state_data) * 100 if len(state_data) > 0 else 0
        st.metric(
            "On-Time %",
            f"{on_time_state:.1f}%"
        )
    
    with col4:
        st.metric(
            "Total Revenue",
            f"${state_data['Sales'].sum():,.0f}"
        )
    
    st.markdown("---")
    
    # Route breakdown
    st.subheader(f"Routes to {selected_state}")
    
    route_breakdown = state_data.groupby('Route').agg({
        'Lead Time': ['mean', 'count'],
        'Sales': 'sum'
    }).round(2)
    route_breakdown.columns = ['Avg Lead Time', 'Orders', 'Total Sales']
    route_breakdown = route_breakdown.sort_values('Avg Lead Time')
    
    fig_route_breakdown = px.bar(
        route_breakdown.reset_index(),
        x='Route',
        y='Avg Lead Time',
        color='Avg Lead Time',
        color_continuous_scale='RdYlGn_r',
        hover_data={'Orders': True, 'Total Sales': ':.0f'},
        title=f"Routes to {selected_state}"
    )
    
    st.plotly_chart(fig_route_breakdown, use_container_width=True)
    
    # Orders table
    st.subheader(f"Recent Orders to {selected_state}")
    
    orders_display = state_data[[
        'Order ID', 'Order Date', 'Ship Date', 'Lead Time',
        'Factory', 'Ship Mode', 'Product Name', 'Sales'
    ]].copy()
    orders_display['Order Date'] = orders_display['Order Date'].dt.strftime('%Y-%m-%d')
    orders_display['Ship Date'] = orders_display['Ship Date'].dt.strftime('%Y-%m-%d')
    orders_display = orders_display.sort_values('Order Date', ascending=False).head(20)
    
    st.dataframe(orders_display, use_container_width=True, height=400)
 
# ============================================================================
# TAB 5: ADVANCED ANALYTICS
# ============================================================================
with tab5:
    st.header("Advanced Analytics")

    col1, col2 = st.columns(2)

    # Lead Time by Ship Mode and Region
    with col1:
        st.subheader("Heatmap: Lead Time by Ship Mode and Region")

        heatmap_data = filtered_df.pivot_table(
            values='Lead Time',
            index='Ship Mode',
            columns='Region',
            aggfunc='mean'
        )

        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Region", y="Ship Mode", color="Avg Lead Time (days)"),
            color_continuous_scale="RdYlGn_r",
            title="Average Lead Time: Shipping Method vs Region"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # Factory Performance
    with col2:
        st.subheader("Factory Performance")

        factory_perf = filtered_df.groupby('Factory').agg({
            'Lead Time': ['mean', 'std', 'count'],
            'Sales': 'sum'
        }).round(2)
        factory_perf.columns = ['Avg LT', 'Std Dev', 'Orders', 'Total Sales']
        factory_perf = factory_perf.sort_values('Avg LT')

        fig_factory = px.bar(
            factory_perf.reset_index(),
            x='Factory',
            y='Avg LT',
            color='Avg LT',
            color_continuous_scale='Viridis',
            hover_data={'Std Dev': ':.2f', 'Orders': True},
            title="Factory Performance - Average Lead Time"
        )
        st.plotly_chart(fig_factory, use_container_width=True)

    # Time Series — full width, no column needed
    st.subheader("Lead Time Trend Over Time")

    time_series = (
        filtered_df.groupby(filtered_df['Order Date'].dt.to_period('W').dt.start_time)['Lead Time']
        .agg(['mean', 'count'])
        .reset_index()
    )
    time_series.columns = ['Week', 'Avg Lead Time', 'Orders']

    fig_trend = px.line(
        time_series,
        x='Week',
        y='Avg Lead Time',
        markers=True,
        title="Lead Time Trend Over Time",
        labels={'Week': 'Week Starting', 'Avg Lead Time': 'Average Lead Time (days)'},
        hover_data={'Orders': True}
    )
    fig_trend.update_xaxes(tickformat="%b %d, %Y")
    st.plotly_chart(fig_trend, use_container_width=True)

    # Efficiency Distribution — full width
    st.subheader("Efficiency Score Distribution")

    fig_efficiency = px.histogram(
        filtered_df,
        x='Efficiency_Score',
        nbins=30,
        title="Distribution of Route Efficiency Scores",
        labels={'Efficiency_Score': 'Efficiency Score (0-100)', 'count': 'Number of Orders'},
        color_discrete_sequence=['#636EFA']
    )
    st.plotly_chart(fig_efficiency, use_container_width=True)
 
# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
 
col1, col2, col3 = st.columns(3)
 
with col1:
    st.info(f"Data Period: {date_min} to {date_max}")
 
with col2:
    st.info(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
 
with col3:
    st.info(f"Data Records: {len(filtered_df):,} / {len(df):,}")
 
st.markdown("""
---
**Nassau Candy Distributor | Shipping Route Efficiency Analysis**
 
*This dashboard provides interactive analytics for optimizing shipping routes and identifying operational bottlenecks.*
 
""")
