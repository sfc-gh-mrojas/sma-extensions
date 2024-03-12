#!/bin/bash

# Define variables
PYTHON="/usr/bin/python3"

# Function to create directory if it doesn't exist
create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "Creating output Directory $1"
    fi
}

# Check if configFile and outputDir are provided as arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <configFile> <outputDir>"
    exit 1
fi

configFile="$1"
outputDir="$2"

# Run function to create output directory
timestamp=$(date +"%m-%d-%YT%H %M")
folderName="Assessment-$timestamp"
outputPath="$outputDir/$folderName"
create_directory "$outputPath"

# Define paths to scripts
inventoryScript="inventory.py"
importInventoryScript="import_inventory.py"
keywordsScript="keywords.py"
literalsScript="literal_analyzer.py"
sqlScripts="sql_scripts_metrics.py"
javaMethods="collect_java_methods.py"
javaStrings="collect_java_strings.py"
javaMaven="collect_gradle_dependencies.py"
javaGradle="collect_maven_dependencies.py"

# Run scripts with arguments
echo "Executing scripts..."
echo "Executing Inventory collection..." 
$PYTHON "$inventoryScript" "$configFile" "$outputPath"
echo "Executing Import Inventory collection..." 
$PYTHON "$importInventoryScript" "$configFile" "$outputPath"
echo "Executing Keywords collection..." 
$PYTHON "$keywordsScript" "$configFile" "$outputPath"
echo "Executing Literals collection..." 
$PYTHON "$literalsScript" "$configFile" "$outputPath"
echo "Executing SQL Scripts collection..." 
$PYTHON "$sqlScripts" "$configFile" "$outputPath"
echo "Executing java methods..." 
$PYTHON "$javaMethods" "$configFile" "$outputPath"
echo "Executing java strings..." 
$PYTHON "$javaStrings" "$configFile" "$outputPath"
echo "Executing java maven..." 
$PYTHON "$javaMaven" "$configFile" "$outputPath"
echo "Executing java gradle..." 
$PYTHON "$javaGradle" "$configFile" "$outputPath"

echo "Scripts executed successfully."
