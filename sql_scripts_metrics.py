import os
import rich
import argparse
import logging
import csv

from rich.console import Console
import yaml
import sqlglot
console = Console()

def process_folder(root_folder):
    import glob
    files = glob.glob(os.path.join(root_folder,"**/*.sql"),recursive=True)
    processed_folder = []
    for file in files:
        folder = os.path.dirname(file)
        if folder not in processed_folder:
            console.print(f"[bold magenta]Scanning folder:[/bold magenta] {folder}")
            processed_folder.append(folder)
        try:
            with open(file,"r") as f:
                logging.info(f"Processing file: {file}")
                sql_script = open(file).read()
                parsed_sql = sqlglot.parse(sql_script,dialect="spark")
                if parsed_sql:
                    for statement in parsed_sql:
                        str_statement = str(statement)
                        LOC = len(str_statement.splitlines())
                        characters = len(str_statement)
                        key = statement.key
                        table_names = ""
                        try:
                            tables = list(statement.find_all(sqlglot.expressions.Table))
                            if tables:
                                table_names = '|'.join([x.name for x in tables if x.name])
                        except Exception as ex1:
                            print("ooops")
                            logging.error("Error extracting tables info")
                        name = statement.name or statement.this.name
                        yield ("OK","",file,key,name, LOC,characters, table_names)
        except Exception as e:
            logging.error(f"Error parsing sql script {file}. Error {e}")
            yield ("ERROR",e,file,None,None,None,None, None)

def scan_folders(folders_config, output_csv, output_csv_errors):
     console = Console()
     with open(output_csv_errors, 'w', newline='', encoding='utf-8') as csv_file_errors:
        fieldnames = ['FileName', 'Error', 'Line','Col']
        csv_file_errors_writer = csv.DictWriter(csv_file_errors, fieldnames=fieldnames)
        csv_file_errors_writer.writeheader()
        with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = [
                'FileName', 'Key', 'Name','Lines','Characters', 'Tables'
            ]
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            csv_writer.writeheader()

            for config in folders_config:
                root_path = config.get("root_path", "")
                console.print(f"[bold cyan]Scanning folder:[/bold cyan] {root_path}")
                logging.info(f"Scanning folder: {root_path}")
                for info in process_folder(root_path):
                    if info is not None:
                        status, exception, file, key,name, loc, chars, table_names = info
                        if status == "OK":
                            file_info = {
                                "FileName": file,
                                "Key": key,
                                "Name":name,
                                "Lines": loc,
                                "Characters": chars,
                                "Tables": table_names
                            }
                            csv_writer.writerow(file_info)
                        else:
                            if isinstance(exception, sqlglot.ParseError):
                                for error in exception.errors:
                                    file_info = {
                                        "FileName": file,
                                        "Error": error['description'],
                                        "Line": error['line'],
                                        "Col": error['col']
                                    }
                                    csv_file_errors_writer.writerow(file_info)
                            #else:
                            #    print(exception)


def setup_logging(log_file):
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    parser = argparse.ArgumentParser(description="Scan folders based on YAML configuration and generate CSV.")
    parser.add_argument("config_file", help="Path to the YAML configuration file")
    parser.add_argument("output_folder", help="Folder for all the tool output")
    #parser.add_argument("output_csv", help="Path to the output CSV file",default="FilesInventory.csv")

    args = parser.parse_args()
    output_folder = args.output_folder
    output_csv = os.path.join(output_folder, "Reports", "SQL_metrics.csv")
    output_csv_errors = os.path.join(output_folder, "Reports", "SQL_metrics_errors.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","sql_metrics.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True);
    setup_logging(log_file)

    try:
        with open(args.config_file, "r") as file:
            config = yaml.safe_load(file)
            folder_config = config.get("folders", [])
            scan_folders(folder_config, output_csv, output_csv_errors)
        print("SQL Scripts Scanning process done")
    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config_file}' not found.")
        logging.error(f"Configuration file '{args.config_file}' not found.")
    except yaml.YAMLError as e:
        print(f"Error in YAML file: {e}")
        logging.error(f"Error in YAML file: {e}")

if __name__ == "__main__":
    main()
