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

# Define paths to scripts
$inventoryScript       = "inventory.py"
$importInventoryScript = "import_inventory.py"
$keywordsScript        = "keywords.py"
$literalsScript        = "literal_analyzer.py"
$sqlScripts            = "sql_scripts_metrics.py"

# Run scripts with arguments
Write-Host "Executing scripts..."
Write-Host "Executing Inventory collection..." -ForegroundColor Green
& $PYTHON $inventoryScript            $configFile $outputPath
Write-Host "Executing Import Inventory collection..." -ForegroundColor Green
& $PYTHON $importInventoryScript      $configFile $outputPath
Write-Host "Executing Keywords collection..." -ForegroundColor Green
& $PYTHON $keywordsScript             $configFile $outputPath
Write-Host "Executing Literals collection..." -ForegroundColor Green
& $PYTHON $literalsScript             $configFile $outputPath
Write-Host "Executing SQL Scripts collection..." -ForegroundColor Green
& $PYTHON $sqlScripts                 $configFile $outputPath



Write-Host "Scripts executed successfully."
