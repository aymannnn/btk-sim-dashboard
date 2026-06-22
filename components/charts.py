import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def plot_user_growth(users_df):
    if 'firstTestDate' not in users_df.columns:
        st.warning("First test date not available for users.")
        return None, None
        
    df = users_df.dropna(subset=['firstTestDate']).copy()
    df['firstTestDate'] = pd.to_datetime(df['firstTestDate']).dt.date
    
    daily_growth = df.groupby('firstTestDate').size().reset_index(name='New Users')
    daily_growth = daily_growth.sort_values('firstTestDate')
    daily_growth['Cumulative Users'] = daily_growth['New Users'].cumsum()
    
    daily_growth.rename(columns={'firstTestDate': 'Date'}, inplace=True)
    
    fig = px.line(
        daily_growth, 
        x='Date', 
        y='Cumulative Users',
        title="User Growth Over Time (Based on First Test)",
        markers=True,
        labels={"Date": "Date of First Test", "Cumulative Users": "Total Users"}
    )
    
    fig.update_traces(fill='tozeroy')
    fig.update_layout(template="plotly_white")
    return fig, daily_growth

def plot_tests_over_time(chats_df):
    completed_chats = chats_df[~chats_df['resultStatus'].isin(['Did Not Complete']) & chats_df['resultStatus'].notna()].copy()
    
    if len(completed_chats) == 0:
        return None, None
        
    completed_chats['Date'] = pd.to_datetime(completed_chats['startTime']).dt.date
    
    daily_tests = completed_chats.groupby(['Date', 'actionType']).size().reset_index(name='Count')
    pivot_df = daily_tests.pivot(index='Date', columns='actionType', values='Count').fillna(0)
    cum_df = pivot_df.cumsum().reset_index()
    melted_df = pd.melt(cum_df, id_vars=['Date'], var_name='Test Type', value_name='Cumulative Completed Tests')
    
    fig = px.area(
        melted_df,
        x='Date',
        y='Cumulative Completed Tests',
        color='Test Type',
        title="Tests Completed Over Time (by Test Type)",
        labels={"Date": "Date", "Cumulative Completed Tests": "Total Completed Tests", "Test Type": "Test Type"}
    )
    
    fig.update_layout(template="plotly_white")
    return fig, melted_df

def plot_tests_over_time_by_domain(chats_df):
    completed_chats = chats_df[~chats_df['resultStatus'].isin(['Did Not Complete']) & chats_df['resultStatus'].notna()].copy()
    
    if len(completed_chats) == 0:
        return None, None
        
    completed_chats['Date'] = pd.to_datetime(completed_chats['startTime']).dt.date
    daily_tests = completed_chats.groupby(['Date', 'domainTitle']).size().reset_index(name='Count')
    pivot_df = daily_tests.pivot(index='Date', columns='domainTitle', values='Count').fillna(0)
    cum_df = pivot_df.cumsum().reset_index()
    melted_df = pd.melt(cum_df, id_vars=['Date'], var_name='Domain', value_name='Cumulative Completed Tests')
    
    fig = px.area(
        melted_df,
        x='Date',
        y='Cumulative Completed Tests',
        color='Domain',
        title="Tests Completed Over Time (by Domain)",
        labels={"Date": "Date", "Cumulative Completed Tests": "Total Completed Tests", "Domain": "Domain"}
    )
    
    fig.update_layout(template="plotly_white")
    return fig, melted_df

def plot_tests_per_user(chats_df):
    """
    Plots a histogram of the number of completed tests per user.
    """
    completed_chats = chats_df[~chats_df['resultStatus'].isin(['Did Not Complete']) & chats_df['resultStatus'].notna()].copy()
    
    if len(completed_chats) == 0:
        return None, None
        
    user_test_counts = completed_chats.groupby('userID').size().reset_index(name='Tests Completed')
    
    fig = px.histogram(
        user_test_counts,
        x='Tests Completed',
        nbins=15,
        title="Distribution of Tests Completed per User",
        labels={'Tests Completed': 'Number of Completed Tests'},
        color_discrete_sequence=['#4C78A8']
    )
    fig.update_layout(template="plotly_white", bargap=0.1)
    
    export_df = user_test_counts.rename(columns={'userID': 'User ID'})
    return fig, export_df

def plot_score_distribution(chats_df):
    if 'overallScore' not in chats_df.columns:
        return None, None
        
    df = chats_df[chats_df['overallScore'] > 0].copy()
    
    fig = px.histogram(
        df,
        x='overallScore',
        nbins=20,
        title="Distribution of Overall Scores",
        labels={'overallScore': 'Overall Score'},
        color_discrete_sequence=['#4C78A8']
    )
    fig.update_layout(template="plotly_white", bargap=0.1)
    
    export_df = df[['id', 'userID', 'examName', 'overallScore']].rename(columns={'id': 'Test ID', 'userID': 'User ID', 'examName': 'Scenario', 'overallScore': 'Overall Score'})
    return fig, export_df

def plot_user_score_history(chats_df, user_id):
    user_chats = chats_df[(chats_df['userID'] == user_id) & (chats_df['overallScore'] > 0)].copy()
    
    if len(user_chats) == 0:
        return None, None
        
    user_chats = user_chats.sort_values('startTime')
    user_chats['Test Number'] = range(1, len(user_chats) + 1)
    
    fig = px.line(
        user_chats,
        x='Test Number',
        y='overallScore',
        title="Score Progression Over Time",
        markers=True,
        hover_data=['examName', 'startTime']
    )
    fig.update_layout(template="plotly_white")
    
    export_df = user_chats[['Test Number', 'examName', 'startTime', 'overallScore']].rename(
        columns={'examName': 'Scenario', 'startTime': 'Date Taken', 'overallScore': 'Overall Score'}
    )
    return fig, export_df

def plot_tests_by_domain(chats_df):
    domain_counts = chats_df['domainTitle'].value_counts().reset_index()
    domain_counts.columns = ['Domain', 'Total Tests']
    
    fig = px.bar(
        domain_counts,
        x='Domain',
        y='Total Tests',
        title="Tests by Medical Domain",
        color='Domain'
    )
    fig.update_layout(template="plotly_white", showlegend=False)
    return fig, domain_counts

def plot_tests_by_action_type(chats_df):
    type_counts = chats_df['actionType'].value_counts().reset_index()
    type_counts.columns = ['Test Type', 'Total Tests']
    
    fig = px.pie(
        type_counts,
        names='Test Type',
        values='Total Tests',
        title="Distribution of Test Types",
        hole=0.4
    )
    return fig, type_counts

def plot_score_trend(chats_df):
    df = chats_df[(chats_df['overallScore'] > 0) & chats_df['startTime'].notna()].copy()
    if len(df) < 2: return None, None, None
    
    df['startTime_numeric'] = pd.to_numeric(df['startTime'])
    
    fig = px.scatter(
        df, x='startTime', y='overallScore', 
        trendline="ols",
        trendline_options=dict(add_constant=True),
        trendline_color_override="red",
        opacity=0.5,
        title="System-Wide Score Trend Over Time",
        labels={'startTime': 'Test Start Time', 'overallScore': 'Overall Score'}
    )
    
    stats = None
    results = px.get_trendline_results(fig)
    if not results.empty:
        model = results.iloc[0]["px_fit_results"]
        stats = {'r2': model.rsquared, 'p': model.pvalues[1] if len(model.pvalues) > 1 else model.pvalues[0]}
        
    fig.update_layout(template="plotly_white")
    
    export_df = df[['id', 'startTime', 'overallScore']].rename(columns={'id': 'Test ID', 'startTime': 'Date', 'overallScore': 'Score'})
    return fig, stats, export_df

def plot_duration_vs_score(chats_df):
    df = chats_df[(chats_df['overallScore'] > 0) & (chats_df['duration'] > 0)].copy()
    if len(df) == 0:
        df = chats_df[(chats_df['overallScore'] > 0) & chats_df['startTime'].notna() & chats_df['endTime'].notna()].copy()
        df['calculated_duration'] = (df['endTime'] - df['startTime']).dt.total_seconds() / 60.0
        duration_col = 'calculated_duration'
    else:
        duration_col = 'duration'
        df[duration_col] = df[duration_col] / 60.0 
        
    df = df[df[duration_col] > 0]
    if len(df) < 2: return None, None, None
        
    fig = px.scatter(
        df, x=duration_col, y='overallScore',
        trendline="ols",
        trendline_color_override="red",
        opacity=0.5,
        title="Test Duration vs. Overall Score",
        labels={duration_col: 'Duration (Minutes)', 'overallScore': 'Overall Score'}
    )
    
    stats = None
    results = px.get_trendline_results(fig)
    if not results.empty:
        model = results.iloc[0]["px_fit_results"]
        stats = {'r2': model.rsquared, 'p': model.pvalues[1] if len(model.pvalues) > 1 else model.pvalues[0]}
        
    fig.update_layout(template="plotly_white")
    export_df = df[['id', duration_col, 'overallScore']].rename(columns={'id': 'Test ID', duration_col: 'Duration (Mins)', 'overallScore': 'Score'})
    return fig, stats, export_df


def plot_tokens_vs_score(chats_df):
    df = chats_df[(chats_df['overallScore'] > 0) & (chats_df['totalTokens'] > 0)].copy()
    if len(df) < 2: return None, None, None
    
    fig = px.scatter(
        df, x='totalTokens', y='overallScore',
        color='actionType',
        trendline="ols",
        trendline_scope="overall",
        trendline_color_override="red",
        opacity=0.5,
        title="Token Usage vs. Overall Score",
        labels={'totalTokens': 'Total Tokens Used', 'overallScore': 'Overall Score', 'actionType': 'Test Type'}
    )
    
    stats = None
    results = px.get_trendline_results(fig)
    if not results.empty:
        model = results.iloc[0]["px_fit_results"]
        stats = {'r2': model.rsquared, 'p': model.pvalues[1] if len(model.pvalues) > 1 else model.pvalues[0]}
        
    fig.update_layout(template="plotly_white")
    export_df = df[['id', 'totalTokens', 'actionType', 'overallScore']].rename(columns={'id': 'Test ID', 'totalTokens': 'Tokens Used', 'actionType': 'Test Type', 'overallScore': 'Score'})
    return fig, stats, export_df
