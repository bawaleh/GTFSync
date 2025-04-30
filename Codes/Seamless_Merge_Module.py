"""
This script compares applies suffixes to all unique identifiers and merges files 
"""

import os
import pandas as pd

# -------------------------------------------
# Define Input Folders
# -------------------------------------------

input_folders = [
    '',
    ''
]

# Corresponding suffixes for each feed (Ensure same number as input_folders)
suffixes = ['Feed_1', 'Feed_2']

# ----------------------------------------------
# Function to load data from a GTFS feed folder
# ----------------------------------------------

def load_gtfs_files(folder):
    files = ['stop_times.txt', 'trips.txt', 'stops.txt', 
             'calendar_dates.txt', 'calendar.txt', 'routes.txt', 
             'agency.txt', 'shapes.txt']
    data = {}
    for file in files:
        path = os.path.join(folder, file)
        if os.path.exists(path):
            data[file] = pd.read_csv(path)
        else:
            print(f"File {file} not found in {folder}, skipping.")
    return data

# --------------------------------------------------
# Function to add suffixes to identifiers in a feed
# --------------------------------------------------

def add_suffix_to_feed(feed_data, suffix):
    updated_feed = {}
    for file_name, df in feed_data.items():
        df = df.copy()  # Avoid modifying the original DataFrame
        for col in df.columns:
            if col in ['direction_id']:
                continue
            if '_id' in col:
                df[col] = df[col].apply(lambda x: f"{x}_{suffix}" if pd.notnull(x) else x)
        updated_feed[file_name] = df
    return updated_feed

# --------------------------------------------------
# Function to merge multiple feeds
# --------------------------------------------------

def merge_feeds(feed_data_list):
    merged_data = {file: [] for file in ['stop_times.txt', 'trips.txt', 'stops.txt', 
                                         'calendar_dates.txt', 'calendar.txt', 
                                         'routes.txt', 'agency.txt', 'shapes.txt']}

    for feed_data in feed_data_list:
        for file_name, df in feed_data.items():
            merged_data[file_name].append(df)

    merged_result = {}
    for file_name, dataframes in merged_data.items():
        if dataframes:  # Only merge if data is available for the file
            merged_result[file_name] = pd.concat(dataframes, ignore_index=True)

    return merged_result

# --------------------------------------------------
# Main Execution
# --------------------------------------------------

if __name__ == "__main__":
    if len(input_folders) != len(suffixes):
        raise ValueError("The number of feed folders and suffixes must match.")

    suffixed_feeds = []

    for folder, suffix in zip(input_folders, suffixes):
        print(f"\nLoading GTFS data from: {folder}")
        feed_data = load_gtfs_files(folder)

        print(f"Applying suffix '{suffix}' to feed data")
        suffixed_feed_data = add_suffix_to_feed(feed_data, suffix)

        suffixed_feeds.append(suffixed_feed_data)

    print("\nMerging feeds...")
    merged_data = merge_feeds(suffixed_feeds)

# --------------------------------------------------
# Define Output Folder
# --------------------------------------------------

    output_folder = ''
    os.makedirs(output_folder, exist_ok=True)

    for file_name, df in merged_data.items():
        output_path = os.path.join(output_folder, file_name)
        df.to_csv(output_path, index=False)
        print(f"Merged {file_name} saved to {output_path}")
