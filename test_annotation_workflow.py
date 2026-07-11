#!/usr/bin/env python3
"""
Tests to verify an annotation workflow folder is ready for use.

Checks that:
1. Required scripts are present (launcher, execute, auto_script)
2. log.csv exists and has the correct format
3. All paths in log.csv point to valid patient session folders
4. Each session folder contains NIfTI scans and a report text file
5. Report numbers are valid and non-duplicate

Usage:
    # Test a specific workflow folder
    python test_annotation_workflow.py --workflow /path/to/annotation_mac

    # Auto-detect workflow folders in current directory
    python test_annotation_workflow.py

    # Verbose output
    python test_annotation_workflow.py -v
"""

import unittest
import csv
import argparse
import sys
from pathlib import Path


# Global variable to store custom workflow path
CUSTOM_WORKFLOW = None


class TestWorkflowReady(unittest.TestCase):
    """Test that a workflow folder is complete and ready for annotation."""

    def setUp(self):
        """Find workflow directories to test."""
        global CUSTOM_WORKFLOW

        self.workflows = []

        if CUSTOM_WORKFLOW:
            workflow_path = Path(CUSTOM_WORKFLOW)
            if workflow_path.exists() and workflow_path.is_dir():
                self.workflows.append(workflow_path)
            return

        # Auto-detect workflow folders in the script's directory
        base_dir = Path(__file__).parent
        for workflow_dir in ['annotation_mac', 'annotation_windows']:
            workflow_path = base_dir / workflow_dir
            if workflow_path.exists() and workflow_path.is_dir():
                self.workflows.append(workflow_path)

    def test_workflow_found(self):
        """At least one workflow directory exists."""
        self.assertGreater(len(self.workflows), 0,
                           "No annotation workflow directories found")

    def test_launcher_script_exists(self):
        """Launcher script exists (run_annotation.command or .bat)."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                launchers = list(wf.glob('run_annotation.*'))
                self.assertGreater(len(launchers), 0,
                                   f"No run_annotation script found in {wf.name}")

    def test_execute_script_exists(self):
        """Execute script exists (execute.sh or .bat)."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                executors = list(wf.glob('execute.*'))
                self.assertGreater(len(executors), 0,
                                   f"No execute script found in {wf.name}")

    def test_auto_script_exists(self):
        """auto_script.py exists."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                self.assertTrue(
                    (wf / 'auto_script.py').exists(),
                    f"auto_script.py not found in {wf.name}")

    def test_log_csv_exists(self):
        """log.csv exists."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                self.assertTrue(
                    (wf / 'log.csv').exists(),
                    f"log.csv not found in {wf.name}")

    def test_log_csv_format(self):
        """log.csv has the correct header: Report,Path,Done."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                with open(log_csv, 'r') as f:
                    header = next(csv.reader(f))

                self.assertEqual(len(header), 3,
                                 f"log.csv should have 3 columns, got {len(header)}")
                self.assertEqual(header, ['Report', 'Path', 'Done'],
                                 f"log.csv header should be ['Report', 'Path', 'Done'], got {header}")

    def test_log_csv_report_numbers_valid(self):
        """All report numbers in log.csv are numeric."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                with open(log_csv, 'r') as f:
                    reader = csv.DictReader(f)
                    for row_num, row in enumerate(reader, start=2):
                        report = row.get('Report', '').strip()
                        self.assertTrue(
                            report.isdigit(),
                            f"Row {row_num}: Report '{report}' is not a valid number")

    def test_log_csv_no_duplicate_reports(self):
        """No duplicate report numbers in log.csv."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                reports = []
                with open(log_csv, 'r') as f:
                    for row in csv.DictReader(f):
                        reports.append(row.get('Report', '').strip())

                duplicates = [r for r in reports if reports.count(r) > 1]
                self.assertEqual(len(set(duplicates)), 0,
                                 f"Duplicate report numbers: {set(duplicates)}")

    def test_log_csv_report_numbers_sequential(self):
        """Report numbers in log.csv are sequential starting from 1."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                numbers = []
                with open(log_csv, 'r') as f:
                    for row in csv.DictReader(f):
                        report = row.get('Report', '').strip()
                        if report.isdigit():
                            numbers.append(int(report))

                if not numbers:
                    self.skipTest("No valid report numbers")

                numbers.sort()
                expected = list(range(1, len(numbers) + 1))
                self.assertEqual(numbers, expected,
                                 f"Report numbers are not sequential: {numbers}")

    def test_patients_directory_exists(self):
        """patients/ directory exists."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                self.assertTrue(
                    (wf / 'patients').exists(),
                    f"patients/ directory not found in {wf.name}")

    def test_session_folders_exist(self):
        """All paths in log.csv point to existing directories."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                with open(log_csv, 'r') as f:
                    for row in csv.DictReader(f):
                        report = row.get('Report', '').strip()
                        path = row.get('Path', '').strip()
                        if path.startswith('./'):
                            path = path[2:]

                        session_dir = wf / path
                        self.assertTrue(
                            session_dir.is_dir(),
                            f"Report {report}: session folder '{path}' does not exist")

    def test_sessions_have_nifti_files(self):
        """Each session folder contains at least one NIfTI file."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                with open(log_csv, 'r') as f:
                    for row in csv.DictReader(f):
                        report = row.get('Report', '').strip()
                        path = row.get('Path', '').strip()
                        if path.startswith('./'):
                            path = path[2:]

                        session_dir = wf / path
                        if not session_dir.exists():
                            continue

                        nifti = list(session_dir.glob('*.nii')) + list(session_dir.glob('*.nii.gz'))
                        self.assertGreater(
                            len(nifti), 0,
                            f"Report {report}: no NIfTI files in {path}")

    def test_sessions_have_report_file(self):
        """Each session folder contains exactly one report_*.txt file."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                log_csv = wf / 'log.csv'
                if not log_csv.exists():
                    self.skipTest(f"log.csv not found in {wf.name}")

                with open(log_csv, 'r') as f:
                    for row in csv.DictReader(f):
                        report = row.get('Report', '').strip()
                        path = row.get('Path', '').strip()
                        if path.startswith('./'):
                            path = path[2:]

                        session_dir = wf / path
                        if not session_dir.exists():
                            continue

                        report_files = list(session_dir.glob('report_*.txt'))
                        self.assertEqual(
                            len(report_files), 1,
                            f"Report {report}: expected 1 report_*.txt in {path}, found {len(report_files)}")

    def test_all_sessions_in_log(self):
        """All scanning_session directories under patients/ are listed in log.csv."""
        for wf in self.workflows:
            with self.subTest(workflow=wf.name):
                patients_dir = wf / 'patients'
                log_csv = wf / 'log.csv'
                if not patients_dir.exists() or not log_csv.exists():
                    self.skipTest(f"patients/ or log.csv not found in {wf.name}")

                # Collect all session paths on disk
                sessions_on_disk = []
                for patient_dir in sorted(patients_dir.iterdir()):
                    if not patient_dir.is_dir():
                        continue
                    for session_dir in sorted(patient_dir.iterdir()):
                        if session_dir.is_dir() and session_dir.name.startswith('scanning_session'):
                            rel = str(session_dir.relative_to(wf))
                            sessions_on_disk.append(rel)

                # Collect all paths from log.csv
                log_paths = []
                with open(log_csv, 'r') as f:
                    for row in csv.DictReader(f):
                        path = row.get('Path', '').strip()
                        if path.startswith('./'):
                            path = path[2:]
                        log_paths.append(path)

                for session in sessions_on_disk:
                    self.assertIn(
                        session, log_paths,
                        f"Session '{session}' exists on disk but is not in log.csv")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test that an annotation workflow folder is ready for use')
    parser.add_argument('--workflow', '-w', type=str,
                        help='Path to a workflow directory to test')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()
    CUSTOM_WORKFLOW = args.workflow

    if args.workflow:
        wf_path = Path(args.workflow)
        if not wf_path.is_dir():
            print(f"ERROR: {args.workflow} is not a directory")
            sys.exit(1)
        print(f"Testing workflow: {wf_path.absolute()}")

    verbosity = 2 if args.verbose else 1

    # Remove our custom args so unittest doesn't see them
    sys.argv = [sys.argv[0]]

    unittest.main(verbosity=verbosity)
