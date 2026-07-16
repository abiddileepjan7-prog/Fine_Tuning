"""
=========================================================
Multi-format Unified Processing → Structured JSON + Timing Report
Library:
1. unstructured (Unstructured.io)
=========================================================
"""

import json
import time
import os
from unstructured.partition.auto import partition
from unstructured.documents.elements import (
    Title,
    NarrativeText,
    Table,
    ListItem,
    Header,
    Footer,
)

# ==========================================================
# All file types used across the earlier scripts
# ==========================================================

FILES = {
    "pdf":   "NIPS-2017-attention-is-all-you-need-Paper.pdf",
    "docx":  "file-sample_100kB.docx",
    "pptx":  "Copy of Stocks Trading Business Plan.pptx",
    "html":  "sample.html",
    "xml":   "BhaRuns.xml",
    "xlsx":  "Covid Dashboard.xlsx",
    "csv":   "Employee_Salary_Dataset.csv",
    # LAS is not supported by Unstructured.io — no LAS partitioner exists.
    # Kept here only as a documented gap, not executed.
    # "las": "20220518_024622_Wellbore_00 1 1.las",
}

OUTPUT_DIR = "unstructured_outputs"
TIMING_JSON = "unstructured_timing_report.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================================
# Unified per-file output schema
# ==========================================================
#
# {
#   "source_file": str,
#   "file_type": str,
#   "num_elements": int,
#   "elements": [ {"type": str, "text": str, "metadata": {...}} ],
#   "titles": [...],
#   "narrative_text": [...],
#   "tables": [...],
#   "list_items": [...],
#   "headers": [...],
#   "footers": [...]
# }
#
# ==========================================================

# ==========================================================
# Timing tracker
# ==========================================================
#
# timings = {
#   "pdf":  {"time_seconds": float, "elements_found": int, ...},
#   "docx": {...},
#   ...
# }
#
# ==========================================================

timings = {}


def time_it(label, func):
    """Runs func(), records elapsed time, returns func's result."""

    start = time.perf_counter()
    output = func()
    end = time.perf_counter()

    elapsed = round(end - start, 4)

    timings[label] = {"time_seconds": elapsed}

    print(f"\n[TIMER] {label} took {elapsed} seconds")

    return output


# ==========================================================
# UNSTRUCTURED.IO — process every file type
# ==========================================================

print("=" * 70)
print("UNSTRUCTURED.IO — MULTI-FORMAT PROCESSING")
print("=" * 70)

for file_type, filepath in FILES.items():

    print("\n" + "=" * 60)
    print(f"Processing : {file_type.upper()}  ({filepath})")
    print("=" * 60)

    file_result = {
        "source_file": filepath,
        "file_type": file_type,
        "num_elements": 0,
        "elements": [],
        "titles": [],
        "narrative_text": [],
        "tables": [],
        "list_items": [],
        "headers": [],
        "footers": []
    }

    def run_partition():
        return partition(filename=filepath)

    try:
        elements = time_it(file_type, run_partition)

    except Exception as e:

        print(f"Skipped {file_type} due to error :", e)
        timings[file_type] = {"time_seconds": None, "error": str(e)}
        continue

    file_result["num_elements"] = len(elements)

    for element in elements:

        element_entry = {
            "type": type(element).__name__,
            "text": element.text if hasattr(element, "text") else "",
            "metadata": {
                "page_number": getattr(element.metadata, "page_number", None),
                "filename": getattr(element.metadata, "filename", None),
            }
        }

        file_result["elements"].append(element_entry)

    file_result["titles"] = [e.text for e in elements if isinstance(e, Title)]
    file_result["narrative_text"] = [e.text for e in elements if isinstance(e, NarrativeText)]
    file_result["tables"] = [e.text for e in elements if isinstance(e, Table)]
    file_result["list_items"] = [e.text for e in elements if isinstance(e, ListItem)]
    file_result["headers"] = [e.text for e in elements if isinstance(e, Header)]
    file_result["footers"] = [e.text for e in elements if isinstance(e, Footer)]

    # Record extraction stats alongside timing
    timings[file_type]["elements_found"] = file_result["num_elements"]
    timings[file_type]["titles_found"] = len(file_result["titles"])
    timings[file_type]["tables_found"] = len(file_result["tables"])
    timings[file_type]["narrative_blocks_found"] = len(file_result["narrative_text"])

    print("Total Elements :", file_result["num_elements"])
    print("Titles :", len(file_result["titles"]))
    print("Narrative Text Blocks :", len(file_result["narrative_text"]))
    print("Tables :", len(file_result["tables"]))
    print("List Items :", len(file_result["list_items"]))
    print("Headers :", len(file_result["headers"]))
    print("Footers :", len(file_result["footers"]))

    # ------------------------------------------------------
    # Save per-file structured JSON
    # ------------------------------------------------------

    out_path = os.path.join(OUTPUT_DIR, f"unstructured_{file_type}_output.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(file_result, f, indent=2, ensure_ascii=False)

    print(f"Saved to {out_path}")

# ==========================================================
# TIMING REPORT — print to terminal + save to file
# ==========================================================

timing_report = {
    "library": "unstructured.io",
    "files_processed": FILES,
    "timings": timings,
    "note": "LAS format has no Unstructured.io partitioner and was skipped."
}

print("\n")
print("=" * 70)
print("TIMING REPORT — UNSTRUCTURED.IO (ALL FILE TYPES)")
print("=" * 70)

print(f"\n{'File Type':<12}{'Time (s)'}")
print("-" * 30)

for file_type, data in timings.items():
    print(f"{file_type:<12}{data.get('time_seconds')}")

print("\nFull Timing Report (JSON)")
print(json.dumps(timing_report, indent=2, ensure_ascii=False))

with open(TIMING_JSON, "w", encoding="utf-8") as f:
    json.dump(timing_report, f, indent=2, ensure_ascii=False)

print(f"\nTiming report saved to {TIMING_JSON}")

print("\nDone.")