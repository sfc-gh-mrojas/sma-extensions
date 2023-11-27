import os
import re
import argparse
import logging
import csv
from rich.console import Console
import yaml

import nbformat

def analyze_jupyter_notebook(file_path):
    # Read the Jupyter notebook
    with open(file_path, 'r', encoding='utf-8') as f:
        notebook_content = nbformat.read(f, as_version=4)

    # Initialize counters
    total_cells = 0
    total_blank_lines = 0
    total_comment_lines = 0
    total_code_lines = 0

    # Iterate through each cell in the notebook
    for cell in notebook_content['cells']:
        total_cells += 1

        # Get the source code of the cell
        source_code = cell['source']

        # Split the source code into lines
        lines = source_code.split('\n')

        # Count the number of blank lines, comment lines, and code lines
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        code_lines = len(lines) - blank_lines - comment_lines

        # Update the total counters
        total_blank_lines += blank_lines
        total_comment_lines += comment_lines
        total_code_lines += code_lines

    # Return the results
    return {
        'total_cells': total_cells,
        'total_blank_lines': total_blank_lines,
        'total_comment_lines': total_comment_lines,
        'total_code_lines': total_code_lines
    }

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
def process_file(file_path,root):
    try:
        if os.path.isfile(file_path):
            # Extract file information
            filename, extension = os.path.splitext(os.path.basename(file_path))
            is_binary = not bool(re.search(r'\.txt$|\.text$|\.md$|\.json$', extension, re.IGNORECASE))
            byte_size = os.path.getsize(file_path)

            # Determine technology based on file extension
            technology = map_technology(extension)

            # Initialize variables for code lines, comment lines, and blank lines
            code_lines, comment_lines, blank_lines = 0, 0, 0
            if file_path.endswith(".ipynb"):
                data = analyze_jupyter_notebook(file_path)
                code_lines = data['total_code_lines']
                comment_lines = data['total_comment_lines']
                blank_lines  = data['total_blank_lines']
            # Process code files for lines of code and comments
            if file_path.endswith(text_files):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if extension in line_comments_by_extension:
                        line_comment_mark = line_comments_by_extension[extension]
                        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith(line_comment_mark))
                        comment_lines = sum(1 for line in lines if line.strip().startswith(line_comment_mark))
                        blank_lines = sum(1 for line in lines if not line.strip())
                    else:
                        line_comment_mark = "#"
                        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith(line_comment_mark))
                        comment_lines = None
                        blank_lines = sum(1 for line in lines if not line.strip())
            rel_path = file_path[len(root):]
            return {
                'FileName': file_path,
                'Extension': extension,
                'Technology': technology,
                'Status': None,  # You can fill in the status information if needed
                'isBinary': is_binary,
                'Bytes': byte_size,
                'ContentType': None,  # You can fill in the content type information if needed
                'ContentLines': code_lines,
                'CommentLines': comment_lines,
                'BlankLines': blank_lines
            }
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")
        return None

def scan_folders(folder_config, output_csv):
    console = Console()

    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            'FileName', 'Extension', 'Technology', 'Status', 'isBinary',
            'Bytes', 'ContentType', 'ContentLines', 'CommentLines', 'BlankLines'
        ]
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for config in folder_config:
            root_path = config.get("root_path", "")
            exclude_folders = config.get("exclude_folders", [])
            exclude_files = config.get("exclude_files", [])

            console.print(f"[bold magenta]Scanning folder:[/bold magenta] {root_path}")
            logging.info(f"Scanning folder: {root_path}")

            for folder in os.listdir(root_path):
                folder_path = os.path.join(root_path, folder)
                if os.path.isfile(folder_path) and not is_excluded(folder_path, exclude_files):
                    do_file_processing(root_path,"", csv_writer, folder_path)
                elif os.path.isdir(folder_path) and not is_excluded(folder, exclude_folders):
                    for root, dirs, files in os.walk(folder_path):
                        current_path = root
                        dirs[:] = [d for d in dirs if not is_excluded(d, exclude_folders)]
                        files = [f for f in files if not is_excluded(f, exclude_files)]

                        for file in files:
                            do_file_processing(root_path,os.path.relpath(current_path,root_path),csv_writer, file)

def do_file_processing(root_path,folder_path,csv_writer, file):
    file_path = os.path.join(root_path,folder_path, file)
    logging.info(f"Processing file: {file_path}")

    try:
        file_info = process_file(file_path, root_path)
        if file_info is not None:
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
    output_csv = os.path.join(output_folder, "Reports","GenericScanner","GenericScannerOutput","FilesInventory.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","files_inventory.log")
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
