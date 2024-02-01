#!/usr/bin/python3
"""
File: clean_up_folder.py

Description:
    This Python script, 'clean_up_folder.py,' serves as a tool for organizing and cleaning up project folders by removing those containing superfluous files. Configuration details are specified in the 'config.yaml' file, which includes paths to root folders and folders to be ignored during the cleaning process.

Configuration File (config.yaml):
    ```
    folders:
      - root_path: "/path/to/workload1"
      - root_path: "/path/to/workload2"
      - root_path: "/path/to/workload3"
    
    ignore_folders:
      - root_path: .git
      - root_path: .conda
      - root_path: .cache
      - root_path: .build
      - root_path: .env
      - root_path: .local
    ```

    - 'folders': List of root paths for workloads to be processed and cleaned.
    - 'ignore_folders': List of folders to be ignored during the cleaning process.

Usage:
    To execute this script, use the following command:
    ```
    python clean_up_folder.py
    ```
    Note: The script reads configuration details from 'config.yaml.'

File Dependencies:
    - os
    - shutil
    - argparse
    - logging
    - yaml

Note:
    Ensure the script is executed with the necessary permissions for file manipulation.

"""

import os
import shutil
import argparse
import logging
import yaml

def ignore_folders(root_folder, to_ignore, action):
    for folder_name in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder_name)

        if os.path.isdir(folder_path) and folder_name in to_ignore:
            if action == 'remove':
                shutil.rmtree(folder_path)
                print(f"Removed folder: {folder_path}")
            elif action == 'move':
                ignore_folder_path = os.path.join(root_folder, 'ignore_folder')
                shutil.move(folder_path, ignore_folder_path)
                print(f"Moved folder {folder_path} to {ignore_folder_path}")
            else:
                print(f"Invalid action: {action}")

if __name__ == "__main__":
    root_folder = input("Enter the root folder path: ")
    to_ignore = ['.git', '.conda', '.env']
    action = input("Enter the action (remove/move): ")

    ignore_folders(root_folder, to_ignore, action)

def setup_logging(log_file):
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("Code Preprocessing: Input Files Clean up")
    print("========================================")
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration, and remove files that can cause noise during the migration")
    parser.add_argument("config_file",   help="Path to the YAML configuration file")
    parser.add_argument("ignore_folder", help="Folder where all ignored folder will be moved")

    args = parser.parse_args()
    output_folder = args.output_folder

    output_csv = os.path.join(output_folder, "Reports","ImportUsagesInventory.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","imports_scanner.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True);
    setup_logging(log_file)

    try:
        with open(args.config_file, "r") as file:
            config = yaml.safe_load(file)
            folder_config = config.get("folders", [])

            scan_folders(folder_config, output_csv)

    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config_file}' not found.")
        logging.error(f"Configuration file '{args.config_file}' not found.")
    except yaml.YAMLError as e:
        print(f"Error in YAML file: {e}")
        logging.error(f"Error in YAML file: {e}")

if __name__ == "__main__":
    main()
