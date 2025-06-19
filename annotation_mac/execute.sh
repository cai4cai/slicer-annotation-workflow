#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./launch_annotation.sh <report_number>"
    exit 1
fi

REPORT_NUMBER=$1
CSV_FILE="log.csv"
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

if [ ! -f "$CSV_FILE" ]; then
    echo "Error: $CSV_FILE not found."
    exit 1
fi

SESSION_FOLDER=$(awk -F',' -v num="$REPORT_NUMBER" '$1 == num {print $2}' "$CSV_FILE")
if [ -z "$SESSION_FOLDER" ]; then
    echo "No path found for report number $REPORT_NUMBER in $CSV_FILE."
    exit 1
fi

OS_TYPE=$(uname)

if [ "$OS_TYPE" == "Darwin" ]; then
    SLICER_EXECUTABLE="/Applications/Slicer.app/Contents/MacOS/Slicer"
else
    if [ -f "$HOME/.local/Slicer-5.8.1-linux-amd64/Slicer" ]; then
        SLICER_EXECUTABLE="$HOME/.local/Slicer-5.8.1-linux-amd64/Slicer"
    else
        SLICER_EXECUTABLE="$(realpath "./Slicer-5.8.1-linux-amd64/Slicer")"
    fi
fi

if [ ! -f "$SLICER_EXECUTABLE" ]; then
    echo "Error: Slicer executable not found at $SLICER_EXECUTABLE"
    exit 1
fi

# Find files and create comma-separated lists
NIFTI_FILES=$(find "$SESSION_FOLDER" -maxdepth 1 -type f \( -iname "*.nii" -o -iname "*.nii.gz" \) | tr '\n' ' ')
MARKUP_FILES=$(find "$SESSION_FOLDER" -maxdepth 1 -type f -iname "*.json" | tr '\n' ' ')
TEXT_FILE=$(find "$SESSION_FOLDER" -maxdepth 1 -type f -iname "*.txt" | head -n 1)

# # Open text report if present
# if [ -n "$TEXT_FILE" ]; then
#     if [ "$OS_TYPE" == "Darwin" ]; then
#         open "$TEXT_FILE" &
#     else
#         xdg-open "$TEXT_FILE" &
#     fi
# else
#     echo "No text report found in $SESSION_FOLDER"
# fi

# Print arguments parse later
# echo "Launching Slicer with the following parameters:"
# echo "SLICER_EXECUTABLE: $SLICER_EXECUTABLE"
# echo "SCRIPT_DIR: $SCRIPT_DIR"
# echo "source_folder: $SESSION_FOLDER"
# echo "nifti_files: $NIFTI_FILES"
# echo "markup_files: $MARKUP_FILES"
# echo "report_number: $REPORT_NUMBER"
# echo "log_csv: $CSV_FILE"

# Launch Slicer with auto_script.py and parameters
"$SLICER_EXECUTABLE" --python-script "$SCRIPT_DIR/auto_script.py" -- \
    --source_folder "$SESSION_FOLDER" \
    --nifti_files $NIFTI_FILES \
    --markup_files $MARKUP_FILES \
    --report_number "$REPORT_NUMBER" \
    --log_csv "$CSV_FILE"

# After Slicer exits, close the text viewer if it was opened
if [ -n "$TEXT_VIEWER_PID" ]; then
    kill "$TEXT_VIEWER_PID" 2>/dev/null
fi

echo "Annotation session closed for $SESSION_FOLDER"
exit 0