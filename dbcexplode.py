"""explodes the dbc files from databricks into more useful python/sql/markdown files."""
from __future__ import print_function
import json
import re
import sys
import os
import zipfile

prefixRegex = "^([\\n]*)(\%\w+)"
extMap = {
  'python': 'py',
  'md': 'md',
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

    
def getExtension(notebook, command):
  cmdstr = command['command']
  if len(cmdstr) == 0:
    return
  
  prefix = getLangPrefix(cmdstr)
  ext = extMap[prefix] if prefix in extMap else None
  
  if ext is None:
    ext = extMap.get(notebook['language'])
    
  return ext if ext is not None else '' 
  
def outdir(inputFile):
  outdir = inputFile + '-exploded'
  if not (os.path.exists(outdir) and os.path.isdir(outdir)):
    os.mkdir(outdir)
  return outdir

def processjsonfile(filepath):
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
  dir = outdir(filepath)

  print(os.path.basename(filepath), '->', os.path.basename(dir))

  notebookName = notebook['name']
  commands = notebook['commands']
  commandNo = 0
  for command in commands:
    commandNo += 1
    cmdstr = command['command']
    if len(cmdstr) > 0:
      ext = getExtension(notebook, command)
      if len(getLangPrefix(cmdstr)) > 0:
        prefixMatches = re.search(prefixRegex, cmdstr, re.IGNORECASE)

        if(prefixMatches):
          prefix = prefixMatches.group(2)[1:]

          # if prefix is in extMap, remove it from cmdstr
          if(prefix in extMap):
            cmdstr = re.sub(prefixRegex, '', cmdstr)
          else:
            ext = "magic"


        # lines = cmdstr.splitlines()
        # cmdstr = '\n'.join(lines[1:])
      path = os.path.join(dir, f"{notebookName}-{commandNo:03d}.{ext}")
      
      with open(path, 'w') as f:
        f.write(cmdstr)

def iszipfile(filepath):
  with open(filepath, 'rb') as f:
    bits = f.read(3)
    return len(bits) == 3 and bits[0] == 'P' and bits[1] == 'K' and bits[2] == '\x03'

def processdir(filepath, deleteFileAfter=False):
  for dir, dirs, files in os.walk(filepath):
      for filepath in files:
        fullpath=os.path.join(dir, filepath)
        processjsonfile(fullpath)
        if deleteFileAfter: os.remove(fullpath)

def processzipfile(filepath):
  import tempfile
  from tempfile import mkdtemp
  from zipfile import ZipFile
  destDir = tempfile.mkdtemp()
  with ZipFile(filepath, 'r') as dbc:
    dbc.extractall(destDir)
  processdir(destDir, deleteFileAfter=True)
  from shutil import move
  move(destDir, filepath + '-exploded')
  
def main():
  
  if len(sys.argv) != 2:
    print('sys.argv', sys.argv)
    print("""
    Usage: dbc-explode <dbc_file>

    Run with example jar:
    dbc-explode /path/file.dbc
    """, file=sys.stderr)
    exit(-1)

  #load file:
  filepath = os.path.abspath(sys.argv[1])
  print(f"Input {filepath}")
  if not os.path.exists(filepath):
    print(f"File or directory {filepath} not found")
    exit(-2)
  if os.path.isdir(filepath):
    print("Input is a directory")
    processdir(filepath)
  else:
    print(f"Processing file {filepath}")
    if zipfile.is_zipfile(filepath):
      processzipfile(filepath)
    else:
      processjsonfile(filepath)


if __name__ == "__main__":
  main()
