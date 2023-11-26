param (
    [string]$configFile,
    [string]$outputDir
)

$PYTHON="/usr/bin/python3"

# Create a timestamp for the folder name
$timestamp = Get-Date -Format "MM-dd-yyyyTHH mm"
$folderName = "Assessment-$timestamp"

# Create the output directory if it doesn't exist
$outputPath = Join-Path $outputDir $folderName
New-Item -ItemType Directory -Force -Path $outputPath

Write-Output "Creating output Directory " $outputPath

# Define paths to Python scripts
$inventoryScript = "inventory.py"
$importInventoryScript = "import_inventory.py"
$keywordsScript = "keywords.py"

# Run Python scripts with arguments
Write-Host "Executing Python scripts..."
Write-Host "Executing Inventory collection..."
& $PYTHON $inventoryScript            $configFile $outputPath
Write-Host "Executing Import Inventory collection..."
& $PYTHON $importInventoryScript      $configFile $outputPath
Write-Host "Executing Keywords collection..."
& $PYTHON $keywordsScript             $configFile $outputPath

Write-Host "Scripts executed successfully."
