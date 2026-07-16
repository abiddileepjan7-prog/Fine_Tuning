"""
=========================================================
PDF Processing → Structured JSON + Timing Report
Libraries:
1. pypdf
2. pdfplumber
3. PyMuPDF (fitz)
4. camelot-py
=========================================================
"""

import json
import os
import time
from pypdf import PdfReader
import pdfplumber
import fitz
import camelot

FILE = "NIPS-2017-attention-is-all-you-need-Paper.pdf"
OUTPUT_JSON = "pdf_structured_output.json"
TIMING_JSON = "pdf_timing_report.json"
IMAGE_DIR = "pdf_images"

os.makedirs(IMAGE_DIR, exist_ok=True)

# ==========================================================
# Unified output schema
# ==========================================================

result = {
    "source_file": FILE,
    "num_pages": 0,
    "metadata": {},
    "pages": []
}

# ==========================================================
# Timing tracker
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
# 1. PYPDF — text + metadata
# ==========================================================

print("=" * 70)
print("1. PYPDF")
print("=" * 70)


def run_pypdf():

    reader = PdfReader(FILE)

    result["num_pages"] = len(reader.pages)

    if reader.metadata:
        result["metadata"] = {
            "title": reader.metadata.title,
            "author": reader.metadata.author,
            "producer": reader.metadata.producer,
        }

    total_chars = 0

    for i, page in enumerate(reader.pages):

        text = page.extract_text() or ""
        total_chars += len(text)

        result["pages"].append({
            "page_number": i + 1,
            "text": text.strip(),
            "tables": [],
            "images": []
        })

    return total_chars


chars_pypdf = time_it("pypdf", run_pypdf)

timings["pypdf"]["pages"] = result["num_pages"]
timings["pypdf"]["chars_extracted"] = chars_pypdf

print("Total Pages :", result["num_pages"])
print("Characters Extracted :", chars_pypdf)

# ==========================================================
# 2. PDFPLUMBER — text (fallback) + tables
# ==========================================================

print("\n")
print("=" * 70)
print("2. PDFPLUMBER")
print("=" * 70)


def run_pdfplumber():

    total_chars = 0
    total_tables = 0

    with pdfplumber.open(FILE) as pdf:

        for i, page in enumerate(pdf.pages):

            if not result["pages"][i]["text"]:
                text = (page.extract_text() or "").strip()
                result["pages"][i]["text"] = text
                total_chars += len(text)

            tables = page.extract_tables()

            if tables:
                result["pages"][i]["tables"].extend(tables)
                total_tables += len(tables)

    return total_chars, total_tables


chars_plumber, tables_plumber = time_it("pdfplumber", run_pdfplumber)

timings["pdfplumber"]["pages"] = result["num_pages"]
timings["pdfplumber"]["chars_extracted"] = chars_plumber
timings["pdfplumber"]["tables_found"] = tables_plumber

print("Tables Found :", tables_plumber)

# ==========================================================
# 3. PYMUPDF (fitz) — images
# ==========================================================

print("\n")
print("=" * 70)
print("3. PYMUPDF (fitz)")
print("=" * 70)


def run_pymupdf():

    total_images = 0

    doc = fitz.open(FILE)

    for page_index in range(len(doc)):

        page = doc[page_index]
        images = page.get_images()

        for img_i, img in enumerate(images):

            xref = img[0]
            base_image = doc.extract_image(xref)

            image_bytes = base_image["image"]
            ext = base_image["ext"]

            filename = f"{IMAGE_DIR}/page{page_index+1}_img{img_i+1}.{ext}"

            with open(filename, "wb") as f:
                f.write(image_bytes)

            result["pages"][page_index]["images"].append(filename)
            total_images += 1

    doc.close()

    return total_images


images_found = time_it("pymupdf", run_pymupdf)

timings["pymupdf"]["pages"] = result["num_pages"]
timings["pymupdf"]["images_extracted"] = images_found

print("Images Extracted :", images_found)

# ==========================================================
# 4. CAMELOT-PY — table extraction
# ==========================================================

print("\n")
print("=" * 70)
print("4. CAMELOT-PY")
print("=" * 70)


def run_camelot():

    total_tables = 0

    try:
        camelot_tables = camelot.read_pdf(FILE, pages="all", flavor="lattice")

        for table in camelot_tables:

            page_num = int(table.page)
            page_entry = result["pages"][page_num - 1]

            page_entry["tables"].append(table.df.values.tolist())
            total_tables += 1

    except Exception as e:
        print("Camelot extraction skipped/failed :", e)

    return total_tables


tables_camelot = time_it("camelot", run_camelot)

timings["camelot"]["pages"] = result["num_pages"]
timings["camelot"]["tables_found"] = tables_camelot

print("Tables Found (camelot) :", tables_camelot)

# ==========================================================
# SAVE STRUCTURED JSON
# ==========================================================

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# ==========================================================
# TIMING REPORT — print to terminal + save to file
# ==========================================================

timing_report = {
    "source_file": FILE,
    "timings": timings
}

print("\n")
print("=" * 70)
print("TIMING REPORT")
print("=" * 70)

print(f"\n{'Library':<15}{'Time (s)'}")
print("-" * 30)

for lib, data in timings.items():
    print(f"{lib:<15}{data['time_seconds']}")

print("\nFull Timing Report (JSON)")
print(json.dumps(timing_report, indent=2, ensure_ascii=False))

with open(TIMING_JSON, "w", encoding="utf-8") as f:
    json.dump(timing_report, f, indent=2, ensure_ascii=False)

print(f"\nTiming report saved to {TIMING_JSON}")

print("\nDone.")