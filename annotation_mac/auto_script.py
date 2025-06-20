# --- Import required modules ---
import os
import argparse
import slicer
import qt
from qt import QTimer
import datetime
import json
import glob

# --- Configure application settings ---
settings = slicer.app.settings()
settings.setValue("SubjectHierarchy/ResetFieldOfViewOnShowVolume", False)
settings.setValue("SubjectHierarchy/ResetViewOrientationOnShowVolume", False)


# --- Parse command line arguments from Slicer ---
parser = argparse.ArgumentParser()
parser.add_argument('--source_folder', required=True)  # Source directory for data
parser.add_argument('--nifti_files', nargs='*', default=[])  # List of NIfTI file paths
parser.add_argument('--markup_files', nargs='*', default=[])  # List of markup JSON files
parser.add_argument('--report_number', required=True)  # Report number for log identification
parser.add_argument('--log_csv', required=True)  # Path to main log CSV file
args = parser.parse_args()

# --- Define paths and initialise variables ---
sourceFolder = os.path.abspath(args.source_folder)
nifti_files = [os.path.normpath(p) for p in args.nifti_files]
markup_files = [os.path.normpath(p) for p in args.markup_files]
markup_log_file = os.path.join(sourceFolder, "markup_log.csv")
loaded_markup_names = []  # Track loaded markup names

# --- Ensure markup log file exists, create with headers if missing ---
if not os.path.exists(markup_log_file):
    with open(markup_log_file, 'w') as log:
        log.write("filename,created_at,content,deleted_at\n")

# --- Set default style as Light ---
slicer.app.setStyle("Light Slicer")

# --- Sanitise filenames easy encoding and decoding
def encode_filename(name):
    replacements = {
        '/': '_S_',
        '\\': '_B_',
        ':': '_C_',
        '*': '_A_',
        '?': '_Q_',
        '"': '_W_',
        '<': '_L_',
        '>': '_G_',
        '|': '_P_',
        '\0': '_N_',
        ' ': '_U_',
        ',': '_Z_',
        '"': '_E_'
    }
    for char, code in replacements.items():
        name = name.replace(char, code)
    return name

def decode_filename(encoded_name):
    replacements = {
        '_S_': '/',
        '_B_': '\\',
        '_C_': ':',
        '_A_': '*',
        '_Q_': '?',
        '_W_': '"',
        '_L_': '<',
        '_G_': '>',
        '_P_': '|',
        '_N_': '\0',
        '_U_': ' ',
        '_Z_': ',',
        '_E_': '"'
    }
    for code, char in replacements.items():
        encoded_name = encoded_name.replace(code, char)
    return encoded_name

# --- Function to load NIfTI and markup files into Slicer ---
def loadEverything():
    if nifti_files:
        for nifti_path in nifti_files:
            print(f"Loading volume: {nifti_path}")
            slicer.util.loadVolume(nifti_path)
    else:
        print("No NIfTI files provided.")

    if markup_files:
        print("Loading markup files...")
        for markup_path in markup_files:
            if markup_path and os.path.isfile(markup_path):
                try:
                    slicer.util.loadMarkups(markup_path)
                    loaded_markup_names.append(os.path.basename(markup_path).replace(".json", ""))
                    print(f"Loaded markup: {markup_path}")
                except Exception as e:
                    print(f"Failed to load markup {markup_path}: {e}")
            else:
                print(f"Markup file not found: {markup_path}")
    else:
        print("No markup files provided.")

    slicer.util.selectModule('Data')
    print("Ready for annotation.")

    setAnatomicalSliceViews()

# --- Set 3D slice visibility on the fourth viewer ---
# Get all slice composite nodes (which control slice visibility in 3D)
scene = slicer.mrmlScene
sliceNodes = scene.GetNodesByClass("vtkMRMLSliceNode")

# Toggle visibility for each slice in 3D view
sliceNodes.InitTraversal()
for i in range(sliceNodes.GetNumberOfItems()):
    sliceNode = sliceNodes.GetItemAsObject(i)
    sliceNode.SetSliceVisible(True)
    # currentVisibility = sliceNode.GetSliceVisible()
    # sliceNode.SetSliceVisible(not currentVisibility)  # Toggle: 1 → 0, 0 → 1

# --- Global references for UI components ---
moduleDropdown = None
customToolBar = None

# --- Add a module selection dropdown to the toolbar ---
def addAllowedModuleDropdown(moduleToolBar, allowedModules=None):
    global moduleDropdown
    if moduleToolBar is None:
        return
    if allowedModules is None:
        allowedModules = ['Data', 'Markups', 'Volumes']

    moduleDropdown = qt.QComboBox(moduleToolBar)
    moduleDropdown.addItems(allowedModules)

    # Event handler to switch module when dropdown selection changes
    def onModuleSelected(index):
        moduleName = moduleDropdown.itemText(index)
        slicer.util.selectModule(moduleName)
        print(f"Switched to module: {moduleName}")

    moduleDropdown.currentIndexChanged.connect(onModuleSelected)
    moduleToolBar.addWidget(moduleDropdown)
    slicer.util.selectModule(allowedModules[0])
    print(f"Available modules now: {allowedModules}")
    return moduleDropdown

# --- Initialise custom UI including favourites and dropdown ---
def initialiseCustomUI():
    global customToolBar
    mw = slicer.util.mainWindow()
    if not mw:
        print("Main window not found, cannot initialise UI")
        return

    # Define favourites list
    favourites = ['Data', 'Markups', 'Volumes']
    # settings = slicer.app.settings()
    # settings.setValue('Modules/FavoriteModules', favourites)

    # # Get existing Modules toolbar
    # favToolbar = mw.findChild(qt.QToolBar, "ModulesToolBar")
    # if favToolbar:
    #     favToolbar.clear()

    #     for moduleName in favourites:
    #         action = qt.QAction(moduleName, favToolbar)
    #         action.connect("triggered()", lambda checked=False, mn=moduleName: slicer.util.selectModule(mn))
    #         favToolbar.addAction(action)

    #     favToolbar.setVisible(True)
    #     print("Favourites toolbar updated and shown.")
    # else:
    #     print("Could not find Favourites toolbar.")

    # Create custom toolbar with dropdown next to it
    customToolBar = qt.QToolBar("CustomModuleToolbar", mw)
    mw.addToolBar(customToolBar)

    # Add dropdown with the favourite modules
    addAllowedModuleDropdown(customToolBar, favourites)

    customToolBar.show()
    print("Custom module dropdown added.")

# # function below shows custom buttons
# def initialiseCustomUI():
#     global customToolBar
#     mw = slicer.util.mainWindow()
#     if not mw:
#         print("Main window not found, cannot create toolbar")
#         return

#     customToolBar = qt.QToolBar("CustomModuleToolbar", mw)
#     mw.addToolBar(customToolBar)

#     # Add module dropdown
#     addAllowedModuleDropdown(customToolBar, ['Data', 'Markups', 'Volumes'])

#     # Function to create a module button with icon and tooltip
#     def createModuleButton(moduleName, iconName):
#         button = qt.QToolButton()
#         button.setIcon(slicer.app.style().standardIcon(getattr(qt.QStyle, iconName)))
#         button.setToolTip(f"Open {moduleName} module")

#         def onClick():
#             slicer.util.selectModule(moduleName)
#             print(f"Switched to module: {moduleName}")

#         button.clicked.connect(onClick)
#         return button

#     # Add module icon-buttons to the toolbar
#     dataButton = createModuleButton("Data", "SP_DirOpenIcon")
#     markupsButton = createModuleButton("Markups", "SP_FileDialogContentsView")
#     volumesButton = createModuleButton("Volumes", "SP_FileDialogDetailedView")

#     customToolBar.addWidget(dataButton)
#     customToolBar.addWidget(markupsButton)
#     customToolBar.addWidget(volumesButton)

#     customToolBar.show()
#     print("Custom module dropdown and icons added.")

# --- Clean up custom UI elements on exit ---
def cleanUpCustomUI():
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

# --- Save markups, update logs, and clean UI on application exit ---
def onAppExit(caller=None, event=None):
    print("Slicer is closing. Cleaning up custom UI...")
    cleanUpCustomUI()

    print("Slicer is closing. Saving all markups...")

    final_markup_nodes = slicer.util.getNodesByClass('vtkMRMLMarkupsNode')

    # Load existing markup log
    markup_log = {}
    if os.path.exists(markup_log_file):
        with open(markup_log_file, 'r') as log:
            for line in log.readlines()[1:]:
                parts = line.strip().split(",", 3)
                if len(parts) >= 4:
                    markup_log[parts[0]] = {
                        'created_at': parts[1],
                        'content': parts[2],
                        'deleted_at': parts[3]
                    }
    # Get the last appended number if markup_log has any entries
    if len(markup_log) != 0:
        max_number = 0
        for markup in markup_log:
            try:
                number_part = int(markup.replace(".json", "").split("_")[-1])
                if number_part > max_number:
                    max_number = number_part
            except ValueError:
                # Skip if filename doesn't end with a number
                continue
    else:
        max_number = 0

    now_str = datetime.datetime.now().isoformat()
    current_filenames = set()

    for markupNode in final_markup_nodes:
        node_name = markupNode.GetName()#.replace(" ", "_")
        encoded_node_name = encode_filename(node_name)

        # Check if this markup has already been saved by looking for filenames starting with node_name_
        existing_file = None
        for fname in markup_log.keys():
            if fname == encoded_node_name+".json":
                existing_file = fname
                break

        if existing_file:
            safe_name = existing_file
        else:
            max_number += 1
            # node_id = markupNode.GetID()
            # base_name = f"{node_name}_{node_id}".replace(" ", "_")
            base_name = encoded_node_name
            safe_name = f"{base_name}_{max_number}.json"

        output_path = os.path.join(sourceFolder, safe_name)
        current_filenames.add(safe_name)

        try:
            markupNode.Modified()
            if slicer.util.saveNode(markupNode, output_path):
                print(f"Saved markup:{output_path}")

                with open(output_path, 'r') as f:
                    content = json.dumps(json.load(f)).replace("\n", "").replace(",", ";")

                if safe_name not in markup_log:
                    markup_log[safe_name] = {
                        'created_at': now_str,
                        'content': content,
                        'deleted_at': ""
                    }
                else:
                    markup_log[safe_name]['content'] = content
                    markup_log[safe_name]['deleted_at'] = ""

            else:
                print(f"Failed to save markup: {node_name}")

        except Exception as e:
            print(f"Error saving markup {node_name}: {e}")

    # Detect deleted markups (present in log but no longer in scene)
    saved_filenames = set(markup_log.keys())
    deleted_files = saved_filenames - current_filenames

    for deleted_file in deleted_files:
        file_path = os.path.join(sourceFolder, deleted_file)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted markup file: {deleted_file}")
            if markup_log.get(deleted_file, {}).get('deleted_at', "") == "":
                markup_log[deleted_file]['deleted_at'] = now_str
        except Exception as e:
            print(f"Failed to delete {deleted_file}: {e}")

    # Save updated markup log
    with open(markup_log_file, 'w') as log:
        log.write("filename,created_at,content,deleted_at\n")
        for fname, data in markup_log.items():
            log.write(f"{fname},{data['created_at']},\"{data['content']}\",{data['deleted_at']}\n")

    # Update report log
    log_csv = os.path.abspath(args.log_csv)
    temp_csv = log_csv + ".tmp"
    report_number = args.report_number

    try:
        done_status = "True" if len(final_markup_nodes) > 0 else ""

        with open(log_csv, 'r') as infile, open(temp_csv, 'w') as outfile:
            for line in infile:
                if line.startswith(report_number + ","):
                    parts = line.strip().split(',')
                    while len(parts) < 3:
                        parts.append("")
                    parts[2] = done_status
                    outfile.write(",".join(parts) + "\n")
                else:
                    outfile.write(line)
        os.replace(temp_csv, log_csv)
        print(f"Updated log for report {report_number} to Done={done_status if done_status else 'Empty'}")
    except Exception as e:
        print(f"Failed to update log file: {e}")

# --- UI customisation routines ---
def hideAllGUIComponents():

    def mainWindow():
        return slicer.util.mainWindow()

    def findChild(parent, name):
        return parent.findChild(qt.QWidget, name)

    mw = mainWindow()
    if mw is None:
        print("No main window found.")
        return

    # # Hide toolbars
    # for toolbar in mw.findChildren(qt.QToolBar):
    #     toolbar.setVisible(False)

    # Hide menubars
    # for menubar in mw.findChildren(qt.QMenuBar):
    #     menubar.setVisible(False)

    # Hide status bar
    if mw.statusBar():
        mw.statusBar().setVisible(False)

    # Hide Python console
    console = mw.pythonConsole().parent()
    if console:
        console.setVisible(False)

    # Hide Error log
    mw.errorLogDockWidget().setVisible(False)

    # # Hide View Controllers
    # lm = slicer.app.layoutManager()
    # if lm:
    #     for viewIndex in range(lm.threeDViewCount):
    #         lm.threeDWidget(viewIndex).threeDController().setVisible(False)
    #     for sliceViewName in lm.sliceViewNames():
    #         lm.sliceWidget(sliceViewName).sliceController().setVisible(False)
    #     for viewIndex in range(lm.tableViewCount):
    #         lm.tableWidget(viewIndex).tableController().setVisible(False)
    #     for viewIndex in range(lm.plotViewCount):
    #         lm.plotWidget(viewIndex).plotController().setVisible(False)

    # Hide module panel title bar
    modulePanelDockWidgets = mw.findChildren(qt.QDockWidget, "PanelDockWidget")
    for dock in modulePanelDockWidgets:
        dock.setTitleBarWidget(qt.QWidget(dock))

    # # Hide application logo
    # logoLabel = findChild(mw, "LogoLabel")
    # if logoLabel:
    #     logoLabel.setVisible(False)

    # Hide Help section
    modulePanel = findChild(mw, "ModulePanel")
    if modulePanel:
        modulePanel.helpAndAcknowledgmentVisible = False

    # Hide Data probe
    dataProbeWidget = findChild(mw, "DataProbeCollapsibleWidget")
    if dataProbeWidget:
        dataProbeWidget.setVisible(False)

# --- Ensure that anatomical coordinates are used ---
def setAnatomicalSliceViews():
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

# --- Custom widget to display report on the right ---
def show_report_dock(report_file_path, report_number):
    mw = slicer.util.mainWindow()

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

    if os.path.exists(report_file_path):
        with open(report_file_path, 'r') as f:
            textBrowser.setPlainText(f.read())
    else:
        textBrowser.setPlainText(f"Report file not found: {report_file_path}")

    dockLayout.addWidget(textBrowser)

    dockWidget.setWidget(dockContents)
    mw.addDockWidget(qt.Qt.RightDockWidgetArea, dockWidget)
    dockWidget.show()

# report_file_path = os.path.join(args.source_folder, f"report_{args.report_number}.txt")
# Find all files matching report_*.txt in the source folder
report_files = glob.glob(os.path.join(args.source_folder, "report_*.txt"))

# If you expect only one match and want to get it:
if report_files:
    report_file_path = report_files[0]  # or handle multiple files if needed
else:
    report_file_path = None  # or raise an error / handle missing file

# --- Bind exit event and initialise app ---
slicer.app.connect("aboutToQuit()", onAppExit)
QTimer.singleShot(50, hideAllGUIComponents)
QTimer.singleShot(100, loadEverything)
QTimer.singleShot(150, initialiseCustomUI)
QTimer.singleShot(200, lambda: show_report_dock(report_file_path, args.report_number))