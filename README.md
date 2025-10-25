# slicer-annotation-workflow

## Annotation Workflow Summary

### 1. Install 3D Slicer
Download and install **3D Slicer 5.8.1**.

### 2. Choose Your Workflow Version

This repository contains **four annotation workflow versions**:

| Folder | Platform | Log Format | Features |
|--------|----------|------------|----------|
| `annotation_mac/` | macOS | CSV | Basic markup logging |
| `annotation_mac_xlsx/` | macOS | Excel | Advanced tracking with markup log table UI |
| `annotation_windows/` | Windows | CSV | Basic markup logging |
| `annotation_windows_xlsx/` | Windows | Excel | Advanced tracking with markup log table UI |

**Recommended**: Use the **Excel versions** (`*_xlsx`) for better markup tracking and visualization.

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

**Excel Versions Only**: Markup details are automatically tracked in `markup_log.xlsx` within each patient's scanning session folder, showing:
- Filename and original markup name
- Creation and deletion timestamps
- Visual table in Slicer UI showing markup-to-report correlation

---

## Differences Between CSV and Excel Versions

### CSV Versions (`annotation_mac/`, `annotation_windows/`)
- ✅ No additional dependencies
- ✅ Simpler, lightweight
- ❌ Basic markup tracking
- Uses filename encoding for special characters

### Excel Versions (`annotation_mac_xlsx/`, `annotation_windows_xlsx/`)
- ✅ Advanced markup tracking with full history
- ✅ Markup log table displayed in Slicer UI
- ✅ Better correlation between markups and report content
- ✅ Automatic filtering of deleted markups
- ⚙️ Auto-installs pandas and openpyxl on first run

---

## Additional Resources

You can find more details about the instructions and videos in [OneDrive folder](https://emckclac-my.sharepoint.com/:f:/g/personal/k23049667_kcl_ac_uk/Ei5hzQrk8yhEksQblKg8FAkBSNba7ot8JC8LkvulSl-nWg?e=TPpxQk)
