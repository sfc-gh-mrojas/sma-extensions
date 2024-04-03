import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import squarify


import argparse

parser = argparse.ArgumentParser(description="A script to build tree map from inventory")

# Required argument
parser.add_argument("input_path", metavar="input_path", type=str, help="Path to the folder to process.")
parser.add_argument("prefix", metavar="prefix", type=str, help="Prefix to remove from all files", default="")
args = parser.parse_args()
file = args.input_path


def get_treemap_data(file,technology = ["Java","Python","Scala"]):
    # Load CSV data into a DataFrame
    df = pd.read_csv(file)
    # Filter the DataFrame based on executionIds and technology
    df = df[df['Technology'].isin(technology)]
    # Filter rows where COLUMN_CODE_LOC > 0
    df = df[df['ContentLines'] > 0]
    # Replace backslashes with forward slashes in FileName
    df['FileName'] = df['FileName'].str.replace('\\', '/',regex=False)
    # Select necessary columns and drop duplicates
    df = df[['FileName', 'ContentLines']].drop_duplicates().reset_index(drop=True)
    # Remove prefix from filenames
    prefix_to_remove = args.prefix
    df['FileName'] = df['FileName'].str.replace(prefix_to_remove, '')
    return df


def add_space(column):
   def append_space(row):
      if row is not None and isinstance(row, str):
         return row + " "
      return row
   return column.apply(append_space)


def buildTreemap(file,technology = ["Java","Python","Scala"]):
   files = get_treemap_data(file, technology)
   
   files = pd.concat([files["FileName"].str.split('/', expand=True), files], axis=1).drop(columns=["FileName"])

   files = files.fillna("temporary_folder_name")
   cols = list(files.columns)
   cols.pop()
   files = files.groupby(cols).agg({"ContentLines":"sum"}).reset_index().replace("temporary_folder_name", None)
   files = files.apply(add_space)
   fig = px.treemap(
      files,
      path=cols,
      values="ContentLines"
   )
   return fig


fig = buildTreemap(file)
# Show the interactive treemap
fig.show()
