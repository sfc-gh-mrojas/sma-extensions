# Define the target folder
$targetFolder = "/path/to/files/"


# Define the output CSV file
$outputCsv = "imports_inventory.csv"

# Initialize an ArrayList to hold the import details
$importDetails = [System.Collections.ArrayList]@()

# Function to process each .py file
function Process-PythonFile {
    param (
        [string]$filePath
    )
    
    # Read the file content
    $lines = Get-Content -Path $filePath

    # Loop through each line to find import statements
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        
        # Check for 'import ' and 'from ' statements
        if ($line -match "^\s*import\s+([a-zA-Z0-9_.]+)" -or $line -match "^\s*from\s+([a-zA-Z0-9_.]+)\s+import") {
            # Extract module name
            $moduleName = $matches[1]
            
            # Create a custom object with the details
            $importDetails.Add([PSCustomObject]@{
                Filename       = $filePath
                LineNumber     = $i + 1
                FullStatement  = $line.Trim()
                ModuleName     = $moduleName
            }) | Out-Null
        }
    }
}

# Recursively find all .py files in the target folder
$pythonFiles = Get-ChildItem -Path $targetFolder -Recurse -Filter *.py

# Process each .py file
foreach ($file in $pythonFiles) {
    Process-PythonFile -filePath $file.FullName
}

# Export the import details to a CSV file
$importDetails | Export-Csv -Path $outputCsv -NoTypeInformation

Write-Host "Import inventory saved to $outputCsv"
