#!/usr/bin/python3
import os
import re
import argparse
import logging
import csv
from rich.console import Console
import yaml
import ast

import nbformat
# Regular expression to match library or require statements
r_lib_pattern = re.compile(r'\b(?:library|require)\(([^\)]+)\)', re.IGNORECASE)
# Regular expression to match Java import statements
java_import_pattern = re.compile(r'\bimport\s+(static\s+)?([\w.]+)\s*;')

# Define regular expressions for different import patterns in scala
import_pattern_scala = re.compile(r'^\s*import\s+([^\s]+(\.[^\s]+)*)\s*$')
from_import_pattern_scala = re.compile(r'^\s*import\s+([^\s]+(\.[^\s]+)*)(\.|\s)({[^}]+}|[^\s]+)\s*$')


def extract_import_info_py(code_line, line):
    try:
        # Parse the code into an abstract syntax tree
        tree = ast.parse(code_line)
        # Iterate through the nodes in the tree
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Handle "import module" statements
                for alias in node.names:
                    yield (alias.name, line, alias.asname, code_line, alias.name)

            elif isinstance(node, ast.ImportFrom):
                # Handle "from module import name" statements
                module_name = node.module
                for alias in node.names:
                    yield (module_name + "." + alias.name, line, alias.asname, code_line, module_name)

    except Exception as e:
        yield None

def extract_import_info_scala(statement, line):
    # Check for "import" statements
    import_match = import_pattern_scala.match(statement)
    if import_match:
        module_path = import_match.group(1)
        yield (module_path,line,"",statement,module_path)

    # Check for "import from" statements
    from_import_match = from_import_pattern_scala.match(statement)
    if from_import_match:
        module_path = from_import_match.group(1)
        for imp in from_import_match.group(4).strip('{}').split(','):
            yield (imp,line,"",statement,module_path)

# yields ElementName, Line, Alias, Statement, ElementPackage
def collect_import_info(extension,statement, line):
    if extension == ".r":
        match = r_lib_pattern.match(statement)
        if match:
            alias = ""
            elementpackage = ""
            elementname = match.group(1)
            yield (elementname,line,alias,statement,elementpackage)
    elif extension == ".java":
        matches = java_import_pattern.findall(statement)
        for import_statement in matches:
            alias = ""
            elementpackage = ""
            elementname = import_statement[1]
            yield (elementname,line,alias,statement,elementpackage)
    elif extension == ".py":
        if "import " in statement:
            yield from extract_import_info_py(statement, line)
    elif extension == ".scala":
        if "import " in statement:
            yield from extract_import_info_scala(statement, line)

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

text_files = ('.rmd','.r','.R', '.py', '.scala', '.java')

def process_file(file_path,root):
    imports_info = []
    try:
        if os.path.isfile(file_path):
            
            # Process code files for lines of code and comments
            if file_path.endswith(text_files):
                rel_path = file_path[len(root):]
                filename, extension = os.path.splitext(os.path.basename(file_path))
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        for info in collect_import_info(extension.lower(),line,i):
                            if info:
                                Element, Line, Alias, Statement, ElementPackage = info
                                imports_info.append(
                                    {
                                        "Element":Element,
                                        "ProjectId":"ProjectId",
                                        "FileId":file_path,
                                        "Count":"1",
                                        "Alias":Alias,
                                        "Kind":"",
                                        "Line":Line,
                                        "PackageName":ElementPackage,
                                        "Supported":"",
                                        "Automated":"",
                                        "Status":"",
                                        "Statement":Statement,
                                        "SessionId":"",
                                        "SnowConvertCoreVersion":"",
                                        "SnowparkVersion":"",
                                        "ElementPackage":""
                                    }
                                )
            
            return imports_info
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")
        return None

def scan_folders(folder_config, output_csv):
    console = Console()

    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            "Element","ProjectId","FileId","Count","Alias",
            "Kind","Line","PackageName","Supported","Automated","Status",
            "Statement","SessionId","SnowConvertCoreVersion","SnowparkVersion","ElementPackage"
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
        imports_info = process_file(file_path, root_path)
        if imports_info is not None:
            for import_detail in imports_info:
                csv_writer.writerow(import_detail)
    except Exception as e:
        logging.error(f"Error processing file: {file_path} - {e}")

def main():
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration and generate CSV about imports.")
    parser.add_argument("config_file",   help="Path to the YAML configuration file")
    parser.add_argument("output_folder", help="Folder for all the tool output")
    #parser.add_argument("output_csv", help="Path to the output CSV file",default="ImportUsagesInventory.csv")

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
