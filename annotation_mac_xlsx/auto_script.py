# =============================================================================
# auto_script.py — 3D Slicer Annotation Workflow (macOS xlsx variant)
#
# This script runs inside 3D Slicer and automates the annotation workflow:
#   1. Loads medical imaging volumes (NIfTI) and existing markup annotations
#   2. Customises Slicer's UI for annotators (hides unnecessary components)
#   3. Displays the radiology report in a side panel
#   4. On exit: saves all markups, detects deletions, and updates the markup log
#
# It is launched by execute.sh, which passes file paths and metadata as arguments.
# No external Python dependencies are required — only Slicer built-ins and stdlib.
# =============================================================================

# --- Import required modules ---
import os
import argparse
import slicer
import qt
from qt import QTimer
import datetime
import json
import glob
import csv
import re

# --- Configure application settings ---
# Prevent Slicer from auto-zooming or reorienting when a new volume is loaded,
# so the annotator's current view is preserved.
settings = slicer.app.settings()
settings.setValue("SubjectHierarchy/ResetFieldOfViewOnShowVolume", False)
settings.setValue("SubjectHierarchy/ResetViewOrientationOnShowVolume", False)


# --- Parse command line arguments passed by execute.sh via Slicer ---
parser = argparse.ArgumentParser()
parser.add_argument('--source_folder', required=True)    # Patient scanning session folder
parser.add_argument('--nifti_files', nargs='*', default=[])   # List of NIfTI volume paths
parser.add_argument('--markup_files', nargs='*', default=[])  # List of existing markup JSON paths
parser.add_argument('--report_number', required=True)    # Report number (matches log.csv row)
parser.add_argument('--log_csv', required=True)          # Path to the main progress log (log.csv)
args = parser.parse_args()

# --- Define paths and initialise variables ---
sourceFolder = os.path.abspath(args.source_folder)
nifti_files = [os.path.normpath(p) for p in args.nifti_files]
markup_files = [os.path.normpath(p) for p in args.markup_files]

# markup_log.csv tracks all markups for this scanning session:
#   Columns: new_filename, report_content, original_filename, created_at, deleted_at
markup_log_file = os.path.join(sourceFolder, "markup_log.csv")

# Track which markups were successfully loaded at startup.
# This is used later to safely detect deletions — only markups that loaded
# successfully can be considered "deleted by the annotator" if they're missing
# from the scene at exit. Markups that failed to load are left untouched.
loaded_markup_names = []

# --- Set default style as Light ---
slicer.app.setStyle("Light Slicer")


# =============================================================================
# DATA LOADING
# =============================================================================

def loadEverything():
    """Load all NIfTI volumes and markup JSON files into the Slicer scene.

    NIfTI files are loaded as volumes (medical imaging data).
    Markup files (*.json) are loaded as annotation nodes (points, lines, ROIs).
    Successfully loaded markup names are tracked in loaded_markup_names for
    safe deletion detection on exit.
    """
    # Load medical imaging volumes
    if nifti_files:
        for nifti_path in nifti_files:
            print(f"Loading volume: {nifti_path}")
            slicer.util.loadVolume(nifti_path)
    else:
        print("No NIfTI files provided.")

    # Load all markup JSON files found in the session folder
    if markup_files:
        print("Loading markup files...")
        for markup_path in markup_files:
            if markup_path and os.path.isfile(markup_path):
                try:
                    slicer.util.loadMarkups(markup_path)
                    # Track the name (without .json) so we know it loaded successfully
                    loaded_markup_names.append(os.path.basename(markup_path).replace(".json", ""))
                    print(f"Loaded markup: {markup_path}")
                except Exception as e:
                    # If a markup fails to load, it will NOT be considered "deleted"
                    # on exit — this prevents accidental data loss
                    print(f"Failed to load markup {markup_path}: {e}")
            else:
                print(f"Markup file not found: {markup_path}")
    else:
        print("No markup files provided.")

    slicer.util.selectModule('Data')
    print("Ready for annotation.")

    # Set anatomical orientations for slice views
    setAnatomicalSliceViews()


# --- Enable 3D slice visibility ---
# Make all slice planes visible in the 3D view so annotators can see
# cross-sections overlaid on the 3D rendering.
scene = slicer.mrmlScene
sliceNodes = scene.GetNodesByClass("vtkMRMLSliceNode")

sliceNodes.InitTraversal()
for i in range(sliceNodes.GetNumberOfItems()):
    sliceNode = sliceNodes.GetItemAsObject(i)
    sliceNode.SetSliceVisible(True)


# =============================================================================
# UI CUSTOMISATION
# =============================================================================

# Global references to custom UI components (needed for cleanup on exit)
moduleDropdown = None
customToolBar = None


def addAllowedModuleDropdown(moduleToolBar, allowedModules=None):
    """Add a dropdown to the toolbar that limits module access.

    Annotators only need Data, Markups, and Volumes modules.
    This hides the full module list to simplify the interface.
    """
    global moduleDropdown
    if moduleToolBar is None:
        return
    if allowedModules is None:
        allowedModules = ['Data', 'Markups', 'Volumes']

    moduleDropdown = qt.QComboBox(moduleToolBar)
    moduleDropdown.addItems(allowedModules)

    def onModuleSelected(index):
        moduleName = moduleDropdown.itemText(index)
        slicer.util.selectModule(moduleName)
        print(f"Switched to module: {moduleName}")

    moduleDropdown.currentIndexChanged.connect(onModuleSelected)
    moduleToolBar.addWidget(moduleDropdown)
    slicer.util.selectModule(allowedModules[0])
    print(f"Available modules now: {allowedModules}")
    return moduleDropdown


def initialiseCustomUI():
    """Create the custom toolbar with the module dropdown.

    This replaces Slicer's default module selector with a simplified
    dropdown containing only the modules annotators need.
    """
    global customToolBar
    mw = slicer.util.mainWindow()
    if not mw:
        print("Main window not found, cannot initialise UI")
        return

    favourites = ['Data', 'Markups', 'Volumes']

    customToolBar = qt.QToolBar("CustomModuleToolbar", mw)
    mw.addToolBar(customToolBar)

    addAllowedModuleDropdown(customToolBar, favourites)

    customToolBar.show()
    print("Custom module dropdown added.")


def cleanUpCustomUI():
    """Remove custom UI components before Slicer exits.

    Disconnects signals and deletes the toolbar and dropdown to avoid
    Qt cleanup warnings and dangling references.
    """
    global moduleDropdown, customToolBar
    if moduleDropdown:
        try:
            moduleDropdown.currentIndexChanged.disconnect()
        except Exception:
            pass
        moduleDropdown.deleteLater()
        moduleDropdown = None
    if customToolBar:
        mw = slicer.util.mainWindow()
        if mw:
            mw.removeToolBar(customToolBar)
        customToolBar.deleteLater()
        customToolBar = None
    print("Custom UI cleaned up.")


def hideAllGUIComponents():
    """Simplify Slicer's interface for annotators.

    Hides components that annotators don't need and would find confusing:
    status bar, Python console, error log, data probe, help section.
    Dock widget title bars are removed but the panels remain visible.
    """

    def mainWindow():
        return slicer.util.mainWindow()

    def findChild(parent, name):
        return parent.findChild(qt.QWidget, name)

    mw = mainWindow()
    if mw is None:
        print("No main window found.")
        return

    # Hide status bar
    if mw.statusBar():
        mw.statusBar().setVisible(False)

    # Hide Python console
    console = mw.pythonConsole().parent()
    if console:
        console.setVisible(False)

    # Hide Error log
    mw.errorLogDockWidget().setVisible(False)

    # Hide module panel title bar but keep the panel visible
    modulePanelDockWidgets = mw.findChildren(qt.QDockWidget, "PanelDockWidget")
    for dock in modulePanelDockWidgets:
        dock.setTitleBarWidget(qt.QWidget(dock))
        dock.setVisible(True)

    # Hide Help section
    modulePanel = findChild(mw, "ModulePanel")
    if modulePanel:
        modulePanel.helpAndAcknowledgmentVisible = False

    # Hide Data probe (coordinate/value display at bottom of slice views)
    dataProbeWidget = findChild(mw, "DataProbeCollapsibleWidget")
    if dataProbeWidget:
        dataProbeWidget.setVisible(False)


def setAnatomicalSliceViews():
    """Set standard anatomical orientations for the slice views.

    Red = Axial, Yellow = Sagittal, Green = Coronal.
    This ensures consistent orientation regardless of Slicer defaults.
    """
    layoutManager = slicer.app.layoutManager()
    sliceViewOrientations = {
        "Red": "Axial",
        "Yellow": "Sagittal",
        "Green": "Coronal"
    }

    for sliceName, orientation in sliceViewOrientations.items():
        try:
            sliceWidget = layoutManager.sliceWidget(sliceName)
            if not sliceWidget:
                print(f"[Slice Orientation] Slice widget '{sliceName}' not found.")
                continue
            sliceNode = sliceWidget.sliceLogic().GetSliceNode()
            sliceNode.SetOrientation(orientation)
            sliceNode.SetSliceVisible(True)
            print(f"[Slice Orientation] Set {sliceName} to {orientation}")
        except Exception as e:
            print(f"[Slice Orientation] Failed to set {sliceName} to {orientation}: {e}")


def show_report_dock(report_file_path, report_number):
    """Display the radiology report in a read-only dock widget on the right.

    The report text is loaded from a .txt file in the session folder.
    Max width is 340px to leave most of the screen for the imaging views.
    """
    mw = slicer.util.mainWindow()

    # Remove any existing report dock (e.g. from a previous load)
    existingDock = mw.findChild(qt.QDockWidget, "ReportDock")
    if existingDock:
        existingDock.close()
        mw.removeDockWidget(existingDock)

    dockWidget = qt.QDockWidget()
    dockWidget.objectName = "ReportDock"
    dockWidget.windowTitle = f"Report: {report_number}"

    dockContents = qt.QWidget()
    dockLayout = qt.QVBoxLayout(dockContents)

    label = qt.QLabel(f"Report for {report_number}")
    label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
    dockLayout.addWidget(label)

    textBrowser = qt.QTextBrowser()
    textBrowser.setReadOnly(True)
    textBrowser.setStyleSheet("background-color: #f0f0f0; font-size:14px")

    if report_file_path and os.path.exists(report_file_path):
        with open(report_file_path, 'r') as f:
            textBrowser.setPlainText(f.read())
    else:
        textBrowser.setPlainText(f"Report file not found: {report_file_path}")

    dockLayout.addWidget(textBrowser)

    dockWidget.setWidget(dockContents)
    dockWidget.setMaximumWidth(340)
    mw.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
    dockWidget.show()


def ensureModulePanelVisible():
    """Final UI check — make sure the module panel is visible after all init."""
    mw = slicer.util.mainWindow()
    if mw:
        for dock in mw.findChildren(qt.QDockWidget, "PanelDockWidget"):
            dock.setVisible(True)
        slicer.util.selectModule('Data')


# =============================================================================
# MARKUP CONTENT EXTRACTION (fallback for save failures)
# =============================================================================

def extract_markup_content(node):
    """Extract markup data programmatically as a JSON string.

    This is a fallback used when slicer.util.saveNode() fails (e.g. due to
    filename issues). It reads control point positions directly from the node
    and converts them from Slicer's internal RAS coordinates to LPS.

    The extracted content is saved to an error log CSV so no annotation data
    is lost even if the normal save path fails.
    """
    try:
        markups_data = {}
        n_points = node.GetNumberOfControlPoints()
        points = []
        for i in range(n_points):
            # Get position in RAS (Slicer internal coordinate system)
            ras_position = [0.0, 0.0, 0.0]
            node.GetNthControlPointPosition(i, ras_position)
            # Convert RAS to LPS: negate R and A components
            lps_position = [-ras_position[0], -ras_position[1], ras_position[2]]
            label = node.GetNthControlPointLabel(i)
            points.append({'label': label, 'position': lps_position})

        markups_data['points'] = points
        markups_data['name'] = node.GetName()
        markups_data['id'] = node.GetID()
        markups_data['number_of_points'] = n_points
        markups_data['coordinateSystem'] = "LPS"

        parent_transform = node.GetParentTransformNode()
        markups_data['parentTransformID'] = parent_transform.GetID() if parent_transform else None

        # For ROI nodes, also extract the bounding box size
        if node.IsA("vtkMRMLMarkupsROINode"):
            try:
                size = [0.0, 0.0, 0.0]
                node.GetRadiusXYZ(size)
                # GetRadiusXYZ() returns half-sizes, multiply by 2 for full size
                size = [s * 2 for s in size]
                markups_data['size'] = size
            except AttributeError:
                print(f"ROI node {node.GetName()} has no GetSize() method.")
                markups_data['size'] = None

        return json.dumps(markups_data)

    except Exception as extract_error:
        print(f"Failed to extract markup content for {node.GetName()}: {extract_error}")
        return "Failed to extract content"


# =============================================================================
# SAVE ON EXIT — triggered when Slicer is closing
# =============================================================================

def onAppExit(caller=None, event=None):
    """Save all markups, detect deletions, and update the markup log on exit.

    This is the core save logic, triggered by Slicer's aboutToQuit() signal.

    Steps:
      1. Read existing markup_log.csv into memory
      2. For each markup node currently in the scene:
         a. Match it to an existing log entry or file on disk
         b. If matched in log: save and update the JSON description from report_content
         c. If new or disk-only: save with auto-generated name (type_N.json)
      3. Detect deleted markups (in log + loaded successfully + not in scene)
      4. Write updated markup_log.csv
      5. If any saves failed, write an error CSV with extracted content
    """
    print("Slicer is closing. Saving all markups...")

    # Get all markup nodes currently in the Slicer scene
    final_markup_nodes = slicer.util.getNodesByClass('vtkMRMLMarkupsNode')

    # --- Step 1: Read existing markup log ---
    markup_log = {}    # {filename: {report_content, original_filename, created_at, deleted_at}}
    markup_error = {}  # Stores data for markups that failed to save

    if os.path.exists(markup_log_file):
        with open(markup_log_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('new_filename'):
                    continue
                markup_log[row['new_filename']] = {
                    'report_content': row.get('report_content', ''),
                    'original_filename': row.get('original_filename', ''),
                    'created_at': row.get('created_at', ''),
                    'deleted_at': row.get('deleted_at', '')
                }

    print("Cleaning up custom UI...")
    cleanUpCustomUI()

    # --- Determine the highest existing markup number ---
    # Scans actual JSON files on disk (not just the log) to prevent filename
    # collisions. E.g. if point_8.json exists, new files start at _9 and above.
    max_number = 0
    for existing_json in glob.glob(os.path.join(sourceFolder, "*.json")):
        basename = os.path.basename(existing_json).replace(".json", "")
        try:
            number_part = int(basename.split("_")[-1])
            if number_part > max_number:
                max_number = number_part
        except ValueError:
            continue

    now_str = datetime.datetime.now().isoformat()
    current_filenames = set()  # Track filenames of nodes currently in the scene

    # --- Step 2: Process each markup node in the scene ---
    for markupNode in final_markup_nodes:
        node_name = markupNode.GetName().strip()
        print(f"DEBUG: Processing node with name='{node_name}'")

        # --- Step 2a: Try to match this node to an existing file ---

        # First, check the markup log for a matching entry
        existing_file = None
        for fname in markup_log.keys():
            if fname.replace(".json", "") == node_name:
                existing_file = fname
                print(f"DEBUG: Matched node '{node_name}' to log entry '{fname}'")
                break

        # If not in log, check if a file with this name exists on disk
        # (handles the case where the log is empty/missing but files exist)
        if not existing_file:
            candidate = node_name + ".json"
            if os.path.isfile(os.path.join(sourceFolder, candidate)):
                existing_file = candidate
                print(f"DEBUG: Matched node '{node_name}' to existing file on disk '{candidate}'")

        if not existing_file:
            print(f"DEBUG: No existing file found for node '{node_name}'")

        # --- Step 2b: Determine the output filename ---
        if existing_file:
            # Reuse the existing filename
            safe_name = existing_file
        else:
            # New markup — assign a sequential filename based on markup type
            max_number += 1
            class_name = markupNode.GetClassName()
            if class_name == "vtkMRMLMarkupsFiducialNode":
                markup_type = "point"
            elif class_name == "vtkMRMLMarkupsLineNode":
                markup_type = "line"
            elif class_name == "vtkMRMLMarkupsROINode":
                markup_type = "roi"
            else:
                markup_type = "markup"
                print(f"Warning: Unknown markup class '{class_name}' for node '{node_name}', using default type 'markup'")
            safe_name = f"{markup_type}_{max_number}.json"

        output_path = os.path.join(sourceFolder, safe_name)
        current_filenames.add(safe_name)

        # Check if this file has an entry in the log (not just exists on disk)
        in_log = existing_file and existing_file in markup_log

        # --- Step 2c: Save the markup ---
        try:
            if in_log:
                # Existing markup with a log entry — save and update description
                updated_report_content = markup_log[existing_file].get('report_content', '')
                current_description = markupNode.GetDescription()

                print(f"Processing {safe_name}: current_desc='{current_description}', new_desc='{updated_report_content}'")

                # Save the markup JSON via Slicer's built-in save
                slicer.util.saveNode(markupNode, output_path)
                print(f"Saved markup: {output_path}")

                # Post-save: write report_content into the JSON's control point
                # description fields. This embeds the report text directly in the
                # markup file so it's available outside of the log.
                if updated_report_content:
                    try:
                        with open(output_path, 'r') as f:
                            markup_data = json.load(f)

                        if 'markups' in markup_data and len(markup_data['markups']) > 0:
                            markup = markup_data['markups'][0]
                            if 'controlPoints' in markup and len(markup['controlPoints']) > 0:
                                for control_point in markup['controlPoints']:
                                    control_point['description'] = updated_report_content

                                with open(output_path, 'w') as f:
                                    json.dump(markup_data, f, indent=4)
                                print(f"  -> Updated description in {len(markup['controlPoints'])} control point(s) to: '{updated_report_content}'")
                    except Exception as json_error:
                        print(f"  WARNING: Failed to update JSON description: {json_error}")

            else:
                # New markup or file exists on disk but not in log.
                # The annotator should have renamed the markup to a report sentence
                # (e.g. "7mm meningioma left anterior clinoid"). We use the node name
                # as report_content and also write it into the JSON's control point
                # description fields so it's embedded in the markup file itself.
                slicer.util.saveNode(markupNode, output_path)
                markup_log[safe_name] = {
                        'report_content': node_name,
                        'original_filename': '',
                        'created_at': now_str,
                        'deleted_at': ''
                }
                print(f"Saved markup: {output_path}")

                # Write node name into the JSON control point descriptions
                if node_name:
                    try:
                        with open(output_path, 'r') as f:
                            markup_data = json.load(f)

                        if 'markups' in markup_data and len(markup_data['markups']) > 0:
                            markup = markup_data['markups'][0]
                            if 'controlPoints' in markup and len(markup['controlPoints']) > 0:
                                for control_point in markup['controlPoints']:
                                    control_point['description'] = node_name

                                with open(output_path, 'w') as f:
                                    json.dump(markup_data, f, indent=4)
                                print(f"  -> Updated description in {len(markup['controlPoints'])} control point(s) to: '{node_name}'")
                    except Exception as json_error:
                        print(f"  WARNING: Failed to update JSON description: {json_error}")

        except OSError as e:
            # Save failed — extract content programmatically so no data is lost
            print(f"Error saving markup {node_name}: {e}")
            markup_error[safe_name] = {
                        'report_content': node_name,
                        'original_filename': '',
                        'created_at': now_str,
                        'deleted_at': '',
                        'json_content': extract_markup_content(markupNode)
                    }

    # --- Step 3: Detect deleted markups ---
    # A markup is considered "deleted by the annotator" only if ALL of:
    #   - It has an active entry in the log (no deleted_at timestamp)
    #   - It was successfully loaded into the scene at startup
    #   - It is no longer present in the scene at exit
    # This prevents accidental deletion of markups that simply failed to load.
    saved_filenames = {k for k, v in markup_log.items() if not v.get('deleted_at', '').strip()}
    loaded_filenames = {name + ".json" for name in loaded_markup_names}
    deleted_files = (saved_filenames & loaded_filenames) - current_filenames

    for deleted_file in deleted_files:
        file_path = os.path.join(sourceFolder, deleted_file)
        try:
            # Remove the JSON file from disk
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted markup file: {deleted_file}")
            # Mark as deleted in the log (preserves history)
            if deleted_file in markup_log:
                if not markup_log[deleted_file].get('deleted_at', '').strip():
                    markup_log[deleted_file]['deleted_at'] = now_str
        except Exception as e:
            print(f"Failed to delete {deleted_file}: {e}")

    # --- Step 4: Write the updated markup log ---
    with open(markup_log_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['new_filename', 'report_content', 'original_filename', 'created_at', 'deleted_at'])
        writer.writeheader()
        for filename, details in markup_log.items():
            writer.writerow({
                'new_filename': filename,
                'report_content': details.get('report_content', ''),
                'original_filename': details.get('original_filename', ''),
                'created_at': details.get('created_at', ''),
                'deleted_at': details.get('deleted_at', '')
            })

    # --- Step 5: Write error log if any saves failed ---
    # The error CSV includes the extracted JSON content so markup data
    # can be recovered even if the normal save path failed.
    if markup_error:
        safe_timestamp = re.sub(r'[:]', '-', now_str)
        error_filename = f"{safe_timestamp}_error.csv"
        error_filepath = os.path.join(sourceFolder, error_filename)

        with open(error_filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['new_filename', 'report_content', 'original_filename', 'created_at', 'deleted_at', 'json_content'])
            writer.writeheader()
            for filename, details in markup_error.items():
                writer.writerow({
                    'new_filename': filename,
                    'report_content': details.get('report_content', ''),
                    'original_filename': details.get('original_filename', ''),
                    'created_at': details.get('created_at', ''),
                    'deleted_at': details.get('deleted_at', ''),
                    'json_content': details.get('json_content', '')
                })

        print(f"Saved markup errors to: {error_filepath}")


# =============================================================================
# FIND THE REPORT TEXT FILE
# =============================================================================

# Look for report_*.txt in the session folder (there should be exactly one)
report_files = glob.glob(os.path.join(args.source_folder, "report_*.txt"))

if report_files:
    report_file_path = report_files[0]
else:
    report_file_path = None


# =============================================================================
# STARTUP SEQUENCE — timed callbacks to allow Slicer's UI to fully initialise
# =============================================================================

# Register the exit handler — onAppExit() runs when Slicer is about to quit
slicer.app.connect("aboutToQuit()", onAppExit)

# Stagger UI setup with QTimer to ensure each step completes before the next:
#   50ms  — Strip down Slicer's UI (hide unnecessary components)
#   100ms — Load volumes and markups into the scene
#   150ms — Add the custom module dropdown toolbar
#   200ms — Show the radiology report in a side panel
#   250ms — Final check that the module panel is visible
QTimer.singleShot(50, hideAllGUIComponents)
QTimer.singleShot(100, loadEverything)
QTimer.singleShot(150, initialiseCustomUI)
QTimer.singleShot(200, lambda: show_report_dock(report_file_path, args.report_number))
QTimer.singleShot(250, ensureModulePanelVisible)
