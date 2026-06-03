import streamlit as st
import pandas as pd
import data_processor
from components import charts

st.set_page_config(page_title="BTK Admin Dashboard", layout="wide", page_icon="📈")

# Main Title
st.title("📈 BTK Admin Dashboard")

# --- FILE UPLOAD ---
st.sidebar.header("1. Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload snapshot.zip", type=["zip"])

if uploaded_file is not None:
    # Process the data
    with st.spinner("Extracting and processing data..."):
        data = data_processor.process_snapshot(uploaded_file)
        users_df = data['users']
        chats_df = data['chats']
        
    st.sidebar.success("Data loaded successfully!")
    
    # --- GLOBAL FILTERS ---
    st.sidebar.header("2. Global Filters")
    
    # Date Range Filter
    min_date = chats_df['startTime'].min()
    max_date = chats_df['startTime'].max()
    
    # Handle NaT
    if pd.isna(min_date) or pd.isna(max_date):
        st.warning("Date parsing issue. Check your data.")
    else:
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        
        # Apply Date Filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (chats_df['startTime'].dt.date >= start_date) & (chats_df['startTime'].dt.date <= end_date)
            filtered_chats = chats_df[mask]
        else:
            filtered_chats = chats_df

        # Domain Filter
        domains = ["All"] + list(filtered_chats['domainTitle'].dropna().unique())
        selected_domain = st.sidebar.selectbox("Filter by Domain", domains)
        if selected_domain != "All":
            filtered_chats = filtered_chats[filtered_chats['domainTitle'] == selected_domain]
            
        # Test Type Filter
        test_types = ["All"] + list(filtered_chats['actionType'].dropna().unique())
        selected_type = st.sidebar.selectbox("Filter by Test Type", test_types)
        if selected_type != "All":
            filtered_chats = filtered_chats[filtered_chats['actionType'] == selected_type]

        # Completion Status Filter
        completion_options = ["All", "Completed", "Did Not Complete"]
        selected_completion = st.sidebar.selectbox("Filter by Completion Status", completion_options)
        if selected_completion == "Completed":
            filtered_chats = filtered_chats[~filtered_chats['resultStatus'].isin(['Did Not Complete']) & filtered_chats['resultStatus'].notna()]
        elif selected_completion == "Did Not Complete":
            filtered_chats = filtered_chats[filtered_chats['resultStatus'].isin(['Did Not Complete']) | filtered_chats['resultStatus'].isna()]

        # Specific Result Status Filter
        status_options = ["All"] + list(filtered_chats['resultStatus'].dropna().unique())
        selected_status = st.sidebar.selectbox("Filter by Specific Result Status", status_options)
        if selected_status != "All":
            filtered_chats = filtered_chats[filtered_chats['resultStatus'] == selected_status]

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Executive Overview", 
        "👤 Single User Analysis", 
        "📝 Performance", 
        "🤖 System Metrics",
        "📈 Statistical Trends"
    ])
    
    with tab1:
        st.header("Executive Overview")
        
        # KPIs
        col1, col2, col3, col4, col5_kpi = st.columns(5)
        
        # A test is considered completed if it has a result status other than 'Did Not Complete' or NaN
        completed_tests_df = filtered_chats[~filtered_chats['resultStatus'].isin(['Did Not Complete']) & filtered_chats['resultStatus'].notna()]
        active_users_count = completed_tests_df['userID'].nunique()
        
        col1.metric("Total Users", active_users_count)
        col2.metric("Total Tests", len(filtered_chats))
        
        completed_tests = len(completed_tests_df)
        col3.metric("Completed Tests", completed_tests)
        
        completion_rate = (completed_tests / len(filtered_chats) * 100) if len(filtered_chats) > 0 else 0
        col4.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        avg_score = filtered_chats[filtered_chats['overallScore'] > 0]['overallScore'].mean()
        col5_kpi.metric("Average Score", f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A")
        
        st.divider()
        
        # User Growth Chart
        user_growth_fig = charts.plot_user_growth(users_df)
        if user_growth_fig:
            st.plotly_chart(user_growth_fig, use_container_width=True)
            
        # Tests Completed Over Time Chart
        tests_over_time_fig = charts.plot_tests_over_time(filtered_chats)
        if tests_over_time_fig:
            st.plotly_chart(tests_over_time_fig, use_container_width=True)
            
    with tab2:
        st.header("Single User Analysis")
        
        user_list = users_df.dropna(subset=['email'])['email'].unique()
        selected_user = st.selectbox("Select a User to analyze", ["-- Select --"] + list(user_list))
        
        if selected_user != "-- Select --":
            u_id = users_df[users_df['email'] == selected_user]['id'].iloc[0]
            
            # User stats
            u_chats = filtered_chats[filtered_chats['userID'] == u_id]
            st.write(f"**Total Tests taken by {selected_user}:** {len(u_chats)}")
            
            score_hist_fig = charts.plot_user_score_history(filtered_chats, u_id)
            if score_hist_fig:
                st.plotly_chart(score_hist_fig, use_container_width=True)
            else:
                st.info("Not enough completed tests to show score history.")
                
            st.subheader("Test Transcript")
            display_cols = ['examName', 'startTime', 'actionType', 'resultStatus', 'overallScore']
            st.dataframe(u_chats[display_cols].sort_values('startTime', ascending=False), use_container_width=True)
            
    with tab3:
        st.header("Examination Performance")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            score_dist_fig = charts.plot_score_distribution(filtered_chats)
            if score_dist_fig:
                st.plotly_chart(score_dist_fig, use_container_width=True)
                
        with col_right:
            domain_fig = charts.plot_tests_by_domain(filtered_chats)
            if domain_fig:
                st.plotly_chart(domain_fig, use_container_width=True)
                
        test_type_fig = charts.plot_tests_by_action_type(filtered_chats)
        if test_type_fig:
            st.plotly_chart(test_type_fig, use_container_width=True)
            
    with tab4:
        st.header("System & Token Metrics")
        
        total_tokens = filtered_chats['totalTokens'].sum()
        st.metric("Total Tokens Used (in filtered data)", f"{total_tokens:,.0f}")
        
        # Token usage over time
        if total_tokens > 0:
            token_df = filtered_chats.dropna(subset=['startTime', 'totalTokens']).copy()
            token_df['Date'] = token_df['startTime'].dt.date
            daily_tokens = token_df.groupby('Date')['totalTokens'].sum().reset_index()
            
            fig = charts.px.bar(
                daily_tokens, 
                x='Date', 
                y='totalTokens', 
                title="Daily Token Usage",
                labels={'totalTokens': 'Tokens Used'}
            )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.header("Statistical Trends & Correlations")
        st.markdown("Explore high-level patterns and correlations across the dataset. Trendlines use Ordinary Least Squares (OLS) regression.")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            fig1, stats1 = charts.plot_score_trend(filtered_chats)
            if fig1:
                st.subheader("System-Wide Score Trend")
                if stats1:
                    st.info(f"**R²**: {stats1['r2']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; **P-value**: {stats1['p']:.4e}")
                st.markdown("*Are overall competency scores generally improving over time?*")
                st.plotly_chart(fig1, use_container_width=True)
                
            fig3, stats3 = charts.plot_complexity_vs_score(filtered_chats)
            if fig3:
                st.subheader("Scenario Complexity vs. Score")
                if stats3:
                    st.info(f"**R²**: {stats3['r2']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; **P-value**: {stats3['p']:.4e}")
                st.markdown("*Do higher complexity scenarios accurately reflect lower performance scores?*")
                st.plotly_chart(fig3, use_container_width=True)
                
        with col_t2:
            fig2, stats2 = charts.plot_duration_vs_score(filtered_chats)
            if fig2:
                st.subheader("Test Duration vs. Score")
                if stats2:
                    st.info(f"**R²**: {stats2['r2']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; **P-value**: {stats2['p']:.4e}")
                st.markdown("*Do students who take longer to complete a scenario perform better or worse?*")
                st.plotly_chart(fig2, use_container_width=True)
                
            fig4, stats4 = charts.plot_tokens_vs_score(filtered_chats)
            if fig4:
                st.subheader("Token Usage vs. Score")
                if stats4:
                    st.info(f"**R²**: {stats4['r2']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; **P-value**: {stats4['p']:.4e}")
                st.markdown("*Does a deeper, longer conversation (more tokens) correlate with a higher score?*")
                st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("👈 Please upload the snapshot.zip file in the sidebar to begin.")
