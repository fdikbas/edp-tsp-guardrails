# -*- coding: utf-8 -*-
"""
Standalone Figure 3 generator for the EDP CEJOR manuscript
-----------------------------------------------------------
This script is tailored to the CSV file:
benchmark_results_2026_04_05_v3_core_stress_bestpostboost_rngfix2_mpalitefix_guardfix_bestenvelope_extbase_seedstability.csv

It generates Fig. 3 (variant-wise comparison of exact gaps on the CORE suite)
with the visual correction requested by the user:
- box rectangles behind the points
- jittered instance-level points above the boxes
- mean diamonds on top

Outputs:
- PNG (400 dpi)
- PDF (400 dpi)
- TIFF (600 dpi)

Spyder/runfile friendly.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

# ------------------------------------------------------------------
# USER INPUT
# ------------------------------------------------------------------
# Edit this path if needed.
INPUT_FILE = r"D:/PythonCodes/TSP EDP/benchmark_results_2026_04_05_v3_core_stress_bestpostboost_rngfix2_mpalitefix_guardfix_bestenvelope_extbase_seedstability.csv"

# Output folder is created next to this script (or current working directory in Spyder).
try:
    ROOT = Path(__file__).resolve().parent
except NameError:
    ROOT = Path.cwd().resolve()

OUT_DIR = ROOT / "fig3_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# EXACT is intentionally excluded from Fig. 3.
VARIANT_ORDER = [
    "CI",
    "NEAREST_INSERTION",
    "FARTHEST_INSERTION",
    "EDP_3SECT",
    "EDP_LOCAL_3SECT",
    "MF_EDP_ILS",
    "BEST_ENVELOPE",
]

COLORS = {
    "CI": "#1f77b4",
    "NEAREST_INSERTION": "#ff7f0e",
    "FARTHEST_INSERTION": "#2ca02c",
    "EDP_3SECT": "#4c9ed9",
    "EDP_LOCAL_3SECT": "#9467bd",
    "MF_EDP_ILS": "#8c564b",
    "BEST_ENVELOPE": "#e377c2",
}

BASE_NAME = "Figure3_variantwise_exact_gap_core_suite"
EXPECTED_N = 24  # CORE suite size in the manuscript


# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
def main():
    csv_path = Path(INPUT_FILE)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found:\n{csv_path}")

    df = pd.read_csv(csv_path)

    required_cols = ["suite", "instance", "variant", "exact_gap_percent"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # CORE only
    df = df.copy()
    df["suite"] = df["suite"].astype(str).str.strip().str.lower()
    df["variant"] = df["variant"].astype(str).str.strip()
    df_core = df[df["suite"] == "core"].copy()

    # Keep only the variants used in Fig. 3
    df_core = df_core[df_core["variant"].isin(VARIANT_ORDER)].copy()
    if df_core.empty:
        raise ValueError("No CORE rows found for the selected variants.")

    # Numeric exact gap
    df_core["exact_gap_percent"] = pd.to_numeric(df_core["exact_gap_percent"], errors="coerce")
    df_core = df_core.dropna(subset=["exact_gap_percent"])

    # Keep one row per instance-variant pair
    df_core = df_core.drop_duplicates(subset=["instance", "variant"], keep="first")

    # Console summary
    counts = df_core.groupby("variant")["instance"].nunique().reindex(VARIANT_ORDER)
    print("\nCounts per variant on CORE suite:")
    print(counts)
    for v, n in counts.items():
        if pd.isna(n) or int(n) != EXPECTED_N:
            print(f"WARNING: {v} has {n} rows, expected {EXPECTED_N}.")

    summary = (
        df_core.groupby("variant")["exact_gap_percent"]
        .agg(["count", "mean", "median", "min", "max"])
        .reindex(VARIANT_ORDER)
    )
    print("\nSummary:")
    print(summary.round(3))

    # Prepare data arrays in manuscript order
    positions = np.arange(1, len(VARIANT_ORDER) + 1)
    data = [
        df_core.loc[df_core["variant"] == v, "exact_gap_percent"].to_numpy(dtype=float)
        for v in VARIANT_ORDER
    ]

    # ------------------------------------------------------------------
    # PLOT
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10.0, 5.8))

    # 1) Boxplots first -> behind the points
    bp = ax.boxplot(
        data,
        positions=positions,
        widths=0.50,
        patch_artist=True,
        showfliers=False,
        whis=1.5,
        medianprops=dict(color="#ff7f0e", linewidth=1.4),
        boxprops=dict(linewidth=1.2),
        whiskerprops=dict(linewidth=1.1),
        capprops=dict(linewidth=1.1),
    )

    for patch, v in zip(bp["boxes"], VARIANT_ORDER):
        c = COLORS[v]
        patch.set_facecolor(to_rgba(c, 0.18))
        patch.set_edgecolor(c)
        patch.set_zorder(1)

    for obj in bp["whiskers"]:
        obj.set_color("black")
        obj.set_zorder(2)

    for obj in bp["caps"]:
        obj.set_color("black")
        obj.set_zorder(2)

    for obj in bp["medians"]:
        obj.set_zorder(2.2)

    # 2) Jittered instance-level points above the boxes
    rng = np.random.default_rng(42)  # deterministic jitter
    for i, v in enumerate(VARIANT_ORDER, start=1):
        vals = df_core.loc[df_core["variant"] == v, "exact_gap_percent"].to_numpy(dtype=float)
        jitter = rng.uniform(-0.09, 0.09, size=len(vals))
        ax.scatter(
            np.full(len(vals), i) + jitter,
            vals,
            s=18,
            color=COLORS[v],
            alpha=0.65,
            edgecolors="none",
            zorder=3,
        )

    # 3) Mean diamonds on top
    means = [np.mean(vals) for vals in data]
    ax.scatter(
        positions,
        means,
        marker="D",
        s=44,
        color="black",
        zorder=4,
    )

    # Axis formatting
    ax.set_xticks(positions)
    ax.set_xticklabels(VARIANT_ORDER, rotation=20, ha="right")
    ax.set_ylabel("Exact gap (%)")

    ymax = max(np.max(vals) for vals in data if len(vals) > 0)
    ax.set_ylim(-1.0, max(20.0, np.ceil((ymax + 0.8) * 2) / 2.0))
    ax.grid(axis="y", linestyle="-", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------
    png_path = OUT_DIR / f"{BASE_NAME}.png"
    pdf_path = OUT_DIR / f"{BASE_NAME}.pdf"
    tif_path = OUT_DIR / f"{BASE_NAME}.tiff"

    fig.savefig(png_path, dpi=400, bbox_inches="tight")
    fig.savefig(pdf_path, dpi=400, bbox_inches="tight")
    fig.savefig(tif_path, dpi=600, bbox_inches="tight")

    plt.show()
    plt.close(fig)

    print("\nSaved:")
    print(png_path)
    print(pdf_path)
    print(tif_path)


if __name__ == "__main__":
    main()
