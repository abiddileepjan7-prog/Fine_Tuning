import lasio
import pandas as pd
import matplotlib.pyplot as plt
from welly import Well

# ------------------------------------------------------------
# Change the filename if needed
# ------------------------------------------------------------

FILE = "20220518_024622_Wellbore_00 1 1.las"

# ============================================================
# LASIO
# ============================================================

print("=" * 70)
print("1. LASIO")
print("=" * 70)

las = lasio.read(FILE)

# ------------------------------------------------------------
# Version
# ------------------------------------------------------------

print("\nVERSION INFORMATION")
print("-" * 40)

for item in las.version:
    print(item)

# ------------------------------------------------------------
# Well Information
# ------------------------------------------------------------

print("\nWELL INFORMATION")
print("-" * 40)

for item in las.well:
    print(f"{item.mnemonic:15} : {item.value}")

# ------------------------------------------------------------
# Data
# ------------------------------------------------------------

print("\nFIRST 10 DATA ROWS")
print("-" * 40)

print(las.data[:10])

# ============================================================
# DATAFRAME
# ============================================================

print("\n")
print("=" * 70)
print("DATAFRAME")
print("=" * 70)

df = las.df()

print("\nShape")
print(df.shape)

print("\nColumns")
print(df.columns.tolist())

print("\nFirst 10 Rows")
print(df.head(10))

print("\nStatistics")
print(df.describe())


# ============================================================
# WELLY
# ============================================================

print("\n")
print("=" * 70)
print("2. WELLY")
print("=" * 70)

well = Well.from_las(FILE)

print("\nWell Name")
print(well.name)

print("\nLocation")
print(well.location)

print("\nCurves")

for curve in well.data:

    print(curve)


# ------------------------------------------------------------
# Convert to DataFrame
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("WELLY DATAFRAME")
print("=" * 70)

welly_df = well.df()

print(welly_df.head())

print("\nShape :", welly_df.shape)

# ------------------------------------------------------------
# Statistics
# ------------------------------------------------------------

print("\nStatistics")

print(welly_df.describe())

print("\nDone.")