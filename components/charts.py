import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def plot_user_growth(users_df):
    """
    Plots the cumulative number of users based on their first test date.
    """
    if 'firstTestDate' not in users_df.columns:
        st.warning("First test date not available for users.")
        return None
        
    # Drop users who haven't taken a test yet
    df = users_df.dropna(subset=['firstTestDate']).copy()
    
    # Extract just the date part for grouping
    df['firstTestDate'] = pd.to_datetime(df['firstTestDate']).dt.date
    
    # Count new users per day
    daily_growth = df.groupby('firstTestDate').size().reset_index(name='New Users')
    daily_growth = daily_growth.sort_values('firstTestDate')
    
    # Calculate cumulative sum
    daily_growth['Cumulative Users'] = daily_growth['New Users'].cumsum()
    
    fig = px.line(
        daily_growth, 
        x='firstTestDate', 
        y='Cumulative Users',
        title="User Growth Over Time (Based on First Test)",
        markers=True,
        labels={"firstTestDate": "Date of First Test", "Cumulative Users": "Total Users"}
    )
    
    # Add an area fill for visual appeal
    fig.update_traces(fill='tozeroy')
    fig.update_layout(template="plotly_white")
    return fig

def plot_tests_over_time(chats_df):
    """
    Plots the number of completed tests over time.
    """
    # Filter for completed tests
    completed_chats = chats_df[~chats_df['resultStatus'].isin(['Did Not Complete']) & chats_df['resultStatus'].notna()].copy()
    
    if len(completed_chats) == 0:
        return None
        
    # Extract date
    completed_chats['Date'] = pd.to_datetime(completed_chats['startTime']).dt.date
    
    # Count tests per day
    daily_tests = completed_chats.groupby('Date').size().reset_index(name='Completed Tests')
    daily_tests = daily_tests.sort_values('Date')
    
    # Cumulative sum
    daily_tests['Cumulative Completed Tests'] = daily_tests['Completed Tests'].cumsum()
    
    fig = px.line(
        daily_tests,
        x='Date',
        y='Cumulative Completed Tests',
        title="Tests Completed Over Time",
        markers=True,
        labels={"Date": "Date", "Cumulative Completed Tests": "Total Completed Tests"}
    )
    
    fig.update_traces(fill='tozeroy')
    fig.update_layout(template="plotly_white")
    return fig

def plot_score_distribution(chats_df):
    """
    Plots a histogram of the overall scores.
    """
    if 'overallScore' not in chats_df.columns:
        return None
        
    df = chats_df[chats_df['overallScore'] > 0] # Optionally exclude 0s if they mean 'Did Not Complete'
    
    fig = px.histogram(
        df,
        x='overallScore',
        nbins=20,
        title="Distribution of Overall Scores",
        labels={'overallScore': 'Overall Score'},
        color_discrete_sequence=['#4C78A8']
    )
    fig.update_layout(template="plotly_white", bargap=0.1)
    return fig

def plot_user_score_history(chats_df, user_id):
    """
    Plots the score history for a single selected user.
    """
    user_chats = chats_df[(chats_df['userID'] == user_id) & (chats_df['overallScore'] > 0)].copy()
    
    if len(user_chats) == 0:
        return None
        
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
    return fig

def plot_tests_by_domain(chats_df):
    """
    Plots the number of tests taken per domain.
    """
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
    return fig

def plot_tests_by_action_type(chats_df):
    """
    Plots a pie chart of the action types (selfpaced, realtime, proctor).
    """
    type_counts = chats_df['actionType'].value_counts().reset_index()
    type_counts.columns = ['Test Type', 'Count']
    
    fig = px.pie(
        type_counts,
        names='Test Type',
        values='Count',
        title="Distribution of Test Types",
        hole=0.4
    )
    return fig

def plot_score_trend(chats_df):
    """
    Plots the trend of overall scores over time using OLS regression.
    """
    df = chats_df[(chats_df['overallScore'] > 0) & chats_df['startTime'].notna()].copy()
    if len(df) < 2: return None, None
    
    # OLS requires numeric x. Convert datetime to timestamp
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
    return fig, stats

def plot_duration_vs_score(chats_df):
    """
    Plots Test Duration vs Score.
    """
    df = chats_df[(chats_df['overallScore'] > 0) & (chats_df['duration'] > 0)].copy()
    # If duration is 0 but we have startTime and endTime, we can calculate it
    if len(df) == 0:
        df = chats_df[(chats_df['overallScore'] > 0) & chats_df['startTime'].notna() & chats_df['endTime'].notna()].copy()
        df['calculated_duration'] = (df['endTime'] - df['startTime']).dt.total_seconds() / 60.0
        duration_col = 'calculated_duration'
    else:
        duration_col = 'duration'
        df[duration_col] = df[duration_col] / 60.0 # convert seconds to minutes
        
    df = df[df[duration_col] > 0]
    if len(df) < 2: return None, None
        
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
    return fig, stats

def plot_complexity_vs_score(chats_df):
    """
    Plots Scenario Complexity vs Score.
    """
    df = chats_df[(chats_df['overallScore'] > 0) & chats_df['complexity'].notna()].copy()
    if len(df) < 2: return None, None
    
    fig = px.scatter(
        df, x='complexity', y='overallScore',
        trendline="ols",
        trendline_color_override="red",
        opacity=0.5,
        title="Scenario Complexity vs. Overall Score",
        labels={'complexity': 'Scenario Complexity', 'overallScore': 'Overall Score'}
    )
    
    stats = None
    results = px.get_trendline_results(fig)
    if not results.empty:
        model = results.iloc[0]["px_fit_results"]
        stats = {'r2': model.rsquared, 'p': model.pvalues[1] if len(model.pvalues) > 1 else model.pvalues[0]}
        
    fig.update_layout(template="plotly_white")
    return fig, stats

def plot_tokens_vs_score(chats_df):
    """
    Plots Total Tokens Used vs Score.
    """
    df = chats_df[(chats_df['overallScore'] > 0) & (chats_df['totalTokens'] > 0)].copy()
    if len(df) < 2: return None, None
    
    fig = px.scatter(
        df, x='totalTokens', y='overallScore',
        trendline="ols",
        trendline_color_override="red",
        opacity=0.5,
        title="Token Usage (Conversational Depth) vs. Overall Score",
        labels={'totalTokens': 'Total Tokens Used', 'overallScore': 'Overall Score'}
    )
    
    stats = None
    results = px.get_trendline_results(fig)
    if not results.empty:
        model = results.iloc[0]["px_fit_results"]
        stats = {'r2': model.rsquared, 'p': model.pvalues[1] if len(model.pvalues) > 1 else model.pvalues[0]}
        
    fig.update_layout(template="plotly_white")
    return fig, stats
