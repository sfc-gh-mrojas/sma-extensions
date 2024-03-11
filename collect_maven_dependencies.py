import os
import re
import argparse
import logging
import yaml
from rich.console import Console
import csv
import xml.etree.ElementTree as ET

def collect_dependencies(path):
    dependencies = []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        
        # Define the XML namespace
        namespace = {'ns': 'http://maven.apache.org/POM/4.0.0'}
        
        # Find all dependency tags
        for dependency in root.findall('.//ns:dependency', namespace):
            group_id = dependency.find('ns:groupId', namespace).text
            artifact_id = dependency.find('ns:artifactId', namespace).text
            version = dependency.find('ns:version', namespace).text
            scope = dependency.find('ns:scope', namespace)
            scope_text = scope.text if scope is not None else "compile"  # Default scope is "compile" if not specified
            dependencies.append({"group":group_id,"artifact": artifact_id, "version":version, "scope":scope_text})
            
    except FileNotFoundError:
        logging.error(f"File not found at {path}")
    except ET.ParseError:
        logging.error(f"Error parsing XML file at {path}")
    return dependencies

def find_maven_files(root_dir):
    maven_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('pom.xml'):
                maven_files.append(os.path.join(root, file))
    return maven_files

all_dependencies = set()

def process_file(maven_file,root_path):
    return collect_dependencies(maven_file)
    
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
                if os.path.isfile(folder_path) and not is_excluded(folder_path, exclude_files) and folder_path.endswith('pom.xml'):
                    do_file_processing(root_path,"", csv_writer, folder_path)
                elif os.path.isdir(folder_path) and not is_excluded(folder, exclude_folders):
                    for root, dirs, files in os.walk(folder_path):
                        current_path = root
                        dirs[:] = [d for d in dirs if not is_excluded(d, exclude_folders)]
                        files = [f for f in files if not is_excluded(f, exclude_files) and f.endswith('pom.xml')]

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
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration to collect maven info and generate CSV.")
    parser.add_argument("config_file", help="Path to the YAML configuration file")
    parser.add_argument("output_folder", help="Folder for all the tool output")

    args = parser.parse_args()


    output_folder = args.output_folder
    output_csv = os.path.join(output_folder, "Reports","maven_dependencies.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","maven_dependencies.log")
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

