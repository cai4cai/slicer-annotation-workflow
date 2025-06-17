# slicer-annotation-workflow

## Annotation Workflow Summary

### 1. Install 3D Slicer  
Download and install **3D Slicer 5.8.1**.

### 2. Run the Annotation Launcher  
Use the appropriate script for your system:

- **macOS**: `run_annotation.command`
- **Windows**: `run_annotation.bat`

### 3. Perform Annotations in 3D Slicer  

Create the following **Markups** as per the radiology report:

- **Point** — for single localised findings.
- **ROI (Region of Interest)** — for lesions or treated areas.
- **Line** — to measure the longest visible axis if specified in the report.

### 4. Logging Progress  

After annotating each case:

- Open the `log.csv` file located in your fold’s directory.
- Update the **Done** column for each completed case.

You can find more details about the instructions and videos in [OneDrive folder](https://emckclac-my.sharepoint.com/:f:/g/personal/k23049667_kcl_ac_uk/Ei5hzQrk8yhEksQblKg8FAkBSNba7ot8JC8LkvulSl-nWg?e=TPpxQk)
