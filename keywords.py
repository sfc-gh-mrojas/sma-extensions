import os
import re
import argparse
import logging
import csv
from rich.console import Console
import yaml

import nbformat

keyword_list = []

def analyze_jupyter_notebook(file_path, keywords):
    # Read the Jupyter notebook
    with open(file_path, 'r', encoding='utf-8') as f:
        total_cells = 0
        keyword_counts = {keyword: 0 for keyword in keywords}
        notebook_content = nbformat.read(f, as_version=4)
        # Iterate through each cell in the notebook
        for cell in notebook_content['cells']:
            total_cells += 1
            # Get the source code of the cell
            source_code = cell['source']
            # Split the source code into lines
            lines = source_code.split('\n')
            for line in lines:
                count_keywords_in_line(keyword_counts, keywords, line)
        return keyword_counts

def setup_logging(log_file):
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def is_excluded(name, exclude_patterns):
    for pattern in exclude_patterns:
        if re.search(pattern, name):
            return True
    return False

def map_technology(extension):
    technology_mappings = {
        '.r': 'R',
        '.rmd': 'RMD',
        '.ipynb':'Notebook',
        '.py': 'Python',
        '.scala': 'Scala',
        '.java': 'Java',
        '.sh': 'Shell',
        '.zsh': 'Shell',
        '.bash': 'Shell',
        '.ps1': 'Shell',
        '.sql': 'SQL',
        '.text': 'TXT',
        '.json':'DATA',
        '.yml':'CONFIG',
        '.yaml':'CONFIG',
        '.config':'CONFIG',
        '.properties':'CONFIG',
        '.xml':'DATA',
        '.csv':'DATA',
        '.md':'DOC',
        '.html':'DOC'
    }
    return technology_mappings.get(extension.lower(), "Unknown")

text_files = ('.Rmd','.r','.R', '.py', '.scala', '.java','.sh', '.zsh', '.bash', '.ps1', '.sql', '.text', '.json', '.yml', '.yaml')
line_comments_by_extension = {
    ".R":"#",
    ".py":"#",
    ".scala":"//",
    ".java":"//",
    ".sh": "#",
    ".zsh": "#",
    ".bash": "#",
    ".ps1":"#",
    ".sql":"--"
}

def count_keywords_in_line(keyword_counts, keywords, line):
    line = line.strip()
    if line=="" or line.startswith("#"):
        return
    words = re.split('\.|,|;|\(|\)|\[|\]|\{|\}', line)
    for word in words:
        if word:
            if word in keywords:
                keyword_counts[word] += 1    

def count_keywords(filename, keywords):
    keyword_counts = {keyword: 0 for keyword in keywords}
    try:
        with open(filename, 'r') as file:
            for line in file:
                count_keywords_in_line(keyword_counts, keywords, line)
        return keyword_counts
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")
        return None


def process_file(keyword_list,file_path,root):
    try:
        if os.path.isfile(file_path):

            if file_path.endswith(".ipynb"):
                return analyze_jupyter_notebook(file_path, keyword_list)
            elif file_path.endswith(text_files):
                return count_keywords(file_path, keyword_list)
            
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")
        return None

def scan_folders(folder_config, keywords_list, output_csv):
    console = Console()

    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            'File','Technology','Keyword','Count'
        ]
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for config in folder_config:
            root_path = config.get("root_path", "")
            root_path_label = config.get("root_path_label", "")
            exclude_folders = config.get("exclude_folders", [])
            exclude_files = config.get("exclude_files", [])

            console.print(f"[bold magenta]Scanning folder:[/bold magenta] {root_path}")
            logging.info(f"Scanning folder: {root_path}")

            for folder in os.listdir(root_path):
                folder_path = os.path.join(root_path, folder)
                if os.path.isfile(folder_path) and not is_excluded(folder_path, exclude_files):
                    do_file_processing(keywords_list,root_path,"", csv_writer, folder_path)
                elif os.path.isdir(folder_path) and not is_excluded(folder, exclude_folders):
                    for root, dirs, files in os.walk(folder_path):
                        current_path = root
                        dirs[:] = [d for d in dirs if not is_excluded(d, exclude_folders)]
                        files = [f for f in files if not is_excluded(f, exclude_files)]

                        for file in files:
                            do_file_processing(keywords_list,root_path,os.path.relpath(current_path,root_path),csv_writer, file)

def do_file_processing(keywords_list,root_path,folder_path,csv_writer, file):
    file_path = os.path.join(root_path,folder_path, file)
    logging.info(f"Processing file: {file_path}")

    try:
        keywords_info = process_file(keywords_list,file_path, root_path)
        if keywords_info is not None:
            filename, extension = os.path.splitext(os.path.basename(file_path))
            for key in keywords_info.keys():
                count = keywords_info[key]
                if count:
                    # only write non-zero 
                    file_info = {
                        'File':file_path,
                        'Technology': map_technology(extension.lower()),
                        'Keyword':key,
                        'Count':keywords_info[key]
                    }
                    csv_writer.writerow(file_info)
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")

def main():
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration and generate CSV.")
    parser.add_argument("config_file", help="Path to the YAML configuration file")
    parser.add_argument("output_folder", help="Folder for all the tool output")
    #parser.add_argument("output_csv", help="Path to the output CSV file",default="FilesInventory.csv")

    args = parser.parse_args()
    output_folder = args.output_folder
    output_csv = os.path.join(output_folder, "Reports","GenericScanner","GenericScannerOutput","Keywords.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","keywords.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True);
    setup_logging(log_file)


    try:
        with open(args.config_file, "r") as file:
            config = yaml.safe_load(file)
            folder_config = config.get("folders", [])
            keyword_list = config.get("keywords", [])

            scan_folders(folder_config,keyword_list, output_csv)

    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config_file}' not found.")
        logging.error(f"Configuration file '{args.config_file}' not found.")
    except yaml.YAMLError as e:
        print(f"Error in YAML file: {e}")
        logging.error(f"Error in YAML file: {e}")

if __name__ == "__main__":
    main()
