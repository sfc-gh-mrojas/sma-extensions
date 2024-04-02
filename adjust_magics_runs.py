#!/usr/bin/python3
"""
Script Name: adjust_magics_runs.py

Description:
    This script recursively processes a folder, adjusting magic RUN blocks within the files. It looks for magic RUN blocks
    and transforms them into python imports like: 
        from file import *
    NOTE: you might need to run a script first to make sure filenames are proper python module names

Command-line Arguments:
    - input_path (str): Path to the folder to process. This is a required argument.

Usage Example:
    python adjust_magics_runs.py /path/to/folder
"""



import os
import re

def fix_filename(file:str)->str:
    # Replace spaces with underscores in the file name
    new_file_name = file.replace(' ', '_').replace('-','_').replace('___','_').replace('__','_')
    new_file_name = new_file_name.replace('.','_').replace('___','_').replace('__','_')
    return new_file_name

def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    j = 0
    modified_lines = []
    for line in lines:
        # Check for the pattern and replace accordingly
        match = re.search(r'# MAGIC %run (.*)', line)
        if match:
            j = j + 1
            module_import = match.group(1).strip().replace('"','').strip()
            file_path_components = module_import.split('/')
            file_path_components[-1] = fix_filename(file_path_components[-1])
            if file_path_components[0] == '.':
                module_name = '.'.join(file_path_components[1:]).strip()
                modified_lines.append(f'from .{module_name} import *\n')
            elif file_path_components[0] == '..':
                module_name = '.'.join(file_path_components[1:]).strip()
    
                modified_lines.append(f'from ..{module_name} import *\n')
            else:
                module_name = '.'.join(file_path_components).strip()
                modified_lines.append(f'from {module_name} import *\n')
        else:
            modified_lines.append(line)

    with open(file_path, 'w') as file:
        file.writelines(modified_lines)
    if j == 0:
        print("===# no run magics")
    else:
        print(f"===> {j} run magics found and adjusted")

def process_folder(folder_path):
    print(f"Procesing {folder_path}")
    i = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                print(f"==>Processing file: {file}")
                file_path = os.path.join(root, file)
                process_file(file_path)
                i = i + 1
    print(f"Processed files: {i}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A script to recursively adjust magic RUN blocks in a folder.")

    # Required argument
    parser.add_argument("input_path", metavar="input_path", type=str, help="Path to the folder to process.")
    args = parser.parse_args()
    process_folder(args.input_path)
