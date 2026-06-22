import streamlit as st
import pandas as pd
import data_processor
from components import charts

st.set_page_config(page_title="BTK Admin Dashboard", layout="wide", page_icon="📈")

def render_chart_with_export(fig, df, filename):
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        if df is not None and len(df) > 0:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Export {filename} Data",
                data=csv,
                file_name=f"{filename.replace(' ', '_').lower()}.csv",
                mime='text/csv',
                key=filename
            )

# Main Title
st.title("📈 BTK Admin Dashboard")

# --- FILE UPLOAD ---
st.sidebar.header("1. Data Upload")

uploaded_data = st.sidebar.file_uploader("Upload snapshot.zip", type=["zip"])

if uploaded_data is not None:
    # Process the data
    with st.spinner("Extracting and processing data..."):
        try:
            data = data_processor.process_snapshot(uploaded_data)
            users_df = data['users']
            chats_df = data['chats']
            
            st.sidebar.success("Data loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")
            st.stop()
    
    # --- GLOBAL FILTERS ---
    st.sidebar.header("2. Global Filters")
    
    # Date Range Filter
    min_date = chats_df['startTime'].min()
    max_date = chats_df['startTime'].max()
    
    if pd.isna(min_date) or pd.isna(max_date):
        st.warning("Date parsing issue. Check your data.")
    else:
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        
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
            
        # Test Type Filter UI
        test_types = ["All"] + list(filtered_chats['actionType'].dropna().unique())
        selected_type = st.sidebar.selectbox("Filter by Test Type", test_types)
        if selected_type != "All":
            filtered_chats = filtered_chats[filtered_chats['actionType'] == selected_type]

        # Completion Status Filter UI
        completion_options = ["All", "Completed", "Did Not Complete"]
        selected_completion = st.sidebar.selectbox("Filter by Completion Status", completion_options)
        if selected_completion == "Completed":
            filtered_chats = filtered_chats[~filtered_chats['resultStatus'].isin(['Did Not Complete']) & filtered_chats['resultStatus'].notna()]
        elif selected_completion == "Did Not Complete":
            filtered_chats = filtered_chats[filtered_chats['resultStatus'].isin(['Did Not Complete']) | filtered_chats['resultStatus'].isna()]

        # Result Status Filter UI
        status_options = ["All"] + list(filtered_chats['resultStatus'].dropna().unique())
        selected_status = st.sidebar.selectbox("Filter by Specific Result Status", status_options)
        if selected_status != "All":
            filtered_chats = filtered_chats[filtered_chats['resultStatus'] == selected_status]

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Executive Overview", 
        "👤 Single User Analysis", 
        "📝 Performance", 
        "🤖 System Metrics",
        "📈 Statistical Trends",
        "🔍 Statistical Exploration"
    ])
    
    with tab1:
        st.header("Executive Overview")
        
        col1, col2, col3, col4, col5_kpi = st.columns(5)
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
        
        user_growth_fig, user_growth_df = charts.plot_user_growth(users_df)
        render_chart_with_export(user_growth_fig, user_growth_df, "User Growth")
            
        tests_by_domain_fig, tests_by_domain_df = charts.plot_tests_over_time_by_domain(filtered_chats)
        render_chart_with_export(tests_by_domain_fig, tests_by_domain_df, "Tests Over Time by Domain")
            
        tests_over_time_fig, tests_over_time_df = charts.plot_tests_over_time(filtered_chats)
        if tests_over_time_fig:
            tests_over_time_fig.update_layout(title="Tests Completed Over Time (by Test Type)")
        render_chart_with_export(tests_over_time_fig, tests_over_time_df, "Tests Over Time")
            
    with tab2:
        st.header("Single User Analysis")
        user_list = users_df.dropna(subset=['email'])['email'].unique()
        selected_user = st.selectbox("Select a User to analyze", ["-- Select --"] + list(user_list))
        
        if selected_user != "-- Select --":
            u_id = users_df[users_df['email'] == selected_user]['id'].iloc[0]
            u_chats = filtered_chats[filtered_chats['userID'] == u_id]
            st.write(f"**Total Tests taken by {selected_user}:** {len(u_chats)}")
            
            score_hist_fig, score_hist_df = charts.plot_user_score_history(filtered_chats, u_id)
            if score_hist_fig:
                render_chart_with_export(score_hist_fig, score_hist_df, "User Score History")
            else:
                st.info("Not enough completed tests to show score history.")
                
            st.subheader("Test Transcript")
            st.markdown("Click on any test row below to view the full chat history.")
            display_cols = ['examName', 'startTime', 'actionType', 'resultStatus', 'overallScore']
            
            # Interactive dataframe that allows row selection
            event = st.dataframe(
                u_chats[display_cols].sort_values('startTime', ascending=False), 
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # If a row is clicked, display the chat history
            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                selected_row = u_chats.sort_values('startTime', ascending=False).iloc[selected_idx]
                
                st.divider()
                st.subheader(f"Session Details: {selected_row['examName']}")
                
                tab_chat, tab_perf = st.tabs(["💬 Chat History", "📊 Performance"])
                
                with tab_chat:
                    transcript_str = selected_row.get('transcript', None)
                    if pd.notna(transcript_str):
                        try:
                            import json
                            import re
                            msgs = json.loads(transcript_str)
                            for m in msgs:
                                role = m.get('role', 'user')
                                content = m.get('message', '')
                                # Strip <sq id="..."/> tags from the text
                                content = re.sub(r'<sq id="\d+"/>', '', content).strip()
                                
                                # Map standard roles to Streamlit chat roles
                                st_role = "assistant" if role in ["assistant", "system", "bot"] else "user"
                                with st.chat_message(st_role):
                                    st.write(content)
                        except Exception as e:
                            st.error(f"Transcript could not be parsed: {e}")
                    else:
                        st.info("No transcript available for this test.")
                        
                with tab_perf:
                    performance_str = selected_row.get('performance', None)
                    if pd.notna(performance_str):
                        try:
                            import json
                            perf_data = json.loads(performance_str)
                            
                            st.markdown(f"### {perf_data.get('exam_title', 'Unknown Exam')}")
                            st.markdown(f"**Surgical Category:** {perf_data.get('surgical_category', 'N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; **Status:** {perf_data.get('pass_status', 'N/A')}")
                            
                            # Layout metrics
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Overall Score", perf_data.get("overall_score", 0))
                            col2.metric("Competency Score", perf_data.get("competency_score", 0))
                            col3.metric("Clarity Score", perf_data.get("clarity_score", 0))
                            
                            st.divider()
                            
                            st.subheader("Identified Knowledge Gaps")
                            st.write(perf_data.get('identified_knowledge_gaps', 'None provided.'))
                            
                            st.subheader("Professionalism Notes")
                            st.write(perf_data.get('professionalism_notes', 'None provided.'))
                            
                            st.subheader("Curriculum Alignment")
                            st.write(perf_data.get('curriculum_alignment', 'None provided.'))
                            
                            st.subheader("Study Plan")
                            st.write(perf_data.get('study_plan', 'None provided.'))
                            
                            if perf_data.get('test_commentary'):
                                st.subheader("Test Commentary")
                                st.write(perf_data.get('test_commentary'))
                            
                            st.subheader("References")
                            refs = []
                            for k in ['reference1A', 'reference1B', 'reference2A', 'reference2B', 'reference3A', 'reference3B']:
                                val = perf_data.get(k)
                                if val and str(val).strip().lower() != 'none':
                                    refs.append(f"- {val}")
                            
                            if refs:
                                st.markdown("\n".join(refs))
                            else:
                                st.write("No references provided.")
                                
                        except Exception as e:
                            st.error(f"Performance data could not be parsed: {e}")
                    else:
                        st.info("No performance data available for this test.")
            
    with tab3:
        st.header("Examination Performance")
        col_left, col_right = st.columns(2)
        
        with col_left:
            score_dist_fig, score_dist_df = charts.plot_score_distribution(filtered_chats)
            render_chart_with_export(score_dist_fig, score_dist_df, "Score Distribution")
                
        with col_right:
            domain_fig, domain_df = charts.plot_tests_by_domain(filtered_chats)
            render_chart_with_export(domain_fig, domain_df, "Tests by Domain")
                
        test_type_fig, test_type_df = charts.plot_tests_by_action_type(filtered_chats)
        render_chart_with_export(test_type_fig, test_type_df, "Tests by Action Type")
            
    with tab4:
        st.header("System & Token Metrics")
        
        st.caption("*Disclaimer: These token metrics strictly represent OpenAI token usage and do NOT count ElevenLabs tokens.*")
        
        col_sys1, col_sys2 = st.columns(2)
        
        total_tokens = filtered_chats['totalTokens'].sum()
        col_sys1.metric("Total Tokens Used (in filtered data)", f"{total_tokens:,.0f}")
        
        completed_chats_for_sys = filtered_chats[~filtered_chats['resultStatus'].isin(['Did Not Complete']) & filtered_chats['resultStatus'].notna()]
        if len(completed_chats_for_sys) > 0:
            avg_tests_per_user = len(completed_chats_for_sys) / completed_chats_for_sys['userID'].nunique()
        else:
            avg_tests_per_user = 0
            
        col_sys2.metric("Average Completed Tests per User", f"{avg_tests_per_user:.1f}")
        
        st.divider()
        
        if total_tokens > 0:
            token_df = filtered_chats.dropna(subset=['startTime', 'totalTokens']).copy()
            token_df['Date'] = token_df['startTime'].dt.date
            
            daily_tokens = token_df.groupby(['Date', 'actionType'])['totalTokens'].sum().reset_index()
            daily_tokens = daily_tokens.rename(columns={'actionType': 'Test Type', 'totalTokens': 'Total Tokens'})
            
            fig = charts.px.bar(
                daily_tokens, 
                x='Date', 
                y='Total Tokens', 
                color='Test Type',
                title="Daily Token Usage (by Test Type)",
                labels={'Total Tokens': 'Tokens Used'}
            )
            fig.update_layout(template="plotly_white")
            
            render_chart_with_export(fig, daily_tokens, "Daily Token Usage")

        tests_per_user_fig, tests_per_user_df = charts.plot_tests_per_user(filtered_chats)
        if tests_per_user_fig:
            render_chart_with_export(tests_per_user_fig, tests_per_user_df, "Tests per User Distribution")

    with tab5:
        st.header("Statistical Trends & Correlations")
        st.markdown("Explore high-level patterns and correlations across the dataset. Trendlines use Ordinary Least Squares (OLS) regression.")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            fig1, stats1, df1 = charts.plot_score_trend(filtered_chats)
            if fig1:
                st.subheader("System-Wide Score Trend")
                if stats1:
                    st.info(f"**R²**: {stats1['r2']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; **P-value**: {stats1['p']:.4e}")
                st.markdown("*Are overall competency scores generally improving over time?*")
                render_chart_with_export(fig1, df1, "Score Trend Over Time")
                
        with col_t2:
            fig2, stats2, df2 = charts.plot_duration_vs_score(filtered_chats)
            if fig2:
                st.subheader("Test Duration vs. Score")
                if stats2:
                    st.info(f"**R²**: {stats2['r2']:.4f} &nbsp;&nbsp;|&nbsp;&nbsp; **P-value**: {stats2['p']:.4e}")
                st.markdown("*Do students who take longer to complete a scenario perform better or worse?*")
                render_chart_with_export(fig2, df2, "Duration vs Score")

    with tab6:
        st.header("Statistical Exploration")
        st.markdown("Select a numeric variable to explore its fundamental statistics based on the current global filters.")
        
        exploration_cols = {
            "Overall Score": "overallScore",
            "Total Tokens Used": "totalTokens",
            "Duration (Minutes)": "duration_mins",
            "Total Conversation Turns": "turnsCount",
            "User Messages Count": "userMessagesCount",
            "Bot Messages Count": "botMessagesCount"
        }
        
        selected_var_name = st.selectbox("Select Variable to Explore", list(exploration_cols.keys()))
        selected_col = exploration_cols[selected_var_name]
        
        explore_df = filtered_chats.copy()
        if selected_col == "duration_mins":
            if 'duration' in explore_df.columns:
                explore_df['duration_mins'] = explore_df['duration'] / 60.0
            else:
                explore_df['duration_mins'] = (explore_df['endTime'] - explore_df['startTime']).dt.total_seconds() / 60.0
                
        clean_s = explore_df[selected_col].dropna()
        if selected_col in ['overallScore', 'totalTokens', 'duration_mins']:
            clean_s = clean_s[clean_s > 0]
            
        if len(clean_s) > 0:
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Mean (Average)", f"{clean_s.mean():.2f}")
            col_s2.metric("Median", f"{clean_s.median():.2f}")
            
            modes = clean_s.mode()
            mode_val = f"{modes.iloc[0]:.2f}" if len(modes) > 0 else "N/A"
            col_s3.metric("Mode", mode_val)
            
            col_s4.metric("Std Deviation", f"{clean_s.std():.2f}")
            
            st.divider()
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Minimum", f"{clean_s.min():.2f}")
            col_m2.metric("Maximum", f"{clean_s.max():.2f}")
            col_m3.metric("25th Percentile", f"{clean_s.quantile(0.25):.2f}")
            col_m4.metric("75th Percentile", f"{clean_s.quantile(0.75):.2f}")
            
            st.divider()
            
            fig = charts.px.histogram(
                clean_s, 
                x=clean_s, 
                title=f"Distribution of {selected_var_name}",
                nbins=20,
                labels={'x': selected_var_name}
            )
            fig.update_layout(template="plotly_white")
            
            hist_export_df = clean_s.reset_index(drop=True).to_frame(name=selected_var_name)
            render_chart_with_export(fig, hist_export_df, f"{selected_var_name} Distribution")
        else:
            st.warning("Not enough valid data to calculate statistics for this variable under the current filters.")

else:
    st.info("👈 Please upload the snapshot.zip file in the sidebar to begin.")
