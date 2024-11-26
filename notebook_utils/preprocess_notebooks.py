import os
import re
import argparse
import nbformat
import csv

found_imports = []
widgets_info = []
sql_magics_info = ""

def convert_to_notebook(processed_lines, notebook_path):
    notebook_cells = []
    current_cell_lines = []

    for line in processed_lines:
        if line.strip() == "# COMMAND ----------":
            if current_cell_lines:
                notebook_cells.append(nbformat.v4.new_code_cell("".join(current_cell_lines)))
                current_cell_lines = []
        else:
            current_cell_lines.append(line)
    
    # Add the last cell if there are remaining lines
    if current_cell_lines:
        notebook_cells.append(nbformat.v4.new_code_cell("".join(current_cell_lines)))

    # Create a notebook structure
    notebook = nbformat.v4.new_notebook()
    notebook.cells = notebook_cells

    # Write the notebook to the target path
    os.makedirs(os.path.dirname(notebook_path), exist_ok=True)
    with open(notebook_path, 'w') as f:
        nbformat.write(notebook, f)

def process_file(file_path, source_path, target_path, output_format):
    global sql_magics_info
    sql_magics_info_header = False

    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    notebook_name = os.path.splitext(os.path.basename(file_path))[0].replace("-","_")
    spark_session_initialized = False
    i = 0

    while i < len(lines):
        line = lines[i]
        if "dbutils.widgets.text" in line.strip():
            # Extract the widget name and value
            try:
                widget_name = line.split('"')[1]
            except:
                widget_name = line.split("'")[1]
            widgets_info_details = {
                "file": file_path,
                "notebook": notebook_name,
                "widget_name": widget_name,
            }
            widgets_info.append(widgets_info_details)
            i += 1
            continue

        # Keep "# Databricks notebook source" and add SparkSession initialization if not already added
        if line.strip() == "# Databricks notebook source":
            output_lines.append(line)
            if not spark_session_initialized:
                output_lines.append("\n")
                output_lines.append(f"from pyspark.sql import SparkSession\n")
                output_lines.append(f'spark = SparkSession.builder.appName("{notebook_name}").getOrCreate()\n')
                output_lines.append("\n")
                spark_session_initialized = True
            i += 1
            continue
        
        # Convert "# MAGIC %run" to "from <module> import *"
        if line.strip().startswith("# MAGIC %run"):
            found_import = line.replace("# MAGIC %run","").strip()
            if not found_import in found_imports:
                found_imports.append({
                    "file": file_path,
                    "line": i,
                    "import": found_import
                })
            module_path = found_import.strip().replace("./", "").replace("/", ".")
            module_name = module_path.split('.')[-1]
            module_name = module_name.replace('"""','') .replace('"','').replace("'",'')
            output_lines.append(f"from {module_name} import *\n")
            i += 1
            continue
        
        # Convert "# dbutils.library.installPyPI" to pip install
        if line.strip().startswith("# dbutils.library.installPyPI"):
            match = re.search(r'"(.*?)".*version\s*=\s*"(.*?)"', line)
            if match:
                package, version = match.groups()
                output_lines.append(f"# !pip install {package}=={version}\n")
            i += 1
            continue
        
        # Handle SQL blocks
        if line.strip().startswith("# MAGIC %sql"):
            sql_lines = []
            while i < len(lines) and lines[i].strip().startswith("# MAGIC"):
                sql_lines.append(lines[i].strip().replace("# MAGIC %sql", "").replace("# MAGIC","").strip())
                i += 1
            sql_query = "\n ".join(sql_lines).strip()
            output_lines.append('spark.sql("""\n')
            output_lines.append(f"{sql_query}\n")
            output_lines.append('""").show()\n')
            if not sql_magics_info_header:
                sql_magics_info += "-- " + file_path + "\n\n"
                sql_magics_info_header = True
            sql_magics_info += f"{sql_query}\n\n"
            continue
        
        # Append unchanged lines
        output_lines.append(line)
        i += 1

    # Write transformed content back to the file
    if output_format == "text":
        new_path = file_path.replace(source_path, target_path).replace("-","_")
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        with open(new_path, "w") as f:
            f.writelines(output_lines)
    else:
        new_path = file_path.replace(source_path, target_path).replace(".py", ".ipynb").replace("-","_")
        convert_to_notebook(output_lines, new_path)


def process_folder(source_path,target_path,output_format):
    for root, _, files in os.walk(source_path):
        for file in files:
            if file.endswith('.py'):
                process_file(os.path.join(root, file),source_path,target_path, output_format)


def main():
    parser = argparse.ArgumentParser(description="Process Databricks notebook Python files.")
    parser.add_argument(
        "source_folder",
        type=str,
        help="The source folder containing Python files to process."
    )
    parser.add_argument(
        "target_folder",
        type=str,
        help="The target folder where processed files and notebooks will be saved."
    )
    parser.add_argument(
        "--format",
        choices=["text", "jupyter"],
        default="text",
        help="Output format: 'text' for plain Python files, 'jupyter' for Jupyter Notebooks. Default is 'text'."
    )
    args = parser.parse_args()

    source_folder = args.source_folder
    target_folder = args.target_folder
    output_format = args.format
    if not os.path.isdir(source_folder):
        print(f"Error: {source_folder} is not a valid directory.")
        return
    os.makedirs(target_folder, exist_ok=True)

    print(f"Processing folder: {source_folder}")
    process_folder(source_folder, target_folder, output_format)
    print("Processing complete.")

    # Write to CSV
    with open("import_details.csv", mode='w', newline='') as file:
        # Get the field names from the keys of the first dictionary
        fieldnames = ["file","line","import"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data rows
        writer.writerows(found_imports)
    with open("widgets.csv", mode='w', newline='') as file:
        # Get the field names from the keys of the first dictionary
        fieldnames = ["file","notebook","widget_name"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data rows
        writer.writerows(widgets_info)


    with open("sql_notebooks.log","w") as f:
        f.write(sql_magics_info)

if __name__ == "__main__":
    main()
