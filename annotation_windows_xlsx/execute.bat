@echo off
setlocal enabledelayedexpansion
:: =============================================================================
:: execute.bat — Finds patient data and launches 3D Slicer with auto_script.py
::
:: Usage: execute.bat <report_number>
::
:: This script:
::   1. Looks up the report number in log.csv to find the patient session folder
::   2. Locates the Slicer executable (Windows default install path)
::   3. Scans the session folder for NIfTI volumes and markup JSON files
::   4. Launches Slicer with most modules disabled, passing auto_script.py
::      and all discovered files as command-line arguments
:: =============================================================================

:: --- Validate arguments ---
if "%~1"=="" (
    echo Usage: execute.bat ^<report_number^>
    exit /b 1
)

set "REPORT_NUMBER=%~1"
set "CSV_FILE=log.csv"
set "SCRIPT_DIR=%~dp0"

:: --- Check that the progress log exists ---
if not exist "%CSV_FILE%" (
    echo Error: %CSV_FILE% not found.
    exit /b 1
)

:: --- Look up the session folder for this report number in log.csv ---
:: Copy to temp file to avoid file locking issues when reading
set "TEMP_CSV=%TEMP%\temp_log.csv"
copy /y "%CSV_FILE%" "%TEMP_CSV%" >nul

:: Parse CSV: find the row where column 1 matches the report number,
:: extract column 2 (the session folder path)
set "SESSION_FOLDER="
for /f "tokens=1,2 delims=," %%A in (%TEMP_CSV%) do (
    if "%%A"=="%REPORT_NUMBER%" (
        set "SESSION_FOLDER=%%B"
    )
)

:: Clean up the temporary copy
del "%TEMP_CSV%"

if "%SESSION_FOLDER%"=="" (
    echo No path found for report number %REPORT_NUMBER% in %CSV_FILE%.
    exit /b 1
)

:: --- Locate the Slicer executable ---
:: Default Windows install path for Slicer 5.8.1
set "SLICER_EXECUTABLE=%LOCALAPPDATA%\slicer.org\Slicer 5.8.1\Slicer.exe"

if not exist "%SLICER_EXECUTABLE%" (
    echo Error: Slicer executable not found at %SLICER_EXECUTABLE%
    exit /b 1
)

:: --- Scan the session folder for data files ---

:: Find all NIfTI volumes (medical imaging data)
set "NIFTI_FILES="
for %%F in ("%SESSION_FOLDER%\*.nii" "%SESSION_FOLDER%\*.nii.gz") do (
    set "NIFTI_FILES=!NIFTI_FILES! "%%F""
)

:: Find all markup JSON files (existing annotations from previous sessions)
set "MARKUP_FILES="
for %%F in ("%SESSION_FOLDER%\*.json") do (
    set "MARKUP_FILES=!MARKUP_FILES! "%%F""
)

:: --- Launch Slicer ---
:: Disable most modules to simplify the UI for annotators.
:: Only Data, Markups, and Volumes are accessible via the custom toolbar dropdown.
:: auto_script.py runs inside Slicer and handles loading, UI setup, and saving.
set "IGNORE_MODULES=Annotations,Models,Transforms,Editor,AtlasTests,BRAINSDWICleanup,BRAINSDeface,BRAINSFit,BRAINSFitRigidRegistrationCrashIssue4139,BRAINSIntensityNormalize,BRAINSROIAuto,BRAINSResample,BRAINSResize,BRAINSStripRotation,BRAINSTransformConvert,CastScalarVolume,CheckerBoardFilter,ColorLegendSelfTest,CompareVolumes,CreateDICOMSeries,CurvatureAnisotropicDiffusion,Decimation,DWIConvert,Endoscopy,EventBroker,ExecutionModelTour,ExtensionWizard,ExtractSkeleton,FiducialLayoutSwitchBug1914,FiducialRegistration,GaussianBlurImageFilter,GradientAnisotropicDiffusion,GrayscaleFillHoleImageFilter,GrayscaleGrindPeakImageFilter,GrayscaleModelMaker,HistogramMatching,ImageLabelCombine,ImportItkSnapLabel,JRC2013Vis,LabelMapSmoothing,LandmarkRegistration,MedianImageFilter,MergeModels,ModelMaker,ModelToLabelMap,MultiplyScalarVolumes,N4ITKBiasFieldCorrection,NeurosurgicalPlanningTutorialMarkupsSelfTest,OrientScalarVolume,PETStandardUptakeValueComputation,PerformMetricTest,PerformanceTests,Plots,PlotsSelfTest,PluggableMarkupsSelfTest,ProbeVolumeWithModel,Reformat,ResampleDTIVolume,ResampleScalarVolume,RobustStatisticsSegmenter,RSNA2012ProstateDemo,RSNAQuantTutorial,RSNAVisTutorial,SampleData,ScenePerformance,SceneViews,ScreenCapture,SegmentEditor,SegmentStatistics,SelfTests,Sequences,SequencesSelfTest,ShaderProperties,SimpleFilters,SimpleRegionGrowingSegmentation,Slicer4Minute,SlicerBoundsTest,SlicerDisplayNodeSequenceTest,SlicerMRBMultipleSaveRestoreLoopTest,SlicerMRBMultipleSaveRestoreTest,SlicerMRBSaveRestoreCheckPathsTest,SlicerOrientationSelectorTest,SlicerScriptedFileReaderWriterTest,SliceLinkLogic,SubtractScalarVolumes,SurfaceToolbox,Tables,TablesSelfTest,Texts,ThresholdScalarVolume,UtilTest,VectorToScalarVolume,ViewControllers,ViewControllersSliceInterpolationBug1926,VolumeRendering,VolumeRenderingSceneClose,VotingBinaryHoleFillingImageFilter,WebEngine,WebServer,Welcome"

"%SLICER_EXECUTABLE%" --modules-to-ignore "%IGNORE_MODULES%" --python-script "%SCRIPT_DIR%auto_script.py" -- ^
    --source_folder "%SESSION_FOLDER%" ^
    --nifti_files %NIFTI_FILES% ^
    --markup_files %MARKUP_FILES% ^
    --report_number "%REPORT_NUMBER%" ^
    --log_csv "%CSV_FILE%"

echo Annotation session closed for %SESSION_FOLDER%
exit /b 0
