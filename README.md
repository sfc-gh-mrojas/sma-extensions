# SnowConvert Tools for R

This repository contains scripts that can be used to collect information about R workloads

Make sure to replace that the script points to the actual path to your Python scripts.

You can then call this PowerShell script from the command line like this:

```
.\RunScripts.ps1 -configFile "Path\To\Your\config.yml" -outputDir "Path\To\Your\OutputDir"
```

Th	is will create a folder with the current timestamp in the specified output directory and run the three Python scripts with the provided configuration file and output directory.
