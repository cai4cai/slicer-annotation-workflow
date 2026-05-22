#!/bin/bash
# =============================================================================
# run_annotation.command — macOS entry point for the annotation workflow
#
# Double-click this file in Finder to start an annotation session.
# It prompts the user for a report number, then calls execute.sh
# which finds the patient data and launches 3D Slicer.
# =============================================================================

# Change to the directory where this script lives (the annotation folder)
cd "$(dirname "$0")"
echo "Current directory is: $(pwd)"

# Prompt the annotator for which report to work on
echo "Enter report number:"
read report_number

# Launch the annotation session
./execute.sh "$report_number"
