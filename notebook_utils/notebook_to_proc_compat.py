# just run pip install rich
from rich import print
from rich.progress import track
import argparse
import os
import glob


# By default sql cells when exported to python or scala scripts are turned into:
# spark.sql(...) snippets
# if the need to be excluded:
# python3 notebook_to_proc_compat.py --input /Users/mrojas/Downloads/RootFolder --output extracted-scala  --format scala-script --extractsql FALSE

arg_parser = argparse.ArgumentParser("Turns notebooks exports into code compatible for SnowProcs Mauricio Rojas\n==============================")
arg_parser.add_argument("--input",help="input file or directory", required=True)
arg_parser.add_argument("--output",help="output directory",required=True)


inventory=[]

args = arg_parser.parse_args()

files = glob.glob(args.input + "/**/*.py", recursive=True)
print(files)
INDENT = "     "
for file in track(files):
    new_file = file.replace(args.input, args.output)
    if file.endswith(".py"):
        print("Processing file: " + file)
        new_lines = []
        with open(file, "r") as f:
            lines = f.readlines()
            is_notebook = False
            for line in lines:
                if line.strip() == "":
                    continue
                if line.strip().startswith("# Databricks notebook source"):
                    is_notebook = True
                    continue
                if is_notebook:
                    if line.strip().startswith("# MAGIC "):
                       current_line= line.strip().replace("# MAGIC ","").strip()
                       if current_line.startswith("%run"):
                          module = os.path.basename(current_line.replace("%run", "").replace('"', ""))
                          new_lines.append(INDENT + "from " + module + " import *\n")
                          continue
                       else:   
                          new_lines.append(INDENT + "# TODO " + line)
                       continue
                    else:
                        new_lines.append(INDENT + line.replace("dbutils","sfutils"))
                        continue
            with open(new_file, "w") as f:
                f.write("from snowflake.snowpark import Session\n")
                f.write("import sfutils\n")
                f.write("import inspect\n")
                f.write("def main(session:Session,args:list):\n")
                f.write(INDENT + "sfutils.set_notebook_name(inspect.currentframe().f_code.co_name)\n")
                f.write("".join(new_lines))