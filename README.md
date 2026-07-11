# Slicer Annotation Workflow

A system for annotating medical imaging data (NIfTI files) based on radiology reports using [3D Slicer](https://www.slicer.org/). Annotators create markups (Points, ROIs, Lines) on brain scans to localise findings described in reports.

> We recommend using a mouse for easier navigation and annotation.

---

## 1. Install 3D Slicer

You can download 3D Slicer from [https://download.slicer.org](https://download.slicer.org).

### macOS

1. Double-click `Slicer-5.8.1-macosx-amd64.dmg` (or the version provided).
2. Drag **3D Slicer.app** to your **Applications** folder.
3. Open 3D Slicer once from Applications to approve security permissions.

### Windows

1. Double-click `Slicer-5.8.1-win-amd64.exe` (or the version provided).
2. If a security prompt appears, click **Yes**.
3. Follow the installation wizard using the default location, click **Next** then **Install**.

---

## 2. Choose Your Platform

| Folder | Platform | Launcher |
|--------|----------|----------|
| `annotation_mac/` | macOS | `run_annotation.command` |
| `annotation_windows/` | Windows | `run_annotation.bat` |

Both versions are functionally identical — only the launcher and execute scripts differ to accommodate each OS.

---

## 3. Folder Structure

After downloading and extracting the provided `.zip` file, you will find the following structure:

```
annotation_mac/ (or annotation_windows/)
├── run_annotation.command (.bat)   # Double-click to start
├── execute.sh (.bat)               # Finds patient data and launches Slicer
├── auto_script.py                  # Runs inside Slicer (loads data, UI, saving)
├── log.csv                         # Tracks annotation progress
└── patients/
    └── patient1/
        └── scanning_session1/
            ├── *.nii.gz            # Medical imaging volumes (NIfTI)
            ├── report_<number>.txt # Radiology report for this session
            ├── point_1.json        # Markup annotations (created by annotator)
            ├── roi_2.json
            ├── line_3.json
            └── markup_log.csv      # Tracks all markup changes for this session
```

### File Naming Conventions

| File | Format | Description |
|------|--------|-------------|
| Patient folders | `patient1/`, `patient2/`, ... | Numbered patient directories |
| Scanning sessions | `scanning_session1/`, `scanning_session2/`, ... | One or more sessions per patient |
| Imaging volumes | `*.nii.gz` or `*.nii` | NIfTI format medical imaging data |
| Radiology reports | `report_<number>.txt` | One plain text report per scanning session |
| Markup annotations | `point_<N>.json`, `roi_<N>.json`, `line_<N>.json` | Auto-numbered by type when created |
| Markup log | `markup_log.csv` | Tracks all markups per scanning session (created automatically) |
| Progress log | `log.csv` | Maps report numbers to session folders with a Done column for self tracking work|

### log.csv Format

```csv
Report,Path,Done
1,./patients/patient1/scanning_session1,
2,./patients/patient1/scanning_session2,True
```

- **Report**: unique identifier for each case
- **Path**: relative path to the patient's scanning session folder
- **Done**: for self tracking annotations

### markup_log.csv Format

```csv
new_filename,report_content,created_at,deleted_at
point_1.json,Right cerebellar convexity enhancing lesion,2026-07-01T10:30:00,
roi_2.json,Right cerebellar convexity enhancing lesion,2026-07-01T10:31:00,
```

- **new_filename**: the JSON filename on disk
- **report_content**: the annotator's description (from the markup name)
- **created_at** / **deleted_at**: ISO timestamps tracking the markup's lifecycle

---

## 4. First-Time Setup

### macOS

When double-clicking `run_annotation.command` for the first time:

1. A window may say *"Apple could not verify run_annotation.command is free of malware"* — click **Done**.
2. Go to **Settings > Privacy & Security**, scroll down, and find *"run_annotation.command was blocked"*.
3. Click **Open Anyway**, then **Open Anyway** again in the prompt that follows.
4. Enter your password if prompted.

If you get a "permission denied" error, open Terminal in the workflow folder and run:
```bash
chmod +x run_annotation.command execute.sh
```

### Windows

When double-clicking `run_annotation.bat` for the first time:

1. If *"Windows protected your PC"* appears, click **More info**, then **Run anyway**.

These security steps only need to be done once.

---

## 5. Running an Annotation Session

1. Double-click `run_annotation.command` (macOS) or `run_annotation.bat` (Windows).
2. A terminal window opens and asks for a report number — type a number from `log.csv` and press Enter.
3. 3D Slicer opens automatically with:
   - **Left panel**: loaded scan files and any existing annotations
   - **Middle panel**: three cross-sectional viewers (Red = Axial, Yellow = Sagittal, Green = Coronal)
   - **Right panel**: the radiology report text

![Annotation GUI](Annotation_GUI.pdf)

### Navigating Slices

- **Mouse scroll wheel**: hover over a viewer and scroll up/down
- **Slider**: use the slider at the top of each viewer panel
- **Double-click** a viewer to maximise it; double-click again to restore all three

### Module Dropdown

A dropdown menu provides access to three modules:

- **Data** — view and toggle scan visibility
- **Markups** — create, edit, or delete annotations
- **Volumes** — adjust visualisation settings (window/level, colour maps, opacity)

---

## 6. Making Annotations

### Markup Types

| Markup | Use For | How to Create |
|--------|---------|---------------|
| **Point** | Centre of a lesion or any finding in the report | Markups > Create > Point List, then click on the location |
| **ROI** | 3D box enclosing a lesion or treated area | Markups > Create > ROI, click bottom-left then top-right to define the box, then drag sides/corners to adjust |
| **Line** | Maximum axial dimension of a lesion (when mentioned in the report) | Markups > Create > Line, click start point then end point |

### Naming Markups

After creating a markup:

1. Right-click on its name in the Markups list (left panel).
2. Choose **Rename**.
3. Enter the **exact wording from the radiology report** for that finding.

> Example: if the report says *"Right cerebellar convexity extra-axial enhancing lesion"*, name the Point, ROI, and Line all exactly: `Right cerebellar convexity extra-axial enhancing lesion`

If the report refers to *"multiple meningiomas in [X location]"*, create a set of annotations per lesion with the report name `multiple meningiomas in [X location]`.

### What to Annotate

| Finding Type | Markups to Create |
|-------------|-------------------|
| **Meningioma lesion** | Point (centre) + ROI (enclosing box) + Line (dimension if mentioned) |
| **Treatment-related** (resection, craniotomy, post-op cavity, radiation change) | Point at the relevant location|
| **Other findings** (hydrocephalus, oedema, haemorrhage, cyst, other tumours, etc.) | Point(s) at the relevant location |

---

## 7. Finishing an Annotation Session

1. Close the 3D Slicer window.
2. If asked *"Do you want to save the scene?"*, choose **Exit (discard modifications)**.
3. Close the terminal window.

Your annotations are **automatically saved** when you close Slicer — there is no need to save the scene.

### What Happens Behind the Scenes

- All markups (Points, ROIs, Lines) are saved as JSON files in the same folder as the scans.
- `markup_log.csv` in each patient's session folder is updated with creation/deletion timestamps and report content.
- You can revisit a case anytime — previously created markups will load automatically.

### Windows-Specific Notes

- **Do not keep `markup_log.csv` open** while Slicer is running. Windows locks files opened in Excel, which prevents the script from updating the log.


---

## Additional Resources

Video tutorials and further instructions are available in the [OneDrive folder](https://emckclac-my.sharepoint.com/:f:/g/personal/k23049667_kcl_ac_uk/Ei5hzQrk8yhEksQblKg8FAkBSNba7ot8JC8LkvulSl-nWg?e=TPpxQk).
