# Databricks to Jupyter Notebook Converter

A Python utility that converts Databricks notebooks (`.dbc` files or JSON format) to Jupyter notebooks (`.ipynb` format). This tool supports multiple languages including Python, SQL, Markdown, and Scala, preserving the original notebook structure and content.

## Features

- Converts individual `.dbc` files to `.ipynb` format
- Processes entire directories containing Databricks notebooks
- Handles both zipped `.dbc` files and unzipped JSON format
- Supports multiple languages:
  - Python
  - SQL (automatically converts to PySpark SQL commands)
  - Markdown
  - Scala
- Maintains notebook structure including code and markdown cells
- Preserves cell execution order
- Automatically handles `%run` magic commands by converting them to Python imports

## Installation

1. Clone this repository or download the script
2. Ensure you have Python 3.8 or later installed

## Usage

The script can be used in three different ways:

### 1. Converting a single .dbc file

```bash
python dbc-to-ipynb.py /path/to/notebook.dbc /path/to/output/folder
```

### 2. Converting a directory of notebooks

```bash
python dbc-to-ipynb.py /path/to/notebook/directory /path/to/output/folder
```

### 3. Converting a single JSON format notebook

```bash
python dbc-to-ipynb.py /path/to/notebook.json /path/to/output/folder
```

## Example Transformations

### SQL Command Transformation
Before (Databricks):
```
%sql
SELECT * FROM my_table
WHERE column > 10
```

After (Jupyter):
```python
spark.sql("""
SELECT * FROM my_table
WHERE column > 10
""").show()
```

### Run Command Transformation
Before (Databricks):
```
%run /Shared/Utils/helper_functions
```

After (Jupyter):
```python
from Shared.Utils.helper_functions import *
```

## Output Structure

The converter creates a directory structure in the output folder that mirrors the original notebook organization:

```
output_folder/
├── notebook1.ipynb
├── folder1/
│   ├── notebook2.ipynb
│   └── notebook3.ipynb
└── folder2/
    └── notebook4.ipynb
```

## Limitations

- Empty cells are skipped in the conversion process
- Output cells from previous executions are not preserved
- Custom Databricks widgets and commands may not be fully supported

## Error Handling

- The script will skip files that are not valid Databricks notebooks
- If the output directory doesn't exist, it will be created automatically
- Invalid or corrupted `.dbc` files will be reported with an error message

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open-source and available under the MIT License.
