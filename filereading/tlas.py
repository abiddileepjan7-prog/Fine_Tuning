"""
=========================================================
LAS Processing → Structured JSON + Timing Report
Library:
1. lasio
=========================================================
"""

import json
import time
import lasio

FILE = "20220518_024622_Wellbore_00 1 1.las"
OUTPUT_JSON = "las_structured_output.json"
TIMING_JSON = "las_timing_report.json"

# ==========================================================
# Unified output schema
# ==========================================================

result = {
    "source_file": FILE,
    "version": {},
    "well_info": {},
    "curves": [],
    "params": {},
    "data": []
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
# 0. LOAD LAS FILE (parsing the whole file into memory)
# ==========================================================

print("=" * 70)
print("LASIO")
print("=" * 70)


def run_load():

    return lasio.read(FILE)


las = time_it("lasio_load", run_load)

print("\nLAS file loaded")

# ==========================================================
# 1. VERSION + WELL INFO — key-value sections
# ==========================================================

print("\n")
print("=" * 70)
print("1. VERSION + WELL INFO")
print("=" * 70)


def run_metadata_sections():

    for item in las.version:
        result["version"][item.mnemonic] = item.value

    for item in las.well:
        result["well_info"][item.mnemonic] = item.value

    for item in las.params:
        result["params"][item.mnemonic] = item.value

    return len(result["version"]) + len(result["well_info"]) + len(result["params"])


meta_fields = time_it("lasio_metadata", run_metadata_sections)

timings["lasio_metadata"]["fields_extracted"] = meta_fields

print("\nVersion Info :", result["version"])
print("Well Info :", result["well_info"])
print("Params :", result["params"])

# ==========================================================
# 2. CURVES — curve metadata list
# ==========================================================

print("\n")
print("=" * 70)
print("2. CURVES")
print("=" * 70)


def run_curves():

    for curve in las.curves:

        result["curves"].append({
            "mnemonic": curve.mnemonic,
            "unit": curve.unit,
            "description": curve.descr
        })

    return len(result["curves"])


curves_found = time_it("lasio_curves", run_curves)

timings["lasio_curves"]["curves_found"] = curves_found

print("\nCurves Found :", curves_found)

for c in result["curves"]:
    print(c)

# ==========================================================
# 3. DATA — row-wise structured records (biggest cost)
# ==========================================================

print("\n")
print("=" * 70)
print("3. DATA (DataFrame conversion)")
print("=" * 70)


def run_data():

    df = las.df()
    df = df.reset_index()

    result["data"] = df.to_dict(orient="records")

    return df.shape


data_shape = time_it("lasio_data", run_data)

timings["lasio_data"]["rows_extracted"] = data_shape[0]
timings["lasio_data"]["columns_extracted"] = data_shape[1]

print("\nData Shape :", data_shape)
print("\nFirst 5 Records")
for row in result["data"][:5]:
    print(row)

# ==========================================================
# SAVE FINAL STRUCTURED JSON
# ==========================================================

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

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

print(f"\n{'Step':<18}{'Time (s)'}")
print("-" * 30)

for step, data in timings.items():
    print(f"{step:<18}{data['time_seconds']}")

print("\nFull Timing Report (JSON)")
print(json.dumps(timing_report, indent=2, ensure_ascii=False))

with open(TIMING_JSON, "w", encoding="utf-8") as f:
    json.dump(timing_report, f, indent=2, ensure_ascii=False)

print(f"\nTiming report saved to {TIMING_JSON}")

print("\nDone.")