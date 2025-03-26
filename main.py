import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Title of the app
st.title("📊 Medication Usage Analysis Dashboard")

# Load the dataset
@st.cache_data  # Add caching for better performance
def load_data():
    df = pd.read_csv("pharma.csv")
    # Convert 'Date' to datetime format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Extract date components
    df["Day"] = df['Date'].dt.day
    df["Month"] = df['Date'].dt.month
    df["Year"] = df['Date'].dt.year
    df["Weekday Name"] = df['Date'].dt.day_name()
    return df

df = load_data()

# Sidebar for user input
st.sidebar.header("🔍 Filter Options")

# Multi-select for medications (now properly working with multiple selections)
medication_columns = [col for col in df.columns if col not in ['Date', 'Day', 'Month', 'Year', 'Weekday Name']]
selected_medications = st.sidebar.multiselect(
    "Select Medication(s)", 
    medication_columns,
    default=medication_columns[0] if len(medication_columns) > 0 else None
)

# Year range selection
min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Month selection (multiple months allowed)
available_months = sorted(df['Month'].unique())
selected_months = st.sidebar.multiselect(
    "Select Month(s)",
    options=available_months,
    default=1
)

# Day selection (now shows proper range based on selected month/year)
max_day = 31  # Default maximum
if len(selected_months) == 1:
    # Get actual max days for the month if only one month selected
    month = selected_months[0]
    if month in [4, 6, 9, 11]:
        max_day = 30
    elif month == 2:
        # Simple February calculation (doesn't account for leap years)
        max_day = 28

selected_day_range = st.sidebar.slider(
    "Select Day Range",
    min_value=1,
    max_value=max_day,
    value=(1, max_day)
)

# Filter data based on user input
filtered_df = df[
    (df['Year'] >= year_range[0]) & 
    (df['Year'] <= year_range[1]) & 
    (df['Month'].isin(selected_months)) & 
    (df['Day'] >= selected_day_range[0]) & 
    (df['Day'] <= selected_day_range[1])
]

# Main display
st.header("📈 Medication Usage Analysis")

if not selected_medications:
    st.warning("Please select at least one medication to analyze.")
else:
    # Display filtered data summary
    st.subheader("🔢 Filtered Data Summary")
    st.write(f"📅 Date Range: {filtered_df['Date'].min().strftime('%Y-%m-%d')} to {filtered_df['Date'].max().strftime('%Y-%m-%d')}")
    st.write(f"📊 Total Records: {len(filtered_df):,}")
    
    # Show raw data with expander
    with st.expander("📋 View Filtered Data"):
        st.dataframe(filtered_df)

    # Tab layout for different analyses
    tab1, tab2, tab3 = st.tabs(["📅 Time Series", "📆 Weekly Pattern", "📊 Statistics"])

    with tab1:
        st.subheader("Time Series Analysis")
        if not filtered_df.empty:
            fig = px.line(
                filtered_df,
                x='Date',
                y=selected_medications,
                title='Medication Usage Over Time',
                labels={'value': 'Usage', 'variable': 'Medication'},
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected filters.")

    with tab2:
        st.subheader("Weekly Usage Pattern")
        if not filtered_df.empty:
            weekday_df = filtered_df.groupby('Weekday Name')[selected_medications].mean().reset_index()
            # Reorder weekdays properly
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekday_df['Weekday Name'] = pd.Categorical(weekday_df['Weekday Name'], categories=weekday_order, ordered=True)
            weekday_df = weekday_df.sort_values('Weekday Name')
            
            fig = px.bar(
                weekday_df,
                x='Weekday Name',
                y=selected_medications,
                barmode='group',
                title='Average Usage by Weekday',
                labels={'value': 'Average Usage', 'variable': 'Medication'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected filters.")

    with tab3:
        st.subheader("Statistical Summary")
        if not filtered_df.empty:
            stats_df = filtered_df[selected_medications].describe().T
            stats_df['sum'] = filtered_df[selected_medications].sum()
            stats_df = stats_df[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 'sum']]
            stats_df.columns = ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max', 'Total']
            st.dataframe(stats_df.style.format("{:.2f}"))
            
            # Add correlation matrix
            st.subheader("Medication Correlations")
            corr_matrix = filtered_df[selected_medications].corr()
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu',
                range_color=[-1, 1],
                title='Correlation Between Medications'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected filters.")

# Add footer
st.markdown("---")
st.markdown("Developed by [Your Name] • [GitHub Repo](#) • v1.0")