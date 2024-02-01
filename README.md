# SMA Extension Scripts

The Snowpark Migrator Accelerator (SMA) already provides a lot of built in functionality to collect data about PySpark or Scala workloads.

This repository provides scripts that can be used alongside the SMA to help in:

- collect metrics in situations where the SMA cannot be installed
- collect metrics for languages not yet supported by SMA (like R or Java)
- perform code extraction or code preparation tasks.

## Usage

To run the scripts you need to have the following installed:

- python3
- Powershell
- all the packages in requirements.txt

You can install the packages with: `pip install -r requirements.txt``

## Before you run

The scripts are controlled by a config file, typically called `config.yml`. This is YAML configuration file
that will indicate which folders need to be processed.

In general the format of the file is:

```yml
folders:
  - root_path: "/path/to/your_workload1/folder1"
  - root_path: "/path/to/your_workload2/folder2"
  - root_path: "/path/to/your_workload3/folder3"
keywords:
  - library
  - SparkR
  - from_unixtime
  - unix_timestamp
  - from_utc_timestamp
  - locate
  - instr
  - datediff
  - date_add
  - date_sub
  - date_format
  - struct
  - named_struct
  - array_max/array_min
  - array_agg
  - arrays_zip
  - array
  - collect_list
  - collect_set
  - explode / explode_outer
  - map_from_arrays
  - from_json
```

The `root_path` is the path to the folder that contains your code. 

The focus of these scripts is to collect information on R and SQL files.You can specificy as many `root_path` folders as you want.

The `keywords` are the keywords that will be used to identify patterns in R and SQL files.

To execute the scripts a powershell script is provided. You can run this script from the command line like this:

```PS1
.\RunScripts.ps1 -configFile Path\To\Your\config.yml -outputDir Path\To\Your\OutputDir
```

When this script runs it will create a folder with the current timestamp in the specified output directory and run all the Python scripts using the provided configuration file and output directory.

Output of the execution looks like this:

```
> ./RunScripts.ps1 --configFile config.yml --outputDir output1

    Directory: /Users/mrojas/snowconvert-tools-for-r/output1

UnixMode   User             Group                 LastWriteTime           Size Name
--------   ----             -----                 -------------           ---- ----
drwxr-xr-x mrojas           staff              11/27/2023 07:35            128 Assessment-11-27-2023T07
                                                                                35
Creating output Directory 
output1/Assessment-11-27-2023T07 35
Executing Python scripts...
Executing Inventory collection...
Scanning folder: /path/to/your_workload/spark-r-notebooks-master
Scanning folder: /path/to/your_workload/sparkr-demo-master
Executing Import Inventory collection...
Scanning folder: /path/to/your_workload/spark-r-notebooks-master
Scanning folder: /path/to/your_workload/sparkr-demo-master
Executing Keywords collection...
Scanning folder: /path/to/your_workload/spark-r-notebooks-master
Scanning folder: /path/to/your_workload/sparkr-demo-master
Executing SQL Scripts collection...
Scanning folder: /path/to/your_workload/spark-r-notebooks-master
Scanning folder: /path/to/your_workload/sparkr-demo-master
SQL Scripts Scanning process done
Scripts executed successfully.
```
