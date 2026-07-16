"""
=========================================================
XML Processing → Structured JSON + Timing Report
Libraries:
1. lxml
2. xml.etree.ElementTree
3. xmltodict
4. BeautifulSoup
=========================================================
"""

import json
import time
import xml.etree.ElementTree as ET
from lxml import etree
import xmltodict
from bs4 import BeautifulSoup

FILE = "BhaRuns.xml"
OUTPUT_JSON = "xml_structured_output.json"
TIMING_JSON = "xml_timing_report.json"

ns = {
    "witsml": "http://www.witsml.org/schemas/1series"
}

# ==========================================================
# Unified output schema
# ==========================================================

result = {
    "source_file": FILE,
    "root_tag": "",
    "bha_runs": [],
    "raw_dict": {}
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
# 1. ELEMENTTREE — structured field extraction
# ==========================================================

print("=" * 70)
print("1. ELEMENTTREE")
print("=" * 70)


def run_elementtree():

    tree = ET.parse(FILE)
    root = tree.getroot()

    result["root_tag"] = root.tag

    bha_runs = root.findall("witsml:bhaRun", ns)

    for run in bha_runs:

        def get_text(tag):
            el = run.find(f"witsml:{tag}", ns)
            return el.text if el is not None else None

        run_entry = {
            "uid": run.attrib.get("uid"),
            "well_uid": run.attrib.get("uidWell"),
            "wellbore_uid": run.attrib.get("uidWellbore"),
            "well_name": get_text("nameWell"),
            "wellbore_name": get_text("nameWellbore"),
            "run_name": get_text("name"),
            "start": get_text("dTimStart"),
            "stop": get_text("dTimStop"),
            "mud_weight": [],
            "flow_rate": []
        }

        result["bha_runs"].append(run_entry)

    return len(bha_runs)


runs_found = time_it("elementtree", run_elementtree)

timings["elementtree"]["bha_runs_found"] = runs_found

print("\nRoot Tag :", result["root_tag"])
print("Number of BHA Runs :", runs_found)

# ==========================================================
# 2. LXML — XPath enrichment (mud weight, flow rate)
# ==========================================================

print("\n")
print("=" * 70)
print("2. LXML")
print("=" * 70)


def run_lxml():

    lxml_tree = etree.parse(FILE)

    mud_values = lxml_tree.xpath("//witsml:wtMud/text()", namespaces=ns)
    flow_values = lxml_tree.xpath("//witsml:flowratePump/text()", namespaces=ns)

    for i, run_entry in enumerate(result["bha_runs"]):

        if i < len(mud_values):
            run_entry["mud_weight"].append(mud_values[i])

        if i < len(flow_values):
            run_entry["flow_rate"].append(flow_values[i])

    return len(mud_values) + len(flow_values)


values_found = time_it("lxml", run_lxml)

timings["lxml"]["values_extracted"] = values_found

print("\nMud/Flow Values Extracted :", values_found)

# ==========================================================
# 3. XMLTODICT — full XML to key-value dict
# ==========================================================

print("\n")
print("=" * 70)
print("3. XMLTODICT")
print("=" * 70)


def run_xmltodict():

    with open(FILE, "r", encoding="utf-8") as f:
        parsed = xmltodict.parse(f.read())

    result["raw_dict"] = parsed

    return len(parsed.keys())


keys_found = time_it("xmltodict", run_xmltodict)

timings["xmltodict"]["top_level_keys"] = keys_found

print("\nTop-level Keys :", list(result["raw_dict"].keys()))

# ==========================================================
# 4. BEAUTIFULSOUP — validation / alternate parsing
# ==========================================================

print("\n")
print("=" * 70)
print("4. BEAUTIFULSOUP")
print("=" * 70)


def run_beautifulsoup():

    with open(FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    bs_well_name = soup.find("nameWell")
    bs_run_name = soup.find("name")

    result["_validation"] = {
        "well_name_match": (
            bs_well_name.text if bs_well_name else None
        ) == (result["bha_runs"][0]["well_name"] if result["bha_runs"] else None)
    }

    return {
        "well_name": bs_well_name.text if bs_well_name else None,
        "run_name": bs_run_name.text if bs_run_name else None
    }


bs_values = time_it("beautifulsoup", run_beautifulsoup)

timings["beautifulsoup"]["well_name_found"] = bs_values["well_name"] is not None
timings["beautifulsoup"]["run_name_found"] = bs_values["run_name"] is not None

print("\nWell Name (BeautifulSoup) :", bs_values["well_name"])
print("Run Name (BeautifulSoup) :", bs_values["run_name"])
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