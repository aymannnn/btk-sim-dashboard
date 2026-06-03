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
    # Create a temporary directory to extract the files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Extract the zip
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # The zip might contain a folder named 'snapshot' or extract files directly.
        # Let's find the directory that contains the CSVs
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
        
        # Load ChatMessages optimized - only need totalTokens per chat
        # Since it's large, we only load specific columns
        try:
            chat_msgs_df = pd.read_csv(
                os.path.join(target_dir, 'ChatMessages.csv'), 
                usecols=['chatID', 'totalTokens'],
                engine='c' # fast parser
            )
            # Aggregate tokens per chat
            tokens_per_chat = chat_msgs_df.groupby('chatID')['totalTokens'].sum().reset_index()
        except Exception as e:
            print(f"Could not load ChatMessages.csv optimally: {e}")
            tokens_per_chat = pd.DataFrame(columns=['chatID', 'totalTokens'])

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
        
        # tokens
        chats_merged = pd.merge(
            chats_merged,
            tokens_per_chat,
            left_on='id',
            right_on='chatID',
            how='left'
        )
        chats_merged['totalTokens'] = chats_merged['totalTokens'].fillna(0)
        
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
        # Cleanup the temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
