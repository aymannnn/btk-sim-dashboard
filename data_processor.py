import os
import zipfile
import tempfile
import pandas as pd
import streamlit as st
import shutil

@st.cache_data(show_spinner=False)
def process_snapshot(zip_file_path):
    """
    Extracts the uploaded snapshot.zip, loads the CSVs, and joins them into analytical dataframes.
    Cached by Streamlit so it only runs once per unique zip file.
    """
    temp_dir = None
    target_dir = None
    
    try:
        # 1. Determine if input is a local directory or a zip file
        if isinstance(zip_file_path, str) and os.path.isdir(zip_file_path):
            target_dir = zip_file_path
            # Check if there is a 'snapshot' subfolder
            if 'snapshot' in os.listdir(target_dir) and os.path.isdir(os.path.join(target_dir, 'snapshot')):
                target_dir = os.path.join(target_dir, 'snapshot')
        else:
            # Create a temporary directory to extract the files
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            target_dir = temp_dir
            if 'snapshot' in os.listdir(temp_dir):
                target_dir = os.path.join(temp_dir, 'snapshot')
            
        # 2. Load the CSVs
        users_df = pd.read_csv(os.path.join(target_dir, 'users.csv'))
        chats_df = pd.read_csv(os.path.join(target_dir, 'chats.csv'))
        domain_df = pd.read_csv(os.path.join(target_dir, 'domain.csv'))
        domain_action_df = pd.read_csv(os.path.join(target_dir, 'domainAction.csv'))
        exam_topic_df = pd.read_csv(os.path.join(target_dir, 'examTopic.csv'))
        exam_titles_df = pd.read_csv(os.path.join(target_dir, 'ExamTitles.csv'))
        
        # Load ChatMessages optimized - only need totalTokens and role per chat
        # Since it's large, we only load specific columns
        try:
            chat_msgs_df = pd.read_csv(
                os.path.join(target_dir, 'ChatMessages.csv'), 
                usecols=['chatID', 'totalTokens', 'role', 'content'],
                engine='c' # fast parser
            )
            
            # Extract transcripts efficiently
            valid_content = chat_msgs_df.dropna(subset=['content']).copy()
            stripped_content = valid_content['content'].str.strip()
            
            transcript_rows = valid_content[stripped_content.str.startswith('[')]
            transcripts = transcript_rows.drop_duplicates(subset=['chatID'], keep='last')[['chatID', 'content']]
            transcripts.rename(columns={'content': 'transcript'}, inplace=True)
            
            performance_rows = valid_content[stripped_content.str.startswith('{')]
            performances = performance_rows.drop_duplicates(subset=['chatID'], keep='last')[['chatID', 'content']]
            performances.rename(columns={'content': 'performance'}, inplace=True)
            
            # Aggregate tokens per chat (summing per user request as self-paced uses OpenAI throughout)
            tokens_per_chat = chat_msgs_df.groupby('chatID')['totalTokens'].sum().reset_index()
            
            # Fast cross-tabulation for roles
            role_counts = chat_msgs_df.groupby(['chatID', 'role']).size().unstack(fill_value=0).reset_index()
            if 'user' not in role_counts.columns: role_counts['user'] = 0
            if 'assistant' not in role_counts.columns: role_counts['assistant'] = 0
            
            role_counts = role_counts.rename(columns={'user': 'userMessagesCount', 'assistant': 'botMessagesCount'})
            role_counts['turnsCount'] = role_counts['userMessagesCount'] + role_counts['botMessagesCount']
            
            chat_stats = pd.merge(tokens_per_chat, role_counts[['chatID', 'userMessagesCount', 'botMessagesCount', 'turnsCount']], on='chatID', how='outer')
            
        except Exception as e:
            print(f"Could not load ChatMessages.csv optimally: {e}")
            chat_stats = pd.DataFrame(columns=['chatID', 'totalTokens', 'userMessagesCount', 'botMessagesCount', 'turnsCount'])

        # 3. Data Transformations & Merges
        
        # Convert unix timestamps to datetime
        chats_df['startTime'] = pd.to_datetime(chats_df['startTime'], unit='s', errors='coerce')
        chats_df['endTime'] = pd.to_datetime(chats_df['endTime'], unit='s', errors='coerce')
        
        # Merge domain mapping
        # chats.domainActionID -> domainAction.id
        chats_merged = pd.merge(
            chats_df, 
            domain_action_df[['id', 'title', 'domainId', 'type']].rename(columns={'id': 'domainActionID', 'title': 'actionTitle', 'type': 'actionType'}),
            on='domainActionID', 
            how='left'
        )
        
        # domainAction.domainId -> domain.id
        chats_merged = pd.merge(
            chats_merged,
            domain_df[['id', 'title']].rename(columns={'id': 'domainId', 'title': 'domainTitle'}),
            on='domainId',
            how='left'
        )
        
        # chats.examTitleID -> ExamTitles.id
        chats_merged = pd.merge(
            chats_merged,
            exam_titles_df[['id', 'title']].rename(columns={'id': 'examTitleID', 'title': 'examName'}),
            on='examTitleID',
            how='left'
        )
        
        # tokens and counts
        chats_merged = pd.merge(
            chats_merged,
            chat_stats,
            left_on='id',
            right_on='chatID',
            how='left'
        )
        chats_merged['totalTokens'] = chats_merged['totalTokens'].fillna(0)
        chats_merged['turnsCount'] = chats_merged['turnsCount'].fillna(0)
        chats_merged['userMessagesCount'] = chats_merged['userMessagesCount'].fillna(0)
        chats_merged['botMessagesCount'] = chats_merged['botMessagesCount'].fillna(0)
        
        # Merge transcripts
        if 'transcripts' in locals():
            chats_merged = pd.merge(
                chats_merged,
                transcripts,
                left_on='id',
                right_on='chatID',
                how='left',
                suffixes=('', '_tr')
            )
            
        # Merge performance
        if 'performances' in locals():
            chats_merged = pd.merge(
                chats_merged,
                performances,
                left_on='id',
                right_on='chatID',
                how='left',
                suffixes=('', '_pf')
            )
        
        # Calculate User First Test Date
        # Find the earliest startTime for each user, but ONLY for completed tests
        completed_only = chats_merged[~chats_merged['resultStatus'].isin(['Did Not Complete']) & chats_merged['resultStatus'].notna()]
        user_first_tests = completed_only.groupby('userID')['startTime'].min().reset_index()
        user_first_tests.rename(columns={'startTime': 'firstTestDate'}, inplace=True)
        
        # Merge this back into users dataframe
        users_df = pd.merge(users_df, user_first_tests, left_on='id', right_on='userID', how='left')
        
        # For tests that are missing a score, fill with 0 or handle appropriately
        chats_merged['overallScore'] = chats_merged['overallScore'].fillna(0)
        
        return {
            "users": users_df,
            "chats": chats_merged
        }

    finally:
        # Cleanup the temp directory if one was created
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)
