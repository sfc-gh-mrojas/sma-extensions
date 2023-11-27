from ply import lex
import os
import rich
import argparse
import logging
import csv

from rich.console import Console
import yaml

# Define the R lexer tokens
tokens = (
    'NUMBER',
    'ID',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'STRING',  
    'COMMENT', 
    'ASSIGN',  
    'EQUAL',
    'NOT_EQUAL',
    'GREATER_THAN',
    'LESS_THAN',
    'GREATER_THAN_EQUAL',
    'LESS_THAN_EQUAL',
    'AND',
    'OR',
    'NOT',
    'LEFT_CURLY',
    'RIGHT_CURLY',
    'LEFT_SQUARE',
    'RIGHT_SQUARE',
    'DOT',
    'COMMA',
    'DOLLAR',
    'PERCENT',
    'TILDE',
    'COLON',
    'SEMICOLON',
    'BITWISE_AND',
    'BACKTICK_ID',
    'BACKSLASH'
)

# Define the regular expressions for the tokens
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_EQUAL = r'=='
t_NOT_EQUAL = r'!='
t_GREATER_THAN = r'>'
t_LESS_THAN = r'<'
t_GREATER_THAN_EQUAL = r'>='
t_LESS_THAN_EQUAL = r'<='
t_AND = r'&&'
t_BITWISE_AND = r'&'
t_OR = r'\|\|'
t_NOT = r'!'
t_LEFT_CURLY = r'{'
t_RIGHT_CURLY = r'}'
t_LEFT_SQUARE = r'\['
t_RIGHT_SQUARE = r'\]'
t_DOT = r'\.'
t_COMMA = r','
t_DOLLAR = r'\$'
t_TILDE = r'~'
t_COLON = r':'
t_SEMICOLON = r';'
t_BACKSLASH = r'\\'

# Define a rule for matching backtick-enclosed identifiers
def t_BACKTICK_ID(t):
    r'`[^`]+`'
    return t

# Define a rule for comments
def t_COMMENT(t):
    r'\#.*'
    pass  # Ignore comments

# Define a rule for matching numbers
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Define a rule for matching identifiers
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    return t

# Define a rule for matching strings
def t_STRING(t):
    r'"[^"]*"|\'[^\']*\''
    t.value = t.value[1:-1]  # Remove quotes from the value
    return t

# Define a rule for tracking line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Define ignored characters (spaces and tabs)
t_ignore = ' \t'

# Error handling rule
def t_error(t):
    logging.error(f"{t.lexer.current_file} Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Define a rule for the assignment operator
def t_ASSIGN(t):
    r'<-|='
    return t

# Define a rule for the % operator
def t_PERCENT(t):
    r'%'
    return t

# Build the lexer
lexer = lex.lex()


def process_folder(root_folder):
    console = Console()
    import glob
    files = glob.glob(os.path.join(root_folder,"**/*.R"),recursive=True)
    processed_folder = []
    for file in files:
        folder = os.path.dirname(file)
        if folder not in processed_folder:
            console.print(f"[bold magenta]Scanning folder:[/bold magenta] {folder}")
            processed_folder.append(folder)
        try:
            with open(file,"r") as f:
                logging.info(f"Processing file: {file}")
                data = f.read()
                lexer.current_file = file
                lexer.lineno = 1
                lexer.input(data)
                # Tokenize and print tokens
                while True:
                    tok = lexer.token()
                    if not tok:
                        break
                    elif tok.type == "STRING":
                        yield (file, tok.value, tok.lineno)
        except Exception as e:
            logging.error(f"Error processing file: {file} - {e}")


def scan_folders(folders_config, output_csv):
     console = Console()
     with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            'FileName', 'Literal', 'Line'
        ]
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for config in folders_config:
            root_path = config.get("root_path", "")          
            logging.info(f"Scanning folder: {root_path}")
            for info in process_folder(root_path):
                if info is not None:
                    file, literal, line = info
                    if len(literal) > 10:
                        file_info = {
                            "FileName": file,
                            "Literal": literal,
                            "Line": line
                        }
                        csv_writer.writerow(file_info)

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
    output_csv = os.path.join(output_folder, "Reports", "R_SQL_Snippets.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    log_file = os.path.join(output_folder,"Logs","sql_snippets.log")
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
