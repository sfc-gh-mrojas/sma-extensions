import os
import re
import argparse
import logging
import yaml
from rich.console import Console
import csv

def collect_dependencies(gradle_file):
    dependencies = list()
    print(f"Processing file: {gradle_file}")
    with open(gradle_file, 'r') as file:
        content = file.read()
        # Regex to match dependencies
        dependency_pattern = re.compile(r"(\w+)\s+['\"](.*?):(.*?):(.*?)['\",]")
        matches = dependency_pattern.findall(content)
        for match in matches:
            if len(match)==4:
                scope, group, artifact, version = match
                dependencies.append({"scoope":scope, "group":group.strip(), "artifact":artifact.strip(), "version":version.strip()})
        dependency_pattern = re.compile(r"(\w+)\s+group:(.*?),\s*name:(.*?),\s*version:\s*(.*)['\",]?")
        matches = dependency_pattern.findall(content)
        for match in matches:
            if len(match)==4:
                scope, group, artifact, version = match
                dependencies.append({"scope":scope,"group":group.strip(), "artifact":artifact.strip(), "version":version.strip()})
    return dependencies

def find_gradle_files(root_dir):
    gradle_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.gradle'):
                gradle_files.append(os.path.join(root, file))
    return gradle_files

all_dependencies = set()

def process_file(gradle_file,root_path):
    return collect_dependencies(gradle_file)
    
def setup_logging(log_file):
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def is_excluded(name, exclude_patterns):
    for pattern in exclude_patterns:
        if re.search(pattern, name):
            return True
    return False

def scan_folders(folder_config, output_csv):
    console = Console()

    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            'FileName', 'scope','group', 'artifact', 'version'
        ]
        csv.register_dialect('pipes', delimiter='|',quoting=csv.QUOTE_NONE,escapechar='\\')
        csv_writer = csv.DictWriter(csv_file, dialect="pipes",fieldnames=fieldnames)
        csv_writer.writeheader()

        for config in folder_config:
            root_path = config.get("root_path", "")
            exclude_folders = config.get("exclude_folders", [])
            exclude_files = config.get("exclude_files", [])

            console.print(f"[bold magenta]Scanning folder:[/bold magenta] {root_path}")
            logging.info(f"Scanning folder: {root_path}")

            for folder in os.listdir(root_path):
                folder_path = os.path.join(root_path, folder)
                if os.path.isfile(folder_path) and not is_excluded(folder_path, exclude_files) and folder_path.endswith('.gradle'):
                    do_file_processing(root_path,"", csv_writer, folder_path)
                elif os.path.isdir(folder_path) and not is_excluded(folder, exclude_folders):
                    for root, dirs, files in os.walk(folder_path):
                        current_path = root
                        dirs[:] = [d for d in dirs if not is_excluded(d, exclude_folders)]
                        files = [f for f in files if not is_excluded(f, exclude_files) and f.endswith('.gradle')]

                        for file in files:
                            do_file_processing(root_path,os.path.relpath(current_path,root_path),csv_writer, file)

def do_file_processing(root_path,folder_path,csv_writer, file):
    file_path = os.path.join(root_path,folder_path, file)
    logging.info(f"Processing file: {file_path}")

    try:
        file_info = process_file(file_path, root_path)
        if file_info is not None:
            for record in file_info:
                record["FileName"]=file_path
                csv_writer.writerow(record)
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")


def main():
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration to collect grandle info and generate CSV.")
    parser.add_argument("config_file", help="Path to the YAML configuration file")
    parser.add_argument("output_folder", help="Folder for all the tool output")

    args = parser.parse_args()


    output_folder = args.output_folder
    output_csv = os.path.join(output_folder, "Reports","gradle_dependencies.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","gradle_dependencies.log")
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

