from __future__ import print_function
import json
import re
import sys
import os
import zipfile
from copy import deepcopy

# Regex for command prefix
prefixRegex = "^([\\n]*)(\%\w+)"

# Language mapping
langMap = {
    'python': 'python',
    'md': 'markdown',
    'sql': 'sql',
    'scala': 'scala',
}

def getLangPrefix(cmdstr):
    regexResult = re.search(prefixRegex, cmdstr)
    if regexResult is not None:
        groups = regexResult.groups()
    else:
        return ''
    prefixGroup = groups[1]
    prefix = prefixGroup[1:]
    return prefix

def get_cell_type_and_source(notebook, command,relpath,inputpath):
    cmdstr = command['command']
    if len(cmdstr) == 0:
        return 'code', '', 'python'
    
    prefix = getLangPrefix(cmdstr)
    lang = langMap[prefix] if prefix in langMap else notebook['language']
    
    # Remove the magic command prefix if present
    if len(prefix) > 0:
        prefixMatches = re.search(prefixRegex, cmdstr, re.IGNORECASE)
        if prefixMatches:
            cmdstr = re.sub(prefixRegex, '', cmdstr)
    
    # Determine cell type
    cell_type = 'markdown' if lang == 'markdown' else 'code'
    if prefix == "run":
        
        include_path = os.path.normpath(os.path.join(relpath,cmdstr.replace("%run","").strip())).strip()
        if include_path.startswith("/"):
            include_path = include_path[1:]
        if include_path.endswith("/"):
            include_path = include_path[:-1]
        cmdstr = f"from {include_path.replace('/','.')} import *"
    elif prefix == "sql":
        print("sql")
        cmdstr = "spark.sql(\"\"\"\n"+cmdstr.replace("%sql","").strip()+"\n\"\"\").show()"
    return cell_type, cmdstr.strip(), lang

def create_notebook_cell(cell_type, source, language):
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": source.splitlines(True),
    }
    
    if cell_type == "code":
        cell["outputs"] = []
        cell["execution_count"] = None
        if language:
            cell["metadata"]["language"] = language
    
    return cell

def convert_to_ipynb(notebook,relpath,inputpath):
    ipynb = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.8"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    for command in notebook['commands']:
        cell_type, source, language = get_cell_type_and_source(notebook, command,relpath,inputpath)
        if len(source) > 0:
            cell = create_notebook_cell(cell_type, source, language)
            ipynb["cells"].append(cell)
    
    return ipynb

def outdir(inputFile):
    outdir = inputFile + '-notebooks'
    if not (os.path.exists(outdir) and os.path.isdir(outdir)):
        os.mkdir(outdir)
    return outdir

def processjsonfile(inputpath, filepath, outputpath):
    with open(filepath) as f:
        try:
            notebook = json.loads(f.read())
        except:
            notebook = None
            pass
    
    # ensure it is a notebook
    if notebook == None or (not notebook['version'] == 'NotebookV1'):
        print('SKIPPING file, ', filepath, '. Not a notebook.')
        return
    
    # prepare output dir:
    relpath = filepath.replace(inputpath,"")
    if relpath[0] == '/':
        relpath = relpath[1:]
    relpath = os.path.dirname(relpath)
    output_path = os.path.join(outputpath, relpath, f"{notebook['name']}.ipynb")
    print(relpath, '->', output_path)
    
    # Convert to ipynb format
    ipynb = convert_to_ipynb(notebook,relpath,inputpath)
    
    # Save as .ipynb file
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        json.dump(ipynb, f, indent=2)

def processdir(inputdir, outputpath, deleteFileAfter=False):
    for dir, dirs, files in os.walk(inputdir):
        for filepath in files:
            fullpath = os.path.join(dir, filepath)
            processjsonfile(inputdir, fullpath,outputpath)
            if deleteFileAfter:
                os.remove(fullpath)

def processzipfile(filepath, outputpath):
    import tempfile
    from tempfile import mkdtemp
    from zipfile import ZipFile
    destDir = tempfile.mkdtemp()
    with ZipFile(filepath, 'r') as dbc:
        dbc.extractall(destDir)
    processdir(destDir, outputpath, deleteFileAfter=True)
    # from shutil import move
    # move(destDir, filepath + '-notebooks')

def main():
    if len(sys.argv) != 3:
        print('sys.argv', sys.argv)
        print("""
        Usage: dbc-to-ipynb <dbc_file or folder> <target_folder> 
        Run with example:
        dbc-to-ipynb /path/file.dbc /path/to/output/folder
        """, file=sys.stderr)
        exit(-1)
    
    filepath = os.path.abspath(sys.argv[1])
    print(f"Input {filepath}")
    outputpath = os.path.expanduser(sys.argv[2])
    if not os.path.exists(filepath):
        print(f"File or directory {filepath} not found")
        exit(-2)
    os.makedirs(outputpath, exist_ok=True)

    if os.path.isdir(filepath):
        print("Input is a directory")
        processdir(filepath,outputpath)
    else:
        print(f"Processing file {filepath}")
        if zipfile.is_zipfile(filepath):
            processzipfile(filepath,outputpath)
        else:
            processjsonfile(filepath,outputpath)

if __name__ == "__main__":
    main()

