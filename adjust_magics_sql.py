#!/usr/bin/python3
"""
Script Name: adjust_magics_sql.py

Description:
    This script recursively processes a folder, adjusting magic SQL blocks within the files. It looks for magic SQL blocks
    and transforms them into Spark SQL blocks using session.sql(\"\"\" sql \"\"\").show(). The script takes the following
    command-line arguments:

Command-line Arguments:
    - input_path (str): Path to the folder to process. This is a required argument.

    -s, --session_variable (str, optional, default='session'):
        Specify the session variable name used when changing magic SQL fragments to Spark SQL blocks.
        The default session variable name is 'session'.

Usage Example:
    python adjust_magics_sql.py /path/to/folder -s custom_session_var
"""
import os
import sys

def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    new_lines = []
    inside_magic_block = False

    for line in lines:
        if not inside_magic_block and '# MAGIC %sql' in line:
            inside_magic_block = True
            new_lines.append('session.sql("""')
            continue
        elif inside_magic_block and line.strip() == '':
            inside_magic_block = False
            new_lines.append('""").show()\n')
            continue

        if inside_magic_block:
            # Replace '# MAGIC' with ''
            line = line.replace('# MAGIC', '')
        new_lines.append(line)
    if inside_magic_block:
        new_lines.append('""").show()\n')
    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.writelines(new_lines)

def process_folder(folder_path):
    print(f"Processing folder {folder_path}")
    i = 0
    for foldername, subfolders, filenames in os.walk(folder_path):
        print(f"Processing {len(filenames)}")
        for filename in filenames:
            print(f"==>Processing file: {filename}")
            if filename.endswith('.py'):
                file_path = os.path.join(foldername, filename)
                process_file(file_path)
                i = i + 1
    print(f"Processed {i} files")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A script to recursively adjust magic SQL blocks in a folder.")

    # Required argument
    parser.add_argument("input_path", metavar="input_path", type=str, help="Path to the folder to process.")

    # Optional argument for session variable name
    parser.add_argument("-s", "--session_variable", metavar="session_variable", type=str, default="session",
                        help="Specify the session variable name used when changing magic SQL fragments. Default is 'session'.")

    args = parser.parse_args()
    process_folder(args.input_path)
    print("Done")
