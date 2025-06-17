#!/bin/bash
cd "$(dirname "$0")"
echo "Current directory is: $(pwd)"
echo "Enter report number:"
read report_number
./execute.sh "$report_number"
