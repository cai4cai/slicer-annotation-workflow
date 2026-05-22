# slicer-annotation-workflow

## Annotation Workflow Summary

### 1. Install 3D Slicer
Download and install **3D Slicer 5.8.1**.

### 2. Choose Your Workflow Version

This repository contains **four annotation workflow versions**:

| Folder | Platform | Features |
|--------|----------|----------|
| `annotation_mac/` | macOS | Basic markup logging with filename encoding |
| `annotation_mac_xlsx/` | macOS | Advanced tracking with report content descriptions |
| `annotation_windows/` | Windows | Basic markup logging with filename encoding |
| `annotation_windows_xlsx/` | Windows | Advanced tracking with report content descriptions |

**Recommended**: Use the `*_xlsx` versions for better markup-to-report tracking. All versions use CSV-based logging with no external dependencies.

### 3. Run the Annotation Launcher
Navigate to your chosen workflow folder and use the appropriate script:

- **macOS**: `./run_annotation.command`
- **Windows**: `run_annotation.bat`

#### First-Time Setup: Security Permissions

**macOS Users:**

When running `run_annotation.command` for the first time, you may encounter a security warning:

1. **If "Unidentified Developer" warning appears:**
   - Right-click (or Control+click) on `run_annotation.command`
   - Select **"Open"** from the context menu
   - Click **"Open"** in the security dialog
   - Alternatively, go to **System Preferences > Security & Privacy > General** and click **"Open Anyway"**

2. **If permission denied:**
   - Open Terminal in the workflow folder
   - Run: `chmod +x run_annotation.command`
   - Run: `chmod +x execute.sh`
   - Then double-click `run_annotation.command` again

**Windows Users:**

When running `run_annotation.bat` for the first time, you may encounter a security warning:

1. **If "Windows protected your PC" SmartScreen warning appears:**
   - Click **"More info"**
   - Click **"Run anyway"**

2. **If User Account Control (UAC) prompt appears:**
   - Click **"Yes"** to allow the script to run

3. **If Windows Defender blocks execution:**
   - Go to **Windows Security > Virus & threat protection > Manage settings**
   - Add the workflow folder to **Exclusions**
   - Or click **"Allow on device"** in the Windows Defender notification

These security checks only occur on first run. Subsequent executions will work normally.

### 4. Perform Annotations in 3D Slicer  

Create the following **Markups** as per the radiology report:

- **Point** — for single localised findings.
- **ROI (Region of Interest)** — for lesions or treated areas.
- **Line** — to measure the longest visible axis if specified in the report.

### 5. Logging Progress

After annotating each case:

- Open the `log.csv` file located in your workflow directory.
- Update the **Done** column for each completed case.

**`*_xlsx` Versions Only**: Markup details are automatically tracked in `markup_log.csv` within each patient's scanning session folder, showing:
- Filename and report content description (from markup name)
- Creation and deletion timestamps
- Report content is also embedded in each markup JSON's control point descriptions

---

## Differences Between Workflow Versions

### CSV Versions (`annotation_mac/`, `annotation_windows/`)
- No additional dependencies
- Simpler, lightweight
- Basic markup tracking using filename encoding for special characters

### `*_xlsx` Versions (`annotation_mac_xlsx/`, `annotation_windows_xlsx/`)
- No additional dependencies (uses Python stdlib only)
- Advanced markup tracking with full history in `markup_log.csv`
- Correlates markups with report content (annotator renames markups to report sentences)
- Report descriptions embedded in markup JSON control point descriptions
- Safe deletion detection (only deletes markups that loaded successfully)
- Auto-numbered filenames by markup type (`point_1.json`, `line_2.json`, `roi_3.json`)

---

## Additional Resources

You can find more details about the instructions and videos in [OneDrive folder](https://emckclac-my.sharepoint.com/:f:/g/personal/k23049667_kcl_ac_uk/Ei5hzQrk8yhEksQblKg8FAkBSNba7ot8JC8LkvulSl-nWg?e=TPpxQk)
