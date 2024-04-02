#!/usr/bin/python3
"""
Script Name: rename_files.py

Description:
    This script recursively processes a folder, adjusting file names. 
    Usually files have names with spaces or special characters like dot or dash and they are
    not valid for python modules.

Command-line Arguments:
    - input_path (str): Path to the folder to process. This is a required argument.

Usage Example:
    python rename_files.py /path/to/folder
"""

import os

def fix_filename(file:str)->str:
    # Replace spaces with underscores in the file name
    new_file_name = file.replace(' ', '_').replace('-','_').replace('___','_').replace('__','_')
    new_file_name, ext = os.path.splitext(new_file_name)
    new_file_name = new_file_name.replace('.','_').replace('___','_').replace('__','_')
    new_file_name = new_file_name + ext
    return new_file_name

def replace_spaces(folder_path):
    # Iterate through all files and directories in the given folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Construct the current file's full path
            current_file_path = os.path.join(root, file)
            new_file_name = fix_filename(file)
            # Construct the new file's full path
            new_file_path = os.path.join(root, new_file_name)
            
            # Rename the file if there's a difference
            if current_file_path != new_file_path:
                os.rename(current_file_path, new_file_path)
                print(f"Renamed: '{current_file_path}' to '{new_file_path}'")

# Example usage

import argparse

parser = argparse.ArgumentParser(description="A script to recursively rename a file if it has spaces.")

# Required argument
parser.add_argument("input_path", metavar="input_path", type=str, help="Path to the folder to process.")


args = parser.parse_args()
replace_spaces(args.input_path)


