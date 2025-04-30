"""
This script compares files in two GTFS feed folders and summarizes differences at various detail levels.
"""

import os
import pandas as pd 
from difflib import unified_diff
from collections import defaultdict

# -------------------------------------------
# Define Input Folders
# -------------------------------------------

input_folders = [
    '',
    ''
]

# -------------------------------------------
# Function to resolve  file encoding issues
# -------------------------------------------

def read_file_with_fallback(file_path):
   
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.readlines()
        
# -------------------------------------------
# Function to compare files in two folders 
# -------------------------------------------

def compare_folders(folder1, folder2):
   
    folder1_files = {f: os.path.join(folder1, f) for f in os.listdir(folder1)}
    folder2_files = {f: os.path.join(folder2, f) for f in os.listdir(folder2)}

    all_files = set(folder1_files.keys()).union(folder2_files.keys())

    changes_summary = {}
    for file in all_files:
        file1_path = folder1_files.get(file)
        file2_path = folder2_files.get(file)

        if file1_path and file2_path:
            f1_lines = read_file_with_fallback(file1_path)
            f2_lines = read_file_with_fallback(file2_path)
            diff = list(unified_diff(f1_lines, f2_lines, lineterm=''))

            if diff:  
                changes_summary[file] = summarize_file_changes(diff, file1_path, file2_path)
            else:
                changes_summary[file] = {"status": "No Changes"}
        elif file1_path:
            changes_summary[file] = {"status": "Removed"}
        elif file2_path:
            changes_summary[file] = {"status": "Added"}

    return changes_summary

# -------------------------------------------
# Function to summarize changed
# -------------------------------------------

def summarize_file_changes(diff, file1_path, file2_path):
    changes = {
        "added": [],
        "removed": [],
        "context_blocks": 0,
        "attribute_changes": defaultdict(list)
    }

    for line in diff:
        if line.startswith('@@'):
            changes["context_blocks"] += 1
        elif line.startswith('+') and not line.startswith('+++'):
            changes["added"].append(line.strip())
        elif line.startswith('-') and not line.startswith('---'):
            changes["removed"].append(line.strip())

    if file1_path.endswith('.txt') and file2_path.endswith('.txt'):
        try:
            # Read files forcing all columns to be strings
            df1 = pd.read_csv(file1_path, dtype=str)
            df2 = pd.read_csv(file2_path, dtype=str)

            common_columns = set(df1.columns).intersection(df2.columns)

            for col in common_columns:
                for idx, (val1, val2) in enumerate(zip(df1[col], df2[col])):
                    val1_nan, val2_nan = pd.isna(val1), pd.isna(val2)

                    # Only report if exactly one is nan, or both non-nan and different
                    if (val1_nan != val2_nan) or (not val1_nan and not val2_nan and val1 != val2):
                        changes["attribute_changes"][col].append((idx, val1, val2))

        except Exception as e:
            changes["error"] = f"Error comparing attributes: {str(e)}"

    return changes

# -------------------------------------------
# Granularity level functions
# -------------------------------------------

def display_high_level_summary(changes_summary):
   
    print("High-Level Summary:")
    for file, changes in changes_summary.items():
        status = changes.get("status", "Modified")
        print(f" - {file}: {status}")

def display_mid_level_summary(changes_summary):
   
    print("Mid-Level Summary:")
    for file, changes in changes_summary.items():
        if changes.get("status"):
            print(f"File: {file}")
            print(f" - Status: {changes['status']}")
        else:
            print(f"File: {file}")
            print(f" - Added Lines: {len(changes['added'])}")
            print(f" - Removed Lines: {len(changes['removed'])}")
            print(f" - Modified Sections: {changes['context_blocks']}")
            if "attribute_changes" in changes:
                for attr, changes_list in changes["attribute_changes"].items():
                    print(f"   - Changes in {attr}: {len(changes_list)} changes")
                    
def display_detailed_changes(file_name, changes):
    
    print(f"\nDetailed Changes for {file_name}:")
    if changes.get("status"):
        print(f" - Status: {changes['status']}")
    else:
        print(f" - Added Lines: {len(changes['added'])}")
        for line in changes['added']:
            print(f"   + {line}")
        print(f" - Removed Lines: {len(changes['removed'])}")
        for line in changes['removed']:
            print(f"   - {line}")
        print(f" - Modified Sections: {changes['context_blocks']}")
        if "attribute_changes" in changes:
            print(" - Attribute-Level Changes:")
            for attr, changes_list in changes["attribute_changes"].items():
                print(f"   Attribute: {attr}")
                for idx, old_val, new_val in changes_list:
                    print(f"     Row {idx}: {old_val} → {new_val}")

# -------------------------------------------
# Save change log
# -------------------------------------------

def save_change_log(changes_summary, output_file):
   
    with open(output_file, 'w') as f:
        f.write("Change Log\n")
        for file, changes in changes_summary.items():
            f.write(f"File: {file}\n")
            if changes.get("status"):
                f.write(f" - Status: {changes['status']}\n")
            else:
                f.write(f" - Added Lines: {len(changes['added'])}\n")
                f.write(f" - Removed Lines: {len(changes['removed'])}\n")
                f.write(f" - Modified Sections: {changes['context_blocks']}\n")
                if "attribute_changes" in changes:
                    f.write(" - Attribute-Level Changes:\n")
                    for attr, changes_list in changes["attribute_changes"].items():
                        f.write(f"   Attribute: {attr}\n")
                        for idx, old_val, new_val in changes_list:
                            f.write(f"     Row {idx}: {old_val} → {new_val}\n")
    print(f"Change log saved to {output_file}.")

# -------------------------------------------
# Interactive Menu
# -------------------------------------------

def interactive_menu(changes_summary):
    
    print("Select granularity level:")
    print("1. High-Level Summary")
    print("2. Mid-Level Summary")
    print("3. Detailed View")
    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == '1':
        display_high_level_summary(changes_summary)
    elif choice == '2':
        display_mid_level_summary(changes_summary)
    elif choice == '3':
        for file, changes in changes_summary.items():
            display_detailed_changes(file, changes)
    else:
        print("Invalid choice. Defaulting to high-level summary.")
        display_high_level_summary(changes_summary)

    further_choice = input("\nDo you want detailed changes for a specific file? (yes/no): ").strip().lower()
    if further_choice == 'yes':
        file_name = input("Enter the file name: ").strip()
        if file_name in changes_summary:
            display_detailed_changes(file_name, changes_summary[file_name])
        else:
            print(f"No changes found for {file_name}.")

    save_choice = input("\nSave the change log to a file? (yes/no): ").strip().lower()
    if save_choice == 'yes':
        output_file = input("Enter the output file name (e.g., changelog.txt): ").strip()
        save_change_log(changes_summary, output_file)

if __name__ == "__main__":
    folder1, folder2 = input_folders

    changes_summary = compare_folders(folder1, folder2)
    interactive_menu(changes_summary)
