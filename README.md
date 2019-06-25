# Photobleaching
Collection of scripts which will measure flourescent photobleaching

What they do: "bleach.py" will bleach a sample for specified time (bleachTime), then let the sample recover in darkness (darkTime), before bleaching the sample again. The cycle continues a specified number of times (bleachNum).

"recovery.py" will bleach the sample for a specified time (bleachTime), then it will track the recovery over the next period of time (recoveryTime) by taking equally spaced samples (sampleNum).

To use: exicute "python recovery.py filename" from the termial in the directory where the output file should be saved. The script will then save filename.csv as the output

To modify: the integration time, bleaching time and recovery times are editable inside the script, near line 100.
