# just run pip install rich
from rich import print
from rich.progress import track
import argparse
import os
import glob

# usage instructions
# Examples:
# To extract all scala
# python3 dbx_magic_process.py --input /Users/mrojas/Downloads/RootFolder --output extracted-scala  --format scala-script
# To extract all python
# python3 dbx_magic_process.py --input /Users/mrojas/Downloads/RootFolder --output extracted-python --format python-script
# To extract all sql
# python3 dbx_magic_process.py --input /Users/mrojas/Downloads/RootFolder --output extracted-sql    --format sql-script

# By default sql cells when exported to python or scala scripts are turned into:
# spark.sql(...) snippets
# if the need to be excluded:
# python3 dbx_magic_process.py --input /Users/mrojas/Downloads/RootFolder --output extracted-scala  --format scala-script --extractsql FALSE

arg_parser = argparse.ArgumentParser("DBX converter by Mauricio Rojas\n==============================")
arg_parser.add_argument("--input",help="input file or directory", required=True)
arg_parser.add_argument("--output",help="output directory",required=True)
arg_parser.add_argument("--format",help="can be notebook or extract", default="notebook")
arg_parser.add_argument("--extract",help="extension to extract for example py/scala/sql")
arg_parser.add_argument("--extractsql",default="TRUE",help="if passed as TRUE then it will put the .sql blocks inside a spark.sql command")

inventory=[]

args = arg_parser.parse_args()

basedir = None

if os.path.isdir(args.input):
  basedir = args.input

def clean_lines(lines, extension="md"):
  while len(lines):
     if lines[0].strip() == '':
       lines.pop(0)
     else:
       break
  first_line = lines[0] if len(lines) else ""
  if ("-- MAGIC" in first_line) or ("# MAGIC" in first_line) or  ("// MAGIC" in first_line):
     first_line = first_line.replace("-- MAGIC ","").lstrip()
     first_line = first_line.replace("# MAGIC ","").lstrip()
     first_line = first_line.replace("// MAGIC ","").lstrip()
     # we need to keep last new line
     if not first_line.endswith("\n"):
       first_line = first_line + "\n"
     if first_line.startswith(f"%{extension}"):
        magic_len=len(extension)+1
        first_line = first_line[magic_len:]
        if first_line.strip() == '':
          lines.pop(0)
        else:
          lines[0]=first_line
     else:
         lines[0] = "%" + first_line
  for l in lines:
    if l.startswith("-- MAGIC"):
       prefix_length = len("-- MAGIC")
       l = l[prefix_length:]
       yield l
    elif l.startswith("# MAGIC"):
       prefix_length = len("# MAGIC")
       l = l[prefix_length:]
       yield l
    elif l.startswith("// MAGIC"):
       prefix_length = len("// MAGIC")
       l = l[prefix_length:]
       yield l       
    else:
        yield l

def process_file(file_name):
  print(f"Processing {file_name}")
  only_fname = os.path.basename(file_name)
  fname, ext = os.path.splitext(only_fname)
  lines = None
  try:
    lines = open(file_name).readlines()
  except Exception as e:
    print(f">>> Error opening file {e}")
    return
  classified_lines = []
  # skip empty lines
  while len(lines):
   if lines[0].strip() == '':
     lines.pop(0)
   else:
     break
  if len(lines) and (lines[0].strip() == '-- Databricks notebook source' or lines[0].strip() == '# Databricks notebook source' or lines[0].strip() == '// Databricks notebook source'):
    pass
  else:
    print("Not recognized DBX source")
    return
  lines.pop(0)
  ## workaround for --DBTITLE
  for i, line in enumerate(lines):
    if line.startswith("-- "):
      lines[i] = line[0:2] ("-- ","# ")
    if line.strip() == "# MAGIC %py":
      lines[i] = "# MAGIC %python"
  def determine_cell_type(cell_lines, extension):
    default_cell_type = extension.lower()
    for l in cell_lines:
      if l.strip()=='':
       continue
      if l.startswith("-- DBTITLE"):
       continue
      if l.startswith("-- MAGIC"):
        l = l.replace("-- MAGIC","").strip().split(" ")[0]
        if l.startswith("%"):
          return l.replace("%","").strip().lower()
      elif l.startswith("// MAGIC"):
        l = l.replace("// MAGIC","").strip().split(" ")[0]
        if l.startswith("%"):
          return l.replace("%","").strip().lower()
      elif l.startswith("# MAGIC"):
        l = l.replace("# MAGIC","").strip().split(" ")[0]
        if l.startswith("%"):
          return l.replace("%","").strip().lower()
        return "unknown"
    return extension
  def group_cells(lines):
    current_cell = []
    cells = []
    for line in lines:
     if ("-- COMMAND" in line) or ("# COMMAND" in line) or ("// COMMAND" in line):
       if len(current_cell) > 0:
         cells.append(current_cell)
         current_cell = []
       else:
         current_cell = []
     else:
       current_cell.append(line)
    if len(current_cell) > 0:
      current_cell.append(current_cell)
    extension = ext.replace(".","")
    return [(determine_cell_type(cell, extension),cell) for cell in cells]
  classified_cells = group_cells(lines)

  if args.format == "notebook":
      import nbformat as nbf
      notebook_cells = []
      nb = nbf.v4.new_notebook()
      for type, code in classified_cells:
        if type == "md":
          notebook_cells.append(nbf.v4.new_markdown_cell("".join(clean_lines(code))))
        else:
           notebook_cells.append(nbf.v4.new_code_cell("".join(clean_lines(code))))
      nb['cells'] = notebook_cells
      if basedir:
        target_name = file_name.replace(args.input,args.output).replace(ext,"ipynb")
      else:
        target_name = os.path.join(args.output, fname + ".ipynb")
      target_dir = os.path.dirname(target_name)
      os.makedirs(target_dir, exist_ok=True)
      with open(target_name, 'w') as f:
          nbf.write(nb, f)
  if args.format == "scala-script":
    if basedir:
        target_name = file_name.replace(args.input,args.output).replace(ext,".scala")
    else:
        target_name = os.path.join(args.output, fname + ".scala")
    target_dir = os.path.dirname(target_name)
    os.makedirs(target_dir, exist_ok=True)
    first_cell = True
    comment_lines = 0
    sql_lines = 0
    code_lines = 0
    other_lines = 0
    with open(target_name, 'w') as f:
      for type, code in classified_cells:
        if type == "md":
          comment_lines = comment_lines + len(code)
          for line in clean_lines(code):
            line = line.replace("%%md","")
            f.write("// " + line)
        elif type == "sql":
          sql_lines = sql_lines + len(code)
          if args.extractsql == 'TRUE':
            sqlcode = "".join(clean_lines(code)).strip()
            full_code = f'spark.sql("""{sqlcode}""")\n'
            f.write(full_code)
          else:
            f.write("// SQL CELL OMITTED\n")
        elif type == "scala":
           code_lines = code_lines + len(code)
           if first_cell:
              f.write("""
// Default imports
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql._
val spark = SparkSession.
  builder.
  appName(config.getString("spark.appName")).
  getOrCreate()
        """)
              first_cell = False
           full_code = "".join(clean_lines(code,"scala"))
           f.write(full_code)
        else:
          other_lines = other_lines + len(code)
      inventory.append((file,code_lines,comment_lines,sql_lines,other_lines))
  if args.format == "python-script":
    if basedir:
        target_name = file_name.replace(args.input,args.output).replace(ext,".py")
    else:
        target_name = os.path.join(args.output, fname + ".py")
    target_dir = os.path.dirname(target_name)
    os.makedirs(target_dir, exist_ok=True)
    with open(target_name, 'w') as f:
      first_cell = True
      comment_lines = 0
      sql_lines = 0
      code_lines = 0
      other_lines = 0      
      for type, code in classified_cells:
        if type == "md":
          comment_lines = comment_lines + len(code)
          for line in clean_lines(code):
            line = line.replace("%%md","")
            f.write("# " + line)
        elif type == "sql":
          sql_lines = sql_lines + len(code)
          if args.extractsql == 'TRUE':
            sqlcode = "".join(clean_lines(code)).strip()
            full_code = f'spark.sql("""{sqlcode}""")\n'
            f.write(full_code)
          else:
            f.write("# SQL CELL OMITTED\n")
        elif type=="py":
              code_lines = code_lines + len(code)
              if first_cell:
                  f.write("""
# Default imports
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
spark = SparkSession.builder.appName("appName").getOrCreate()
""")
                  first_cell = False
              full_code = "".join(clean_lines(code,"py"))
              f.write(full_code)
        else:
            other_lines = other_lines + len(code)
      inventory.append((file,code_lines,comment_lines,sql_lines,other_lines))
  if args.format == "sql-script":
    if basedir:
        target_name = file_name.replace(args.input,args.output).replace(ext,".sql")
    else:
        target_name = os.path.join(args.output, fname + ".sql")
    target_dir = os.path.dirname(target_name)
    os.makedirs(target_dir, exist_ok=True)
    with open(target_name, 'w') as f:
      first_cell = True
      comment_lines = 0
      sql_lines = 0
      code_lines = 0
      other_lines = 0      
      for type, code in classified_cells:
        if type == "md":
          comment_lines = comment_lines + len(code)
          for line in clean_lines(code):
            line = line.replace("%%md","")
            f.write("-- " + line)
        elif type == "sql":
          sql_lines = sql_lines + len(code)
          sqlcode = "".join(clean_lines(code)).strip()
          sqlcode = sqlcode.replace("%%sql","")
          f.write(sqlcode)
        else:
            other_lines = other_lines + len(code)
      inventory.append((file,code_lines,comment_lines,sql_lines,other_lines))
  if args.format == "notebook-almond":
      import nbformat as nbf
      notebook_cells = []
      nb = nbf.v4.new_notebook()
      for type, code in classified_cells:
        if type == "md":
          notebook_cells.append(nbf.v4.new_markdown_cell("".join(clean_lines(code))))
        elif type == "sql":
          sqlcode = "".join(clean_lines(code))
          full_code = f'spark.sql("{sqlcode}")'
          notebook_cells.append(nbf.v4.new_code_cell(full_code))
        else:
           notebook_cells.append(nbf.v4.new_code_cell("".join(clean_lines(code,"scala"))))
      nb['cells'] = notebook_cells
      if basedir:
        target_name = file_name.replace(args.input,args.output).replace(ext,"ipynb")
      else:
        target_name = os.path.join(args.output, fname + ".ipynb")
      target_dir = os.path.dirname(target_name)
      os.makedirs(target_dir, exist_ok=True)
      with open(target_name, 'w') as f:
          nbf.write(nb, f)
  if args.format == "extract":
      if basedir:
        target_name = file_name.replace(args.input,args.output).replace(ext,args.extract)
      else:
        target_name = os.path.join(args.output, fname + "." + args.extract)
      target_dir = os.path.dirname(target_name)
      os.makedirs(target_dir, exist_ok=True)
      with open(target_name, 'w') as f:
         for _, code in [cell for cell in classified_cells if cell[0] == args.extract]:
           code.pop(0)
           f.writelines(clean_lines(code, args.extract))
           f.write("\n\n")
files = [args.input]

if basedir:
  print(f"Input {basedir} is a folder.")
  print(f"Looking for all files. This might take a while")
  # if args.format == "python-script":
  #   files = glob.glob(os.path.join(args.input,"**/*.py"), recursive=True)
  # elif args.format == "scala-script":
  #   files = glob.glob(os.path.join(args.input,"**/*.scala"), recursive=True)
  # else:
  #   print("Processing all extensions")
  files = glob.glob(os.path.join(args.input,"**/*.*"), recursive=True)

print(f" {len(files)} found")

for file in track(files):
  if os.path.isfile(file):
    process_file(file)
if len(inventory):
  inventory_filename = os.path.join(args.output,"inventory.csv")
  import csv
  with open(inventory_filename,"w") as f:
      f.write("file,code_lines,comment_lines,sql_lines,other_lines\n")
      writer = csv.writer(f)
      for row in inventory:
        # write a row to the csv file
        writer.writerow(row)