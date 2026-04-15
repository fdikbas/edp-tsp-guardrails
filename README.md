# EDP TSP benchmark package 

This repository contains the minimal reproducibility package for the manuscript on the Equal Detour Point (EDP) heuristic for the symmetric Traveling Salesman Problem.

## What is included

- `tsp_edp_benchmark_2026.04.15.v4_2_paper_final_core_nopostboost_noseedstability_noplots.py`  
  Main paper-final benchmark script.
- `results/`  
  Final CSV outputs from the paper-final CORE-only run.
- `scripts/Figure3_variantwise_exact_gap_core_suite_standalone.py`  
  Standalone helper script for Figure 3.
- `requirements.txt`  
  Python package list.

## What is intentionally NOT included

- TSPLIB instance files (`*.tsp`, `*.opt.tour`)  
  These should be obtained separately and placed in a local `tsplib_instances/` folder next to the main script.
- Large plot folders and intermediate experimental files.
- The manuscript Word file.

## Why this is the minimal package

For the manuscript as currently written, **the code file alone is not ideal**.  
The paper also states that processed benchmark outputs are openly shared.  
Therefore the minimal reliable public package is:

1. the main benchmark script,
2. the final results CSV files,
3. a short README,
4. a requirements file.

## How to rerun the paper-final benchmark

1. Create a folder named `tsplib_instances/` next to the main script.
2. Put the TSPLIB problem files used in the paper into that folder.
3. Install the dependencies from `requirements.txt`.
4. Run the main Python file.
5. New CSV files will be written under `results/`.

## Important run policy

This script is the **paper-final** configuration:

- CORE suite only
- STRESS disabled in the main run
- BEST_POSTBOOST disabled
- MF seed-stability disabled
- route plotting disabled
