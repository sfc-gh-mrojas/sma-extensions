#!/usr/bin/python3



import os
import re

def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        # Check for the pattern and replace accordingly
        match = re.search(r'# MAGIC %run \.\.\/(.*)', line)
        if match:
            file_path_components = match.group(1).split('/')
            module_name = '.'.join(file_path_components).replace("-","_").strip()
            modified_lines.append(f'from ..{module_name} import *\n')
        else:
            match = re.search(r'# MAGIC %run \./(.*)', line)
            if match:
                file_path_components = match.group(1).split('/')
                module_name = '.'.join(file_path_components).replace("-","_").strip()
                modified_lines.append(f'from {module_name} import *\n')
            else:
                match = re.search(r'# MAGIC %run (.*)', line)
                if match:
                    file_path_components = match.group(1).split('/')
                    module_name = '.'.join(file_path_components).replace("-","_").strip()
                    modified_lines.append(f'from {module_name} import *\n')
                else:                
                    modified_lines.append(line)

    with open(file_path, 'w') as file:
        file.writelines(modified_lines)

def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                process_file(file_path)

if __name__ == "__main__":

    process_folder(args.input_path)
