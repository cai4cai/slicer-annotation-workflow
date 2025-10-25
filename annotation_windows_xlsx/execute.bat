@echo off
setlocal enabledelayedexpansion

:: Check argument count
if "%~1"=="" (
    echo Usage: launch_annotation.bat ^<report_number^>
    exit /b 1
)

set "REPORT_NUMBER=%~1"
set "CSV_FILE=log.csv"
set "SCRIPT_DIR=%~dp0"

:: Check if CSV file exists
if not exist "%CSV_FILE%" (
    echo Error: %CSV_FILE% not found.
    exit /b 1
)

set "TEMP_CSV=%TEMP%\temp_log.csv"
copy /y "%CSV_FILE%" "%TEMP_CSV%" >nul

:: Now read from the copy
set "SESSION_FOLDER="
for /f "tokens=1,2 delims=," %%A in (%TEMP_CSV%) do (
    if "%%A"=="%REPORT_NUMBER%" (
        set "SESSION_FOLDER=%%B"
    )
)

:: Delete the temporary copy
del "%TEMP_CSV%"

if "%SESSION_FOLDER%"=="" (
    echo No path found for report number %REPORT_NUMBER% in %CSV_FILE%.
    exit /b 1
)

:: Define Slicer executable path
set "SLICER_EXECUTABLE=%LOCALAPPDATA%\slicer.org\Slicer 5.8.1\Slicer.exe"

if not exist "%SLICER_EXECUTABLE%" (
    echo Error: Slicer executable not found at %SLICER_EXECUTABLE%
    exit /b 1
)

:: Find NIfTI files
set "NIFTI_FILES="
for %%F in ("%SESSION_FOLDER%\*.nii" "%SESSION_FOLDER%\*.nii.gz") do (
    set "NIFTI_FILES=!NIFTI_FILES! "%%F""
)

:: Find Markup files
set "MARKUP_FILES="
for %%F in ("%SESSION_FOLDER%\*.json") do (
    set "MARKUP_FILES=!MARKUP_FILES! "%%F""
)

:: Find first text file
set "TEXT_FILE="
for %%F in ("%SESSION_FOLDER%\*.txt") do (
    set "TEXT_FILE=%%F"
    goto :found_text
)
:found_text

:: Module ignore list to match Bash
set "IGNORE_MODULES=Annotations,Models,Transforms,Editor"
:: set "IGNORE_MODULES=Annotations,Models,Transforms,Editor,AtlasTests,BRAINSDWICleanup,BRAINSDeface,BRAINSFit,BRAINSFitRigidRegistrationCrashIssue4139,BRAINSIntensityNormalize,BRAINSROIAuto,BRAINSResample,BRAINSResize,BRAINSStripRotation,BRAINSTransformConvert,Cameras,CastScalarVolume,CheckerBoardFilter,ColorLegendSelfTest,CompareVolumes,CreateDICOMSeries,CurvatureAnisotropicDiffusion,Decimation,DWIConvert,Endoscopy,EventBroker,ExecutionModelTour,ExtensionWizard,ExtractSkeleton,FiducialLayoutSwitchBug1914,FiducialRegistration,GaussianBlurImageFilter,GradientAnisotropicDiffusion,GrayscaleFillHoleImageFilter,GrayscaleGrindPeakImageFilter,GrayscaleModelMaker,HistogramMatching,ImageLabelCombine,ImportItkSnapLabel,JRC2013Vis,LabelMapSmoothing,LandmarkRegistration,MedianImageFilter,MergeModels,ModelMaker,ModelToLabelMap,MultiplyScalarVolumes,N4ITKBiasFieldCorrection,NeurosurgicalPlanningTutorialMarkupsSelfTest,OrientScalarVolume,PETStandardUptakeValueComputation,PerformMetricTest,PerformanceTests,Plots,PlotsSelfTest,PluggableMarkupsSelfTest,ProbeVolumeWithModel,Reformat,ResampleDTIVolume,ResampleScalarVolume,RobustStatisticsSegmenter,RSNA2012ProstateDemo,RSNAQuantTutorial,RSNAVisTutorial,SampleData,ScenePerformance,SceneViews,ScreenCapture,SegmentEditor,SegmentStatistics,SelfTests,Sequences,SequencesSelfTest,ShaderProperties,SimpleFilters,SimpleRegionGrowingSegmentation,Slicer4Minute,SlicerBoundsTest,SlicerDisplayNodeSequenceTest,SlicerMRBMultipleSaveRestoreLoopTest,SlicerMRBMultipleSaveRestoreTest,SlicerMRBSaveRestoreCheckPathsTest,SlicerOrientationSelectorTest,SlicerScriptedFileReaderWriterTest,SliceLinkLogic,SubtractScalarVolumes,SurfaceToolbox,Tables,TablesSelfTest,Texts,ThresholdScalarVolume,UtilTest,VectorToScalarVolume,ViewControllers,ViewControllersSliceInterpolationBug1926,VolumeRendering,VolumeRenderingSceneClose,VotingBinaryHoleFillingImageFilter,WebEngine,WebServer,Welcome"

:: Launch Slicer with auto_script.py and parameters including module ignore
"%SLICER_EXECUTABLE%" --modules-to-ignore "%IGNORE_MODULES%" --python-script "%SCRIPT_DIR%auto_script.py" -- ^
    --source_folder "%SESSION_FOLDER%" ^
    --nifti_files %NIFTI_FILES% ^
    --markup_files %MARKUP_FILES% ^
    --report_number "%REPORT_NUMBER%" ^
    --log_csv "%CSV_FILE%"

echo Annotation session closed for %SESSION_FOLDER%
exit /b 0
