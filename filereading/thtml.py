"""
=========================================================
HTML Processing → Structured JSON + Timing Report
Libraries:
1. BeautifulSoup
2. lxml
=========================================================
"""

import json
import time
from bs4 import BeautifulSoup
from lxml import html

FILE = "sample.html"
OUTPUT_JSON = "html_structured_output.json"
TIMING_JSON = "html_timing_report.json"

# ==========================================================
# Unified output schema
# ==========================================================

result = {
    "source_file": FILE,
    "title": "",
    "headings": {"h1": [], "h2": [], "h3": []},
    "paragraphs": [],
    "links": [],
    "images": [],
    "tables": [],
    "lists": [],
    "forms": []
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
# 1. BEAUTIFULSOUP — main structured extraction
# ==========================================================

print("=" * 70)
print("1. BEAUTIFULSOUP")
print("=" * 70)


def run_beautifulsoup():

    with open(FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # ------------------------------------------------------
    # Title
    # ------------------------------------------------------

    if soup.title:
        result["title"] = soup.title.text.strip()

    # ------------------------------------------------------
    # Headings
    # ------------------------------------------------------

    for tag in ["h1", "h2", "h3"]:

        for heading in soup.find_all(tag):
            result["headings"][tag].append(heading.text.strip())

    # ------------------------------------------------------
    # Paragraphs
    # ------------------------------------------------------

    for p in soup.find_all("p"):

        text = p.text.strip()

        if text:
            result["paragraphs"].append(text)

    # ------------------------------------------------------
    # Links
    # ------------------------------------------------------

    for link in soup.find_all("a"):

        result["links"].append({
            "text": link.text.strip(),
            "url": link.get("href", "")
        })

    # ------------------------------------------------------
    # Images
    # ------------------------------------------------------

    for img in soup.find_all("img"):

        src = img.get("src")

        if src:
            result["images"].append(src)

    # ------------------------------------------------------
    # Tables
    # ------------------------------------------------------

    for table in soup.find_all("table"):

        rows = []

        for row in table.find_all("tr"):

            cells = [cell.text.strip() for cell in row.find_all(["th", "td"])]

            if cells:
                rows.append(cells)

        result["tables"].append(rows)

    # ------------------------------------------------------
    # Lists
    # ------------------------------------------------------

    for li in soup.find_all("li"):

        text = li.text.strip()

        if text:
            result["lists"].append(text)

    # ------------------------------------------------------
    # Forms
    # ------------------------------------------------------

    for form in soup.find_all("form"):

        inputs = []

        for inp in form.find_all("input"):

            inputs.append({
                "type": inp.get("type", ""),
                "name": inp.get("name", "")
            })

        result["forms"].append({"inputs": inputs})

    return len(result["paragraphs"])


paragraphs_bs = time_it("beautifulsoup", run_beautifulsoup)

timings["beautifulsoup"]["paragraphs_extracted"] = paragraphs_bs
timings["beautifulsoup"]["links_found"] = len(result["links"])
timings["beautifulsoup"]["images_found"] = len(result["images"])
timings["beautifulsoup"]["tables_found"] = len(result["tables"])

print("\nTitle :", result["title"])
print("Paragraphs Found :", paragraphs_bs)
print("Links Found :", len(result["links"]))
print("Images Found :", len(result["images"]))
print("Tables Found :", len(result["tables"]))

# ==========================================================
# 2. LXML — cross-validation via XPath
# ==========================================================

print("\n")
print("=" * 70)
print("2. LXML")
print("=" * 70)


def run_lxml():

    with open(FILE, "r", encoding="utf-8") as f:
        tree = html.fromstring(f.read())

    lxml_title = tree.xpath("//title/text()")
    lxml_h1 = tree.xpath("//h1/text()")
    lxml_links = tree.xpath("//a/@href")
    lxml_images = tree.xpath("//img/@src")

    result["_validation"] = {
        "title_match": (lxml_title[0].strip() if lxml_title else "") == result["title"],
        "links_count_match": len(lxml_links) == len(result["links"]),
        "images_count_match": len(lxml_images) == len(result["images"])
    }

    return {
        "links_found": len(lxml_links),
        "images_found": len(lxml_images)
    }


lxml_counts = time_it("lxml", run_lxml)

timings["lxml"]["links_found"] = lxml_counts["links_found"]
timings["lxml"]["images_found"] = lxml_counts["images_found"]

print("\nLinks Found (lxml) :", lxml_counts["links_found"])
print("Images Found (lxml) :", lxml_counts["images_found"])
print("Validation :", result["_validation"])

# ==========================================================
# SAVE FINAL STRUCTURED JSON
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

print(f"\n{'Library':<18}{'Time (s)'}")
print("-" * 30)

for lib, data in timings.items():
    print(f"{lib:<18}{data['time_seconds']}")

print("\nFull Timing Report (JSON)")
print(json.dumps(timing_report, indent=2, ensure_ascii=False))

with open(TIMING_JSON, "w", encoding="utf-8") as f:
    json.dump(timing_report, f, indent=2, ensure_ascii=False)

print(f"\nTiming report saved to {TIMING_JSON}")

print("\nDone.")