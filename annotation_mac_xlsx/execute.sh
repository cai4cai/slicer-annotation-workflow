#!/bin/bash
# =============================================================================
# execute.sh — Finds patient data and launches 3D Slicer with auto_script.py
#
# Usage: ./execute.sh <report_number>
#
# This script:
#   1. Looks up the report number in log.csv to find the patient session folder
#   2. Locates the Slicer executable (macOS or Linux)
#   3. Scans the session folder for NIfTI volumes and markup JSON files
#   4. Launches Slicer with most modules disabled, passing auto_script.py
#      and all discovered files as command-line arguments
# =============================================================================

# --- Validate arguments ---
if [ "$#" -ne 1 ]; then
    echo "Usage: ./execute.sh <report_number>"
    exit 1
fi

REPORT_NUMBER=$1
CSV_FILE="log.csv"
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# --- Check that the progress log exists ---
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: $CSV_FILE not found."
    exit 1
fi

# --- Look up the session folder for this report number in log.csv ---
# log.csv format: Report,Path,Done
# Extract the Path column where Report matches the given number
SESSION_FOLDER=$(awk -F',' -v num="$REPORT_NUMBER" '$1 == num {print $2}' "$CSV_FILE")
if [ -z "$SESSION_FOLDER" ]; then
    echo "No path found for report number $REPORT_NUMBER in $CSV_FILE."
    exit 1
fi

# --- Locate the Slicer executable ---
# On macOS: standard Applications path
# On Linux: check home directory or current directory for Slicer installation
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

# --- Scan the session folder for data files ---

# Find all NIfTI volumes (medical imaging data)
# Uses null-delimited output to safely handle spaces in file paths
NIFTI_FILES=()
while IFS= read -r -d '' f; do
    NIFTI_FILES+=("$f")
done < <(find "$SESSION_FOLDER" -maxdepth 1 -type f \( -iname "*.nii" -o -iname "*.nii.gz" \) -print0)

# Find all markup JSON files (existing annotations from previous sessions)
MARKUP_FILES=()
while IFS= read -r -d '' f; do
    MARKUP_FILES+=("$f")
done < <(find "$SESSION_FOLDER" -maxdepth 1 -type f -iname "*.json" -print0)

# --- Launch Slicer ---
# Disable most modules to simplify the UI for annotators.
# Only Data, Markups, and Volumes are accessible via the custom toolbar dropdown.
# auto_script.py runs inside Slicer and handles loading, UI setup, and saving.
IGNORE_MODULES="Annotations,Models,Transforms,Editor,AtlasTests,BRAINSDWICleanup,BRAINSDeface,BRAINSFit,BRAINSFitRigidRegistrationCrashIssue4139,BRAINSIntensityNormalize,BRAINSROIAuto,BRAINSResample,BRAINSResize,BRAINSStripRotation,BRAINSTransformConvert,CastScalarVolume,CheckerBoardFilter,ColorLegendSelfTest,CompareVolumes,CreateDICOMSeries,CurvatureAnisotropicDiffusion,Decimation,DWIConvert,Endoscopy,EventBroker,ExecutionModelTour,ExtensionWizard,ExtractSkeleton,FiducialLayoutSwitchBug1914,FiducialRegistration,GaussianBlurImageFilter,GradientAnisotropicDiffusion,GrayscaleFillHoleImageFilter,GrayscaleGrindPeakImageFilter,GrayscaleModelMaker,HistogramMatching,ImageLabelCombine,ImportItkSnapLabel,JRC2013Vis,LabelMapSmoothing,LandmarkRegistration,MedianImageFilter,MergeModels,ModelMaker,ModelToLabelMap,MultiplyScalarVolumes,N4ITKBiasFieldCorrection,NeurosurgicalPlanningTutorialMarkupsSelfTest,OrientScalarVolume,PETStandardUptakeValueComputation,PerformMetricTest,PerformanceTests,Plots,PlotsSelfTest,PluggableMarkupsSelfTest,ProbeVolumeWithModel,Reformat,ResampleDTIVolume,ResampleScalarVolume,RobustStatisticsSegmenter,RSNA2012ProstateDemo,RSNAQuantTutorial,RSNAVisTutorial,SampleData,ScenePerformance,SceneViews,ScreenCapture,SegmentEditor,SegmentStatistics,SelfTests,Sequences,SequencesSelfTest,ShaderProperties,SimpleFilters,SimpleRegionGrowingSegmentation,Slicer4Minute,SlicerBoundsTest,SlicerDisplayNodeSequenceTest,SlicerMRBMultipleSaveRestoreLoopTest,SlicerMRBMultipleSaveRestoreTest,SlicerMRBSaveRestoreCheckPathsTest,SlicerOrientationSelectorTest,SlicerScriptedFileReaderWriterTest,SliceLinkLogic,SubtractScalarVolumes,SurfaceToolbox,Tables,TablesSelfTest,Texts,ThresholdScalarVolume,UtilTest,VectorToScalarVolume,ViewControllers,ViewControllersSliceInterpolationBug1926,VolumeRendering,VolumeRenderingSceneClose,VotingBinaryHoleFillingImageFilter,WebEngine,WebServer,Welcome"

"$SLICER_EXECUTABLE" --modules-to-ignore "$IGNORE_MODULES" --python-script "$SCRIPT_DIR/auto_script.py" -- \
    --source_folder "$SESSION_FOLDER" \
    --nifti_files "${NIFTI_FILES[@]}" \
    --markup_files "${MARKUP_FILES[@]}" \
    --report_number "$REPORT_NUMBER" \
    --log_csv "$CSV_FILE"

echo "Annotation session closed for $SESSION_FOLDER"
exit 0
