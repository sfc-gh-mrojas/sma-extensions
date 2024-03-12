import os
import re
import argparse
import logging
import yaml
from rich.console import Console
import csv
import xml.etree.ElementTree as ET
import javalang

def is_sql_statement(input_string):
    keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
    for keyword in keywords:
        if keyword in input_string.upper():
            return True
    return False

def extract_strings_from_method(method_node):
    tokens = []
    for path,node in method_node.filter(javalang.tree.Literal):
        if isinstance(node.value, str):
            tokens.append(node)
    return tokens

def get_class_name(path):
    for node in reversed(path):
        if isinstance(node, javalang.tree.ClassDeclaration):
            return node.name
    return "Unknown"

def is_inside_method(path):
    for node in reversed(path):
        if isinstance(node, javalang.tree.ClassDeclaration):
            return False
        if isinstance(node, javalang.tree.MethodDeclaration):
            return True
    return False

def extract_strings_from_java_file(file_path):
    with open(file_path, 'r') as file:
        java_code = file.read()

    tokens = []
    try:
        tree = javalang.parse.parse(java_code)
        for path, node in tree:
            if isinstance(node, javalang.tree.VariableDeclarator):
                field_name = node.name
                class_name = get_class_name(path)
                if is_inside_method(path):
                    continue
                mytokens = extract_strings_from_method(node)
                for token in mytokens:
                    if  is_sql_statement(token.value):
                        tokens.append({"class_name":class_name,
                                       "field_name":field_name,
                                       "line":token.position.line,
                                       "column":token.position.column,
                                       "length":len(token.value)
                                       })
            if isinstance(node, javalang.tree.MethodDeclaration):
                method_name = node.name
                class_name = get_class_name(path)
                mytokens = extract_strings_from_method(node)
                for token in mytokens:
                    if  is_sql_statement(token.value):
                        tokens.append({"class_name":class_name,
                                       "method_name":method_name,
                                       "line":token.position.line,
                                       "column":token.position.column,
                                       "length":len(token.value)
                                       })
    except javalang.parser.JavaSyntaxError as e:
        logging.error(f"Syntax error [{e.description} at {e.at}] in file: {file_path}")
    
    return tokens


def process_file(maven_file,root_path):
    return extract_strings_from_java_file(maven_file)
    
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
            'FileName', 'class_name','field_name','method_name','line','column', 'length'
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
                if os.path.isfile(folder_path) and not is_excluded(folder_path, exclude_files) and folder_path.endswith('.java'):
                    do_file_processing(root_path,"", csv_writer, folder_path)
                elif os.path.isdir(folder_path) and not is_excluded(folder, exclude_folders):
                    for root, dirs, files in os.walk(folder_path):
                        current_path = root
                        dirs[:] = [d for d in dirs if not is_excluded(d, exclude_folders)]
                        files = [f for f in files if not is_excluded(f, exclude_files) and f.endswith('.java')]
                        for file in files:
                            do_file_processing(root_path,os.path.relpath(current_path,root_path),csv_writer, file)

def do_file_processing(root_path,folder_path,csv_writer, file):
    file_path = os.path.join(root_path,folder_path, file)
    logging.info(f"Processing file: {file_path}")
    try:
        file_info = process_file(file_path, root_path)
        if file_info:
            for record in file_info:
                record["FileName"]=file_path
                csv_writer.writerow(record)
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")

def main():
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration to collect strings info and generate CSV.")
    parser.add_argument("config_file", help="Path to the YAML configuration file")
    parser.add_argument("output_folder", help="Folder for all the tool output")

    args = parser.parse_args()


    output_folder = args.output_folder
    output_csv = os.path.join(output_folder, "Reports","java_strings_possible_sql.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","java_strings_possible_sql.log")
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

