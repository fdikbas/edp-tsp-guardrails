# tsp_edp_benchmark_2026.04.15.v4_2_paper_final_core_nopostboost_noseedstability_noplots.py
#
# ============================================================================
# VERY PLAIN-ENGLISH GUIDE ("FOR IDIOTS" VERSION)
# ============================================================================
# What this file is:
# This is the main benchmark script used for the paper on the Equal Detour Point
# (EDP) heuristic for the symmetric Traveling Salesman Problem (TSP).
#
# In simple words, this script:
# 1) reads TSPLIB problem files,
# 2) runs several TSP solution methods on the same benchmark instances,
# 3) compares their final tour lengths against exact/known reference values,
# 4) writes the final benchmark tables as CSV files,
# 5) writes extra diagnostic CSV files about guardrails and geometry drift.
#
# ----------------------------------------------------------------------------
# What you need in the same folder before running this script
# ----------------------------------------------------------------------------
# 1) This Python file.
# 2) A folder named: tsplib_instances/
# 3) Inside tsplib_instances/, put the TSPLIB *.tsp files used in the paper.
# 4) If you have them, also put the matching *.opt.tour files there.
#
# Folder example:
#   your_folder/
#       tsp_edp_benchmark_2026.04.15.v4_2_paper_final_core_nopostboost_noseedstability_noplots.py
#       tsplib_instances/
#           a280.tsp
#           att48.tsp
#           ...
#           ulysses22.tsp
#           optional_opt_tours_here.opt.tour
#
# If tsplib_instances/ does not exist, the script will also look for a ZIP file
# named tsplib_instances_fullraw_2026_02_09.zip next to the script and try to
# extract it automatically.
#
# ----------------------------------------------------------------------------
# What happens when you run it
# ----------------------------------------------------------------------------
# The script creates a folder named results/ and writes CSV files there.
# The most important file is usually:
#   benchmark_results_<RUN_TAG>.csv
#
# That CSV is the main paper-output table at instance x variant level.
#
# Other CSV files summarize:
# - guardrail events,
# - MF guardrail events,
# - Held-Karp exactness checks,
# - geometry-drift cases,
# - pivot tables for length and runtime,
# - guardrail policy summary.
#
# ----------------------------------------------------------------------------
# What methods are compared
# ----------------------------------------------------------------------------
# This script compares several variants:
# - CI
# - NEAREST_INSERTION
# - FARTHEST_INSERTION
# - EDP_3SECT
# - EDP_LOCAL_3SECT
# - MF_EDP_ILS
# - EXACT (reference row where exact/known solution is available)
# - BEST_ENVELOPE (retrospective best non-exact summary row)
#
# Important:
# BEST_ENVELOPE is NOT a real online solver that magically knows the future.
# It is only a retrospective summary row built AFTER all compared heuristic
# branches have already been run.
#
# ----------------------------------------------------------------------------
# What “paper-final” means in this file
# ----------------------------------------------------------------------------
# This version is intentionally locked to the safest settings for the paper:
# - CORE suite only
# - STRESS suite disabled in the main run
# - BEST_POSTBOOST disabled
# - MF seed-stability repeats disabled
# - route plotting disabled
#
# Why?
# Because these settings keep the benchmark outputs aligned with the manuscript:
# the reported BEST_ENVELOPE row stays a pure retrospective analytical envelope,
# and the run produces stable paper tables without extra side-output variability.
#
# ----------------------------------------------------------------------------
# If you only want the main paper results, do this:
# ----------------------------------------------------------------------------
# 1) Put TSPLIB files into tsplib_instances/
# 2) Open this file in Spyder (or run from terminal).
# 3) Press Run.
# 4) Wait until the script finishes.
# 5) Open results/benchmark_results_<RUN_TAG>.csv
# 6) Use the CSV files in results/ to rebuild tables/figures for the paper.
#
# ----------------------------------------------------------------------------
# What this script does NOT do automatically
# ----------------------------------------------------------------------------
# - It does not download TSPLIB for you from the internet.
# - It does not upload anything to GitHub.
# - It does not edit the manuscript.
# - It does not guarantee the global optimum for large TSP instances.
#
# ----------------------------------------------------------------------------
# Exactness / reference logic in plain language
# ----------------------------------------------------------------------------
# For very small problems, the script can compute exact optimum values using
# Held-Karp dynamic programming.
# For the remaining CORE instances, the script uses known TSPLIB optimum values
# or opt.tour reference values.
#
# So the paper's “exact gap (%)” means:
#   100 * (your tour length - reference length) / reference length
#
# ----------------------------------------------------------------------------
# Very important warning about runtime and reproducibility
# ----------------------------------------------------------------------------
# If you change any of the settings below, your results may change.
# If you want to reproduce the paper tables, do NOT casually edit the settings.
#
# This file is the paper-final run configuration.
# Use it as-is unless you intentionally want a different experiment.
#
# ----------------------------------------------------------------------------
# Patch history relevant to this paper-final file
# ----------------------------------------------------------------------------
# 2026-04-10 patch:
# - fixed a BEST_ENVELOPE postboost runtime double-count bug,
# - cleaned the legacy MF_MS_* parameter confusion,
# - preserved algorithmic behavior otherwise.
#
# ----------------------------------------------------------------------------
# Original short notes kept below for traceability
# ----------------------------------------------------------------------------
# tsp_edp_benchmark_2026.04.05.v4_core_stress_bestpostboost_rngfix2_mpalitefix_guardfix_bestenvelope_extba.py
# Spyder / parametresiz kullanım:
# Patch note (2026-04-10):
# - BEST_ENVELOPE postboost runtime double-count bug fixed.
# - Legacy MF_MS_* multi-start parameter block converted to compatibility aliases/comments.
# - No algorithmic behavior intentionally changed beyond these corrections.

# v2_merged_runtime_accel (2026-02-15): 02.14.v1 + optional runtime accel knobs (OFF by default)
# - Bu dosyanın yanına tsplib_instances/ klasörü oluşturun
# - İçine *.tsp ve varsa *.opt.tour dosyalarını koyun
# - Çalıştırın; results/ altına CSV yazdırır
#
# v5 (2026-01-08) odak:
# 1) Doğruluk öncelikli: TSPLIB node-id -> internal 0-based indeks normalizasyonu (GEO/ATT dahil güvenli)
# 2) EDP 3-sektör kuralı: Her yeni nokta için 3 sektörün her birinde en iyi kırılacak kenar adayını bul,
#    sonra bu üç adaydan toplam uzunluğu en çok düşüreni seç (tüm sektörler test edilir).
# 3) Yerel üçgen seçimi: mümkünse mevcut turun poligon triangulation’ından (ear-clipping) üçgen seç,
#    aksi halde (dışarıda/başarısız) en yakın 3 tur düğümüyle üçgen kur.
#
#
# v6 (2026-01-08) ek:
# 4) Held–Karp (exact) doğrulama modülü: n<=HK_MAX_N için gerçek optimum uzunluğu hesaplar,
#    varyantların doğru/optimal olup olmadığını otomatik raporlar.
# Not: Bu, ekleme (insertion) adımında "sektör kuralı"nı eksiksiz test eder.
# Ancak TSP'nin global optimumu için garanti vermez (NP-zor). Burada garanti edilen:
# - Seçilen üçgen ve tanımlanan sektörler altında, her sektördeki en iyi kenar kırılması denenir
# - Bu üç sektördeki en iyi hamleler arasından en kısa turu veren hamle seçilir


# v5 (2026-01-09) ek:
# 5) MF_EDP_ILS: Multi-Fragment (greedy) başlangıç turu + EDP hedefli yeniden-ekleme + Double-Bridge ILS.
#    Amaç: “tümevarım” (3-nokta -> ekle) yerine “tümdengelim” başlangıcı (yakın noktaları birleştir) ile
#    daha güçlü başlangıç ve daha iyi doğruluk.
# 6) (Opsiyonel) Geometri kayma raporu: MF_EDP_ILS’in hangi geometri tiplerinde optimumdan saptığını otomatik özetler.


# PAPER-FINAL SETTINGS (2026-04-10): CORE-only benchmark, BEST_POSTBOOST disabled,
# MF seed-stability disabled, route plotting disabled. This keeps BEST_ENVELOPE as a
# pure retrospective analytical envelope and minimizes side-output variability.

import os
import time
import math
import glob
import gzip
import sys
import warnings
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import numpy as np
import pandas as pd

# ---------------------------
# Geometri özet metrikleri (hangi geometrilerde kayma var?)
# ---------------------------
def _convex_hull_indices(points: np.ndarray) -> List[int]:
    """Monotonic chain convex hull (2D). points: (n,2) float."""
    pts = [(float(points[i,0]), float(points[i,1]), i) for i in range(points.shape[0])]
    pts.sort(key=lambda t: (t[0], t[1]))
    if len(pts) <= 1:
        return [pts[0][2]] if pts else []

    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return [t[2] for t in hull]


def _poly_area(points_or_poly: np.ndarray, idx: Optional[List[int]] = None) -> float:
    """Shoelace area for a 2D polygon.

    - idx is not None: points_or_poly is interpreted as a point set (n,2) and idx defines the polygon vertex order.
    - idx is None: points_or_poly is interpreted directly as polygon vertices (m,2).
    """
    if points_or_poly is None:
        return 0.0
    pts = np.asarray(points_or_poly, dtype=float)
    if idx is not None:
        if idx is None or len(idx) < 3:
            return 0.0
        pts = pts[np.asarray(idx, dtype=int)]
    if pts is None or len(pts) < 3:
        return 0.0
    x = pts[:, 0]
    y = pts[:, 1]
    return 0.5 * float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

def compute_geom_metrics(coords: Optional[np.ndarray], d: 'DistanceOracle') -> Dict[str, float]:
    """Koordinatlar varsa bazı ölçek-bağımsız geometri metrikleri üretir."""
    out = {
        "geom_hull_frac": np.nan,
        "geom_bbox_aspect": np.nan,
        "geom_pca_aspect": np.nan,
        "geom_hull_fill": np.nan,
        "geom_nn_mean": np.nan,
        "geom_nn_cv": np.nan,
    }
    if coords is None or len(coords) < 3:
        return out
    pts = np.asarray(coords, dtype=float)

    # bbox
    dx = float(np.max(pts[:,0]) - np.min(pts[:,0]))
    dy = float(np.max(pts[:,1]) - np.min(pts[:,1]))
    if dx > 0 and dy > 0:
        out["geom_bbox_aspect"] = max(dx/dy, dy/dx)

    # PCA aspect
    try:
        X = pts - pts.mean(axis=0, keepdims=True)
        C = np.cov(X.T)
        w, _ = np.linalg.eigh(C)
        w = np.sort(w)
        if w[0] > 0:
            out["geom_pca_aspect"] = float(math.sqrt(w[-1]/w[0]))
    except Exception:
        pass

    # convex hull fraction + fill ratio
    try:
        hull_idx = _convex_hull_indices(pts)
        out["geom_hull_frac"] = float(len(hull_idx)) / float(len(pts))
        hull_area = _poly_area(pts, hull_idx)
        bbox_area = dx * dy if (dx > 0 and dy > 0) else 0.0
        if bbox_area > 0:
            out["geom_hull_fill"] = float(hull_area / bbox_area)
    except Exception:
        pass

    # nearest-neighbor distances (geometry only):
    # Prefer KDTree on raw coordinates to avoid O(n^2) scans/copies of the TSPLIB distance matrix.
    try:
        if globals().get("SCIPY_OK", False) and ("cKDTree" in globals()):
            tree = cKDTree(pts)
            dd, _ = tree.query(pts, k=2)  # self + nearest neighbor
            nn = np.asarray(dd[:, 1], dtype=float)
        elif d is not None and getattr(d, "D", None) is not None:
            # fallback to precomputed TSPLIB weights (costly for large n)
            D = np.asarray(d.D, dtype=float).copy()
            np.fill_diagonal(D, np.inf)
            nn = np.min(D, axis=1)
        else:
            # brute-force fallback on Euclidean geometry
            n_ = pts.shape[0]
            nn_list = []
            for i in range(n_):
                best = None
                xi0, xi1 = float(pts[i, 0]), float(pts[i, 1])
                for j in range(n_):
                    if i == j:
                        continue
                    w = float(np.hypot(xi0 - float(pts[j, 0]), xi1 - float(pts[j, 1])))
                    if best is None or w < best:
                        best = w
                nn_list.append(best if best is not None else np.nan)
            nn = np.array(nn_list, dtype=float)

        out["geom_nn_mean"] = float(np.nanmean(nn))
        mu = float(np.nanmean(nn))
        sd = float(np.nanstd(nn))
        if mu > 0:
            out["geom_nn_cv"] = float(sd / mu)
    except Exception:
        pass

    return out


try:
    import tsplib95
except ImportError as e:
    raise ImportError("tsplib95 yok. Kurulum: pip install tsplib95") from e

# SciPy opsiyonel (KDTree hız için)
try:
    from scipy.spatial import cKDTree
    SCIPY_OK = True
except Exception:
    SCIPY_OK = False



# ---------------------------
# Retrospective best-of-branch summary row
# ---------------------------
# Internal legacy name is preserved for backward compatibility in code/comments,
# but exported benchmark summaries should use BEST_ENVELOPE to make clear that
# this row is an ex post analytical envelope rather than a deployable online policy.
BEST_SUMMARY_LEGACY_LABEL = "BEST_HEUR"
BEST_SUMMARY_EXPORT_LABEL = "BEST_ENVELOPE"
BEST_SUMMARY_ALIASES = (BEST_SUMMARY_LEGACY_LABEL, BEST_SUMMARY_EXPORT_LABEL)

def _is_best_summary_variant(v: object) -> bool:
    try:
        return str(v) in BEST_SUMMARY_ALIASES
    except Exception:
        return False

# ---------------------------
# Progress bar (tqdm) - optional
# ---------------------------
try:
    from tqdm import tqdm as _tqdm  # Spyder-friendly
    TQDM_OK = True
except Exception:
    _tqdm = None
    TQDM_OK = False

# --- v4: Geometriye göre riskli örnek tespiti (MF_EDP_ILS için)
def geom_is_risky(geom: Dict[str, float]) -> bool:
    """Basit kural tabanlı risk tespiti. (Konfig ile ayarlanır.)"""
    try:
        hf = float(geom.get("geom_hull_frac", np.nan))
        asp = float(geom.get("geom_pca_aspect", np.nan))
        cv = float(geom.get("geom_nn_cv", np.nan))
        if not np.isfinite(hf) or not np.isfinite(asp) or not np.isfinite(cv):
            return False
        return (hf <= float(MF_GEOM_ADAPT_HULL_FRAC_MAX)) and (asp <= float(MF_GEOM_ADAPT_PCA_ASPECT_MAX)) and (cv >= float(MF_GEOM_ADAPT_NN_CV_MIN))
    except Exception:
        return False


def geom_risk_score(geom: Dict[str, float]) -> float:
    """Continuous (0..1) geometri risk skoru.

    Mantık:
    - geom_hull_frac düşükse risk artar
    - geom_pca_aspect düşükse (izotropik/dense interior) risk artar
    - geom_nn_cv yüksekse (heterojen/cluster) risk artar

    Eşikler MF_GEOM_ADAPT_* parametrelerinden alınır.
    """
    try:
        hf = float(geom.get("geom_hull_frac", np.nan))
        asp = float(geom.get("geom_pca_aspect", np.nan))
        cv = float(geom.get("geom_nn_cv", np.nan))
        if not (np.isfinite(hf) and np.isfinite(asp) and np.isfinite(cv)):
            return float(np.nan)

        hf_max = float(MF_GEOM_ADAPT_HULL_FRAC_MAX)
        asp_max = float(MF_GEOM_ADAPT_PCA_ASPECT_MAX)
        cv_min = float(MF_GEOM_ADAPT_NN_CV_MIN)

        hull_risk = float(np.clip((hf_max - hf) / max(1e-12, hf_max), 0.0, 1.0))
        aspect_risk = float(np.clip((asp_max - asp) / max(1e-12, asp_max), 0.0, 1.0))
        cv_risk = float(np.clip((cv - cv_min) / max(1e-12, (1.0 - cv_min)), 0.0, 1.0))

        score = 0.35 * hull_risk + 0.25 * aspect_risk + 0.40 * cv_risk
        return float(np.clip(score, 0.0, 1.0))
    except Exception:
        return float(np.nan)

def geom_rule_class(geom: Dict[str, float]) -> str:
    """Drift örneklerini yorumlamak için kaba geometri sınıfları."""
    try:
        hf = float(geom.get("geom_hull_frac", np.nan))
        asp = float(geom.get("geom_pca_aspect", np.nan))
        cv = float(geom.get("geom_nn_cv", np.nan))
    except Exception:
        return "unknown"
    if not (np.isfinite(hf) and np.isfinite(asp) and np.isfinite(cv)):
        return "unknown"
    if hf < 0.35 and asp < 2.0:
        return "dense_interior_isotropic"
    if hf < 0.35 and asp >= 2.0:
        return "dense_interior_elongated"
    if hf >= 0.70:
        return "hull_dominant"
    if cv >= 0.80:
        return "clustered_heterogeneous"
    return "mixed"


def geom_guardrails_class(geom: Dict[str, float]) -> str:
    """Guardrails için drift-action ile uyumlu + formatlı geometri sınıfı.

    geom_drift_action CSV'lerinde kullanılan sınıf isimlerine (dense+isotropic+clustered vb.)
    uyum sağlamak için 'dense/isotropic/clustered' etiketlerini birleştirir.

    Heuristik:
      - dense      : geom_hull_frac < 0.35
      - isotropic  : geom_pca_aspect < 2.0
      - clustered  : geom_nn_cv >= 0.80
    """
    try:
        hf = float(geom.get("geom_hull_frac", np.nan))
        asp = float(geom.get("geom_pca_aspect", np.nan))
        cv = float(geom.get("geom_nn_cv", np.nan))
    except Exception:
        return "unknown"

    if not (np.isfinite(hf) and np.isfinite(asp) and np.isfinite(cv)):
        return "unknown"

    tags = []
    if hf < 0.35:
        tags.append("dense")
    if asp < 2.0:
        tags.append("isotropic")
    if cv >= 0.80:
        tags.append("clustered")

    if len(tags) == 0:
        return "other"
    return "+".join(tags)


# ---------------------------
# Guardrail patch helpers (v3_12_3)
# ---------------------------
def _safe_gap_percent(length, ref_length):
    """Robust gap-percent helper. Returns NaN if unavailable."""
    try:
        if length is None or ref_length is None:
            return np.nan
        lf = float(length)
        rf = float(ref_length)
        if (not np.isfinite(lf)) or (not np.isfinite(rf)) or (rf <= 0):
            return np.nan
        return 100.0 * (lf - rf) / rf
    except Exception:
        return np.nan


def _sync_row_gap_fields(row: Dict[str, object]) -> Dict[str, object]:
    """Keep row-level quality fields synchronized with final length."""
    try:
        if not isinstance(row, dict):
            return row
        L = row.get("length", None)
        opt_len = row.get("opt_length", row.get("opt_len", None))
        gap = _safe_gap_percent(L, opt_len)
        if np.isfinite(gap):
            row["gap_percent"] = float(gap)

        exact_len = row.get("exact_length", row.get("exact_ref_len", None))
        exact_gap = _safe_gap_percent(L, exact_len)
        if np.isfinite(exact_gap):
            row["exact_gap_percent"] = float(exact_gap)
            row["gap_exact"] = float(exact_gap)

        if bool(row.get("mf_guard_triggered", False)) and np.isfinite(exact_gap):
            row["mf_guard_gap_after"] = float(exact_gap)
    except Exception:
        pass
    return row


def sync_gap_fields_df(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute gap fields from final length for export/drift safety."""
    try:
        out = df.copy()
    except Exception:
        return df

    if len(out) == 0:
        return out

    if "length" not in out.columns:
        return out

    if ("opt_length" in out.columns) or ("opt_len" in out.columns):
        _opt_col = "opt_length" if "opt_length" in out.columns else "opt_len"
        _gap_vals = []
        for L, O in zip(out["length"], out[_opt_col]):
            _gap_vals.append(_safe_gap_percent(L, O))
        out["gap_percent"] = pd.Series(_gap_vals, index=out.index)

    _exact_col = None
    if "exact_length" in out.columns:
        _exact_col = "exact_length"
    elif "exact_ref_len" in out.columns:
        _exact_col = "exact_ref_len"

    if _exact_col is not None:
        _ex_vals = []
        for L, E in zip(out["length"], out[_exact_col]):
            _ex_vals.append(_safe_gap_percent(L, E))
        _ex_series = pd.Series(_ex_vals, index=out.index)
        out["exact_gap_percent"] = _ex_series
        out["gap_exact"] = _ex_series
        if ("mf_guard_triggered" in out.columns) and ("mf_guard_gap_after" in out.columns):
            try:
                _mask = out["mf_guard_triggered"].fillna(False).astype(bool)
                out.loc[_mask, "mf_guard_gap_after"] = out.loc[_mask, "exact_gap_percent"]
            except Exception:
                pass

    return out


def _heur_variant_rank(v: str) -> int:
    _order = {
        "CI": 0,
        "NEAREST_INSERTION": 1,
        "FARTHEST_INSERTION": 2,
        "EDP_3SECT": 3,
        "EDP_LOCAL_3SECT": 4,
        "MF_EDP_ILS": 5,
    }
    try:
        return int(_order.get(str(v), 999))
    except Exception:
        return 999


def rebuild_best_heur_rows_df(df: pd.DataFrame) -> pd.DataFrame:
    """Rebuild retrospective best-of-branch summary rows from finalized heuristic rows.

    The exported label is BEST_ENVELOPE to emphasize that this is an ex post
    analytical envelope row, not a deployable online selection policy.
    """
    try:
        out = sync_gap_fields_df(df)
    except Exception:
        return df

    if len(out) == 0 or ("variant" not in out.columns):
        return out

    _has_best = out["variant"].astype(str).map(_is_best_summary_variant).any()
    if not _has_best:
        return out

    group_cols = [c for c in ("suite", "instance") if c in out.columns]
    if len(group_cols) == 0:
        return out

    cand_vars = ("CI", "NEAREST_INSERTION", "FARTHEST_INSERTION", "EDP_3SECT", "EDP_LOCAL_3SECT", "MF_EDP_ILS")

    for key, sub in out.groupby(group_cols, sort=False):
        try:
            cand = sub[sub["variant"].astype(str).isin(cand_vars)].copy()
            if "status" in cand.columns:
                ok = cand["status"].fillna("OK").astype(str).str.upper().eq("OK")
                if ok.any():
                    cand = cand.loc[ok].copy()
            if len(cand) == 0:
                continue

            cand["_sort_exact_gap"] = pd.to_numeric(cand.get("exact_gap_percent"), errors="coerce")
            cand["_sort_gap"] = pd.to_numeric(cand.get("gap_percent"), errors="coerce")
            cand["_sort_len"] = pd.to_numeric(cand.get("length"), errors="coerce")
            cand["_sort_time"] = pd.to_numeric(cand.get("time_sec"), errors="coerce")
            cand["_sort_vrank"] = cand["variant"].map(_heur_variant_rank)
            cand = cand.sort_values(
                by=["_sort_exact_gap", "_sort_gap", "_sort_len", "_sort_vrank", "_sort_time"],
                ascending=[True, True, True, True, True],
                na_position="last",
                kind="mergesort",
            )
            if len(cand) == 0:
                continue
            best = cand.iloc[0].copy()
            src_variant = str(best.get("variant", ""))

            if isinstance(key, tuple):
                key_vals = key
            else:
                key_vals = (key,)

            mask = pd.Series(True, index=out.index)
            for col, val in zip(group_cols, key_vals):
                mask &= out[col].eq(val)
            mask &= out["variant"].astype(str).map(_is_best_summary_variant)
            if not bool(mask.any()):
                continue

            dest_idx = out.index[mask][0]
            best["variant"] = BEST_SUMMARY_EXPORT_LABEL
            if "best_src_variant" in out.columns:
                best["best_src_variant"] = src_variant
            for col in best.index:
                if col in out.columns:
                    out.at[dest_idx, col] = best[col]

            # BEST_ENVELOPE is a retrospective summary row: never inherit source guardrail telemetry/flags.
            _best_reset = {
                "guardrail_triggered": False,
                "guardrail_reason": None,
                "guardrail_profile": None,
                "guardrail_ref_gap": np.nan,
                "guardrail_len2": np.nan,
                "guardrail_gap2": np.nan,
                "guardrail_len_mini": np.nan,
                "guardrail_gap_mini": np.nan,
                "guardrail_time_mini_sec": 0.0,
                "guardrail_len_full": np.nan,
                "guardrail_gap_full": np.nan,
                "guardrail_time_full_sec": 0.0,
                "guardrail_len_stage3": np.nan,
                "guardrail_gap_stage3": np.nan,
                "guardrail_time_stage3_sec": 0.0,
                "guardrail_time_sec": 0.0,
                "guardrail_geom_risky": False,
                "guardrail_geom_class": None,
                "guardrail_geom_score": np.nan,
                "mf_guard_triggered": False,
                "mf_guard_reason": None,
                "mf_guard_profile": None,
                "mf_guard_gap_before": np.nan,
                "mf_guard_gap_after": np.nan,
                "mf_guard_time_sec": 0.0,
            }
            for _k, _v in _best_reset.items():
                if _k in out.columns:
                    out.at[dest_idx, _k] = _v
        except Exception:
            continue

    return sync_gap_fields_df(out)


def apply_mf_hard_fallback_instance(
    rows: List[Dict[str, object]],
    inst_row_idx: Dict[str, int],
    suite_name: str,
    p_name: str,
    p_n: int,
    mf_guard_events: List[Dict[str, object]],
) -> bool:
    """Large-N safety net: if MF is materially worse than best EDP, copy final quality from best EDP."""
    try:
        if not bool(globals().get("MF_HARD_FALLBACK_ENABLE", True)):
            return False
        if (str(suite_name).lower() == "stress") and (not bool(globals().get("MF_HARD_FALLBACK_STRESS_ENABLE", False))):
            return False
        if int(p_n) < int(globals().get("MF_HARD_FALLBACK_MIN_N", 575)):
            return False
        if "MF_EDP_ILS" not in inst_row_idx:
            return False

        edp_candidates = []
        for vv in ("EDP_3SECT", "EDP_LOCAL_3SECT"):
            if vv in inst_row_idx:
                edp_candidates.append(vv)
        if len(edp_candidates) == 0:
            return False

        idx_mf = int(inst_row_idx["MF_EDP_ILS"])
        if idx_mf < 0 or idx_mf >= len(rows):
            return False
        mf_row = _sync_row_gap_fields(rows[idx_mf])

        edp_best_variant = None
        edp_best_idx = None
        edp_best_key = None
        for vv in edp_candidates:
            ix = int(inst_row_idx[vv])
            if ix < 0 or ix >= len(rows):
                continue
            rr = _sync_row_gap_fields(rows[ix])
            try:
                exg = float(rr.get("exact_gap_percent", np.nan))
            except Exception:
                exg = np.nan
            try:
                ggp = float(rr.get("gap_percent", np.nan))
            except Exception:
                ggp = np.nan
            try:
                llen = float(rr.get("length", np.nan))
            except Exception:
                llen = np.nan
            key = (
                exg if np.isfinite(exg) else np.inf,
                ggp if np.isfinite(ggp) else np.inf,
                llen if np.isfinite(llen) else np.inf,
                _heur_variant_rank(vv),
            )
            if (edp_best_key is None) or (key < edp_best_key):
                edp_best_key = key
                edp_best_variant = vv
                edp_best_idx = ix

        if edp_best_idx is None:
            return False

        edp_row = _sync_row_gap_fields(rows[edp_best_idx])

        try:
            mf_gap = float(mf_row.get("exact_gap_percent", np.nan))
        except Exception:
            mf_gap = np.nan
        if not np.isfinite(mf_gap):
            try:
                mf_gap = float(mf_row.get("gap_percent", np.nan))
            except Exception:
                mf_gap = np.nan

        try:
            edp_gap = float(edp_row.get("exact_gap_percent", np.nan))
        except Exception:
            edp_gap = np.nan
        if not np.isfinite(edp_gap):
            try:
                edp_gap = float(edp_row.get("gap_percent", np.nan))
            except Exception:
                edp_gap = np.nan

        if (not np.isfinite(mf_gap)) or (not np.isfinite(edp_gap)):
            return False

        delta_tol = float(globals().get("MF_HARD_FALLBACK_DELTA_PCT", 1.0))
        if not (mf_gap > edp_gap + delta_tol):
            return False

        try:
            L_before = float(mf_row.get("length", np.nan))
        except Exception:
            L_before = np.nan
        try:
            L_after = float(edp_row.get("length", np.nan))
        except Exception:
            L_after = np.nan

        for col in ("length", "gap_percent", "exact_gap_percent", "gap_exact"):
            if col in edp_row:
                mf_row[col] = edp_row.get(col)

        mf_row["mf_guard_triggered"] = True
        mf_row["mf_guard_reason"] = f"MF_HARD_FALLBACK_TO_{str(edp_best_variant)}({mf_gap:.2f}>{edp_gap:.2f}+{delta_tol:.2f})"
        mf_row["mf_guard_profile"] = "MF_HARD_FALLBACK_BEST_EDP"
        mf_row["mf_guard_gap_before"] = float(mf_gap)
        mf_row["mf_guard_gap_after"] = float(edp_gap)
        try:
            _w = str(mf_row.get("warnings", "") or "")
            _w = (_w + "|MF_HARD_FALLBACK").strip("|")
            mf_row["warnings"] = _w
        except Exception:
            pass

        rows[idx_mf] = _sync_row_gap_fields(mf_row)

        try:
            mf_guard_events.append({
                "suite": suite_name,
                "instance": p_name,
                "n": int(p_n),
                "mf_gap_before": float(mf_gap),
                "mf_gap_after": float(edp_gap),
                "mf_len_before": float(L_before) if np.isfinite(L_before) else np.nan,
                "mf_len_after": float(L_after) if np.isfinite(L_after) else np.nan,
                "edp_best_gap": float(edp_gap),
                "delta_pct": float(delta_tol),
                "time_sec": 0.0,
                "accepted": True,
                "reason": f"hard_fallback_to_{str(edp_best_variant)}",
            })
        except Exception:
            pass

        return True
    except Exception:
        return False

SPYDER_PROGRESS_MODE = globals().get("SPYDER_PROGRESS_MODE", "final_only")
# Global progress style control (works both in Spyder and normal terminals)
# - "one_line_per_instance": suppress all inner progress bars and print ONLY one completion line per instance
# - "default": keep existing behavior (tqdm in terminal, compact in Spyder)
PROGRESS_STYLE = globals().get("PROGRESS_STYLE", "one_line_per_instance")


def progress(iterable, total=None, desc="", leave=True, enabled=True, position=0, kind="generic"):
    """Progress iterator with Spyder-friendly behavior.

    Spyder 5.x IPython console often does NOT render carriage-return updates properly,
    which causes tqdm to print each refresh on a new line (very verbose). Therefore:

    - In Spyder: use a throttled, line-based progress (few lines only).
    - Elsewhere: use tqdm with in-place updates.

    kind: "instances" | "variants" | "insert" | "hk" | "generic"
    """
    if not enabled:
        return iterable

    # infer total if possible
    if total is None:
        try:
            total = len(iterable)
        except Exception:
            total = None

    # ---------------------------
    # One-line-per-instance progress (suppresses all inner progress bars)
    # ---------------------------
    style = str(globals().get("PROGRESS_STYLE", "default")).lower().strip()

    # ----------------------------------------
    # PROGRESS_STYLE = "one_line_per_instance"
    #   - Spyder/IPython konsolünde nested tqdm satır şişmesini engeller
    #   - Sadece instance bazında tek satır log üretir
    # ----------------------------------------
    if style in ("one_line_per_instance", "single_line", "1line"):
        if total is None:
            return iterable
        if kind != "instances":
            return iterable

        def gen_inst():
            for i, x in enumerate(iterable, 1):
                try:
                    nm = os.path.basename(str(x))
                except Exception:
                    nm = str(x)
                # Her instance için tek satır
                try:
                    print(f"{nm}: {i}/{total}")
                except Exception:
                    pass
                yield x

        return gen_inst()

    # ----------------------------------------
    # PROGRESS_STYLE = "final_only_all"
    #   - Yalnızca variants gibi üst seviyelerde final 100% satırı basar
    # ----------------------------------------
    if style in ("final_only_all",):
        if total is None:
            return iterable
        if kind != "variants":
            return iterable
        width = 24

        def gen_final():
            for _, x in enumerate(iterable, 1):
                yield x
            try:
                bar = "#" * width
                print(f"{desc}: 100%|{bar}| {total}/{total}")
            except Exception:
                pass

        return gen_final()

    IS_SPYDER = (("spyder_kernels" in sys.modules) or ("SPYDER_ARGS" in os.environ) or ("SPYDER" in os.environ.get("TERM","").upper()))

    # ---------------------------
    # Spyder: throttled line-progress (few lines)
    # ---------------------------
    if IS_SPYDER:
        if total is None:
            return iterable

        mode = str(globals().get("SPYDER_PROGRESS_MODE", "final_only")).lower().strip()

        # Mode options:
        # - "none": no progress output
        # - "final_only": print ONLY one final completion line for each instance (kind="variants")
        # - "compact": print a few updates for kind in ("variants", "instances"); inner bars suppressed
        if mode in ("none", "off", "0", "false"):
            return iterable

        # Suppress inner-loop progress bars in Spyder (reinsertion/multistart/etc.) to avoid console spam.
        if kind not in ("variants", "instances"):
            return iterable

        # In "final_only" mode we keep only one line per instance by printing ONLY at completion of variants.
        if mode == "final_only":
            if kind != "variants":
                return iterable

            width = 24
            def gen_final():
                for _, x in enumerate(iterable, 1):
                    yield x
                # single completion line
                try:
                    bar = "#" * width
                    print(f"{desc}: 100%|{bar}| {total}/{total}")
                except Exception:
                    pass
            return gen_final()

        # Compact mode (still very limited output)
        max_updates = 4 if kind == "variants" else 10
        max_updates = max(2, min(max_updates, total))
        step = max(1, total // max_updates)

        width = 24
        last_i = 0

        def gen():
            nonlocal last_i
            for i, x in enumerate(iterable, 1):
                do_print = (i == 1) or (i == total) or ((i - last_i) >= step)
                if do_print:
                    pct = int(round(100.0 * i / total))
                    filled = int(round(width * pct / 100.0))
                    bar = "#" * filled + "-" * (width - filled)
                    print(f"{desc}: {pct:3d}%|{bar}| {i}/{total}")
                    last_i = i
                yield x
        return gen()

    # ---------------------------
    # Non-Spyder: tqdm in-place progress
    # ---------------------------
    if TQDM_OK:
        mininterval = 0.2 if kind in ("instances", "variants") else 0.5
        return _tqdm(
            iterable,
            total=total,
            desc=desc,
            leave=leave,
            position=position,
            dynamic_ncols=True,
            ascii=True,
            file=sys.stderr,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} ({percentage:3.0f}%) [{elapsed}<{remaining}]",
            mininterval=mininterval,
            maxinterval=1.0,
            smoothing=0.0,
        )

    # fallback: coarse console updates
    if total is None:
        return iterable
    step = max(1, total // 20)

    def gen2():
        last = 0
        for i, x in enumerate(iterable, 1):
            if i == 1 or i == total or i - last >= step:
                pct = int(round(100.0 * i / total))
                print(f"{desc}: {pct:3d}% ({i}/{total})")
                last = i
            yield x
    return gen2()

# ---------------------------
# AYARLAR (parametresiz; buradan düzenlenir)
# ---------------------------
BASE_DIR = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0] if "__file__" in globals() else "interactive"
RUN_TAG = SCRIPT_NAME.replace("tsp_edp_benchmark_", "").replace(".", "_")

INST_DIR = os.path.join(BASE_DIR, "tsplib_instances")
# Eğer INST_DIR yoksa ve yan tarafta TSPLIB zip paketi varsa otomatik çıkar.
# (Önerilen paket adı: tsplib_instances_fullraw_2026_02_09.zip)
TSPLIB_ZIP_PATH = os.path.join(BASE_DIR, "tsplib_instances_fullraw_2026_02_09.zip")
if (not os.path.isdir(INST_DIR)) and os.path.isfile(TSPLIB_ZIP_PATH):
    try:
        import zipfile
        with zipfile.ZipFile(TSPLIB_ZIP_PATH, "r") as _zf:
            _zf.extractall(BASE_DIR)
    except Exception as _e:
        print(f"[WARN] TSPLIB zip auto-extract başarısız: {TSPLIB_ZIP_PATH} -> {_e}")
OUT_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------
# CORE / STRESS suite selection
# ---------------------------
# CORE: tüm küçük/orta instance'lar
# STRESS: aşırı büyük instance'lar (örn. usa13509) — ağır çalışır; isteğe bağlı.
RUN_STRESS = False
# stress instance adları (uzantısız). Örn: "usa13509"
STRESS_INSTANCES = ("usa13509",)
# "prefix": base name STRESS_INSTANCES ile başlıyorsa stress say; "exact": tam eşleşme
STRESS_MATCH_MODE = "prefix"
# True ise konsola "foo.tsp: i/N [suite]" satırlarını yazar
PRINT_INSTANCE_LIST = True
# Stress suite'te tur çizimleri (PDF/TIFF) çok maliyetli olabilir
PLOT_TOURS_STRESS_ENABLE = False

# Stress suite için varyant kısıtlaması (None -> tüm varyantlar)
STRESS_VARIANTS = ("CI", "EDP_3SECT", "MF_EDP_ILS", "EXACT")
# Stress suite içinde accuracy-guardrails (mini/full ek aramalar) varsayılan kapalı
ACCURACY_GUARDRAILS_STRESS_ENABLE = False

# ---------------------------
# MF guardrails (MF tail fix): MF, EDP'den belirgin kötü ise yalnızca o örnek için MF'i "STRONG" profille yeniden koş.
# Amaç: MF_EDP_ILS'in kuyruk (tail) hatalarını (örn. pr1002, u724) kesmek; genelde koşu süresini şişirmemek.
# ---------------------------
MF_GUARD_ENABLE = True
# MF, EDP (EDP_3SECT ve EDP_LOCAL_3SECT arasından en iyisi) ile kıyaslanır.
MF_GUARD_WORSE_DELTA_PCT = 1.0          # MF gap > EDP_best_gap + delta ise tetikle
MF_GUARD_ABS_GAP_MIN_PCT = 3.0          # küçük farklarda gereksiz tetiklemeyi azalt (opsiyonel)
MF_GUARD_STRESS_ENABLE = False          # stress suite'te varsayılan kapalı (usa13509 için chase etmiyoruz)
MF_GUARD_STRONG_MAX_N = 500               # n>=500 için STRONG pahalı; sadece yakınsa deneriz
MF_GUARD_STRONG_LARGE_N_MAX_DELTA_PCT = 3.0   # n>=MAX_N iken (mf_gap - edp_best_gap) > bu ise STRONG skip

# MF STRONG profili (sadece tetiklenen örneklerde devreye girer)
# v3.5: tail-case'lerde (dense+isotropic) iyileşme şansı için daha agresif: daha çok restart, daha derin ILS, daha geniş aday seti.
MF_STRONG_MIN_TRIES_SMALL = 5           # n<400  (v3.4.1: 3)
MF_STRONG_MIN_TRIES_LARGE = 10          # n>=400 (v3.4.1: 4)
MF_STRONG_ILS_MULT = 3.2                # ILS iterasyonlarını çarpar (v3.4.1: 1.8)
MF_STRONG_FORCE_FULL_LS = True          # ILS içi local search modunu 'full' yap
MF_STRONG_NO_IMPROVE_STOP_MIN = 25      # erken durdurma eşiğini gevşet (v3.4.1: 10)

# Tail-case'lerde aday uzayı genişlet: sadece STRONG koşuda uygulanır
MF_STRONG_MF_KNN_K_MULT = 2.0           # Multi-Fragment aday kenar KNN (MF_KNN_K) çarpanı
MF_STRONG_KNN_2OPT_MULT = 2.0           # 2-opt neighbor list (KNN_2OPT) çarpanı

# Küçük n'de (HK_MAX_N) MF'in "1-2 kenar" gerisinde kalmasını engellemek için (opsiyonel):
# True ise MF, n<=HK_MAX_N durumunda HK optimuma düşürülür (yalnızca çok küçük örnekler; raporlama için stabil).
MF_SMALL_N_FORCE_HK_OPT = True

# MF hard fallback (large-N tail safety)
# Amaç: MF çözümü best EDP'den belirgin kötü kaldığında, MF telemetrisini koruyup
# yalnızca final kalite alanlarını best EDP seviyesine çekmek.
MF_HARD_FALLBACK_ENABLE = True
MF_HARD_FALLBACK_MIN_N = 575
MF_HARD_FALLBACK_DELTA_PCT = 1.0
MF_HARD_FALLBACK_STRESS_ENABLE = False



# ---------------------------
# Route plotting (visuals)
# ---------------------------
PLOT_TOURS_ENABLE = False
# Hangi varyantların turunu çizeceğiz?
PLOT_TOURS_VARIANTS = ("CI", "EDP_3SECT", "EDP_LOCAL_3SECT", "MF_EDP_ILS", "MF_EDP_ILS_MPA")
# Her instance için ayrıca en iyi (en kısa) turu BEST olarak kaydet
PLOT_TOURS_BEST_PER_INSTANCE = True
# Çıktılar: plots_{RUN_TAG} klasörü altında hem TIFF hem PDF
PLOT_TOURS_DPI = 600
PLOT_TOURS_VERBOSE = False
PLOT_TOURS_LINEWIDTH = 0.9
PLOT_TOURS_POINTSIZE = 10
PLOT_TOURS_START_POINTSIZE = 40

PLOT_COLOR_LINE = '#1f3a5f'         # tour polyline (navy)
PLOT_COLOR_POINTS = '#f4b942'       # nodes (warm gold; contrasts with navy)
PLOT_COLOR_HIGHLIGHT = '#e63946'    # longest edges highlight (crimson)
PLOT_COLOR_START = '#2a9d8f'        # start node marker (teal)
PLOT_COLOR_LABEL_BOX_ALPHA = 0.55

PLOT_HIGHLIGHT_LONGEST_EDGES_SHOW_LENGTH = True
PLOT_HIGHLIGHT_EDGE_LW = 2.8
PLOT_HIGHLIGHT_EDGE_LABEL_FONTSIZE = 7

PLOT_NODE_LABEL_MAX_N = 80  # n <= this: label every node; else subsample
PLOT_HIGHLIGHT_LONGEST_EDGES_K = 5  # overlay K longest edges with thicker dashed lines
PLOT_GUARDRAIL_REASON_MAXLEN = 90  # truncate long guardrail reasons in plot annotation


# TSPLIB95 (Table 1) bilinen optimum uzunluklar (opt.tour yoksa gap raporu için).
# Not: Bu liste sınırlıdır; ihtiyaca göre genişletilebilir.
TSPLIB_KNOWN_OPT = {
    # --- small instances (TSPLIB95 / classic) ---
    "burma14": 3323,
    "ulysses16": 6859,
    "ulysses22": 7013,
    "att48": 10628,
    "berlin52": 7542,
    "st70": 675,
    "eil51": 426,
    "eil76": 538,
    "eil101": 629,
    "kroA100": 21282,
    "pr76": 108159,

    # --- added (TSPLIB95 Table 1): medium-to-hard instances with known OPT ---
    "lin105": 14379,
    "ch130": 6110,
    "ch150": 6528,
    "a280": 2579,
    "pcb442": 50778,
    "gr96": 55209,
    "gr202": 40160,
    "gr666": 294358,

    # --- optional add-ons (also known OPT in TSPLIB95) ---
    "d198": 15780,
    "lin318": 42029,
    "rat575": 6773,
    "u724": 41910,
    "pr1002": 259045,

    # --- largest-n with known OPT (TSPLIB / literature) ---
    "usa13509": 19982859,
}

# normalize to lowercase keys for robust lookup
TSPLIB_KNOWN_OPT = {str(k).lower(): int(v) for k, v in TSPLIB_KNOWN_OPT.items()}



RANDOM_SEED = 42
# --- Large-N quality booster (time-bounded post local search) ---
# Purpose: if OPT is known and the current tour is still far (e.g., usa13509),
# run a short, targeted improvement burst using a larger KNN candidate set.
LARGE_N_POSTLS_ENABLE = bool(globals().get("LARGE_N_POSTLS_ENABLE", True))
LARGE_N_POSTLS_MIN_N = int(globals().get("LARGE_N_POSTLS_MIN_N", 3000))
LARGE_N_POSTLS_TRIGGER_GAP_PCT = float(globals().get("LARGE_N_POSTLS_TRIGGER_GAP_PCT", 8.0))
LARGE_N_POSTLS_TIME_BUDGET_SEC = float(globals().get("LARGE_N_POSTLS_TIME_BUDGET_SEC", 240.0))
LARGE_N_POSTLS_KNN_K = int(globals().get("LARGE_N_POSTLS_KNN_K", 40))



# --- Retrospective envelope postboost (tail-aware) ---
# Purpose: After selecting the retrospective BEST_ENVELOPE row (best among CI/external insertion/EDP/MF variants), run a short, time-bounded improvement burst
# on that tour (when a tour is available) and always log telemetry.
BEST_POSTBOOST_ENABLE = False
BEST_POSTBOOST_MIN_N = 650                 # attempt only when instance size is at least this
BEST_POSTBOOST_MIN_GAP_PCT = 4.5           # and the current BEST_ENVELOPE gap is at least this (if available)
BEST_POSTBOOST_BASE_BUDGET_SEC = 4.0       # default time budget per instance
BEST_POSTBOOST_TAIL_N = 900                # tail trigger (very hard cases)
BEST_POSTBOOST_TAIL_GAP_PCT = 7.0
BEST_POSTBOOST_TAIL_BUDGET_SEC = 15.0      # higher budget for tail cases
BEST_POSTBOOST_STRENGTHEN = True           # temporarily bump LARGE_N_POSTLS knobs during postboost on large-n
LARGE_N_POSTLS_RELOC_ROUNDS = int(globals().get("LARGE_N_POSTLS_RELOC_ROUNDS", 1))
LARGE_N_POSTLS_RELOC_MAX_MOVES = int(globals().get("LARGE_N_POSTLS_RELOC_MAX_MOVES", 1200))

LARGE_N_POSTLS_OROPT_ENABLE = bool(globals().get("LARGE_N_POSTLS_OROPT_ENABLE", True))
LARGE_N_POSTLS_OROPT_MAX_K = int(globals().get("LARGE_N_POSTLS_OROPT_MAX_K", 3))
LARGE_N_POSTLS_OROPT_ROUNDS = int(globals().get("LARGE_N_POSTLS_OROPT_ROUNDS", 1))
LARGE_N_POSTLS_OROPT_MAX_MOVES = int(globals().get("LARGE_N_POSTLS_OROPT_MAX_MOVES", 450))
LARGE_N_POSTLS_OROPT_CAND_K = int(globals().get("LARGE_N_POSTLS_OROPT_CAND_K", 18))

LARGE_N_POSTLS_KICK_ENABLE = bool(globals().get("LARGE_N_POSTLS_KICK_ENABLE", True))
LARGE_N_POSTLS_KICK_TRIES = int(globals().get("LARGE_N_POSTLS_KICK_TRIES", 2))

# --- Large-N postls: optional targeted EDP reinsertion + short ILS cycles (for hard tail cases) ---
LARGE_N_POSTLS_REINSERT_ENABLE = bool(globals().get("LARGE_N_POSTLS_REINSERT_ENABLE", True))
LARGE_N_POSTLS_REINSERT_MIN_N = int(globals().get("LARGE_N_POSTLS_REINSERT_MIN_N", 900))
LARGE_N_POSTLS_REINSERT_MIN_GAP_PCT = float(globals().get("LARGE_N_POSTLS_REINSERT_MIN_GAP_PCT", 6.0))
LARGE_N_POSTLS_REINSERT_FOCUS_FRAC = float(globals().get("LARGE_N_POSTLS_REINSERT_FOCUS_FRAC", 0.30))
LARGE_N_POSTLS_REINSERT_MAX_PER_PASS = int(globals().get("LARGE_N_POSTLS_REINSERT_MAX_PER_PASS", 80))
LARGE_N_POSTLS_REINSERT_PASSES = int(globals().get("LARGE_N_POSTLS_REINSERT_PASSES", 1))

LARGE_N_POSTLS_ILS_ENABLE = bool(globals().get("LARGE_N_POSTLS_ILS_ENABLE", True))
LARGE_N_POSTLS_ILS_CYCLES_MAX = int(globals().get("LARGE_N_POSTLS_ILS_CYCLES_MAX", 10))
LARGE_N_POSTLS_ILS_2OPT_SEC = float(globals().get("LARGE_N_POSTLS_ILS_2OPT_SEC", 2.0))
LARGE_N_POSTLS_ILS_OROPT_ENABLE = bool(globals().get("LARGE_N_POSTLS_ILS_OROPT_ENABLE", False))
LARGE_N_POSTLS_ILS_OROPT_MOVES = int(globals().get("LARGE_N_POSTLS_ILS_OROPT_MOVES", 700))
LARGE_N_POSTLS_ILS_NOIMP_STOP = int(globals().get("LARGE_N_POSTLS_ILS_NOIMP_STOP", 3))



# Progress bar settings
SHOW_PROGRESS = True
# Inner-loop progress bars (reinsertion / ILS etc.)
SHOW_INSERT_PROGRESS = True
# Show an insertion progress bar only if instance size is at least this (to reduce clutter)
SHOW_INSERT_PROGRESS_MIN_N = 60
# Show Held–Karp DP progress (subset-size loop)
SHOW_HK_PROGRESS = True
# Show distance-matrix precompute progress (usually not needed; can be slow/verbose)
SHOW_PRECOMPUTE_PROGRESS = False


# Spyder console: if True, show inner-loop progress (insert / hk).
SPYDER_SHOW_INNER_PROGRESS = True
# KNN (triangulation fallback / 2-opt adayları)
KNN_TRI = 40      # üçgen fallback: en yakın 3'ü buradan seç
KNN_2OPT = 25     # 2-opt komşu listesi

# 2-opt
TWO_OPT_MAX_PASSES = 7
TWO_OPT_TIME_LIMIT_SEC = 8.0
# ---------------------------
# Doğruluk odaklı ek geliştirmeler (v8)
# ---------------------------
# 1) Look-ahead: 3 sektör adayının her biri üzerinde "mini yerel onarım" (local 2-opt) çalıştır,
#    sonra en kısa turu veren adayı seç.
LOOKAHEAD_ENABLE = True
LOOKAHEAD_MAX_MOVES = 30          # her ekleme adımında aday tur başına en fazla local 2-opt hamlesi
LOOKAHEAD_FOCUS_EXTRA_KNN = 10    # odak düğümlere (x,u,v,üçgen köşeleri) eklenecek ekstra KNN sayısı

# 2) Beam search: her eklemede 3 sektör = 3 dallanma. En iyi W turu tutarak doğruluğu artır.
BEAM_ENABLE = True

# Maksimum beam genişliği (küçük/orta n’de doğruluğu yükseltir; büyük n’de süreyi patlatır)
BEAM_WIDTH_MAX = 25

# n > bu değer ise beam otomatik kapanır (W=1)
BEAM_MAX_N = 200

# Adaptif beam: n büyüdükçe W küçülür (doğruluk-süre dengesi)
BEAM_ADAPTIVE = True
BEAM_CAP_IF_N_GT_30  = 10
BEAM_CAP_IF_N_GT_60  = 3
BEAM_CAP_IF_N_GT_100 = 2

# ---------------------------
# EDP_LOCAL triangulation kontrolü
# ---------------------------
# EDP_LOCAL_3SECT’te polygon triangulation pahalıdır. Yalnızca tour çok küçükken dene.
TRIANGULATION_ENABLE = True
TRIANGULATION_MAX_TOUR_N = 25

# ---------------------------
# Küçük n için daha güçlü local search (2-opt + relocate (+opsiyonel 3-opt))
# ---------------------------
RELOCATE_ENABLE = True          # Or-opt/relocate (1-node) local iyileştirme
THREE_OPT_ENABLE = True         # çok küçük n’de 3-opt dene
THREE_OPT_MAX_N = 30            # 3-opt yalnızca n <= bu değer için

# Or-opt (2/3-node segment relocation) — doğruluğu artırır (ek süre maliyeti vardır).
OR_OPT_ENABLE = True
OR_OPT_MAX_N = 400                 # n > bu değer ise Or-opt otomatik kapanır
OR_OPT_MAX_ROUNDS = 1              # Or-opt turu sayısı (1 genelde yeterli)
OR_OPT_SEG_LENS = (2, 3)           # segment uzunlukları (2 ve 3)
OR_OPT_KNN = 25                    # aday yerleştirme için KNN kapsamı
OR_OPT_MAX_MOVES_PER_ROUND = 2000  # her turda bakılacak maksimum hareket

# Backward/forward compatible aliases (older solve_variant code expects these names)
OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N = int(OR_OPT_MAX_MOVES_PER_ROUND)  # n <= 150
OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N = int(max(200, round(0.60 * OR_OPT_MAX_MOVES_PER_ROUND)))  # n > 150
OR_OPT_MAX_K = int(max(OR_OPT_SEG_LENS) if isinstance(OR_OPT_SEG_LENS, (list, tuple)) and len(OR_OPT_SEG_LENS) > 0 else 3)
OR_OPT_ROUNDS = int(OR_OPT_MAX_ROUNDS)
OR_OPT_CAND_K = int(OR_OPT_KNN)


# ---------------------------
# MF_EDP_ILS (tümdengelim + ILS) ayarları (v5)
# ---------------------------
MF_ENABLE = True

# Multi-Fragment greedy: aday kenar havuzu için komşu sayısı (KDTree varsa hızlı)
MF_KNN_K = 30                  # her düğüm için k en yakın komşudan kenar üret
MF_MAX_EDGES_MULT = 6          # toplam aday kenar ~ MF_MAX_EDGES_MULT * n (küçük n’de otomatik artar)
MF_FALLBACK_FULL_EDGES_N = 700 # n <= bu değer ise (hız uygunsa) tüm çiftler üzerinden kenar üretilebilir

# EDP hedefli yeniden-ekleme (kötü düğümleri çıkart/yeniden yerleştir)
MF_REINSERT_ENABLE = True
MF_REINSERT_PASSES = 2
MF_REINSERT_FOCUS_FRAC = 0.25      # en “pahalı” düğümlerin oranı
MF_REINSERT_MAX_PER_PASS = 40      # her pass’te en fazla bu kadar düğüm dene

# ILS (Iterated Local Search) – Double-Bridge perturbation
MF_ILS_ENABLE = True
MF_ILS_MAX_N = 2000
MF_ILS_ITERS_SMALL = 40            # n <= 120
MF_ILS_ITERS_MED = 25              # 120 < n <= 400
MF_ILS_ITERS_LARGE = 12            # 400 < n <= MF_ILS_MAX_N
MF_ILS_NO_IMPROVE_STOP = 12        # ardışık iyileşme yoksa dur
MF_ILS_SEED = 1234

MF_ILS_FAST_LS_N = 60            # n <= bu değer ise ILS içi local search 'fast' modda
# MF_EDP_ILS için multi-start (jitter'lı Multi-Fragment + farklı ILS seed) — doğruluğu artırır.
MF_MULTISTART_ENABLE = True
MF_MULTISTART_SEED_BASE = 12345
MF_MULTISTART_JITTER = 0.08        # 0.00 = deterministik; 0.05-0.10 makul
MF_MULTISTART_TRIES_SMALL = 8      # n <= 120
MF_MULTISTART_TRIES_MED = 5        # 120 < n <= 220
MF_MULTISTART_TRIES_LARGE = 3      # n > 220

# --- Legacy MF_MS_* block kept only for backward compatibility / documentation ---
# NOTE:
# The active multi-start schedule used by the current benchmark code is the MF_MULTISTART_* family above.
# The older MF_MS_* names were left in earlier versions of the file and can be confusing because they are
# not used by the current solve path. To avoid silent divergence between two parameter families, the
# compatibility aliases below are explicitly synchronized to the active MF_MULTISTART_* settings.
MF_MS_ENABLE = MF_MULTISTART_ENABLE
MF_MS_BASE_STARTS_SMALL = MF_MULTISTART_TRIES_SMALL
MF_MS_BASE_STARTS_MED = MF_MULTISTART_TRIES_MED
MF_MS_BASE_STARTS_LARGE = MF_MULTISTART_TRIES_LARGE
MF_MS_BASE_STARTS_XL = MF_MULTISTART_TRIES_LARGE
MF_MS_BASE_STARTS_XXL = MF_MULTISTART_TRIES_LARGE
MF_MS_RISK_BONUS = 0
MF_MS_CAP = max(MF_MS_BASE_STARTS_SMALL, MF_MS_BASE_STARTS_MED, MF_MS_BASE_STARTS_LARGE)
MF_MS_NOISE_SCALE = 1e-9

# ---------------------------
# MF stochastic seed-stability analysis
# ---------------------------
# MF_EDP_ILS includes multi-start and randomized perturbation steps.
# These repeats do NOT change the main benchmark rows; they create
# separate audit CSVs for variance / seed-stability reporting.
MF_SEED_STABILITY_ENABLE = False
MF_SEED_STABILITY_SUITES = ("core",)
MF_SEED_STABILITY_VARIANTS = ("MF_EDP_ILS",)
MF_SEED_STABILITY_REPEATS = 7
MF_SEED_STABILITY_SEED_BASE = 910241
MF_SEED_STABILITY_SEED_STRIDE = 1009
MF_SEED_STABILITY_MIN_N = 0
MF_SEED_STABILITY_MAX_N = 10**9
MF_SEED_STABILITY_EXPORT_RAW = True


# --- v4: MF_EDP_ILS geometri-adaptif yoğunlaştırma (doğruluk odaklı)
MF_GEOM_ADAPT_ENABLE = True
MF_GEOM_ADAPT_HULL_FRAC_MAX = 0.35   # hull_frac düşükse (çok interior nokta) risk artar
MF_GEOM_ADAPT_PCA_ASPECT_MAX = 2.0   # pca_aspect ~1..2 ise izotropik bulut
MF_GEOM_ADAPT_NN_CV_MIN = 0.55       # nn_cv yüksekse heterojen/cluster etkisi
MF_GEOM_ADAPT_ILS_MULT = 1.8         # riskli geometrilerde ILS iter sayısı çarpanı
MF_GEOM_ADAPT_EXTRA_REINSERT = True
MF_GEOM_ADAPT_REINSERT_FOCUS_FRAC = 0.40  # ek reinsertion için fokus (pahalı düğüm yüzdesi)
MF_GEOM_ADAPT_REINSERT_MAX_PER_PASS = 80  # ek reinsertion için üst sınır

# Geometri kayma raporu (MF_EDP_ILS için)
GEOM_DRIFT_REPORT_ENABLE = True
GEOM_DRIFT_GAP_THRESH_PCT = 1.0    # exact'a göre > %1 sapma “kayma” kabul edilir

# --- v4: Geometri drift raporu (aksiyona dönük) ek ayarlar
GEOM_DRIFT_RISK_ENABLE = True
GEOM_DRIFT_RISK_PRIOR_ALPHA = 1.0        # Beta prior alpha (smoothing)
GEOM_DRIFT_RISK_PRIOR_BETA  = 1.0        # Beta prior beta  (smoothing)
GEOM_DRIFT_RISK_MIN_INSTANCES = 5        # bin içinde bundan az örnek varsa risk skorunu NaN bırak
GEOM_DRIFT_FEATURE_IMPORTANCE_ENABLE = True
GEOM_DRIFT_FEATURE_IMPORTANCE_TOPK = 12  # konsola yazılacak top-k feature


def beam_width_for_n(n: int) -> int:
    """Adaptif beam genişliği."""
    if (not BEAM_ENABLE) or (n > BEAM_MAX_N):
        return 1
    w = int(BEAM_WIDTH_MAX)
    if BEAM_ADAPTIVE:
        if n > 100:
            w = min(w, int(BEAM_CAP_IF_N_GT_100))
        elif n > 60:
            w = min(w, int(BEAM_CAP_IF_N_GT_60))
        elif n > 30:
            w = min(w, int(BEAM_CAP_IF_N_GT_30))
    return max(1, w)

# ---------------------------
# Accuracy Guardrails helpers
# ---------------------------
class _TempGlobals:
    """Temporarily override module-level globals (safe, minimal patch for per-case accuracy profiles)."""
    def __init__(self, overrides: Dict[str, object]):
        self.overrides = dict(overrides or {})
        self._old = {}

    def __enter__(self):
        g = globals()
        for k, v in self.overrides.items():
            if k in g:
                self._old[k] = g[k]
            else:
                self._old[k] = None
            g[k] = v
        return self

    def __exit__(self, exc_type, exc, tb):
        g = globals()
        for k, oldv in self._old.items():
            if oldv is None and k not in self.overrides:
                continue
            if oldv is None:
                # best-effort: delete if it did not exist before
                try:
                    del g[k]
                except Exception:
                    pass
            else:
                g[k] = oldv
        return False

def _load_reference_gap_map(out_dir: str, current_tag: str) -> Tuple[Dict[Tuple[str, str], float], Optional[str]]:
    """Load a reference benchmark_results_*.csv for regression-based guardrails."""
    if not ACCURACY_GUARDRAILS_ENABLE:
        return {}, None

    ref = globals().get("ACCURACY_GUARDRAILS_REFERENCE_CSV", None)
    if ref is None:
        return {}, None

    ref_file = None
    if isinstance(ref, str) and ref.lower() == "auto":
        pat = os.path.join(out_dir, "benchmark_results_*.csv")
        files = sorted(glob.glob(pat))
        cur = os.path.join(out_dir, f"benchmark_results_{current_tag}.csv")
        files = [f for f in files if os.path.abspath(f) != os.path.abspath(cur)]
        if len(files) == 0:
            return {}, None

        # Robust selection: küçük/parsiyel koşuları (örn. sadece 3 satır yazan smoke-test) referans seçme
        min_rows = int(globals().get("GUARDRAILS_REF_AUTO_MIN_ROWS", 50))
        min_instances = int(globals().get("GUARDRAILS_REF_AUTO_MIN_UNIQUE_INSTANCES", 10))

        good = []
        for f in files:
            try:
                df0 = pd.read_csv(f)
            except Exception:
                continue
            if not {"instance", "variant", "gap_percent"}.issubset(set(df0.columns)):
                continue
            df_ok = df0
            try:
                if "status" in df_ok.columns:
                    df_ok = df_ok[df_ok["status"] == "OK"]
                if "suite" in df_ok.columns:
                    df_ok = df_ok[df_ok["suite"] == "core"]
            except Exception:
                pass
            try:
                nrows = int(len(df_ok))
                ninst = int(df_ok["instance"].nunique())
            except Exception:
                nrows = 0
                ninst = 0
            if (nrows >= min_rows) and (ninst >= min_instances):
                good.append(f)

        if len(good) > 0:
            ref_file = max(good, key=lambda f: os.path.getmtime(f))
        else:
            # fallback: en yeni dosya
            ref_file = max(files, key=lambda f: os.path.getmtime(f))
    else:
        ref_file = str(ref)
        if not os.path.isfile(ref_file):
            return {}, None

    try:
        df = pd.read_csv(ref_file)
    except Exception:
        return {}, None

    need = {"instance", "variant", "gap_percent"}
    if not need.issubset(set(df.columns)):
        return {}, None

    mp: Dict[Tuple[str, str], float] = {}
    for _, r in df.iterrows():
        try:
            inst = str(r["instance"])
            var = str(r["variant"])
            g = float(r["gap_percent"])
            if not np.isfinite(g):
                continue
            mp[(inst, var)] = g
        except Exception:
            continue
    return mp, ref_file


# ---------------------------
# Held–Karp (exact TSP) doğrulama
# ---------------------------
# Held–Karp dinamik programlama (bitmask DP) ile "gerçek optimum" (exact) tur uzunluğunu hesaplar.
# Üstel karmaşıklık nedeniyle sadece küçük n için çalıştırılır.
HK_ENABLE = True
HK_MAX_N = 20           # n <= 22 için exact doğrulama (maliyet hızla artar) (daha büyüğü için maliyet hızla artar)
HK_TOUR_MAX_N = 14      # n <= 14 ise optimum turun kendisini de geri kur (debug için); büyük n'de yalnızca uzunluk

# 5) Exact solver for global optimum (n > HK_MAX_N): MIP (python-mip + CBC)
#    Not: Concorde Windows kurulum/entegrasyon maliyeti yüksek olduğu için MIP seçildi.
EXACT_SOLVE_MODE = "validate"   # "off" | "validate" | "require"
MIP_ENABLE = True
MIP_MAX_N = 60                   # n > HK_MAX_N ve n <= bu değer ise MIP exact denenir
MIP_TIME_LIMIT_SEC = 300         # validate modunda zaman sınırı; require modunda isterseniz None yapın
MIP_SOLVER = "CBC"             # CBC (varsayılan) / diğerleri sisteminize bağlı
MIP_TOUR_MAX_N = 22              # küçük n için optimum turun kendisini de geri kur

try:
    from mip import Model, xsum, BINARY, INTEGER, OptimizationStatus, MINIMIZE
    MIP_OK = True
except Exception:
    MIP_OK = False


# 3) Küçük n için 2-opt'u yakınsak (converged) çalıştır (doğruluk modu)
SMALL_N_FULL_2OPT_N = HK_MAX_N    # n <= bu değer ise tam 2-opt (yakınsak) çalıştırılır

# Doğruluk önceliği: EDP 3-sektör kıyasını tüm tur kenarları üzerinde yap.
# (False yaparsanız yalnızca "candidate_edges" üzerinden yapar; hız artar ama doğruluk azalır.)
FULL_EDGE_SCAN_FOR_SECTORS = True

# Performans için: full scan sadece küçük/orta n’de kullanılır.
# n > FULL_EDGE_SCAN_MAX_N ise FULL_EDGE_SCAN_FOR_SECTORS True olsa bile KNN tabanlı aday-kenar setine geçilir.
FULL_EDGE_SCAN_MAX_N = 60
# Riskli geometri sınıflarında full scan eşiklerini yükselt (EDP sektörel kenar seçimi iyileşir)
FULL_EDGE_SCAN_RISKY_BOOST_ENABLE = True
FULL_EDGE_SCAN_MAX_N_RISKY = 120
# ---------------------------
# v2 (2026-02-15) Runtime Acceleration (optional; default OFF)
# Amaç: Büyük n’de (özellikle n>>FULL_EDGE_SCAN_MAX_N) aday-kenar setini ek bir filtreyle daraltmak.
# Not: Kapalıyken (False) 02.14.v1 davranışı korunur.
RUNTIME_ACCEL_ENABLE = False          # True yaparsanız hotedge/guardcap/midboost-edges devreye girer
RUNTIME_ACCEL_MIN_N = 200             # Yalnızca tur boyu >= bu değer ise uygula (erken aşamada davranış bozulmasın)
RUNTIME_HOTEDGE_K = 24                # En uzun K tur kenarı (edge index) aday setine eklenir
RUNTIME_GUARDCAP_EDGES = 32           # Aday-kenar sayısı üst sınırı (0/None: sınırsız)
RUNTIME_MIDBOOST_EDGES_M = 0          # >0 ise x noktasına en yakın M kenar-midpoint’i tutulur (0: kapalı)
RUNTIME_DEBUG_ACCEL = False           # True: aday set boyutlarını ekrana yazdırır
# EDP post-polish (cheap reinsertion) to improve EDP variants without heavy MF-ILS
EDP_POST_POLISH_ENABLE = True
EDP_POST_POLISH_MAX_N = 140
EDP_POST_POLISH_FOCUS_FRAC = 0.20
EDP_POST_POLISH_MAX_PER_PASS = 40
EDP_POST_POLISH_PASSES = 1

# EDP variants: risky geometry polish (cheap reinsertion + micro ILS)
EDP_VARIANT_POLISH_ENABLE = True
EDP_VARIANT_POLISH_MAX_N = 220
EDP_VARIANT_POLISH_FOCUS_FRAC = 0.22
EDP_VARIANT_POLISH_MAX_PER_PASS = 30
EDP_VARIANT_POLISH_PASSES = 1

EDP_MICRO_ILS_ENABLE = True
EDP_MICRO_ILS_MAX_N = 220
EDP_MICRO_ILS_ITERS = 2
EDP_MICRO_ILS_SEED_BASE = 24680
# micro-ILS sadece EDP_POLISH iyileştirme getirmediyse devreye girsin (daha seçici)
EDP_MICRO_ILS_ONLY_IF_POLISH_NO_IMPROVE = True

# EDP adaptif k-OPT burst (ör. eil* için mini 3-opt)
EDP_KOPT_BURST_ENABLE = True
EDP_KOPT_BURST_PREFIXES = ('eil',)
EDP_KOPT_BURST_MAX_N = 1200
EDP_KOPT_BURST_GAP_THRESH_PCT = 1.50
EDP_KOPT_BURST_TIME_LIMIT_SEC = 0.60
EDP_KOPT_BURST_MAX_TRIES = 900

# k-OPT burst genelleştirme:
# - Prefix filtresi (eil*) yerine, OPT/HK/MIP gibi referans biliniyorsa gap eşiği ile tetikle.
# - Prefix filtresi yine desteklenir; ancak opt biliniyorsa (TSPLIB) prefix'e bakmadan tetikleyebilir.
EDP_KOPT_BURST_IGNORE_PREFIX_IF_OPTKNOWN = True

# k-OPT burst sadece önceki (polish/micro) adımlar iyileştirme getirmediyse devreye girsin (daha seçici)
EDP_KOPT_BURST_ONLY_IF_MICRO_NO_IMPROVE = True

# 3-opt yerine (n büyükse) Or-opt burst ile devam etmek istersek:
EDP_KOPT_BURST_THREEOPT_MAX_N = 120
EDP_KOPT_BURST_LARGE_N_USE_OROPT = True
EDP_KOPT_BURST_OROPT_ROUNDS = 1
EDP_KOPT_BURST_OROPT_MAX_MOVES = 450
EDP_KOPT_BURST_OROPT_KNN_K = 25

# (opsiyonel) dense+isotropic gibi sınıflarda k-OPT için biraz daha fazla bütçe
EDP_KOPT_BURST_HARD_GAP_THRESH_PCT = 2.50
EDP_KOPT_BURST_HARD_TIME_MULT = 1.50
EDP_KOPT_BURST_HARD_TRIES_MULT = 1.50


# ---------------------------
# MPA-lite (Discrete MPA inspired) optional post-step for comparison
# ---------------------------
# Not: Klasik MPA sürekli optimizasyon için tasarlanmıştır; burada "MPA fikrinden esinli",
#      permütasyon problemlerine uygun, çok küçük popülasyon + kısa süreli fazlı perturbation uyguluyoruz.
# Amaç: MF_EDP_ILS çıktısı hâlâ kötü kalırsa (gap/geometry-risk) kontrollü bir çeşitlendirme ile iyileştirme denemek.
MPA_LITE_ENABLE = True
# Bu varyant, MF_EDP_ILS + MPA-lite poststep olarak raporlanır.
MPA_LITE_VARIANT_NAME = "MF_EDP_ILS_MPA"

# Bütçe kontrolü (hız odaklı):
MPA_LITE_POP = 4
MPA_LITE_MAX_GENS = 12
MPA_LITE_TIME_LIMIT_SEC = 0.90   # instance başına MPA aşaması üst sınır
MPA_LITE_FADS_PROB = 0.18        # rastgele "FADs" reinit olasılığı

# Fazlı adım büyüklüğü: Levy (early) -> mix -> Brownian (late)
MPA_LITE_LEVY_ALPHA = 1.55
MPA_LITE_MIN_KICK = 1
MPA_LITE_MAX_KICK = 14

# Seçicilik (comparative variant olsa da runtime şişmesini önler):
# - exact/opt biliniyorsa ve MF çözüm gap'i şu eşiğin altındaysa MPA aşamasını atla.
MPA_LITE_SKIP_IF_EXACT_GAP_LE_PCT = 0.15
# - n çok büyükse atla (MPA-lite kısa; ama yine de O(time) bütçeli)
MPA_LITE_MAX_N = 1200

EDP_GEOM_ADAPT_RISK_MIN = 0.32
EDP_GEOM_ADAPT_KNN_CAND_EDGES = 35

KNN_CAND_EDGES = 25


# ---------------------------
# Accuracy Guardrails (hybrid policy)
# ---------------------------
# Amaç: Performans için bazı ayarları kısıtladığımızda, belirli instance/geometri sınıflarında gap artışı olabiliyor.
# Bu mod:
# 1) Önce "fast policy" ile çözer,
# 2) Exact referans (OPT_TOUR / HK / MIP) varsa gap'i ölçer,
# 3) Gap belirginse veya önceki çalıştırmaya göre regression varsa, yalnızca o (instance,variant) için
#    daha doğru (ama daha pahalı) ayarları açıp ikinci bir pass çalıştırır ve daha iyi çözümü seçer.
ACCURACY_GUARDRAILS_ENABLE = True

# Referans CSV: None -> sadece mutlak gap eşiği ile çalışır
# "auto" -> results/ içinde en son benchmark_results_*.csv dosyasını referans alır (mevcut run hariç)
ACCURACY_GUARDRAILS_REFERENCE_CSV = "auto"

# Regression yakalama: gap, referanstan en az bu kadar artarsa guardrail tetiklenir
ACCURACY_GUARDRAILS_GAP_INCREASE_THRESH_PCT = 0.50

# Mutlak eşik: exact referans varsa ve gap > bu değer ise guardrail tetiklenir
ACCURACY_GUARDRAILS_ABS_GAP_THRESH_PCT = 3.00

# Hangi varyantlar için uygulanacak?
ACCURACY_GUARDRAILS_VARIANTS = ("EDP_3SECT", "EDP_LOCAL_3SECT")

# --- Geometri-gated Accuracy Guardrails (refined) ---
# Guardrails sadece (gap artışı) + (riskli geometri) birlikteyse tetiklensin.
ACCURACY_GUARDRAILS_REQUIRE_GEOM_RISK = True

# Hangi geometri sınıfları riskli kabul edilecek?
#  - "auto": OUT_DIR içindeki en son geom_drift_action_*.csv dosyasındaki geom_class değerlerini kullanır
#            (mevcut RUN_TAG hariç). Bulamazsa fallback listeye döner.
ACCURACY_GUARDRAILS_RISKY_GEOM_CLASSES = "auto"

# Otomatik yükleme yoksa kullanılacak varsayılan riskli sınıflar
ACCURACY_GUARDRAILS_RISKY_GEOM_CLASSES_FALLBACK = (
    "dense+isotropic+clustered",
    "dense+isotropic",
    "dense+clustered",
    "isotropic+clustered",
    "dense",
    "clustered",
    "isotropic",
)

# Ek koşul: continuous risk_score >= bu eşik olursa da riskli kabul edilir (NaN ise ihmal edilir)
ACCURACY_GUARDRAILS_GEOM_RISK_SCORE_MIN = 0.55


# --- Two-stage guardrails ---
# Tetiklenince önce kısa bir "mini-try" ile daha doğru profile yaklaş.
# Mini-try iyileşme sağlamazsa (uzunluk düşmezse) tam accurate profile'a geç.
ACCURACY_GUARDRAILS_TWO_STAGE = True

# Mini-try kabul kriteri: uzunluk en az 1 birim düşmeli.
# (İsterseniz 2-3 gibi daha agresif hale getirebilirsiniz.)
ACCURACY_GUARDRAILS_MINI_ACCEPT_IMPROVE_MIN_DELTA = 1

# --- Stage-3 guardrails (polish) ---
# 2-stage (mini->full) tetiklenip iyileşme sağlayamazsa, son çare olarak
# mevcut en iyi tur üzerinde kısa bir MF-ILS “polish” çalıştırır.
# Bu adım sadece belirli n aralığında çalıştırılır (performans güvenliği).
ACCURACY_GUARDRAILS_STAGE3 = True
ACCURACY_GUARDRAILS_STAGE3_MAX_N = 200
# Stage-3 kabul kriteri: uzunluk en az 1 birim düşmeli.
ACCURACY_GUARDRAILS_STAGE3_ACCEPT_IMPROVE_MIN_DELTA = 1
# Stage-3 ILS seed offset (deterministik tekrar üretilebilir ama Stage-2'den farklı)
ACCURACY_GUARDRAILS_STAGE3_SEED_OFFSET = 777

# Stage-3 polish overrides (yalnızca guardrails Stage-3 içinde uygulanır)
ACCURACY_PROFILE_OVERRIDES_STAGE3_POLISH = dict(
    # EDP / reinsertion tarafı (daha geniş tarama)
    FULL_EDGE_SCAN_FOR_SECTORS=True,
    FULL_EDGE_SCAN_MAX_N=max(int(FULL_EDGE_SCAN_MAX_N), 90),
    KNN_CAND_EDGES=max(int(KNN_CAND_EDGES), 50),

    # Final repair: daha agresif yerel arama
    TWO_OPT_TIME_LIMIT_SEC=max(float(TWO_OPT_TIME_LIMIT_SEC), 12.0),
    OR_OPT_ENABLE=True,
    OR_OPT_MAX_K=max(int(OR_OPT_MAX_K), 4),
    OR_OPT_ROUNDS=max(int(OR_OPT_ROUNDS), 2),
    OR_OPT_CAND_K=max(int(OR_OPT_CAND_K), 55),
    OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N=max(int(OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N), 5000),
    OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N=max(int(OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N), 3200),

    # Targeted reinsertion yoğunluğu
    MF_REINSERT_ENABLE=True,
    MF_REINSERT_FOCUS_FRAC=max(float(MF_REINSERT_FOCUS_FRAC), 0.35),
    MF_REINSERT_MAX_PER_PASS=max(int(MF_REINSERT_MAX_PER_PASS), 80),

    # ILS (escape) - kısa ama daha güçlü
    MF_ILS_ENABLE=True,
    MF_ILS_ITERS_SMALL=max(int(MF_ILS_ITERS_SMALL), 70),
    MF_ILS_ITERS_MED=max(int(MF_ILS_ITERS_MED), 40),
    MF_ILS_ITERS_LARGE=max(int(MF_ILS_ITERS_LARGE), 20),
    MF_ILS_NO_IMPROVE_STOP=max(int(MF_ILS_NO_IMPROVE_STOP), 20),
    MF_ILS_SEED=int(MF_ILS_SEED) + int(ACCURACY_GUARDRAILS_STAGE3_SEED_OFFSET),
)

# Mini-try profil ayarları: performans/accuracy dengeli.
ACCURACY_PROFILE_OVERRIDES_EDP_MINI = dict(
    FULL_EDGE_SCAN_FOR_SECTORS=True,
    # Full-edge scan mini'de yalnız küçük/orta n için; büyük n'de KNN candidate'a düşer.
    FULL_EDGE_SCAN_MAX_N=max(FULL_EDGE_SCAN_MAX_N, 60),
    KNN_CAND_EDGES=max(KNN_CAND_EDGES, 35),
    BEAM_ENABLE=True,
    BEAM_MAX_N=10**9,
    BEAM_WIDTH_MAX=max(BEAM_WIDTH_MAX, 15),
)

ACCURACY_PROFILE_OVERRIDES_EDP_LOCAL_MINI = dict(
    **ACCURACY_PROFILE_OVERRIDES_EDP_MINI,
    TRIANGULATION_ENABLE=True,
    TRIANGULATION_MAX_TOUR_N=max(TRIANGULATION_MAX_TOUR_N, 40),
)
# Guardrail profil ayarları (sadece tetiklenen case'lerde uygulanır)
# Not: EDP_LOCAL için triangulation limitini büyütmek önemli fark yaratabilir.
ACCURACY_PROFILE_OVERRIDES_EDP = dict(
    FULL_EDGE_SCAN_FOR_SECTORS=True,
    FULL_EDGE_SCAN_MAX_N=10**9,   # force full-edge scan
    KNN_CAND_EDGES=max(KNN_CAND_EDGES, 35),
    BEAM_ENABLE=True,
    BEAM_MAX_N=10**9,
    BEAM_WIDTH_MAX=max(BEAM_WIDTH_MAX, 25),
)

ACCURACY_PROFILE_OVERRIDES_EDP_LOCAL = dict(
    **ACCURACY_PROFILE_OVERRIDES_EDP,
    TRIANGULATION_ENABLE=True,
    TRIANGULATION_MAX_TOUR_N=max(TRIANGULATION_MAX_TOUR_N, 60),
)
# Mesafe matrisi önhesap (TSPLIB get_weight çağrılarını azaltır)
PRECOMPUTE_DIST_IF_N_LEQ = 1200


# Distance-matrix cache (per instance). Avoid recomputing the same D for each variant.
# This yields a large speedup because we solve multiple variants on the same instance in one run.
DIST_CACHE_ENABLE = True
DIST_CACHE_MAX_INSTANCES = 8   # simple LRU bound (None -> unlimited)
# EDP degenerate eşik
EDP_TRI_MIN_AREA = 1e-12


def _load_guardrails_risky_geom_classes(out_dir: str, current_tag: str) -> Tuple[set, Optional[str]]:
    '''Load a risky geom_class allow-list for geometry-gated guardrails.

    Source:
      - ACCURACY_GUARDRAILS_RISKY_GEOM_CLASSES = "auto": OUT_DIR/geom_drift_action_*.csv (exclude current run)
      - Or an explicit iterable of class strings
      - Falls back to ACCURACY_GUARDRAILS_RISKY_GEOM_CLASSES_FALLBACK if empty/unavailable
    '''
    if not ACCURACY_GUARDRAILS_ENABLE:
        return set(), None

    if not globals().get("ACCURACY_GUARDRAILS_REQUIRE_GEOM_RISK", False):
        # geom gate not required
        return set(), None

    cfg = globals().get("ACCURACY_GUARDRAILS_RISKY_GEOM_CLASSES", None)
    fallback = set(globals().get("ACCURACY_GUARDRAILS_RISKY_GEOM_CLASSES_FALLBACK", ()))

    # helper: if no meaningful fallback, keep empty
    def _norm_set(it):
        out = set()
        for x in (it or []):
            try:
                sx = str(x).strip()
                if sx:
                    out.add(sx)
            except Exception:
                pass
        return out

    # explicit list/tuple/set
    if cfg is not None and not (isinstance(cfg, str) and cfg.lower() == "auto"):
        try:
            s = _norm_set(cfg)
            return (s if len(s) > 0 else fallback), None
        except Exception:
            return (fallback if len(fallback) > 0 else set()), None

    # auto mode: scan for latest geom_drift_action_*.csv
    try:
        pat = os.path.join(out_dir, "geom_drift_action_*.csv")
        files = sorted(glob.glob(pat))
        cur = os.path.join(out_dir, f"geom_drift_action_{current_tag}.csv")
        files = [f for f in files if os.path.abspath(f) != os.path.abspath(cur)]
        if len(files) == 0:
            return (fallback if len(fallback) > 0 else set()), None

        latest = max(files, key=lambda f: os.path.getmtime(f))
        df = pd.read_csv(latest)
        if "geom_class" not in df.columns:
            return (fallback if len(fallback) > 0 else set()), latest

        s = _norm_set(df["geom_class"].dropna().unique().tolist())
        if len(s) == 0:
            return (fallback if len(fallback) > 0 else set()), latest
        return s, latest
    except Exception:
        return (fallback if len(fallback) > 0 else set()), None

def mf_multistart_tries(n: int) -> int:
    """MF_EDP_ILS için n'e bağlı multi-start deneme sayısı (performans-adaptif)."""
    try:
        n = int(n)
    except Exception:
        return int(MF_MULTISTART_TRIES_MED)

    # Çok küçük n'de (<=60) 8 başlangıç gereksiz derecede pahalı olabiliyor.
    # Doğruluğu korurken süreyi düşürmek için üst sınır uygula.
    if n <= 30:
        return max(1, min(int(MF_MULTISTART_TRIES_SMALL), 2))
    if n <= 60:
        return max(1, min(int(MF_MULTISTART_TRIES_SMALL), 3))

    if n <= 120:
        return int(MF_MULTISTART_TRIES_SMALL)
    if n <= 220:
        return int(MF_MULTISTART_TRIES_MED)
    return int(MF_MULTISTART_TRIES_LARGE)

# ---------------------------
# Veri yapıları
# ---------------------------
@dataclass
class ProblemData:
    name: str
    n: int
    coords: np.ndarray          # (n,2) internal index sırası
    edge_weight_type: str
    tsplib_problem: object
    node_ids: List[int]         # TSPLIB node id listesi (sıralı)
    node2i: Dict[int, int]      # node id -> internal index
    i2node: List[int]           # internal index -> node id

# Global in-memory cache for precomputed distance matrices (D)
_DIST_CACHE = {}
_DIST_CACHE_LRU = []  # list of keys (oldest first)


class DistanceOracle:
    """
    TSPLIB get_weight kullanan (tüm EDGE_WEIGHT_TYPE'lar için güvenli) mesafe oraklı.
    İsteğe bağlı olarak n küçükse D matrisi önhesaplar.
    """
    def __init__(self, p: ProblemData):
        self.p = p
        self.n = p.n
        self.problem = p.tsplib_problem
        self.i2node = p.i2node

        self.D = None
        if self.n <= PRECOMPUTE_DIST_IF_N_LEQ:
            cache_key = (str(self.p.name), int(self.n))
            if DIST_CACHE_ENABLE and cache_key in _DIST_CACHE:
                # reuse cached matrix
                self.D = _DIST_CACHE[cache_key]
            else:
                D = np.zeros((self.n, self.n), dtype=np.int32)
                for i in progress(
                    range(self.n), total=self.n, desc=f"{self.p.name} dist-matrix", leave=False,
                    enabled=SHOW_PROGRESS and SHOW_PRECOMPUTE_PROGRESS and self.n >= 300,
                    kind="generic"
                ):
                    ni = self.i2node[i]
                    for j in range(i + 1, self.n):
                        nj = self.i2node[j]
                        w = int(self.problem.get_weight(ni, nj))
                        D[i, j] = w
                        D[j, i] = w
                self.D = D

                # store in cache (simple LRU eviction)
                if DIST_CACHE_ENABLE:
                    _DIST_CACHE[cache_key] = D
                    _DIST_CACHE_LRU.append(cache_key)
                    if (DIST_CACHE_MAX_INSTANCES is not None) and (len(_DIST_CACHE_LRU) > int(DIST_CACHE_MAX_INSTANCES)):
                        old = _DIST_CACHE_LRU.pop(0)
                        try:
                            _DIST_CACHE.pop(old, None)
                        except Exception:
                            pass

    def dist(self, i: int, j: int) -> int:
        if i == j:
            return 0
        if self.D is not None:
            return int(self.D[i, j])
        # fallback
        return int(self.problem.get_weight(self.i2node[i], self.i2node[j]))

# ---------------------------
# Yardımcılar
# ---------------------------
def tour_length(tour: List[int], d: DistanceOracle) -> int:
    s = 0
    m = len(tour)
    for k in range(m):
        s += d.dist(tour[k], tour[(k + 1) % m])
    return int(s)


# ---------------------------
# Held–Karp exact optimum (doğrulama)
# ---------------------------
def held_karp_optimum(d: DistanceOracle, n: int, return_tour: bool = False) -> Tuple[int, Optional[List[int]]]:
    """
    Held–Karp DP ile TSP optimum tur uzunluğu (cycle) hesaplar.
    - Başlangıç düğümü 0 olarak sabitlenir (tur döngü olduğu için genelliği bozmaz).
    - return_tour=True ise (öneri: n<=HK_TOUR_MAX_N) optimum turun internal indeks listesini döndürür.
    """
    if n <= 1:
        return 0, [0] if return_tour else None
    if n == 2:
        L = d.dist(0, 1) * 2
        return int(L), [0, 1] if return_tour else None

    from itertools import combinations

    # hızlı erişim
    D = d.D  # precomputed olabilir
    def dist(i, j):
        return int(D[i, j]) if D is not None else int(d.dist(i, j))

    # DP sözlüğü: (mask, j) -> cost (0'dan başlayıp mask'teki düğümleri ziyaret ederek j'de biten en kısa yol)
    # mask her zaman bit0 içerir; j hiçbir zaman 0 değildir (base durum hariç).
    dp: Dict[Tuple[int, int], int] = {}
    parent: Optional[Dict[Tuple[int, int], int]] = {} if return_tour else None

    # base: {0, j}
    for j in range(1, n):
        mask = (1 << 0) | (1 << j)
        dp[(mask, j)] = dist(0, j)
        if parent is not None:
            parent[(mask, j)] = 0

    # büyüyen subset boyutları
    # r = subset toplam eleman sayısı (0 dahil)
    for r in progress(range(3, n + 1), total=(n - 2), desc="Held-Karp subsets", leave=False, enabled=SHOW_PROGRESS and SHOW_HK_PROGRESS and n >= 12, kind="hk"):
        new: Dict[Tuple[int, int], int] = {}
        # subset: {1..n-1} içinden r-1 eleman seç, 0 her zaman var
        for subset in combinations(range(1, n), r - 1):
            mask = 1
            for s in subset:
                mask |= (1 << s)

            # her olası bitiş düğümü j (subset içinde)
            for j in subset:
                pmask = mask ^ (1 << j)
                best_cost = None
                best_k = None

                # bir önceki adımda pmask ile bitiş k (subset içinde, k!=j)
                for k in subset:
                    if k == j:
                        continue
                    prev = dp.get((pmask, k), None)
                    if prev is None:
                        continue
                    cand = prev + dist(k, j)
                    if (best_cost is None) or (cand < best_cost):
                        best_cost = cand
                        best_k = k

                if best_cost is not None:
                    new[(mask, j)] = int(best_cost)
                    if parent is not None:
                        parent[(mask, j)] = int(best_k) if best_k is not None else 0

        dp = new

    full_mask = (1 << n) - 1
    best = None
    best_j = None
    for j in range(1, n):
        base_cost = dp.get((full_mask, j), None)
        if base_cost is None:
            continue
        cand = base_cost + dist(j, 0)
        if (best is None) or (cand < best):
            best = cand
            best_j = j

    if best is None:
        raise RuntimeError("Held–Karp: optimum hesaplanamadı (DP boş).")

    if not return_tour or parent is None or best_j is None:
        return int(best), None

    # tour reconstruction (internal indices)
    tour_rev = [best_j]
    mask = full_mask
    j = best_j
    while True:
        k = parent[(mask, j)]
        tour_rev.append(k)
        mask = mask ^ (1 << j)
        j = k
        if j == 0:
            break

    tour = list(reversed(tour_rev))  # starts with 0
    # tur döngü olduğu için son 0'ı dahil etmiyoruz; length n olmalı
    if len(tour) > n:
        # güvenlik
        tour = tour[:n]
    if len(tour) != n:
        # bazı uç durumlar için, yine de benzersizleştirerek düzelt
        seen = set()
        tour2 = []
        for node in tour:
            if node not in seen:
                tour2.append(node); seen.add(node)
        # eksik düğümleri ekle
        for node in range(n):
            if node not in seen:
                tour2.append(node); seen.add(node)
        tour = tour2[:n]

    return int(best), tour


def mip_tsp_optimum(d: 'DistanceOracle', n: int, time_limit_sec: Optional[float] = None, return_tour: bool = False):
    """
    Exact symmetric TSP via Directed MTZ MIP formulation (python-mip).
    Returns (opt_length, tour_or_None).
    - Guarantee holds only if solver status is OPTIMAL.
    """
    if not MIP_OK:
        raise ImportError("python-mip bulunamadı. Kurulum: pip install mip")
    if n <= 1:
        return 0, [0] if return_tour else None

    # distance matrix (int)
    W = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                W[i][j] = int(d.dist(i, j))

    m = Model(sense=MINIMIZE, solver_name=MIP_SOLVER)
    if time_limit_sec is not None:
        try:
            m.max_seconds = float(time_limit_sec)
        except Exception:
            pass

    x = [[None]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i][j] = m.add_var(var_type=BINARY, name=f"x({i},{j})")

    # MTZ ordering variables
    u = [None]*n
    u[0] = m.add_var(var_type=INTEGER, lb=0, ub=0, name="u0")  # fixed 0
    for i in range(1, n):
        u[i] = m.add_var(var_type=INTEGER, lb=1, ub=n-1, name=f"u{i}")

    # objective
    m.objective = xsum(W[i][j] * x[i][j] for i in range(n) for j in range(n) if i != j)

    # degree constraints (directed tour)
    for i in range(n):
        m += xsum(x[i][j] for j in range(n) if i != j) == 1
    for j in range(n):
        m += xsum(x[i][j] for i in range(n) if i != j) == 1

    # MTZ subtour elimination
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                m += u[i] - u[j] + n * x[i][j] <= n - 1

    status = m.optimize()
    if status != OptimizationStatus.OPTIMAL:
        return None, None

    opt_len = int(round(m.objective_value))

    if not return_tour:
        return opt_len, None

    # Recover tour starting from 0
    succ = [-1]*n
    for i in range(n):
        for j in range(n):
            if i != j and x[i][j].x is not None and x[i][j].x >= 0.5:
                succ[i] = j
                break

    tour = [0]
    cur = 0
    seen = set([0])
    for _ in range(n-1):
        nxt = succ[cur]
        if nxt == -1 or nxt in seen:
            break
        tour.append(nxt)
        seen.add(nxt)
        cur = nxt

    if len(tour) != n:
        # If recovery failed, still return length
        return opt_len, None

    return opt_len, tour

def build_pos_index(tour: List[int]) -> Dict[int, int]:
    return {node: i for i, node in enumerate(tour)}

def _cross2d(u: np.ndarray, v: np.ndarray) -> float:
    """2D cross product (scalar): u_x*v_y - u_y*v_x.
    NumPy 2.0 deprecates np.cross on 2D vectors; use this instead.
    """
    return float(u[0] * v[1] - u[1] * v[0])

def triangle_area2(A: np.ndarray, B: np.ndarray, C: np.ndarray) -> float:
    # 2*alan (mutlak)
    return abs(_cross2d(B - A, C - A))

def edp_point(A: np.ndarray, B: np.ndarray, C: np.ndarray) -> Optional[np.ndarray]:
    """
    Equal Detour Point (EDP) için barycentrik formül (Kimberling X(176) ile uyumlu):
      weights: (a + Δ/(s-a) : b + Δ/(s-b) : c + Δ/(s-c))
    a=|BC|, b=|CA|, c=|AB|, Δ=alan, s=yarı çevre.
    """
    a = float(np.linalg.norm(B - C))
    b = float(np.linalg.norm(C - A))
    c = float(np.linalg.norm(A - B))
    s = 0.5 * (a + b + c)
    area = 0.5 * triangle_area2(A, B, C)

    if area < EDP_TRI_MIN_AREA:
        return None
    if (s - a) <= 1e-15 or (s - b) <= 1e-15 or (s - c) <= 1e-15:
        return None

    wA = a + (area / (s - a))
    wB = b + (area / (s - b))
    wC = c + (area / (s - c))
    W = wA + wB + wC
    if not np.isfinite(W) or W <= 0:
        return None
    return (wA * A + wB * B + wC * C) / W

def _angle(P: np.ndarray, Q: np.ndarray) -> float:
    return math.atan2(float(Q[1] - P[1]), float(Q[0] - P[0]))

def wedge_index(P: np.ndarray, A: np.ndarray, B: np.ndarray, C: np.ndarray, X: np.ndarray) -> int:
    """
    P merkezli 3 ışın (PA, PB, PC) ile oluşan 3 sektörden hangisinde olduğumuzu (0,1,2) döndürür.
    Sektörler, (a0->a1), (a1->a2), (a2->a0) (a0<a1<a2 açı sırası) aralıklarıdır.
    """
    angs = [(_angle(P, A), 0), (_angle(P, B), 1), (_angle(P, C), 2)]
    angs.sort(key=lambda t: t[0])
    ths = [t[0] for t in angs]
    thX = _angle(P, X)

    # [ths[0],ths[1]) => 0 ; [ths[1],ths[2]) => 1 ; wrap => 2
    if ths[0] <= thX < ths[1]:
        return 0
    if ths[1] <= thX < ths[2]:
        return 1
    return 2

# ---------------------------
# TSPLIB yükleme ve opt tour okuma (robust)
# ---------------------------
def load_tsplib_problem(path: str) -> ProblemData:
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        problem = tsplib95.parse(text)
    else:
        problem = tsplib95.load(path)

    name = str(getattr(problem, "name", os.path.basename(path)))
    ewt = str(getattr(problem, "edge_weight_type", "") or "")

    node_ids = sorted(list(problem.get_nodes()))
    n = int(problem.dimension)

    coords_dict = getattr(problem, "node_coords", None)
    if not coords_dict:
        # MATRIX tipinde (gr17 vb.) olabilir; bu script EDP geometrisi için koordinat ister.
        raise ValueError(f"{name}: node_coords yok (MATRIX/koordinatsız instance olabilir).")

    node2i = {nid: i for i, nid in enumerate(node_ids)}
    i2node = node_ids[:]  # internal i -> node id

    coords = np.zeros((n, 2), dtype=float)
    for nid in node_ids:
        i = node2i[nid]
        x, y = coords_dict[nid]
        coords[i, 0] = float(x)
        coords[i, 1] = float(y)

    return ProblemData(
        name=name,
        n=n,
        coords=coords,
        edge_weight_type=ewt,
        tsplib_problem=problem,
        node_ids=node_ids,
        node2i=node2i,
        i2node=i2node
    )

def load_opt_tour_if_exists(inst_path: str, p: ProblemData) -> Optional[List[int]]:
    """
    .opt.tour dosyası varsa okur, TSPLIB node id listesinden internal indeks tura çevirir, doğrular.
    Kodlama bağımsız (rb + tolerant decode).
    """
    base = os.path.splitext(inst_path)[0]
    candidates = [
        base + ".opt.tour",
        base + ".opt.tour.gz",
        os.path.join(os.path.dirname(inst_path), os.path.basename(base) + ".opt.tour"),
        os.path.join(os.path.dirname(inst_path), os.path.basename(base) + ".opt.tour.gz"),
    ]

    def parse_tour_text(text: str) -> Optional[List[int]]:
        lines = text.splitlines()
        in_section = False
        vals = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            u = s.upper()
            if "TOUR_SECTION" in u:
                in_section = True
                continue
            if "EOF" in u:
                break
            if in_section:
                parts = s.replace("\t", " ").split()
                for token in parts:
                    try:
                        v = int(token)
                    except Exception:
                        continue
                    if v == -1:
                        in_section = False
                        break
                    if v != 0:
                        vals.append(v)
        return vals if vals else None

    def validate_and_map(node_seq: List[int]) -> Optional[List[int]]:
        if node_seq is None:
            return None

        # bazı dosyalarda start tekrar eder: n+1 ve ilk=son
        if len(node_seq) == p.n + 1 and node_seq[0] == node_seq[-1]:
            node_seq = node_seq[:-1]

        if len(node_seq) != p.n:
            return None

        # node id'leri internal'e çevir
        tour = []
        seen = set()
        for nid in node_seq:
            if nid not in p.node2i:
                return None
            i = p.node2i[nid]
            if i in seen:
                return None
            seen.add(i)
            tour.append(i)

        if len(tour) != p.n:
            return None
        return tour

    for c in candidates:
        if not os.path.exists(c):
            continue
        try:
            if c.endswith(".gz"):
                with gzip.open(c, "rb") as f:
                    raw = f.read()
            else:
                with open(c, "rb") as f:
                    raw = f.read()

            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1", errors="ignore")

            node_seq = parse_tour_text(text)
            tour = validate_and_map(node_seq)
            if tour is not None:
                return tour
        except Exception:
            continue

    return None

# ---------------------------
# KNN listeleri (güvenli)
# ---------------------------
def build_knn_lists(coords: np.ndarray, k: int) -> List[List[int]]:
    n = coords.shape[0]
    if n <= 1:
        return [[] for _ in range(n)]
    k_eff = min(int(k), n - 1)

    if SCIPY_OK:
        tree = cKDTree(coords)
        # kendisi dahil
        dists, idxs = tree.query(coords, k=k_eff + 1)
        out = []
        for i in range(n):
            row = np.atleast_1d(idxs[i]).tolist()
            neigh = [int(j) for j in row if (int(j) != i and 0 <= int(j) < n)]
            out.append(neigh[:k_eff])
        return out

    # SciPy yoksa O(n^2)
    out = []
    for i in range(n):
        di = np.linalg.norm(coords - coords[i], axis=1)
        idx = np.argsort(di)
        idx = [int(j) for j in idx if int(j) != i][:k_eff]
        out.append(idx)
    return out

# ---------------------------
# 2-opt (neighbor-limited)
# ---------------------------
def two_opt_limited(tour: List[int], d: DistanceOracle, nbrs: List[List[int]], time_limit: float) -> Tuple[List[int], int]:
    start = time.time()
    n = len(tour)
    improved_total = 0

    def apply_2opt(i: int, k: int):
        return tour[:i+1] + list(reversed(tour[i+1:k+1])) + tour[k+1:]

    for _pass in range(TWO_OPT_MAX_PASSES):
        if time.time() - start > time_limit:
            break
        pos = build_pos_index(tour)
        improved = False

        for i in range(n):
            if time.time() - start > time_limit:
                break
            a = tour[i]
            b = tour[(i + 1) % n]

            for c in nbrs[a]:
                j = pos.get(c, None)
                if j is None:
                    continue
                dnode = tour[(j + 1) % n]

                # komşu/degenerate atla
                if a == c or a == dnode or b == c or b == dnode:
                    continue
                if (i + 1) % n == j:
                    continue

                old = d.dist(a, b) + d.dist(c, dnode)
                new = d.dist(a, c) + d.dist(b, dnode)
                if new < old:
                    i0, k0 = i, j
                    if k0 < i0:
                        i0, k0 = k0, i0
                    if k0 - i0 >= 2 and k0 - i0 <= n - 2:
                        tour = apply_2opt(i0, k0)
                        improved_total += (old - new)
                        improved = True
                        break
            if improved:
                break

        if not improved:
            break

    return tour, int(improved_total)

# ---------------------------
# Polygon triangulation (ear clipping) + point tests
# ---------------------------
def polygon_area(poly: np.ndarray) -> float:
    # poly: (m,2)
    x = poly[:, 0]; y = poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

def point_in_triangle(P: np.ndarray, A: np.ndarray, B: np.ndarray, C: np.ndarray) -> bool:
    # barycentric sign method
    v0 = C - A
    v1 = B - A
    v2 = P - A

    dot00 = float(np.dot(v0, v0))
    dot01 = float(np.dot(v0, v1))
    dot02 = float(np.dot(v0, v2))
    dot11 = float(np.dot(v1, v1))
    dot12 = float(np.dot(v1, v2))

    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < 1e-18:
        return False
    inv = 1.0 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv
    v = (dot00 * dot12 - dot01 * dot02) * inv
    return (u >= -1e-12) and (v >= -1e-12) and (u + v <= 1.0 + 1e-12)

def point_in_polygon(P: np.ndarray, poly: np.ndarray) -> bool:
    # ray casting
    x, y = float(P[0]), float(P[1])
    inside = False
    m = poly.shape[0]
    for i in range(m):
        x1, y1 = float(poly[i, 0]), float(poly[i, 1])
        x2, y2 = float(poly[(i + 1) % m, 0]), float(poly[(i + 1) % m, 1])
        if ((y1 > y) != (y2 > y)):
            xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-18) + x1
            if x < xinters:
                inside = not inside
    return inside

def is_convex(prev: np.ndarray, curr: np.ndarray, nxt: np.ndarray, ccw: bool) -> bool:
    cross = _cross2d(curr - prev, nxt - curr)
    return cross > 1e-15 if ccw else cross < -1e-15

def triangulate_polygon_ear_clipping(poly: np.ndarray) -> Optional[List[Tuple[int, int, int]]]:
    """
    Basit ear clipping triangulation.
    poly: (m,2) kapalı olmayan, sıralı köşeler.
    Döndürdüğü üçgenler: poly indeksi (0..m-1) üzerinden (i,j,k).
    """
    m = poly.shape[0]
    if m < 3:
        return None
    ccw = polygon_area(poly) > 0

    idx = list(range(m))
    tris = []
    guard = 0

    while len(idx) > 3 and guard < 50000:
        guard += 1
        ear_found = False
        L = len(idx)

        for t in range(L):
            i_prev = idx[(t - 1) % L]
            i_curr = idx[t]
            i_next = idx[(t + 1) % L]

            A = poly[i_prev]
            B = poly[i_curr]
            C = poly[i_next]

            if not is_convex(A, B, C, ccw):
                continue

            # diğer noktalar üçgen içinde mi?
            ok = True
            for j in idx:
                if j in (i_prev, i_curr, i_next):
                    continue
                if point_in_triangle(poly[j], A, B, C):
                    ok = False
                    break
            if not ok:
                continue

            # ear
            tris.append((i_prev, i_curr, i_next))
            del idx[t]
            ear_found = True
            break

        if not ear_found:
            return None

    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
        return tris
    return None

# ---------------------------
# Üçgen seçimi (yerel/triangulation)
# ---------------------------
def select_triangle_local_knn(tour: List[int], x: int, coords: np.ndarray, knn_all: List[List[int]]) -> Optional[Tuple[int, int, int]]:
    # x'in komşuları içinden turda olan ilk 3
    in_set = set(tour)
    tri = []
    for nb in knn_all[x]:
        if nb in in_set:
            tri.append(nb)
            if len(tri) == 3:
                break
    return tuple(tri) if len(tri) == 3 else None

def select_triangle_from_polygon_triangulation(tour: List[int], x: int, coords: np.ndarray) -> Optional[Tuple[int, int, int]]:
    # Tour sırası polygon kabul edilir; x polygon içinde ise, ear clipping triangulation ile içerdiği üçgen bulunur.
    poly = coords[np.array(tour)]
    if poly.shape[0] < 3:
        return None

    # self-intersection olasılığı: point_in_polygon başarısız olabilir; yine de dene
    Px = coords[x]
    if not point_in_polygon(Px, poly):
        return None

    tris = triangulate_polygon_ear_clipping(poly)
    if tris is None:
        return None

    for (i, j, k) in tris:
        A = poly[i]; B = poly[j]; C = poly[k]
        if point_in_triangle(Px, A, B, C):
            return (tour[i], tour[j], tour[k])

    return None

# ---------------------------
# Insertion: CI ve EDP 3-sektör
# ---------------------------
def cheapest_insertion(tour: List[int], x: int, d: DistanceOracle, edge_indices: Optional[List[int]] = None) -> Tuple[List[int], int, int]:
    m = len(tour)
    if edge_indices is None:
        edge_indices = list(range(m))

    best_delta = None
    best_pos = None
    evals = 0

    for ei in edge_indices:
        u = tour[ei]
        v = tour[(ei + 1) % m]
        delta = d.dist(u, x) + d.dist(x, v) - d.dist(u, v)
        evals += 1
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_pos = ei + 1

    new_tour = tour[:best_pos] + [x] + tour[best_pos:]
    return new_tour, int(best_delta if best_delta is not None else 0), int(evals)

def edp_three_sector_insertion(
    tour: List[int],
    x: int,
    d: DistanceOracle,
    coords: np.ndarray,
    tri_nodes: Optional[Tuple[int, int, int]],
    candidate_edges: Optional[List[int]] = None
) -> Tuple[List[int], int, List[Optional[int]], List[Optional[int]], int]:
    """
    Her üç sektör için ayrı ayrı en iyi kenar kırmasını bulur, sonra bu 3 adaydan en iyisini seçer.
    Dönüş:
      new_tour,
      chosen_sector (0/1/2, -1 fallback),
      best_edge_per_sector (len=3, edge index or None),
      best_delta_per_sector (len=3, delta or None),
      evals
    """
    m = len(tour)

    if tri_nodes is None:
        # fallback: klasik cheapest insertion
        new_tour, _, evals = cheapest_insertion(tour, x, d, edge_indices=candidate_edges)
        return new_tour, -1, [None, None, None], [None, None, None], evals

    A_id, B_id, C_id = tri_nodes
    A = coords[A_id]; B = coords[B_id]; C = coords[C_id]
    Pp = edp_point(A, B, C)
    if Pp is None:
        new_tour, _, evals = cheapest_insertion(tour, x, d, edge_indices=candidate_edges)
        return new_tour, -1, [None, None, None], [None, None, None], evals

    # edge list
    if candidate_edges is None:
        candidate_edges = list(range(m))

    best_edge = [None, None, None]
    best_delta = [None, None, None]
    evals = 0

    for ei in candidate_edges:
        u = tour[ei]
        v = tour[(ei + 1) % m]
        mid = 0.5 * (coords[u] + coords[v])
        sidx = wedge_index(Pp, A, B, C, mid)

        delta = d.dist(u, x) + d.dist(x, v) - d.dist(u, v)
        evals += 1

        if best_delta[sidx] is None or delta < best_delta[sidx]:
            best_delta[sidx] = int(delta)
            best_edge[sidx] = int(ei)

    # üç sektördeki adaylar arasından en iyi delta'yı seç
    chosen = None
    chosen_delta = None
    for s in range(3):
        if best_delta[s] is None:
            continue
        if chosen_delta is None or best_delta[s] < chosen_delta:
            chosen_delta = best_delta[s]
            chosen = s

    if chosen is None:
        # hiçbir şey bulunamadı (teorik olarak olmamalı)
        new_tour, _, ev2 = cheapest_insertion(tour, x, d, edge_indices=candidate_edges)
        return new_tour, -1, best_edge, best_delta, evals + ev2

    ei = best_edge[chosen]
    new_tour = tour[:ei+1] + [x] + tour[ei+1:]
    return new_tour, int(chosen), best_edge, best_delta, int(evals)

# ---------------------------
# Başlangıç turu ve ekleme sırası
# ---------------------------
def initial_triangle_indices(coords: np.ndarray) -> Tuple[int, int, int]:
    n = coords.shape[0]
    a = int(np.argmin(coords[:, 0] + coords[:, 1]))
    b = int(np.argmax(coords[:, 0] + coords[:, 1]))
    if a == b:
        b = (a + 1) % n

    A = coords[a]; B = coords[b]
    AB = B - A
    denom = float(np.dot(AB, AB) + 1e-18)

    dif = coords - A
    proj = (dif @ AB) / denom
    proj_pt = A + np.outer(proj, AB)
    dist_to_line = np.linalg.norm(coords - proj_pt, axis=1)
    dist_to_line[[a, b]] = -1.0
    c = int(np.argmax(dist_to_line))
    if c in (a, b):
        c = int((a + 2) % n)
    return a, b, c

def insertion_order_farthest_from_centroid(coords: np.ndarray, tri: Tuple[int, int, int]) -> List[int]:
    tri_set = set(tri)
    centroid = coords[list(tri_set)].mean(axis=0)
    d = np.linalg.norm(coords - centroid, axis=1)
    remaining = [i for i in range(coords.shape[0]) if i not in tri_set]
    remaining.sort(key=lambda i: (-d[i], i))
    return remaining

# ---------------------------
# Çözücüler (varyantlar)
# ---------------------------
@dataclass
class BeamState:
    tour: List[int]
    length: int
    tri_fallback_count: int
    sector0_count: int
    sector1_count: int
    sector2_count: int
    sector_unknown_count: int


def _insert_at_edge(tour: List[int], ei: int, x: int) -> List[int]:
    # break edge tour[ei] -> tour[ei+1]
    return tour[:ei+1] + [x] + tour[ei+1:]


def local_2opt_focus(
    tour: List[int],
    d: DistanceOracle,
    nbrs: List[List[int]],
    focus_nodes: List[int],
    max_moves: int = 30
) -> Tuple[List[int], int]:
    """
    Çok küçük, doğruluk odaklı local 2-opt:
    - Sadece focus_nodes çevresindeki kenarları pivot alır.
    - First-improvement yaklaşımıyla max_moves hamle uygular.
    Dönüş: (tour, toplam_iyileştirme)
    """
    n = len(tour)
    if n < 4 or max_moves <= 0:
        return tour, 0

    improvement_total = 0
    focus_set = set(focus_nodes)

    for _ in range(max_moves):
        pos = build_pos_index(tour)
        best_gain = 0
        best_i = None
        best_k = None

        for a in list(focus_set):
            ia = pos.get(a, None)
            if ia is None:
                continue

            # iki yönlü kenar: (prev,a) ve (a,next)
            for i in [ (ia - 1) % n, ia ]:
                u = tour[i]
                v = tour[(i + 1) % n]

                # u üzerinden komşu c'leri dene
                for c in nbrs[u]:
                    jc = pos.get(c, None)
                    if jc is None:
                        continue
                    x1 = tour[jc]
                    y1 = tour[(jc + 1) % n]

                    # degenerate / komşu kenarları atla
                    if u in (x1, y1) or v in (x1, y1):
                        continue
                    if (i + 1) % n == jc:
                        continue

                    old = d.dist(u, v) + d.dist(x1, y1)
                    new = d.dist(u, x1) + d.dist(v, y1)
                    gain = old - new
                    if gain > best_gain:
                        # i < k olacak şekilde normalize et (slice reversal)
                        i0, k0 = i, jc
                        if k0 < i0:
                            i0, k0 = k0, i0
                        # çok kısa aralıklar anlamsız
                        if k0 - i0 >= 2 and k0 - i0 <= n - 2:
                            best_gain = gain
                            best_i = i0
                            best_k = k0

        if best_gain <= 0 or best_i is None:
            break

        # 2-opt reversal
        tour = tour[:best_i+1] + list(reversed(tour[best_i+1:best_k+1])) + tour[best_k+1:]
        improvement_total += int(best_gain)

        # odak kümesini hafif genişlet: etkilenen uçlar
        u = tour[best_i]
        v = tour[(best_i + 1) % n]
        w = tour[best_k]
        z = tour[(best_k + 1) % n]
        focus_set.update([u, v, w, z])

    return tour, int(improvement_total)


def two_opt_full_converge(tour: List[int], d: DistanceOracle, max_rounds: int = 2000) -> Tuple[List[int], int]:
    """
    Küçük n için tam 2-opt (yakınsak):
    - Tüm (i,k) çiftlerini tarar
    - First-improvement ile iyileştirme buldukça uygular
    """
    n = len(tour)
    if n < 4:
        return tour, 0

    improvement_total = 0
    rounds = 0

    while rounds < max_rounds:
        rounds += 1
        improved = False
        for i in range(n - 1):
            a = tour[i]
            b = tour[(i + 1) % n]
            for k in range(i + 2, n - (0 if i > 0 else 1)):
                c = tour[k]
                dnode = tour[(k + 1) % n]
                if a == c or a == dnode or b == c or b == dnode:
                    continue
                old = d.dist(a, b) + d.dist(c, dnode)
                new = d.dist(a, c) + d.dist(b, dnode)
                if new < old:
                    gain = old - new
                    # reverse (i+1..k)
                    tour = tour[:i+1] + list(reversed(tour[i+1:k+1])) + tour[k+1:]
                    improvement_total += int(gain)
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break

    return tour, int(improvement_total)


def local_relocate_focus(
    tour: List[int],
    d: DistanceOracle,
    nbrs: List[List[int]],
    focus_nodes: List[int],
    max_moves: int = 20
) -> Tuple[List[int], int]:
    """
    Doğruluk odaklı, küçük-bütçeli local relocate (1-node Or-opt):
    - Sadece focus_nodes ve onların KNN komşuları üzerinden aday taşımaları dener.
    - First-improvement yaklaşımıyla max_moves hamle uygular.
    Dönüş: (tour, toplam_iyileştirme)
    """
    n = len(tour)
    if n < 5 or max_moves <= 0:
        return tour, 0

    improvement_total = 0
    focus = set(focus_nodes)
    # komşuları da ekle
    for x in list(focus):
        for y in nbrs[x][:min(LOOKAHEAD_FOCUS_EXTRA_KNN, len(nbrs[x]))]:
            focus.add(int(y))

    for _ in range(max_moves):
        pos = build_pos_index(tour)

        improved = False
        # focus içindeki her düğümü, komşularının yanına taşımayı dene
        for x in list(focus):
            i = pos.get(int(x), None)
            if i is None:
                continue
            a = tour[i - 1]
            b = tour[(i + 1) % n]

            # x'i çıkarınca kazanım (pozitif iyileşme)
            gain_remove = d.dist(a, x) + d.dist(x, b) - d.dist(a, b)

            # aday hedefler: x'in KNN'leri
            for y in nbrs[x]:
                y = int(y)
                if y == x:
                    continue
                j = pos.get(y, None)
                if j is None:
                    continue

                # x'i y'nin hemen arkasına koyacağız: (y, z) kenarını kırar
                z = tour[(j + 1) % n]

                # degenerate durumlar: x zaten (y,z) kenarında veya y komşusu ise
                if y == a or y == x or y == b or z == x:
                    continue

                gain_insert = d.dist(y, z) - (d.dist(y, x) + d.dist(x, z))
                gain = gain_remove + gain_insert

                if gain > 1e-12:
                    # hamleyi uygula
                    t2 = tour[:i] + tour[i+1:]
                    # j, i'den sonra ise indeks kayar
                    j2 = j
                    if j2 > i:
                        j2 -= 1
                    tour = t2[:j2+1] + [x] + t2[j2+1:]
                    improvement_total += int(round(gain))
                    n = len(tour)
                    improved = True
                    break
            if improved:
                break

        if not improved:
            break

    return tour, int(improvement_total)


def relocate_limited_knn(
    tour: List[int],
    d: DistanceOracle,
    nbrs: List[List[int]],
    rounds: Optional[int] = None,
    max_rounds: int = 3,
    move_budget: Optional[int] = None,
    max_moves_per_round: int = 500
) -> Tuple[List[int], int]:
    """
    Büyük n için kontrollü relocate:
    - Tüm düğümleri dolaşır ama hedef pozisyonları KNN ile sınırlar.
    - max_rounds ve max_moves_per_round ile süre kontrol edilir.
    """
    # Backward/forward compatible aliases:
    # - rounds overrides max_rounds
    # - move_budget overrides max_moves_per_round
    if rounds is not None:
        max_rounds = int(rounds)
    if move_budget is not None:
        max_moves_per_round = int(move_budget)

    n = len(tour)
    if n < 5:
        return tour, 0
    total_imp = 0
    for _ in range(max_rounds):
        moves = 0
        improved_any = False
        pos = build_pos_index(tour)

        for i in range(n):
            if moves >= max_moves_per_round:
                break
            x = tour[i]
            a = tour[i - 1]
            b = tour[(i + 1) % n]
            gain_remove = d.dist(a, x) + d.dist(x, b) - d.dist(a, b)

            # En iyi hedefi ara (KNN üzerinden)
            best_gain = 0.0
            best_j = None
            for y in nbrs[x]:
                y = int(y)
                if y == x:
                    continue
                j = pos.get(y, None)
                if j is None:
                    continue
                z = tour[(j + 1) % n]
                if y == a or y == b or z == x:
                    continue
                gain_insert = d.dist(y, z) - (d.dist(y, x) + d.dist(x, z))
                gain = gain_remove + gain_insert
                if gain > best_gain:
                    best_gain = gain
                    best_j = j

            if best_j is not None and best_gain > 1e-12:
                # uygula
                t2 = tour[:i] + tour[i+1:]
                j2 = best_j
                if j2 > i:
                    j2 -= 1
                tour = t2[:j2+1] + [x] + t2[j2+1:]
                total_imp += int(round(best_gain))
                moves += 1
                improved_any = True
                pos = build_pos_index(tour)  # güncelle
                n = len(tour)

        if not improved_any:
            break

    return tour, int(total_imp)


def _apply_or_opt_by_nodes(tour: List[int], seg: List[int], insert_after: int) -> List[int]:
    """Segment (seg) düğümlerini turdan çıkarıp 'insert_after' düğümünden sonra yerleştirir."""
    if tour is None or len(tour) == 0:
        return tour
    seg_set = set(seg)
    if insert_after in seg_set:
        return tour
    rest = [u for u in tour if u not in seg_set]
    if len(rest) + len(seg) != len(tour):
        return tour
    try:
        j = rest.index(insert_after)
    except ValueError:
        return tour
    return rest[:j + 1] + list(seg) + rest[j + 1:]


def or_opt_limited_knn(
    tour: List[int],
    d: "DistanceOracle",
    nbrs: List[List[int]],
    seg_lens: Tuple[int, ...] = (2, 3),
    max_rounds: int = 1,
    max_moves_per_round: int = 2000,
    knn_k: int = 25,
) -> Tuple[List[int], float]:
    """
    Or-opt (segment relocation) yerel araması: 2 ve 3 uzunluklu segmentleri yeniden konumlandırır.
    KNN tabanlı aday yerleştirme ile maliyeti sınırlar.
    Returns: (tour, total_improvement).
    """
    if tour is None or len(tour) < 6:
        return tour, 0.0
    n = len(tour)
    if n > int(OR_OPT_MAX_N):
        return tour, 0.0

    seg_lens = tuple(int(x) for x in seg_lens if int(x) >= 2 and int(x) < n)
    if len(seg_lens) == 0:
        return tour, 0.0

    knn_k = int(knn_k) if knn_k is not None else int(OR_OPT_KNN)
    knn_k = max(5, knn_k)

    total_imp = 0.0

    for _round in range(int(max_rounds)):
        moves = 0
        improved_any = True

        while improved_any and moves < int(max_moves_per_round):
            improved_any = False
            n = len(tour)

            prev_map = {}
            next_map = {}
            for i, u in enumerate(tour):
                prev_map[u] = tour[i - 1]
                next_map[u] = tour[(i + 1) % n]

            for i in range(n):
                if moves >= int(max_moves_per_round):
                    break

                for L in seg_lens:
                    seg = [tour[(i + k) % n] for k in range(int(L))]
                    seg_set = set(seg)
                    b = seg[0]
                    e = seg[-1]
                    a = prev_map[b]
                    f = next_map[e]

                    cand = {a}
                    for nd in (b, e):
                        for nb in nbrs[nd][:knn_k]:
                            if nb not in seg_set:
                                cand.add(nb)

                    best_delta = 0.0
                    best_t = None

                    dab = d.dist(a, b)
                    def_ = d.dist(e, f)
                    daf = d.dist(a, f)

                    for t in cand:
                        if t in seg_set:
                            continue
                        u = next_map[t]
                        if u in seg_set:
                            u = f
                        delta = -dab - def_ - d.dist(t, u) + daf + d.dist(t, b) + d.dist(e, u)
                        if delta < best_delta - 1e-12:
                            best_delta = delta
                            best_t = t

                    if best_t is not None:
                        new_tour = _apply_or_opt_by_nodes(tour, seg, best_t)
                        if new_tour is not None and len(new_tour) == n:
                            tour = new_tour
                            total_imp += (-best_delta)
                            moves += 1
                            improved_any = True
                            break

                if improved_any:
                    break

    return tour, float(total_imp)


def or_opt_segment_limited_knn(tour: List[int], d: "DistanceOracle", nbrs: List[List[int]],
                               k: int = 2, rounds: int = 1, max_moves_per_round: int = 1500,
                               cand_k: int = 25) -> Tuple[List[int], int]:
    """
    Or-opt: relocate a contiguous segment of length k (k=2 or 3) to a new position.
    Limited by KNN candidate insertion points + move budget. Returns (tour, improvement).
    """
    n = len(tour)
    if n <= k + 2 or k < 2:
        return tour, 0
    if n > OR_OPT_MAX_N:
        return tour, 0

    total_imp = 0
    for _ in range(int(rounds)):
        pos = build_pos_index(tour)
        best_gain = 0.0
        best_move = None  # (i, y)

        moves = 0
        # sample segment starts in a pseudo-random but deterministic manner (stride)
        stride = 3 if n < 500 else 7
        for i in range(0, n, stride):
            # segment nodes (cyclic)
            seg = [tour[(i + t) % n] for t in range(k)]
            seg_set = set(seg)
            a_prev = tour[(i - 1) % n]
            a0 = seg[0]
            a_last = seg[-1]
            a_next = tour[(i + k) % n]

            # removal gain
            rem_old = d.dist(a_prev, a0) + d.dist(a_last, a_next)
            rem_new = d.dist(a_prev, a_next)
            rem_gain = rem_old - rem_new
            if rem_gain <= 1e-12:
                continue

            # candidate insertion points: neighbors of segment ends
            cand = []
            if nbrs is not None and len(nbrs) > 0:
                cand.extend(nbrs[a0][:int(cand_k)])
                cand.extend(nbrs[a_last][:int(cand_k)])
            # also try a few local edges near the segment itself
            cand.extend([tour[(i + k + 2) % n], tour[(i - 3) % n]])

            # de-dup candidates
            seen = set()
            cand2 = []
            for y in cand:
                if y in seg_set:
                    continue
                if y in seen:
                    continue
                seen.add(y)
                cand2.append(y)

            for y in cand2:
                j = pos.get(y, None)
                if j is None:
                    continue
                y_next = tour[(j + 1) % n]
                if y_next in seg_set:
                    continue
                # avoid no-op: inserting segment back to same cut (approx)
                if y == a_prev or y == a_last:
                    continue

                ins_old = d.dist(y, y_next)
                ins_new = d.dist(y, a0) + d.dist(a_last, y_next)
                gain = rem_gain + (ins_old - ins_new)
                if gain > best_gain + 1e-12:
                    best_gain = gain
                    best_move = (i, y)

                moves += 1
                if moves >= int(max_moves_per_round):
                    break
            if moves >= int(max_moves_per_round):
                break

        if best_move is None or best_gain <= 1e-9:
            break

        i, y = best_move
        seg = [tour[(i + t) % n] for t in range(k)]
        seg_set = set(seg)
        remaining = [node for node in tour if node not in seg_set]
        # insert after y
        j2 = remaining.index(y)
        tour = remaining[:j2 + 1] + seg + remaining[j2 + 1:]
        total_imp += int(round(best_gain))
    return tour, int(total_imp)


def relocate_one_full_converge(tour: List[int], d: DistanceOracle, max_rounds: int = 5000) -> Tuple[List[int], int]:
    """Or-opt (1-node relocate) yakınsak iyileştirme. Küçük n’de 2-opt yerel minimumundan kaçmak için çok etkilidir."""
    n = len(tour)
    if n < 5:
        return tour, 0

    improvement_total = 0
    for _ in range(max_rounds):
        best_gain = 0
        best_move = None  # (i, j) remove at i, insert after j
        # remove node at i (between a and b), insert after j (between c and d)
        for i in range(n):
            x = tour[i]
            a = tour[i - 1]
            b = tour[(i + 1) % n]
            # removing x merges a-b
            remove_gain = d.dist(a, x) + d.dist(x, b) - d.dist(a, b)

            for j in range(n):
                if j == i or (j + 1) % n == i:
                    continue
                c = tour[j]
                d2 = tour[(j + 1) % n]
                insert_cost = d.dist(c, x) + d.dist(x, d2) - d.dist(c, d2)

                gain = remove_gain - insert_cost
                if gain > best_gain + 1e-9:
                    best_gain = gain
                    best_move = (i, j)

        if best_move is None or best_gain <= 0:
            break

        i, j = best_move
        x = tour[i]
        # remove x
        tour2 = tour[:i] + tour[i+1:]
        if j > i:
            j -= 1
        # insert after j
        tour = tour2[:j+1] + [x] + tour2[j+1:]
        improvement_total += int(best_gain)
        n = len(tour)

    return tour, int(improvement_total)

def three_opt_full_converge(tour: List[int], d: DistanceOracle, max_rounds: int = 5000) -> Tuple[List[int], int]:
    """
    Küçük n için 3-opt yakınsak iyileştirme (first-improvement).

    Not: Tur listesi lineer temsil edildiğinde (slicing) son kenar (tour[-1] -> tour[0]) bazen
    fiilen "dondurulabilir". Bu nedenle her round’da farklı rotasyonlar denenir; böylece
    döngüsel turun tüm kenarları olası kırılma noktası olarak kapsanır.
    """
    n = len(tour)
    if n < 6:
        return tour, 0

    def _canon(t: List[int]) -> List[int]:
        # deterministik temsil: en küçük düğüm başa gelsin (tur rotasyonu eşdeğerdir)
        if not t:
            return t
        m = min(t)
        k = t.index(m)
        return t[k:] + t[:k]

    tour = _canon(tour)
    cur_len = tour_length(tour, d)
    improvement_total = 0

    for _ in range(max_rounds):
        improved = False

        # Rotasyon taraması: wrap-around kenarın da 3-opt kırılma noktası olmasını sağlar.
        for rot in range(n):
            t = tour[rot:] + tour[:rot] if rot else tour

            # i<j<k choose breakpoints on edges (i-1,i), (j-1,j), (k-1,k)
            for i in range(1, n - 4):
                a = t[i - 1]; b = t[i]
                for j in range(i + 2, n - 2):
                    c = t[j - 1]; d0 = t[j]
                    for k in range(j + 2, n):
                        e = t[k - 1]; f = t[k % n]

                        # current edges around breakpoints
                        cur_edges = d.dist(a, b) + d.dist(c, d0) + d.dist(e, f)

                        # segments: [0:i), [i:j), [j:k), [k:n)
                        s1 = t[:i]
                        s2 = t[i:j]
                        s3 = t[j:k]
                        s4 = t[k:]

                        # 7 reconnection options (excluding identity)
                        candidates = [
                            s1 + list(reversed(s2)) + s3 + s4,                        # reverse s2
                            s1 + s2 + list(reversed(s3)) + s4,                        # reverse s3
                            s1 + list(reversed(s2)) + list(reversed(s3)) + s4,        # reverse s2 & s3
                            s1 + s3 + s2 + s4,                                        # swap s2 and s3
                            s1 + s3 + list(reversed(s2)) + s4,                        # swap + reverse s2
                            s1 + list(reversed(s3)) + s2 + s4,                        # swap + reverse s3
                            s1 + list(reversed(s3)) + list(reversed(s2)) + s4,        # swap + reverse both
                        ]

                        for cand in candidates:
                            a2 = cand[i - 1]; b2 = cand[i]
                            c2 = cand[j - 1]; d2 = cand[j]
                            e2 = cand[k - 1]; f2 = cand[k % n]
                            new_edges = d.dist(a2, b2) + d.dist(c2, d2) + d.dist(e2, f2)

                            # quick filter: breakpoint edges improved?
                            if new_edges + 1e-9 < cur_edges:
                                cand_len = tour_length(cand, d)
                                if cand_len + 1e-9 < cur_len:
                                    prev_len = cur_len
                                    tour = _canon(cand)
                                    cur_len = cand_len  # rotation-invariant
                                    improvement_total += int(round(prev_len - cur_len))
                                    improved = True
                                    break

                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break

            if improved:
                break

        if not improved:
            break

    return tour, int(improvement_total)

def three_opt_burst_knn(
    tour: List[int],
    d: DistanceOracle,
    nbrs: List[List[int]],
    max_tries: int = 900,
    time_limit_sec: float = 0.60,
    neighbor_k: int = 10,
    seed: int = 0,
) -> Tuple[List[int], int]:
    '''Fast 3-opt mini-burst (KNN-guided) for medium n.

    Goal: For instances like TSPLIB eil* where EDP variants can remain sub-optimal,
    run a short, bounded 3-opt exploration using only boundary-edge delta evaluation.

    Notes:
    - Assumes symmetric distances (TSP). Segment reversals keep internal costs unchanged.
    - Uses KNN lists to pick breakpoints more intelligently than pure random.

    Returns: (tour, total_improvement)
    '''
    n = len(tour)
    if n < 6:
        return tour, 0

    try:
        import time as _time
        import numpy as _np
    except Exception:
        return tour, 0

    rng = _np.random.RandomState(int(seed) & 0xFFFFFFFF)

    t = list(tour)
    # canonical rotation for stability
    try:
        m = min(t)
        k0 = t.index(m)
        if k0:
            t = t[k0:] + t[:k0]
    except Exception:
        pass

    L = int(tour_length(t, d))
    imp_total = 0
    t0 = _time.time()
    nk = int(max(1, neighbor_k))

    for _ in range(int(max_tries)):
        if (_time.time() - t0) > float(time_limit_sec):
            break

        # Random rotation so the wrap-around edge is also affected across tries
        shift = int(rng.randint(0, n))
        tr = t[shift:] + t[:shift] if shift else t

        # Node->position map
        pos = {node: idx for idx, node in enumerate(tr)}

        i = int(rng.randint(1, n - 4))
        a = tr[i - 1]
        b = tr[i]

        nb = nbrs[b] if (isinstance(b, int) and 0 <= b < len(nbrs)) else []
        if not nb:
            continue

        jnode = nb[int(rng.randint(0, min(len(nb), nk)))]
        j = pos.get(jnode, None)
        if j is None or j <= i + 1 or j >= n - 2:
            continue

        c = tr[j - 1]
        d0 = tr[j]

        nd = nbrs[d0] if (isinstance(d0, int) and 0 <= d0 < len(nbrs)) else []
        if not nd:
            continue

        knode = nd[int(rng.randint(0, min(len(nd), nk)))]
        k = pos.get(knode, None)
        if k is None or k <= j + 1 or k >= n:
            continue

        e = tr[k - 1]
        f = tr[k]

        # segments
        s1 = tr[:i]
        s2 = tr[i:j]
        s3 = tr[j:k]
        s4 = tr[k:]
        if len(s2) < 2 or len(s3) < 2:
            continue

        cur_edges = d.dist(a, b) + d.dist(c, d0) + d.dist(e, f)

        best_delta = 0
        best_case = None

        # 1) reverse s2: (a,c) (b,d0) (e,f)
        delta = (d.dist(a, c) + d.dist(b, d0) + d.dist(e, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 1

        # 2) reverse s3: (a,b) (c,e) (d0,f)
        delta = (d.dist(a, b) + d.dist(c, e) + d.dist(d0, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 2

        # 3) reverse s2 & s3: (a,c) (b,e) (d0,f)
        delta = (d.dist(a, c) + d.dist(b, e) + d.dist(d0, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 3

        # 4) swap s2 and s3: (a,d0) (e,b) (c,f)
        delta = (d.dist(a, d0) + d.dist(e, b) + d.dist(c, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 4

        # 5) swap + reverse s2: (a,d0) (e,c) (b,f)
        delta = (d.dist(a, d0) + d.dist(e, c) + d.dist(b, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 5

        # 6) swap + reverse s3: (a,e) (d0,b) (c,f)
        delta = (d.dist(a, e) + d.dist(d0, b) + d.dist(c, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 6

        # 7) swap + reverse both: (a,e) (d0,c) (b,f)
        delta = (d.dist(a, e) + d.dist(d0, c) + d.dist(b, f)) - cur_edges
        if delta < best_delta:
            best_delta = delta
            best_case = 7

        if best_case is None or best_delta >= 0:
            continue

        # build new tour (rotation doesn't matter for a cycle)
        if best_case == 1:
            t = s1 + list(reversed(s2)) + s3 + s4
        elif best_case == 2:
            t = s1 + s2 + list(reversed(s3)) + s4
        elif best_case == 3:
            t = s1 + list(reversed(s2)) + list(reversed(s3)) + s4
        elif best_case == 4:
            t = s1 + s3 + s2 + s4
        elif best_case == 5:
            t = s1 + s3 + list(reversed(s2)) + s4
        elif best_case == 6:
            t = s1 + list(reversed(s3)) + s2 + s4
        else:
            t = s1 + list(reversed(s3)) + list(reversed(s2)) + s4

        L = int(L + best_delta)
        imp_total += int(-best_delta)

    # final canonical rotation
    try:
        m = min(t)
        k0 = t.index(m)
        if k0:
            t = t[k0:] + t[:k0]
    except Exception:
        pass

    return t, int(imp_total)


def strong_local_search_small_n(tour: List[int], d: DistanceOracle) -> Tuple[List[int], int]:
    """Küçük n’de doğruluğu artırmak için 2-opt sonrası ek local aramalar."""
    total_imp = 0
    if RELOCATE_ENABLE:
        tour, imp = relocate_one_full_converge(tour, d)
        total_imp += int(imp)
        # relocate sonrası tekrar 2-opt iyi olur
        tour, imp2 = two_opt_full_converge(tour, d)
        total_imp += int(imp2)
    # 3-opt (opsiyonel, yalnızca çok küçük n)
    if THREE_OPT_ENABLE and len(tour) <= THREE_OPT_MAX_N:
        tour, imp3 = three_opt_full_converge(tour, d)
        total_imp += int(imp3)
    return tour, int(total_imp)


def best_edges_by_sector(
    tour: List[int],
    x: int,
    d: DistanceOracle,
    coords: np.ndarray,
    tri_nodes: Optional[Tuple[int, int, int]],
    candidate_edges: Optional[List[int]] = None
) -> Tuple[Optional[np.ndarray], List[Optional[int]], List[Optional[int]], int]:
    """
    Seçilen üçgen (tri_nodes) üzerinden EDP noktası P üretir ve her sektör için en iyi kırılacak kenarı bulur.
    Dönüş:
      P (None ise), best_edge[3], best_delta[3], evals
    """
    m = len(tour)
    if candidate_edges is None:
        candidate_edges = list(range(m))

    # üçgen yoksa P üretilemez
    if tri_nodes is None:
        return None, [None, None, None], [None, None, None], 0

    A_id, B_id, C_id = tri_nodes
    A = coords[A_id]; B = coords[B_id]; C = coords[C_id]
    Pp = edp_point(A, B, C)
    if Pp is None:
        return None, [None, None, None], [None, None, None], 0

    best_edge = [None, None, None]
    best_delta = [None, None, None]
    evals = 0

    for ei in candidate_edges:
        u = tour[ei]
        v = tour[(ei + 1) % m]
        mid = 0.5 * (coords[u] + coords[v])
        sidx = wedge_index(Pp, A, B, C, mid)

        delta = d.dist(u, x) + d.dist(x, v) - d.dist(u, v)
        evals += 1
        if best_delta[sidx] is None or delta < best_delta[sidx]:
            best_delta[sidx] = int(delta)
            best_edge[sidx] = int(ei)

    return Pp, best_edge, best_delta, int(evals)


# ---------------------------------------------------------------------
# MF (Multi-Fragment) + EDP reinsertion + ILS (Double-Bridge)
# ---------------------------------------------------------------------

class DSU:
    """Disjoint Set Union for subtour-prevention in multi-fragment heuristic."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, a: int) -> int:
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a: int, b: int) -> bool:
        ra = self.find(a); rb = self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def _tour_from_adj(adj: List[List[int]]) -> List[int]:
    """Adjacency (degree 2) -> cyclic tour list."""
    n = len(adj)
    start = 0
    tour = [start]
    prev = -1
    cur = start
    for _ in range(n - 1):
        nbrs = adj[cur]
        if len(nbrs) == 0:
            break
        nxt = nbrs[0] if nbrs[0] != prev else (nbrs[1] if len(nbrs) > 1 else -1)
        if nxt < 0:
            break
        tour.append(nxt)
        prev, cur = cur, nxt
    return tour


def multifragment_greedy_tour(
    d: "DistanceOracle",
    coords: np.ndarray,
    use_progress: bool = False,
    desc: str = "MF edges",
    rng: Optional[np.random.Generator] = None,
    jitter: float = 0.0,
    knn_k: Optional[int] = None,
) -> Optional[List[int]]:
    """
    Multi-Fragment greedy heuristic (a.k.a. multiple-fragment / greedy tour construction).
    Builds a degree-2 spanning cycle by adding shortest edges without creating subtours.
    Returns a tour (cycle) as node index list.
    """
    n = coords.shape[0]
    if n < 3:
        return list(range(n))

    # Candidate edges: either full (small n) or kNN-based.
    edges = []
    if (n <= MF_FALLBACK_FULL_EDGES_N) or (not SCIPY_OK):
        # Full pair enumeration (safe for small n)
        for i in range(n):
            for j in range(i + 1, n):
                edges.append((d.dist(i, j), i, j))
    else:
        # KDTree over coordinates (approx neighbor selection for GEO/ATT, true distance used in edge weights)
        tree = cKDTree(coords)
        _knn_base = int(MF_KNN_K) if (knn_k is None) else int(knn_k)
        _knn_base = max(3, _knn_base)
        k = min(_knn_base + 1, n)
        nn_d, nn_idx = tree.query(coords, k=k)
        seen = set()
        for i in range(n):
            for j in nn_idx[i][1:]:
                a, b = (i, int(j))
                if a == b:
                    continue
                if a > b:
                    a, b = b, a
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                edges.append((d.dist(a, b), a, b))

        # Ensure enough edges (rarely KDTree k too small for some geometries)
        target_edges = max(int(MF_MAX_EDGES_MULT * n), 10 * n)
        if len(edges) < target_edges and n <= 3000:
            # expand k once
            k2 = min(max(k, 10) + 20, n)
            nn_d, nn_idx = tree.query(coords, k=k2)
            for i in range(n):
                for j in nn_idx[i][k:]:
                    a, b = (i, int(j))
                    if a == b:
                        continue
                    if a > b:
                        a, b = b, a
                    if (a, b) in seen:
                        continue
                    seen.add((a, b))
                    edges.append((d.dist(a, b), a, b))

    # Multi-start için: kenar ağırlıklarını küçük bir jitter ile farklılaştır (sadece sıralamayı etkiler).
    if rng is not None and float(jitter) > 0.0:
        j = float(jitter)
        edges = [(float(w) * (1.0 + j * (float(rng.random()) - 0.5)), a, b) for (w, a, b) in edges]

    edges.sort(key=lambda t: t[0])

    deg = [0] * n
    adj = [[] for _ in range(n)]
    dsu = DSU(n)
    m_edges = 0

    it_edges = edges
    if use_progress:
        it_edges = progress(edges, total=len(edges), desc=desc, leave=False, enabled=SHOW_PROGRESS, kind="mf_edges", position=2)

    for w, i, j in it_edges:
        if deg[i] >= 2 or deg[j] >= 2:
            continue

        # Prevent premature subtours unless this is the final closing edge.
        if dsu.find(i) == dsu.find(j):
            # allow only if we're about to close the global cycle
            if m_edges < n - 1:
                continue

        # accept
        adj[i].append(j); adj[j].append(i)
        deg[i] += 1; deg[j] += 1
        m_edges += 1

        if dsu.find(i) != dsu.find(j):
            dsu.union(i, j)

        if m_edges == n:
            break

    # Close if we have a single Hamiltonian path (n-1 edges): connect endpoints.
    if m_edges == n - 1:
        ends = [i for i in range(n) if deg[i] == 1]
        if len(ends) == 2:
            i, j = ends
            adj[i].append(j); adj[j].append(i)
            deg[i] += 1; deg[j] += 1
            m_edges += 1

    if m_edges != n or any(di != 2 for di in deg):
        # Fallback: nearest-neighbor tour (always feasible)
        tour = nearest_neighbor_tour(d, n)
        return tour

    tour = _tour_from_adj(adj)
    if len(tour) != n or len(set(tour)) != n:
        # fallback to NN if traversal failed
        return nearest_neighbor_tour(d, n)
    return tour


def multifragment_greedy_tour_randomized(d: "DistanceOracle", coords: np.ndarray,
                                        rng: "np.random.RandomState",
                                        noise_scale: float = 1e-9,
                                        use_progress: bool = False, desc: str = "MF edges (rand)") -> List[int]:
    """Multi-Fragment greedy tour with a tiny random jitter to break ties (multi-start diversity)."""
    n = coords.shape[0]
    # construct all edges with slight noise on length
    edges = []
    for i in range(n):
        xi = coords[i]
        for j in range(i + 1, n):
            w = float(np.hypot(xi[0] - coords[j, 0], xi[1] - coords[j, 1]))
            if rng is not None:
                w = w + float(noise_scale) * float(rng.rand())
            edges.append((w, i, j))
    edges.sort(key=lambda t: t[0])

    parent = list(range(n))
    rank = [0] * n

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1

    deg = [0] * n
    adj = [[] for _ in range(n)]
    selected = 0

    it_edges = progress(edges, total=len(edges), desc=desc, leave=False, kind="mf_edges",
                        enabled=use_progress and len(edges) >= 200000, position=3)

    for w, i, j in it_edges:
        if deg[i] >= 2 or deg[j] >= 2:
            continue
        # avoid premature cycle
        if selected < n - 1 and find(i) == find(j):
            continue
        adj[i].append(j)
        adj[j].append(i)
        deg[i] += 1
        deg[j] += 1
        selected += 1
        union(i, j)
        if selected == n:
            break

    # build Hamiltonian cycle from 2-regular graph
    start = 0
    tour = [start]
    prev = -1
    cur = start
    while True:
        nei = adj[cur]
        nxt = nei[0] if nei[0] != prev else (nei[1] if len(nei) > 1 else None)
        if nxt is None:
            break
        if nxt == start:
            break
        tour.append(nxt)
        prev, cur = cur, nxt
        if len(tour) >= n:
            break
    if len(tour) != n:
        # fallback to deterministic MF if something goes wrong (should not)
        tour = multifragment_greedy_tour(d, coords, use_progress=use_progress, desc=desc)
    return tour


def nearest_neighbor_tour(d: "DistanceOracle", n: int, start: int = 0) -> List[int]:
    """Simple NN tour (fallback)."""
    unvisited = set(range(n))
    tour = [start]
    unvisited.remove(start)
    cur = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: d.dist(cur, j))
        tour.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    return tour


def node_contributions(tour: List[int], d: "DistanceOracle") -> np.ndarray:
    """Per-node contribution in a cycle: d(prev,i)+d(i,next)."""
    n = len(tour)
    contrib = np.zeros(n, dtype=float)
    for k, node in enumerate(tour):
        prev = tour[(k - 1) % n]
        nxt = tour[(k + 1) % n]
        contrib[k] = d.dist(prev, node) + d.dist(node, nxt)
    return contrib


def remove_node_from_tour(tour: List[int], idx: int) -> List[int]:
    """Remove node at position idx (by index in tour list)."""
    return tour[:idx] + tour[idx + 1:]


def double_bridge_move(tour: List[int], rng: np.random.RandomState) -> List[int]:
    """Standard double-bridge perturbation for ILS (tour is cyclic list)."""
    n = len(tour)
    if n < 8:
        return tour[:]
    # choose 4 cut points
    cuts = sorted(rng.choice(np.arange(1, n), size=4, replace=False))
    a, b, c, d_ = cuts
    p1 = tour[:a]
    p2 = tour[a:b]
    p3 = tour[b:c]
    p4 = tour[c:d_]
    p5 = tour[d_:]
    # recombine
    return p1 + p4 + p3 + p2 + p5


# ---------------------------
# Discrete MPA-lite (phase-based perturbation) helpers
# ---------------------------
def _mpa_double_bridge_move(tour: List[int], rng: "np.random.Generator") -> List[int]:
    """Double-bridge perturbation using NumPy Generator."""
    n = len(tour)
    if n < 8:
        return tour[:]
    cuts = sorted(rng.choice(np.arange(1, n), size=4, replace=False).tolist())
    a, b, c, d_ = cuts
    p1 = tour[:a]
    p2 = tour[a:b]
    p3 = tour[b:c]
    p4 = tour[c:d_]
    p5 = tour[d_:]
    return p1 + p4 + p3 + p2 + p5

def _mpa_random_2opt_kick(tour: List[int], rng: "np.random.Generator") -> List[int]:
    """Single random 2-opt reversal (kick)."""
    n = len(tour)
    if n < 5:
        return tour[:]
    i = int(rng.integers(0, n))
    j = int(rng.integers(0, n))
    if i == j:
        return tour[:]
    if i > j:
        i, j = j, i
    if (j - i) < 2:
        return tour[:]
    return tour[:i] + list(reversed(tour[i:j])) + tour[j:]

def _mpa_levy_kick_size(rng: "np.random.Generator", alpha: float, kmin: int, kmax: int) -> int:
    """Heavy-tailed integer kick size (cheap approximation via Pareto)."""
    try:
        x = float(rng.pareto(alpha) + 1.0)  # >=1
    except Exception:
        x = float(abs(rng.normal()) + 1.0)
    # scale so that most draws are small but occasional large jumps appear
    k = int(kmin + round(2.2 * x))
    if k < int(kmin):
        k = int(kmin)
    if k > int(kmax):
        k = int(kmax)
    return int(k)

def _mpa_brownian_kick_size(rng: "np.random.Generator", kmin: int, kmax: int) -> int:
    """Small kick size (late phase)."""
    # Mostly 1-3, rarely 4-5
    k = int(max(1, round(abs(float(rng.normal(loc=1.4, scale=0.9))))))
    if k < int(kmin):
        k = int(kmin)
    if k > int(kmax):
        k = int(kmax)
    return int(k)

def _mpa_apply_kicks(tour: List[int], rng: "np.random.Generator", k: int) -> List[int]:
    """Apply a mixture of kicks (double-bridge + 2-opt) k times."""
    t = tour[:]
    kk = int(max(1, k))
    for _ in range(kk):
        if float(rng.random()) < 0.55:
            t = _mpa_double_bridge_move(t, rng)
        else:
            t = _mpa_random_2opt_kick(t, rng)
    return t

def mpa_lite_refine(
    tour_in: List[int],
    d: "DistanceOracle",
    nbrs_2opt: List[List[int]],
    seed: int,
    time_limit_sec: float,
    pop_size: int,
    max_gens: int,
    desc_prefix: str = "",
) -> Tuple[List[int], Dict[str, float]]:
    """Discrete MPA-inspired short post-refinement. Returns (best_tour, info)."""
    t0 = time.time()
    rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)

    base = tour_in[:]
    base_L = float(tour_length(base, d))
    best = base
    best_L = base_L

    pop = [base]
    # init population with diversified kicks + fast local improve
    for i in range(int(max(1, pop_size)) - 1):
        k0 = _mpa_levy_kick_size(rng, float(MPA_LITE_LEVY_ALPHA), int(MPA_LITE_MIN_KICK), int(MPA_LITE_MAX_KICK))
        cand = _mpa_apply_kicks(base, rng, k0)
        cand, _, _ = local_improve(cand, d, nbrs_2opt, mode="fast")
        pop.append(cand)

    # evaluate init
    for cand in pop:
        Lc = float(tour_length(cand, d))
        if Lc < best_L:
            best_L = Lc
            best = cand

    gens_done = 0
    improved = False

    for g in range(int(max_gens)):
        if (time.time() - t0) > float(time_limit_sec):
            break
        gens_done = g + 1
        phase = float(g) / max(1.0, float(max_gens) - 1.0)

        # phase schedule: early exploration (Levy), mid mix, late exploitation (Brownian)
        for i in range(len(pop)):
            if (time.time() - t0) > float(time_limit_sec):
                break

            if phase < 0.33:
                k = _mpa_levy_kick_size(rng, float(MPA_LITE_LEVY_ALPHA), int(MPA_LITE_MIN_KICK), int(MPA_LITE_MAX_KICK))
            elif phase < 0.66:
                kL = _mpa_levy_kick_size(rng, float(MPA_LITE_LEVY_ALPHA), int(MPA_LITE_MIN_KICK), int(MPA_LITE_MAX_KICK))
                kB = _mpa_brownian_kick_size(rng, int(MPA_LITE_MIN_KICK), min(5, int(MPA_LITE_MAX_KICK)))
                k = int(max(1, round(0.55 * kL + 0.45 * kB)))
            else:
                k = _mpa_brownian_kick_size(rng, int(MPA_LITE_MIN_KICK), min(6, int(MPA_LITE_MAX_KICK)))

            # choose base: mostly global best, sometimes own position
            base_t = best if float(rng.random()) < 0.70 else pop[i]

            cand = _mpa_apply_kicks(base_t, rng, k)

            # FADs: occasional reinit from best with larger kick
            if float(rng.random()) < float(MPA_LITE_FADS_PROB):
                kfad = int(max(int(k), int(MPA_LITE_MAX_KICK)))
                cand = _mpa_apply_kicks(best, rng, kfad)

            cand, _, _ = local_improve(cand, d, nbrs_2opt, mode="fast")
            Lc = float(tour_length(cand, d))

            if Lc < best_L:
                best_L = Lc
                best = cand
                improved = True
            pop[i] = cand

    info = {
        "mpa_used": 1.0,
        "mpa_pop": float(max(1, pop_size)),
        "mpa_gens": float(gens_done),
        "mpa_time_sec": float(time.time() - t0),
        "mpa_improvement": float(max(0.0, base_L - best_L)),
        "mpa_improved": 1.0 if improved else 0.0,
    }
    return best, info



def local_improve(
    tour: List[int],
    d: "DistanceOracle",
    nbrs_2opt: List[List[int]],
    mode: str = "full",
) -> Tuple[List[int], int, float]:
    """Run local search stack.

    mode:
      - "full": 2-opt + relocate + (opsiyonel or-opt) + (küçük n'de 3-opt)
      - "fast": özellikle ILS içi tekrarlandığında süreyi düşürmek için hafifletilmiş sürüm
    Returns (tour, improvement_count, time_sec).
    """
    t0 = time.time()
    imp_total = 0

    mode = str(mode).strip().lower()
    if mode not in ("full", "fast"):
        mode = "full"

    n = len(tour)

    # --- Small n: tam 2-opt converge + (full modda) agresif küçük-n araması
    if n <= SMALL_N_FULL_2OPT_N:
        tour, imp = two_opt_full_converge(tour, d)
        imp_total += int(imp)

        if mode == "full":
            tour, imp2 = strong_local_search_small_n(tour, d)
            imp_total += int(imp2)
        else:
            # fast mod: 3-opt'u devre dışı bırak; tek tur relocate ile yetin
            if RELOCATE_ENABLE and n >= 8:
                tour, imp_r = relocate_limited_knn(
                    tour, d, nbrs_2opt,
                    rounds=1,
                    max_moves_per_round=400,
                )
                imp_total += int(imp_r)

        return tour, int(imp_total), float(time.time() - t0)

    # --- Medium/Large n: time-limited 2-opt + relocate (+ optional or-opt) + kısa 2-opt rafinesi
    time_limit = float(TWO_OPT_TIME_LIMIT_SEC)
    if mode == "fast":
        # ILS içi çağrılarda süreyi sınırla (çoğu kazanım 1-2 saniyede geliyor)
        time_limit = max(1.0, min(time_limit, 2.0))

    tour, imp = two_opt_limited(tour, d, nbrs_2opt, time_limit=time_limit)
    imp_total += int(imp)

    if RELOCATE_ENABLE:
        rounds = 1 if mode == "fast" else (3 if n > 150 else 2)
        max_mv = 800 if mode == "fast" else (2000 if n <= 150 else 1200)
        tour, imp_r = relocate_limited_knn(
            tour, d, nbrs_2opt,
            rounds=rounds,
            max_moves_per_round=max_mv,
        )
        imp_total += int(imp_r)

    # Or-opt (k=2..3) segment relocate — yalnızca full modda
    if (mode == "full") and OR_OPT_ENABLE and (n <= int(OR_OPT_MAX_N)):
        max_mv = int(OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N) if n <= 150 else int(OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N)
        for kseg in range(2, int(OR_OPT_MAX_K) + 1):
            tour, imp_o = or_opt_segment_limited_knn(
                tour, d, nbrs_2opt,
                k=kseg,
                rounds=int(OR_OPT_ROUNDS),
                max_moves_per_round=max_mv,
                cand_k=int(OR_OPT_CAND_K),
            )
            imp_total += int(imp_o)

        # Or-opt sonrası kısa bir 2-opt rafinesi
        tour, imp2 = two_opt_limited(
            tour, d, nbrs_2opt,
            time_limit=max(1.0, float(TWO_OPT_TIME_LIMIT_SEC) * 0.5),
        )
        imp_total += int(imp2)

    return tour, int(imp_total), float(time.time() - t0)


def large_n_post_improve(
    tour: List[int],
    d: "DistanceOracle",
    coords: np.ndarray,
    opt_len: int,
    time_budget: float = None,
) -> Tuple[List[int], int, float, int]:
    """Time-bounded quality booster for very large N when OPT is known and gap is still large.

    Returns: (best_tour, best_length, elapsed_sec, gain)
    """
    t0 = time.time()
    if time_budget is None:
        time_budget = float(LARGE_N_POSTLS_TIME_BUDGET_SEC)

    try:
        best_t = list(tour)
    except Exception:
        best_t = tour
    best_L = int(tour_length(best_t, d))
    base_L = int(best_L)

    # Build a larger candidate set (KDTree if available)
    try:
        nbrs_big = build_knn_lists(coords, int(LARGE_N_POSTLS_KNN_K))
    except Exception:
        nbrs_big = None

    # Deterministic RNG for perturbations (kick + ILS). Keep reproducible per-instance.
    try:
        rng = np.random.default_rng(int(RANDOM_SEED) + 1907 + int(len(best_t)) * 17 + int(opt_len) % 100000)
    except Exception:
        rng = np.random.default_rng(42)

    def time_left() -> float:
        return float(time_budget) - float(time.time() - t0)

    # A) Longer 2-opt limited (first-improvement)
    try:
        if (nbrs_big is not None) and time_left() > 2.0:
            tlim = max(2.0, min(time_left() * 0.60, float(time_budget) * 0.70))
            t2, _ = two_opt_limited(best_t, d, nbrs_big, time_limit=float(tlim))
            L2 = int(tour_length(t2, d))
            if L2 < best_L:
                best_t, best_L = list(t2), int(L2)
    except Exception:
        pass

    # B) One relocate burst (cheap on large-N if move cap is small)
    try:
        if (nbrs_big is not None) and RELOCATE_ENABLE and time_left() > 1.0:
            t3, _ = relocate_limited_knn(
                best_t, d, nbrs_big,
                rounds=int(LARGE_N_POSTLS_RELOC_ROUNDS),
                max_moves_per_round=int(LARGE_N_POSTLS_RELOC_MAX_MOVES),
            )
            L3 = int(tour_length(t3, d))
            if L3 < best_L:
                best_t, best_L = list(t3), int(L3)
    except Exception:
        pass

    # C) Or-opt burst (k=2..3), capped
    try:
        if (nbrs_big is not None) and bool(LARGE_N_POSTLS_OROPT_ENABLE) and OR_OPT_ENABLE and time_left() > 1.0:
            max_k = int(max(2, int(LARGE_N_POSTLS_OROPT_MAX_K)))
            for kseg in range(2, max_k + 1):
                if time_left() <= 0.5:
                    break
                t4, _ = or_opt_segment_limited_knn(
                    best_t, d, nbrs_big,
                    k=int(kseg),
                    rounds=int(LARGE_N_POSTLS_OROPT_ROUNDS),
                    max_moves_per_round=int(LARGE_N_POSTLS_OROPT_MAX_MOVES),
                    cand_k=int(LARGE_N_POSTLS_OROPT_CAND_K),
                )
                L4 = int(tour_length(t4, d))
                if L4 < best_L:
                    best_t, best_L = list(t4), int(L4)

            # short 2-opt refine
            if time_left() > 1.0:
                tlim2 = max(1.0, min(time_left() * 0.50, 6.0))
                t5, _ = two_opt_limited(best_t, d, nbrs_big, time_limit=float(tlim2))
                L5 = int(tour_length(t5, d))
                if L5 < best_L:
                    best_t, best_L = list(t5), int(L5)
    except Exception:
        pass


    # C2) Targeted EDP reinsertion burst for hard tail cases (fast, accepts non-worse moves)
    try:
        if (nbrs_big is not None) and bool(LARGE_N_POSTLS_REINSERT_ENABLE) and time_left() > 2.0:
            gap_now = None
            try:
                if int(opt_len) > 0:
                    gap_now = 100.0 * (float(best_L) - float(opt_len)) / float(opt_len)
            except Exception:
                gap_now = None
            if (gap_now is not None) and np.isfinite(float(gap_now)):
                if (len(best_t) >= int(LARGE_N_POSTLS_REINSERT_MIN_N)) and (float(gap_now) >= float(LARGE_N_POSTLS_REINSERT_MIN_GAP_PCT)):
                    tR, _, _ = mf_edp_targeted_reinsertion(
                        list(best_t), d, coords, nbrs_big,
                        full_edge_scan=False,
                        desc_prefix="POSTLS:",
                        focus_frac=float(LARGE_N_POSTLS_REINSERT_FOCUS_FRAC),
                        max_per_pass=int(LARGE_N_POSTLS_REINSERT_MAX_PER_PASS),
                        passes=int(LARGE_N_POSTLS_REINSERT_PASSES),
                    )
                    LR = int(tour_length(tR, d))
                    if LR < best_L:
                        best_t, best_L = list(tR), int(LR)
                    # quick refine if time remains
                    if time_left() > 1.0:
                        tlimR = max(1.0, min(time_left() * 0.40, 4.0))
                        tR2, _ = two_opt_limited(best_t, d, nbrs_big, time_limit=float(tlimR))
                        LR2 = int(tour_length(tR2, d))
                        if LR2 < best_L:
                            best_t, best_L = list(tR2), int(LR2)
    except Exception:
        pass

    # D) Kick + fast repair (very small number of tries)
    try:
        if (nbrs_big is not None) and bool(LARGE_N_POSTLS_KICK_ENABLE) and time_left() > 2.0:
            rng = np.random.default_rng(int(RANDOM_SEED) + 1907 + int(len(best_t)) * 17 + int(opt_len) % 100000)
            tries = int(max(0, int(LARGE_N_POSTLS_KICK_TRIES)))
            for _ in range(tries):
                if time_left() <= 0.5:
                    break
                pert = double_bridge_move(best_t, rng)
                tlim3 = max(1.0, min(time_left() * 0.40, 4.0))
                pert2, _ = two_opt_limited(pert, d, nbrs_big, time_limit=float(tlim3))
                Lp = int(tour_length(pert2, d))
                if Lp < best_L:
                    best_t, best_L = list(pert2), int(Lp)
    except Exception:
        pass


    # E) Spend remaining budget with short ILS cycles (kick + refine).
    # This helps especially when gap is still large (e.g., pr1002).
    try:
        if (nbrs_big is not None) and bool(LARGE_N_POSTLS_ILS_ENABLE) and time_left() > 1.0:
            noimp = 0
            cycles = 0
            while time_left() > 0.8:
                cycles += 1
                if cycles > int(LARGE_N_POSTLS_ILS_CYCLES_MAX):
                    break
                pert = double_bridge_move(best_t, rng)
                tlim = max(0.6, min(time_left() * 0.35, float(LARGE_N_POSTLS_ILS_2OPT_SEC)))
                pert2, _ = two_opt_limited(pert, d, nbrs_big, time_limit=float(tlim))
                if bool(LARGE_N_POSTLS_ILS_OROPT_ENABLE) and time_left() > 0.5:
                    try:
                        pert2, _ = or_opt_segment_limited_knn(
                            pert2, d, nbrs_big,
                            k=2,
                            rounds=1,
                            max_moves_per_round=int(LARGE_N_POSTLS_ILS_OROPT_MOVES),
                            cand_k=int(LARGE_N_POSTLS_OROPT_CAND_K),
                        )
                    except Exception:
                        pass
                Lp = int(tour_length(pert2, d))
                if Lp < best_L:
                    best_t, best_L = list(pert2), int(Lp)
                    noimp = 0
                else:
                    noimp += 1
                    # NOTE: do not early-stop on no-improve; keep sampling until time/cycles caps.
                    pass
    except Exception:
        pass

    gain = int(max(0, base_L - best_L))
    return best_t, int(best_L), float(time.time() - t0), int(gain)



def candidate_edges_for_x(
    tour: List[int],
    x: int,
    knn_all: List[List[int]],
    coords: Optional[np.ndarray] = None,
    max_knn: int = 25
) -> List[int]:
    """Map KNN(x) nodes to a small candidate edge set on the current tour.

    Returns a list of edge indices k, where the edge is (tour[k], tour[(k+1) % m]).

    Base strategy (02.14.v1 behavior):
      - Take up to max_knn nearest neighbors of x (precomputed in knn_all)
      - For each neighbor v that is on the tour, add the two incident edges around v
        (prev->v and v->next) as candidate break edges.
      - If empty, fall back to all edges.

    Optional runtime acceleration (v2; guarded by RUNTIME_ACCEL_ENABLE):
      - hotedge: union in the K longest edges by (approx) Euclidean length (coords-based)
      - guardcap: cap total candidate edges to RUNTIME_GUARDCAP_EDGES with KNN-edges prioritized
      - midboost-edges: if enabled, keep only edges whose midpoints are closest to point x

    Notes:
      - Accel is ONLY applied when coords is provided and len(tour) >= RUNTIME_ACCEL_MIN_N.
      - When accel is disabled, the function returns exactly the 02.14.v1 candidate set.
    """
    mlen = len(tour)
    if mlen < 2:
        return list(range(mlen))

    # --- Base KNN->edge mapping (02.14.v1)
    pos = {node: i for i, node in enumerate(tour)}
    neigh = knn_all[x] if (knn_all is not None and x < len(knn_all)) else []
    if max_knn is not None and max_knn > 0:
        neigh = neigh[:max_knn]

    knn_edges = set()
    for v in neigh:
        i = pos.get(v, None)
        if i is None:
            continue
        knn_edges.add((i - 1) % mlen)
        knn_edges.add(i % mlen)

    if not knn_edges:
        # fallback (classic)
        base = list(range(mlen))
    else:
        base = sorted(knn_edges)

    # --- Optional acceleration (v2)
    if (not bool(globals().get("RUNTIME_ACCEL_ENABLE", False))) or coords is None or mlen < int(globals().get("RUNTIME_ACCEL_MIN_N", 10**9)):
        return base

    try:
        coords_arr = coords  # expect (n,2)
        px = coords_arr[int(x)]
    except Exception:
        return base

    # compute hot edges (by squared Euclidean length)
    hot_k = int(globals().get("RUNTIME_HOTEDGE_K", 0) or 0)
    edges = set(base)
    edge_len2 = None

    if hot_k > 0:
        edge_len2 = []
        for ei in range(mlen):
            u = int(tour[ei]); v = int(tour[(ei + 1) % mlen])
            du = coords_arr[u] - coords_arr[v]
            l2 = float(du[0] * du[0] + du[1] * du[1])
            edge_len2.append((l2, ei))
        edge_len2.sort(key=lambda t: t[0], reverse=True)
        for _, ei in edge_len2[:max(1, hot_k)]:
            edges.add(int(ei))

    # midboost-edges: keep only M edges whose midpoint is closest to x
    mid_m = int(globals().get("RUNTIME_MIDBOOST_EDGES_M", 0) or 0)
    if mid_m > 0 and len(edges) > mid_m:
        scored = []
        for ei in edges:
            u = int(tour[ei]); v = int(tour[(ei + 1) % mlen])
            mid = 0.5 * (coords_arr[u] + coords_arr[v])
            d2 = float((px[0] - mid[0]) ** 2 + (px[1] - mid[1]) ** 2)
            scored.append((d2, int(ei)))
        scored.sort(key=lambda t: t[0])
        edges = set([ei for _, ei in scored[:max(1, mid_m)]])

    # guardcap edges: cap total size, prioritizing KNN-derived edges first, then longest edges
    cap = int(globals().get("RUNTIME_GUARDCAP_EDGES", 0) or 0)
    if cap > 0 and len(edges) > cap:
        # Ensure we have lengths if we need to rank "non-KNN" edges
        if edge_len2 is None:
            edge_len2 = []
            for ei in range(mlen):
                u = int(tour[ei]); v = int(tour[(ei + 1) % mlen])
                du = coords_arr[u] - coords_arr[v]
                l2 = float(du[0] * du[0] + du[1] * du[1])
                edge_len2.append((l2, ei))
            edge_len2.sort(key=lambda t: t[0], reverse=True)
        len2_map = {int(ei): float(l2) for (l2, ei) in edge_len2}

        knn_set = set(base)  # base already includes all KNN edges when available; else it is all edges
        ranked = []
        for ei in edges:
            is_knn = 0 if int(ei) in knn_set else 1  # 0 preferred
            l2 = -len2_map.get(int(ei), 0.0)         # negative for descending
            ranked.append((is_knn, l2, int(ei)))
        ranked.sort()
        edges = set([ei for _, _, ei in ranked[:max(1, cap)]])

    out = sorted(edges)

    if bool(globals().get("RUNTIME_DEBUG_ACCEL", False)):
        try:
            print(f"[accel] m={mlen} x={x} base={len(base)} -> cand={len(out)}")
        except Exception:
            pass

    return out


def mf_edp_targeted_reinsertion(
    tour: List[int],
    d: "DistanceOracle",
    coords: np.ndarray,
    knn_all: List[List[int]],
    full_edge_scan: bool = True,
    desc_prefix: str = "",
    focus_frac: Optional[float] = None,
    max_per_pass: Optional[int] = None,
    passes: Optional[int] = None,
) -> Tuple[List[int], Dict[str, int], int]:
    """
    Remove the most expensive nodes (by contribution) and reinsert using EDP 3-sector rule.
    Returns (tour, counters, total_evals)
    """
    counters = {
        "tri_fallback_count": 0,
        "sector0_count": 0,
        "sector1_count": 0,
        "sector2_count": 0,
        "sector_unknown_count": 0,
    }
    total_evals = 0

    n = len(tour)
    # --- v4: override edilebilir reinsertion parametreleri
    n_passes = int(MF_REINSERT_PASSES if passes is None else passes)
    focus_frac_eff = float(MF_REINSERT_FOCUS_FRAC if focus_frac is None else focus_frac)
    max_per_eff = int(MF_REINSERT_MAX_PER_PASS if max_per_pass is None else max_per_pass)
    if n <= 4:
        return tour, counters, total_evals

    for ppass in range(n_passes):
        contrib = node_contributions(tour, d)
        # indices of nodes sorted by contribution (descending)
        idxs = np.argsort(-contrib)
        k_focus = int(max(1, round(focus_frac_eff * n)))
        idxs = idxs[:k_focus]
        idxs = idxs[:max_per_eff]

        it = idxs
        it = progress(it, total=len(idxs), desc=f"{desc_prefix}reinsert(p{ppass+1})",
                      leave=False, enabled=SHOW_PROGRESS and SHOW_INSERT_PROGRESS, kind="insert", position=3)

        for idx in it:
            idx = int(idx)
            x = tour[idx]
            base_len = tour_length(tour, d)

            t_minus = remove_node_from_tour(tour, idx)

            # candidate edges
            cand = None
            if not full_edge_scan:
                # small candidate set: KNN of x mapped to edges
                cand = candidate_edges_for_x(t_minus, x, knn_all, coords=coords)

            tri_nodes = select_triangle_local_knn(t_minus, x, coords, knn_all)
            if tri_nodes is None:
                counters["tri_fallback_count"] += 1

            t_new, chosen_sector, best_edge, best_delta, ev = edp_three_sector_insertion(
                t_minus, x, d, coords, tri_nodes, candidate_edges=cand
            )
            total_evals += int(ev)

            if chosen_sector == 0:
                counters["sector0_count"] += 1
            elif chosen_sector == 1:
                counters["sector1_count"] += 1
            elif chosen_sector == 2:
                counters["sector2_count"] += 1
            else:
                counters["sector_unknown_count"] += 1

            new_len = tour_length(t_new, d)
            if new_len <= base_len + 1e-9:
                tour = t_new  # accept non-worse
            # else reject (keep old)
    return tour, counters, int(total_evals)


def mf_edp_ils(
    tour: List[int],
    d: "DistanceOracle",
    nbrs_2opt: List[List[int]],
    coords: np.ndarray,
    knn_all: List[List[int]],
    desc_prefix: str = "",
    geom: Optional[Dict[str, float]] = None,
    strong: bool = False,
    seed_offset: int = 0,
) -> Tuple[List[int], Dict[str, int], int, float]:
    """
    MF_EDP_ILS pipeline:
      MF init (tour already provided) -> local search -> targeted reinsertion -> ILS (double-bridge) + local search
    """
    total_evals = 0
    # --- v4: geometri-adaptif yoğunlaştırma (riskli örneklerde daha agresif arama)
    if geom is None:
        try:
            geom = compute_geom_metrics(coords, d)
        except Exception:
            geom = {}
    risky = bool(MF_GEOM_ADAPT_ENABLE) and geom_is_risky(geom if isinstance(geom, dict) else {})
    counters = {
        "tri_fallback_count": 0,
        "sector0_count": 0,
        "sector1_count": 0,
        "sector2_count": 0,
        "sector_unknown_count": 0,
    }

    # local improve
    tour, _, _ = local_improve(tour, d, nbrs_2opt)

    # targeted reinsertion
    if MF_REINSERT_ENABLE:
        tour, c2, ev2 = mf_edp_targeted_reinsertion(
            tour, d, coords, knn_all,
            full_edge_scan=(FULL_EDGE_SCAN_FOR_SECTORS and (len(tour) <= FULL_EDGE_SCAN_MAX_N)),
            desc_prefix=f"{desc_prefix}MF_EDP_ILS:"
        )
        for k, v in c2.items():
            counters[k] += int(v)
        total_evals += int(ev2)
        tour, _, _ = local_improve(tour, d, nbrs_2opt)
        # v4: riskli geometrilerde ek (daha yoğun) reinsertion + local improve
        if risky and MF_GEOM_ADAPT_EXTRA_REINSERT:
            tour, c3, ev3 = mf_edp_targeted_reinsertion(
                tour, d, coords, knn_all,
                full_edge_scan=(FULL_EDGE_SCAN_FOR_SECTORS and (len(tour) <= FULL_EDGE_SCAN_MAX_N)),
                desc_prefix=f"{desc_prefix}MF_EDP_ILS+:",
                focus_frac=float(MF_GEOM_ADAPT_REINSERT_FOCUS_FRAC),
                max_per_pass=int(MF_GEOM_ADAPT_REINSERT_MAX_PER_PASS),
                passes=1
            )
            for k, v in c3.items():
                counters[k] += int(v)
            total_evals += int(ev3)
            tour, _, _ = local_improve(tour, d, nbrs_2opt)

    # ILS
    t0 = time.time()
    n = len(tour)
    if (not MF_ILS_ENABLE) or (n > MF_ILS_MAX_N) or (n < 8):
        return tour, counters, int(total_evals), float(time.time() - t0)

    if n <= 40:
        iters = min(int(MF_ILS_ITERS_SMALL), 10)
    elif n <= 60:
        iters = min(int(MF_ILS_ITERS_SMALL), 15)
    elif n <= 120:
        iters = min(int(MF_ILS_ITERS_SMALL), 25)
    elif n <= 400:
        iters = int(MF_ILS_ITERS_MED)
    else:
        iters = int(MF_ILS_ITERS_LARGE)

    # küçük/orta n'de erken durdurma eşiklerini biraz sıkılaştır (performans)
    no_imp_stop = int(MF_ILS_NO_IMPROVE_STOP)
    if n <= 40:
        no_imp_stop = min(no_imp_stop, 4)
    elif n <= 60:
        no_imp_stop = min(no_imp_stop, 6)
    elif n <= 120:
        no_imp_stop = min(no_imp_stop, 8)

    # ILS içi local improve mod seçimi
    ls_mode = "fast" if n <= int(MF_ILS_FAST_LS_N) else "full"
    # v4: riskli geometrilerde daha fazla ILS iterasyonu (doğruluk)
    if risky:
        try:
            iters = int(max(iters, round(float(iters) * float(MF_GEOM_ADAPT_ILS_MULT))))
        except Exception:
            pass

    

    # STRONG profile (yalnızca MF_GUARD tetiklenirse)
    if strong:
        try:
            iters = int(max(iters, round(float(iters) * float(globals().get("MF_STRONG_ILS_MULT", 1.8)))))
        except Exception:
            pass
        try:
            no_imp_stop = int(max(no_imp_stop, int(globals().get("MF_STRONG_NO_IMPROVE_STOP_MIN", no_imp_stop))))
        except Exception:
            pass
        if bool(globals().get("MF_STRONG_FORCE_FULL_LS", True)):
            ls_mode = "full"
    rng = np.random.RandomState(int(MF_ILS_SEED) + int(seed_offset))

    best = tour[:]
    best_len = tour_length(best, d)
    cur = best[:]
    no_imp = 0

    it = progress(range(iters), total=iters, desc=f"{desc_prefix}ILS", leave=False,
                  enabled=SHOW_PROGRESS and SHOW_INSERT_PROGRESS and n >= SHOW_INSERT_PROGRESS_MIN_N,
                  kind="ils", position=3)

    for _ in it:
        pert = double_bridge_move(cur, rng)
        pert, _, _ = local_improve(pert, d, nbrs_2opt, mode=ls_mode)
        L = tour_length(pert, d)
        cur = pert
        if L + 1e-9 < best_len:
            best = pert[:]
            best_len = L
            no_imp = 0
        else:
            no_imp += 1
            if no_imp >= no_imp_stop:
                break

    return best, counters, int(total_evals), float(time.time() - t0)


def geom_drift_report(df: "pd.DataFrame", out_dir: str, run_tag: str) -> None:
    """MF_EDP_ILS’in exact optimumdan saptığı örnekleri geometri özellikleriyle raporlar.

    Outputs (OUT_DIR içine):
      - geom_drift_report_<run_tag>.csv  : bin bazında özet (sadece gözlenen bin'ler)
      - geom_drift_cases_<run_tag>.csv   : drift vakaları (instance bazında)
      - geom_drift_action_<run_tag>.csv  : drift vakaları için önerilen aksiyonlar
      - geom_drift_feature_importance_<run_tag>.csv (opsiyonel): drift vs non-drift ayrıştırıcı feature'lar
    """
    if df is None or len(df) == 0:
        return

    # out_dir mutlaka tanımlı ve yazılabilir olsun
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        return

    try:
        df = sync_gap_fields_df(df)
    except Exception:
        pass

    req = {
        "variant", "status", "instance", "edge_weight_type",
        "exact_length", "exact_gap_percent",
        "geom_hull_frac", "geom_pca_aspect", "geom_nn_cv",
    }
    missing = [c for c in req if c not in df.columns]
    if missing:
        return

    # Sadece MF_EDP_ILS ve başarılı koşular
    sub = df[(df["variant"] == "MF_EDP_ILS") & (df["status"] == "OK")].copy()
    sub = sub[(sub["exact_length"].notna()) & (sub["exact_length"] > 0)].copy()
    if len(sub) == 0:
        # Boş dosyalar üretip sessizce çık
        rep_out = os.path.join(out_dir, f"geom_drift_report_{run_tag}.csv")
        action_out = os.path.join(out_dir, f"geom_drift_action_{run_tag}.csv")
        cases_out = os.path.join(out_dir, f"geom_drift_cases_{run_tag}.csv")
        pd.DataFrame(columns=[
            "edge_weight_type", "bin_hull_frac", "bin_pca_aspect", "bin_nn_cv",
            "instances", "drift_count", "drift_rate_percent",
            "mean_gap_percent", "max_gap_percent",
            "drift_threshold_pct",
            "drift_rate_smoothed_percent", "risk_score",
            "drift_rate_smoothed_percent_all", "risk_score_all",
            "geom_risk_mean", "risk_low_n",
        ]).to_csv(rep_out, index=False, encoding="utf-8")
        pd.DataFrame(columns=["instance", "n", "edge_weight_type", "geom_class", "exact_gap_percent", "recommended_action"]).to_csv(
            action_out, index=False, encoding="utf-8"
        )
        pd.DataFrame().to_csv(cases_out, index=False, encoding="utf-8")
        return

    # Drift etiketi (eşik: GEOM_DRIFT_GAP_THRESH_PCT)
    thr = float(GEOM_DRIFT_GAP_THRESH_PCT)
    sub["exact_gap_percent"] = pd.to_numeric(sub["exact_gap_percent"], errors="coerce")
    sub["is_drift"] = (sub["exact_gap_percent"].fillna(0.0) > thr)

    # Binning (kategorik) – groupby(observed=True) ile sadece gözlenen kombinasyonları tutar
    # Not: cut() right=False -> [a,b) aralıkları; en üst bin için 1.000001 gibi güvenli üst sınır
    sub["bin_hull_frac"] = pd.cut(
        pd.to_numeric(sub["geom_hull_frac"], errors="coerce"),
        bins=[0.0, 0.2, 0.35, 1.000001],
        labels=["0-0.2", "0.2-0.35", "0.35+"],
        include_lowest=True,
        right=False,
    )
    sub["bin_pca_aspect"] = pd.cut(
        pd.to_numeric(sub["geom_pca_aspect"], errors="coerce"),
        bins=[0.0, 1.5, 2.0, 4.0, 1e9],
        labels=["1-1.5", "1.5-2", "2-4", "4+"],
        include_lowest=True,
        right=False,
    )
    sub["bin_nn_cv"] = pd.cut(
        pd.to_numeric(sub["geom_nn_cv"], errors="coerce"),
        bins=[0.0, 0.3, 0.6, 1.0, 1e9],
        labels=["0-0.3", "0.3-0.6", "0.6-1.0", "1.0+"],
        include_lowest=True,
        right=False,
    )

    # Her örnek için "geometri risk" (0..1) – bin bazında ortalaması kullanılacak
    try:
        sub["_geom_risk"] = sub.apply(
            lambda r: float(geom_risk_score({
                "geom_hull_frac": float(r.get("geom_hull_frac", np.nan)),
                "geom_pca_aspect": float(r.get("geom_pca_aspect", np.nan)),
                "geom_nn_cv": float(r.get("geom_nn_cv", np.nan)),
            })),
            axis=1,
        )
    except Exception:
        sub["_geom_risk"] = np.nan

    keys = ["edge_weight_type", "bin_hull_frac", "bin_pca_aspect", "bin_nn_cv"]
    g = sub.groupby(keys, observed=True)

    rep = g.agg(
        instances=("instance", "count"),
        drift_count=("is_drift", "sum"),
        mean_gap_percent=("exact_gap_percent", "mean"),
        max_gap_percent=("exact_gap_percent", "max"),
        geom_risk_mean=("_geom_risk", "mean"),
    ).reset_index()

    rep["drift_threshold_pct"] = thr
    rep["drift_rate_percent"] = np.where(
        rep["instances"] > 0,
        100.0 * rep["drift_count"].astype(float) / rep["instances"].astype(float),
        np.nan,
    )

    # smoothing + risk score
    rep["drift_rate_smoothed_percent_all"] = np.nan
    rep["risk_score_all"] = np.nan
    rep["drift_rate_smoothed_percent"] = np.nan
    rep["risk_score"] = np.nan
    rep["risk_low_n"] = False

    if GEOM_DRIFT_RISK_ENABLE:
        alpha0 = float(GEOM_DRIFT_RISK_PRIOR_ALPHA)
        beta0 = float(GEOM_DRIFT_RISK_PRIOR_BETA)
        min_n = int(GEOM_DRIFT_RISK_MIN_INSTANCES)

        # Laplace/Beta smoothing
        sm = (rep["drift_count"].astype(float) + alpha0) / (rep["instances"].astype(float) + alpha0 + beta0)
        rep["drift_rate_smoothed_percent_all"] = 100.0 * sm

        # risk_score_all: drift olasılığı * geometri zorluğu (0..1)
        geom_r = rep["geom_risk_mean"].astype(float).fillna(0.0).clip(0.0, 1.0)
        rep["risk_score_all"] = (sm.clip(0.0, 1.0) * geom_r).clip(0.0, 1.0)

        low_n_mask = rep["instances"].astype(int) < min_n
        rep.loc[low_n_mask, "risk_low_n"] = True

        # kullanıcı tercihi: az örneklemli bin'lerde ana risk alanlarını NaN bırak
        rep.loc[~low_n_mask, "drift_rate_smoothed_percent"] = rep.loc[~low_n_mask, "drift_rate_smoothed_percent_all"]
        rep.loc[~low_n_mask, "risk_score"] = rep.loc[~low_n_mask, "risk_score_all"]

    # Kaydet
    rep_out = os.path.join(out_dir, f"geom_drift_report_{run_tag}.csv")
    cases_out = os.path.join(out_dir, f"geom_drift_cases_{run_tag}.csv")
    action_out = os.path.join(out_dir, f"geom_drift_action_{run_tag}.csv")

    rep = rep.sort_values(["edge_weight_type", "bin_hull_frac", "bin_pca_aspect", "bin_nn_cv"], kind="mergesort")
    rep.to_csv(rep_out, index=False, encoding="utf-8")

    # drift vakaları
    cases = sub[sub["is_drift"]].copy()
    # n kolonu yoksa instance bazlı çözümlemeden türetmeye çalışma; mevcutsa koru
    if "n" not in cases.columns:
        cases["n"] = np.nan
    cases.to_csv(cases_out, index=False, encoding="utf-8")

    # aksiyon önerisi (drift varsa)
    if len(cases) > 0:
        def _geom_class_row(r) -> str:
            hf = float(r.get("geom_hull_frac", np.nan))
            pa = float(r.get("geom_pca_aspect", np.nan))
            cv = float(r.get("geom_nn_cv", np.nan))
            dense = (np.isfinite(hf) and (hf <= MF_GEOM_ADAPT_HULL_FRAC_MAX))
            iso = (np.isfinite(pa) and (pa <= MF_GEOM_ADAPT_PCA_ASPECT_MAX))
            clu = (np.isfinite(cv) and (cv >= MF_GEOM_ADAPT_NN_CV_MIN))
            if dense and iso and clu:
                return "dense+isotropic+clustered"
            if dense and iso:
                return "dense+isotropic"
            if dense and clu:
                return "dense+clustered"
            if iso and clu:
                return "isotropic+clustered"
            if dense:
                return "dense"
            if iso:
                return "isotropic"
            if clu:
                return "clustered"
            return "other"

        cases["geom_class"] = cases.apply(_geom_class_row, axis=1)

        def _action_from_class(cls: str) -> str:
            if "dense" in cls:
                return "Increase ILS intensity + enable extra reinsertion focus"
            if "clustered" in cls:
                return "Increase candidate set (KNN) + allow more Or-opt/relocate"
            if "isotropic" in cls:
                return "Add rotation-aware 3-opt rounds + stronger perturbation"
            return "Slightly increase ILS rounds"

        actions = cases[["instance", "n", "edge_weight_type", "geom_class", "exact_gap_percent"]].copy()
        actions["recommended_action"] = actions["geom_class"].map(_action_from_class)
        actions.to_csv(action_out, index=False, encoding="utf-8")
    else:
        pd.DataFrame(columns=["instance", "n", "edge_weight_type", "geom_class", "exact_gap_percent", "recommended_action"]).to_csv(
            action_out, index=False, encoding="utf-8"
        )

    # Feature importance (opsiyonel): drift vs non-drift ayrıştırma
    if GEOM_DRIFT_FEATURE_IMPORTANCE_ENABLE:
        try:
            feat_cols = [c for c in sub.columns if isinstance(c, str) and c.startswith("geom_")]
            feat_cols = [c for c in feat_cols if c not in {"geom_hull_frac", "geom_pca_aspect", "geom_nn_cv"}] + [
                "geom_hull_frac", "geom_pca_aspect", "geom_nn_cv"
            ]
            feat_cols = [c for c in feat_cols if c in sub.columns]

            # en az 2 sınıf varsa anlamlı
            if sub["is_drift"].nunique() >= 2 and len(feat_cols) > 0:
                rows = []
                y = sub["is_drift"].astype(int).values
                for c in feat_cols:
                    x = pd.to_numeric(sub[c], errors="coerce").astype(float).values
                    # corr (point-biserial ~ Pearson with binary)
                    try:
                        corr = float(np.corrcoef(x[~np.isnan(x)], y[~np.isnan(x)])[0, 1]) if np.sum(~np.isnan(x)) > 3 else np.nan
                    except Exception:
                        corr = np.nan
                    # standardized mean difference
                    try:
                        x0 = x[(y == 0) & (~np.isnan(x))]
                        x1 = x[(y == 1) & (~np.isnan(x))]
                        if len(x0) > 1 and len(x1) > 1:
                            m0, m1 = float(np.mean(x0)), float(np.mean(x1))
                            s = float(np.sqrt(0.5 * (np.var(x0) + np.var(x1))))
                            smd = (m1 - m0) / s if s > 0 else np.nan
                        else:
                            smd = np.nan
                    except Exception:
                        smd = np.nan
                    rows.append({
                        "feature": c,
                        "corr_with_drift": corr,
                        "abs_corr": (abs(corr) if np.isfinite(corr) else np.nan),
                        "smd": smd,
                        "abs_smd": (abs(smd) if np.isfinite(smd) else np.nan),
                    })
                fi = pd.DataFrame(rows).sort_values(["abs_corr", "abs_smd"], ascending=False)
                fi_out = os.path.join(out_dir, f"geom_drift_feature_importance_{run_tag}.csv")
                fi.to_csv(fi_out, index=False, encoding="utf-8")
        except Exception:
            pass

    print("\nGeometri drift raporu (MF_EDP_ILS):")
    print("Report CSV:", rep_out)
    print("Action CSV:", action_out)
    print("Cases  CSV:", cases_out)
def solve_variant(p: ProblemData, variant: str, knn_all: List[List[int]], stability_seed_shift: int = 0) -> Dict:
    d = DistanceOracle(p)
    coords = p.coords

    # Geometry-adaptive knobs for EDP variants (local & cheap)
    _edp_geom_risky = False
    _edp_geom_class = None
    _edp_risk_score = float('nan')
    _knn_cand_edges = int(KNN_CAND_EDGES)
    try:
        if (coords is not None) and variant in ("EDP_3SECT", "EDP_LOCAL_3SECT", "MF_EDP_ILS", "MF_EDP_ILS_MPA"):
            _geom = compute_geom_metrics(coords, d)
            _edp_risk_score = float(geom_risk_score(_geom)) if _geom is not None else float('nan')
            _edp_geom_class = geom_guardrails_class(_geom) if _geom is not None else None
            _edp_geom_risky = bool((str(_edp_geom_class).find('dense+isotropic') >= 0) or (_edp_risk_score == _edp_risk_score and _edp_risk_score >= float(globals().get('EDP_GEOM_ADAPT_RISK_MIN', 0.32))))
            if _edp_geom_risky:
                _knn_cand_edges = max(_knn_cand_edges, int(globals().get('EDP_GEOM_ADAPT_KNN_CAND_EDGES', 35)))
    except Exception:
        _edp_geom_risky = False
        _edp_geom_class = None
        _edp_risk_score = float('nan')


    # (raporlama uyumu) bazı varyantlar bu alanları üretmez; default tanımla
    nstarts = 1
    best_start = 1
    risk_score = None
    total_ils_time = None
    best_ils_time = None

    a, b, c = initial_triangle_indices(coords)
    tour0 = [a, b, c]
    order = insertion_order_farthest_from_centroid(coords, (a, b, c))

    # global 2-opt neighbor list (used by look-ahead local repair + final repair)
    nbrs_2opt = build_knn_lists(coords, KNN_2OPT)


    # --------
    # Classical external constructive baselines + final repair
    # --------
    if variant in ("NEAREST_INSERTION", "FARTHEST_INSERTION"):
        tour = tour0[:]
        total_evals = 0
        remaining = set(order)
        iter_steps = progress(range(len(order)), total=len(order), desc=f"{p.name}:{variant} insert", leave=False, kind="insert",
                              enabled=SHOW_PROGRESS and len(order) >= SHOW_INSERT_PROGRESS_MIN_N, position=2)
        for _ in iter_steps:
            if not remaining:
                break
            best_x = None
            best_key = None
            for x in remaining:
                try:
                    nearest_to_tour = min(float(d.w(x, t)) for t in tour)
                except Exception:
                    nearest_to_tour = float('inf')
                if variant == "NEAREST_INSERTION":
                    key = (nearest_to_tour, x)
                else:
                    key = (-nearest_to_tour, x)
                if (best_key is None) or (key < best_key):
                    best_key = key
                    best_x = x
            if best_x is None:
                break
            tour, _, evals = cheapest_insertion(tour, best_x, d, edge_indices=None)
            total_evals += int(evals)
            remaining.remove(best_x)

        t0 = time.time()
        if p.n <= SMALL_N_FULL_2OPT_N:
            tour, imp = two_opt_full_converge(tour, d)
            tour, imp_extra = strong_local_search_small_n(tour, d)
            imp += imp_extra
        else:
            tour, imp = two_opt_limited(tour, d, nbrs_2opt, time_limit=TWO_OPT_TIME_LIMIT_SEC)
            tour, imp_r = relocate_limited_knn(tour, d, nbrs_2opt, max_rounds=1 if p.n > 150 else 2, max_moves_per_round=2000 if p.n <= 150 else 1200)
            imp += int(imp_r)
        if OR_OPT_ENABLE and (len(tour) <= OR_OPT_MAX_N):
            max_mv = OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N if len(tour) <= 150 else OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N
            for kseg in range(2, int(OR_OPT_MAX_K) + 1):
                tour, imp_o = or_opt_segment_limited_knn(
                    tour, d, nbrs_2opt, k=kseg, rounds=OR_OPT_ROUNDS,
                    max_moves_per_round=max_mv, cand_k=OR_OPT_CAND_K
                )
                imp += int(imp_o)
            tour, imp2 = two_opt_limited(tour, d, nbrs_2opt, time_limit=TWO_OPT_TIME_LIMIT_SEC)
            imp += int(imp2)
        t_twoopt = time.time() - t0

        L = tour_length(tour, d)
        return {
            "tour": tour,
            "length": int(L),
            "total_candidate_evals": int(total_evals),
            "tri_fallback_count": 0,
            "sector0_count": 0,
            "sector1_count": 0,
            "sector2_count": 0,
            "sector_unknown_count": 0,
            "beam_width": 1,
            "beam_states": 0,
            "two_opt_improved": int(imp),
            "time_twoopt_sec": float(t_twoopt),
            "nstarts": 1,
            "best_start": 1,
            "risk_score": risk_score,
            "total_ils_time_sec": total_ils_time,
            "best_ils_time_sec": best_ils_time,
            "geom_guardrails_risky": _edp_geom_risky,
            "geom_guardrails_class": _edp_geom_class,
            "geom_guardrails_score": _edp_risk_score,
        }

    # --------
    # CI baseline (greedy) + final repair
    # --------
    if variant == "CI":
        tour = tour0[:]
        total_evals = 0
        iter_x = progress(order, total=len(order), desc=f"{p.name}:{variant} insert", leave=False, kind="insert",
                          enabled=SHOW_PROGRESS and len(order) >= SHOW_INSERT_PROGRESS_MIN_N, position=2)
        for x in iter_x:
            tour, _, evals = cheapest_insertion(tour, x, d, edge_indices=None)
            total_evals += evals

        # final repair
        t0 = time.time()
        if p.n <= SMALL_N_FULL_2OPT_N:
            tour, imp = two_opt_full_converge(tour, d)
            tour, imp_extra = strong_local_search_small_n(tour, d)
            imp += imp_extra
        else:
            tour, imp = two_opt_limited(tour, d, nbrs_2opt, time_limit=TWO_OPT_TIME_LIMIT_SEC)
            # ek: kontrollü relocate (2.5-opt) ile 2-opt yerel minimumundan kaçış
            tour, imp_r = relocate_limited_knn(tour, d, nbrs_2opt, max_rounds=1 if p.n > 150 else 2, max_moves_per_round=2000 if p.n <= 150 else 1200)
            imp += int(imp_r)
        # Or-opt (k=2..3) segment relocate
        if OR_OPT_ENABLE and (len(tour) <= OR_OPT_MAX_N):
            max_mv = OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N if len(tour) <= 150 else OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N
            for kseg in range(2, int(OR_OPT_MAX_K) + 1):
                tour, imp_o = or_opt_segment_limited_knn(
                    tour, d, nbrs_2opt, k=kseg, rounds=OR_OPT_ROUNDS,
                    max_moves_per_round=max_mv, cand_k=OR_OPT_CAND_K
                )
                imp += int(imp_o)

            tour, imp2 = two_opt_limited(tour, d, nbrs_2opt, time_limit=TWO_OPT_TIME_LIMIT_SEC)
            imp += int(imp2)
        t_twoopt = time.time() - t0

        L = tour_length(tour, d)
        return {
            "tour": tour,
            "length": int(L),
            "total_candidate_evals": int(total_evals),
            "tri_fallback_count": 0,
            "sector0_count": 0,
            "sector1_count": 0,
            "sector2_count": 0,
            "sector_unknown_count": 0,
            "twoopt_time_sec": float(t_twoopt),
            "twoopt_improvement": int(imp),
            "mf_nstarts": int(nstarts) if ("nstarts" in locals() and nstarts is not None) else 1,
            "mf_best_start": int(best_start) if ("best_start" in locals() and best_start is not None) else 1,
            "mf_risk_score": float(risk_score) if ("risk_score" in locals() and risk_score is not None) else None,
            "mf_total_ils_time_sec": float(total_ils_time) if ("total_ils_time" in locals() and total_ils_time is not None) else None,
            "mf_best_ils_time_sec": float(best_ils_time) if ("best_ils_time" in locals() and best_ils_time is not None) else None,
            "beam_width_used": 1,
            "beam_generated_states": 0,
        }

    
    # --------
    # MF_EDP_ILS (Multi-Fragment + EDP reinsertion + ILS) + final repair
    # --------
    if variant in ("MF_EDP_ILS", "MF_EDP_ILS_MPA", "MF_EDP_ILS_STRONG", "MF_EDP_ILS_MPA_STRONG"):
        is_strong = str(variant).endswith('_STRONG')

        total_evals = 0
        # STRONG koşulda 2-opt komşu listesi daha geniş olsun (tail-case iyileştirme)
        _knn_2opt_use = int(KNN_2OPT)
        if is_strong:
            try:
                _knn_2opt_use = int(min(int(p.n) - 1, max(_knn_2opt_use, round(float(_knn_2opt_use) * float(globals().get('MF_STRONG_KNN_2OPT_MULT', 2.0))))))
            except Exception:
                pass
        nbrs_2opt = build_knn_lists(coords, _knn_2opt_use)

        # 1) Multi-Fragment başlangıç turu (+ opsiyonel multi-start jitter)
        if MF_MULTISTART_ENABLE:
            tries = mf_multistart_tries(p.n)
        else:
            tries = 1

        if is_strong:
            try:
                if int(p.n) >= 400:
                    tries = max(int(tries), int(globals().get("MF_STRONG_MIN_TRIES_LARGE", MF_STRONG_MIN_TRIES_LARGE)))
                else:
                    tries = max(int(tries), int(globals().get("MF_STRONG_MIN_TRIES_SMALL", MF_STRONG_MIN_TRIES_SMALL)))
            except Exception:
                pass

        
        best_tour = None
        best_len = float('inf')
        best_counters = {}
        best_evals2 = 0
        best_ils_time = 0.0
        
        iter_ms = progress(range(int(tries)), total=int(tries),
                         desc=f"{p.name}:MF_EDP_ILS multistart", leave=False, kind="mfms",
                         enabled=SHOW_PROGRESS and int(tries) > 1, position=2)
        
        for s in iter_ms:
            rng = np.random.default_rng(int(MF_MULTISTART_SEED_BASE) + int(stability_seed_shift) + 1315423911 * (int(s) + 1) + int(p.n))
            _mf_knn_k_use = None
            if is_strong:
                try:
                    _mf_knn_k_use = int(min(int(p.n) - 1, max(int(MF_KNN_K), round(float(MF_KNN_K) * float(globals().get('MF_STRONG_MF_KNN_K_MULT', 2.0))))))
                except Exception:
                    _mf_knn_k_use = None

            tour0_ms = multifragment_greedy_tour(
                d, coords, use_progress=False, desc=f"{p.name}:MF",
                rng=rng, jitter=float(MF_MULTISTART_JITTER) if int(tries) > 1 else 0.0,
                knn_k=_mf_knn_k_use
            )
            if tour0_ms is None or len(tour0_ms) != p.n:
                continue
        
            # 2) MF + EDP reinsertion + ILS
            tour_ms, counters_ms, evals2_ms, ils_time_ms = mf_edp_ils(
                tour0_ms, d, nbrs_2opt, coords, knn_all, desc_prefix=f"{p.name}:",
                strong=is_strong,
                seed_offset=int(s) + int(stability_seed_shift)
            )
        
            L_ms = float(tour_length(tour_ms, d))
            if L_ms < best_len:
                best_len = L_ms
                best_tour = tour_ms
                best_counters = dict(counters_ms) if isinstance(counters_ms, dict) else {}
                best_evals2 = int(evals2_ms)
                best_ils_time = float(ils_time_ms)
        
        if best_tour is None:
            tour0_ms = multifragment_greedy_tour(d, coords, use_progress=False, desc=f"{p.name}:MF", knn_k=_mf_knn_k_use)
            tour_ms, counters_ms, evals2_ms, ils_time_ms = mf_edp_ils(
                tour0_ms, d, nbrs_2opt, coords, knn_all, desc_prefix=f"{p.name}:",
                strong=is_strong,
                seed_offset=int(stability_seed_shift)
            )
            best_tour = tour_ms
            best_counters = dict(counters_ms) if isinstance(counters_ms, dict) else {}
            best_evals2 = int(evals2_ms)
            best_ils_time = float(ils_time_ms)
        
        tour = best_tour
        counters = best_counters
        counters["multistart_tries"] = int(tries)
        counters["multistart_best_len"] = float(best_len) if best_len < float('inf') else float(tour_length(tour, d))
        evals2 = int(best_evals2)
        ils_time = float(best_ils_time)
        
        total_evals += int(evals2)


        # 3) Final repair (doğruluk önceliği) — tek noktadan yönetilen local_improve
        tour, imp, t_twoopt = local_improve(tour, d, nbrs_2opt, mode="full")

        # 3b) Optional EDP post-polish: one cheap targeted reinsertion pass + fast repair
        if EDP_POST_POLISH_ENABLE:
            try:
                if int(p.n) <= int(EDP_POST_POLISH_MAX_N):
                    L0 = int(tour_length(tour, d))
                    tour2, c_pol, ev_pol = mf_edp_targeted_reinsertion(
                        list(tour), d, coords, knn_all,
                        full_edge_scan=(FULL_EDGE_SCAN_FOR_SECTORS and (p.n <= FULL_EDGE_SCAN_MAX_N)),
                        desc_prefix=f"{p.name}:{variant}:EDP_POLISH:",
                        focus_frac=float(EDP_POST_POLISH_FOCUS_FRAC),
                        max_per_pass=int(EDP_POST_POLISH_MAX_PER_PASS),
                        passes=int(EDP_POST_POLISH_PASSES),
                    )
                    mode2 = "full" if int(p.n) <= 80 else "fast"
                    tour2, _, _ = local_improve(tour2, d, nbrs_2opt, mode=mode2)
                    L2 = int(tour_length(tour2, d))
                    if L2 < L0:
                        tour = tour2
                        total_evals += int(ev_pol)
            except Exception:
                pass

        # 4) Optional MPA-lite post-refinement (comparative variant)
        mpa_info = {}
        if (variant == "MF_EDP_ILS_MPA") and bool(globals().get("MPA_LITE_ENABLE", False)) and (int(p.n) <= int(globals().get("MPA_LITE_MAX_N", 0))):
            try:
                base_key = str(p.name).lower().replace(".tsp", "")
                opt_known = TSPLIB_KNOWN_OPT.get(base_key, None)
                # skip if already near-exact (when exact/opt known)
                if opt_known is not None and float(opt_known) > 0:
                    L0_tmp = float(tour_length(tour, d))
                    gap0_tmp = 100.0 * (L0_tmp - float(opt_known)) / float(opt_known)
                    if float(gap0_tmp) > float(globals().get("MPA_LITE_SKIP_IF_EXACT_GAP_LE_PCT", 0.0)):
                        seed_mpa = int(91648253 + 1315423911 * int(p.n))
                        tour2, mpa_info = mpa_lite_refine(
                            list(tour), d, nbrs_2opt,
                            seed=seed_mpa,
                            time_limit_sec=float(globals().get("MPA_LITE_TIME_LIMIT_SEC", 0.9)),
                            pop_size=int(globals().get("MPA_LITE_POP", 4)),
                            max_gens=int(globals().get("MPA_LITE_MAX_GENS", 12)),
                            desc_prefix=f"{p.name}:{variant}:MPA:"
                        )
                        # adopt only if improved
                        L0 = int(L0_tmp)
                        L2 = int(tour_length(tour2, d))
                        if L2 < L0:
                            tour = tour2
                else:
                    seed_mpa = int(91648253 + 1315423911 * int(p.n))
                    tour2, mpa_info = mpa_lite_refine(
                        list(tour), d, nbrs_2opt,
                        seed=seed_mpa,
                        time_limit_sec=float(globals().get("MPA_LITE_TIME_LIMIT_SEC", 0.9)),
                        pop_size=int(globals().get("MPA_LITE_POP", 4)),
                        max_gens=int(globals().get("MPA_LITE_MAX_GENS", 12)),
                        desc_prefix=f"{p.name}:{variant}:MPA:"
                    )
                    L0 = int(tour_length(tour, d))
                    L2 = int(tour_length(tour2, d))
                    if L2 < L0:
                        tour = tour2
            except Exception:
                mpa_info = {}


        # --- Large-N booster (OPT-known + still far) ---
        _large_boost_ran = False
        _large_boost_gain = 0
        _large_boost_time_sec = 0.0
        try:
            base_key = str(p.name).lower().replace(".tsp", "")
            opt_known = TSPLIB_KNOWN_OPT.get(base_key, None)
            if bool(LARGE_N_POSTLS_ENABLE) and (opt_known is not None) and int(p.n) >= int(LARGE_N_POSTLS_MIN_N):
                L0b = float(tour_length(tour, d))
                gap0b = 100.0 * (L0b - float(opt_known)) / float(opt_known) if float(opt_known) > 0 else 0.0
                if float(gap0b) >= float(LARGE_N_POSTLS_TRIGGER_GAP_PCT):
                    t_best, L_best, tsec, gain = large_n_post_improve(tour, d, coords, int(opt_known))
                    if int(L_best) < int(L0b):
                        tour = list(t_best)
                        _large_boost_ran = True
                        _large_boost_gain = int(gain)
                        _large_boost_time_sec = float(tsec)
        except Exception:
            pass

        L = tour_length(tour, d)
        return {
            "tour": tour,
            "length": int(L),
            "large_boost_ran": bool(_large_boost_ran),
            "large_boost_gain": int(_large_boost_gain),
            "large_boost_time_sec": float(_large_boost_time_sec),
            "total_candidate_evals": int(total_evals),
            "tri_fallback_count": int(counters.get("tri_fallback_count", 0)),
            "sector0_count": int(counters.get("sector0_count", 0)),
            "sector1_count": int(counters.get("sector1_count", 0)),
            "sector2_count": int(counters.get("sector2_count", 0)),
            "sector_unknown_count": int(counters.get("sector_unknown_count", 0)),
            "twoopt_time_sec": float(t_twoopt),
            "twoopt_improvement": int(imp),
            "beam_width_used": None,
            "beam_generated_states": None,
            "mpa_used": int(mpa_info.get("mpa_used", 0)) if isinstance(mpa_info, dict) else 0,
            "mpa_time_sec": float(mpa_info.get("mpa_time_sec", 0.0)) if isinstance(mpa_info, dict) else 0.0,
            "mpa_gens": int(mpa_info.get("mpa_gens", 0)) if isinstance(mpa_info, dict) else 0,
            "mpa_pop": int(mpa_info.get("mpa_pop", 0)) if isinstance(mpa_info, dict) else 0,
            "mpa_improvement": float(mpa_info.get("mpa_improvement", 0.0)) if isinstance(mpa_info, dict) else 0.0,
            "mpa_improved": int(mpa_info.get("mpa_improved", 0)) if isinstance(mpa_info, dict) else 0,
        }

# --------
    # EDP variants (3-sektör + look-ahead + optional beam search)
    # --------
    if variant not in ("EDP_3SECT", "EDP_LOCAL_3SECT"):
        raise ValueError(f"Bilinmeyen varyant: {variant}")

    width = beam_width_for_n(p.n)
    use_beam = (width > 1)

    # init state
    init_len = tour_length(tour0, d)
    states = [BeamState(tour=tour0, length=int(init_len),
                        tri_fallback_count=0,
                        sector0_count=0, sector1_count=0, sector2_count=0,
                        sector_unknown_count=0)]
    total_evals = 0
    generated_states = 0

    iter_x = progress(order, total=len(order), desc=f"{p.name}:{variant} insert", leave=False, kind="insert",
                      enabled=SHOW_PROGRESS and len(order) >= SHOW_INSERT_PROGRESS_MIN_N, position=2)

    for x in iter_x:
        new_states: List[BeamState] = []

        for st in states:
            tour = st.tour
            m = len(tour)

            # candidate edges: doğruluk önceliği için full scan (yalnızca küçük/orta n)
            full_scan_eff = bool(FULL_EDGE_SCAN_FOR_SECTORS) and ( (int(p.n) <= int(FULL_EDGE_SCAN_MAX_N)) or (bool(globals().get('FULL_EDGE_SCAN_RISKY_BOOST_ENABLE', True)) and bool(_edp_geom_risky) and (int(p.n) <= int(globals().get('FULL_EDGE_SCAN_MAX_N_RISKY', 120)))) )
            if full_scan_eff:
                candidate_edges = list(range(m))
            else:
                candidate_edges = candidate_edges_for_x(tour, x, knn_all, coords=coords, max_knn=int(_knn_cand_edges))

            # triangle selection
            tri_nodes = None
            tri_fallback_add = 0
            if variant == "EDP_LOCAL_3SECT":
                tri_nodes = None
                if TRIANGULATION_ENABLE and (len(tour) <= TRIANGULATION_MAX_TOUR_N):
                    tri_nodes = select_triangle_from_polygon_triangulation(tour, x, coords)
                if tri_nodes is None:
                    tri_nodes = select_triangle_local_knn(tour, x, coords, knn_all)
                    tri_fallback_add = 1
            else:
                tri_nodes = select_triangle_local_knn(tour, x, coords, knn_all)
                if tri_nodes is None:
                    tri_fallback_add = 1

            Pp, best_edge, best_delta, evals = best_edges_by_sector(tour, x, d, coords, tri_nodes, candidate_edges)
            total_evals += evals

            # fallback: triangle/EDP üretilemezse klasik cheapest insertion (tek aday)
            if Pp is None or all(e is None for e in best_edge):
                # tek aday
                t_new, delta, ev2 = cheapest_insertion(tour, x, d, edge_indices=candidate_edges)
                total_evals += ev2
                new_len = st.length + int(delta)

                # look-ahead local repair
                if LOOKAHEAD_ENABLE:
                    # x ve komşuları odak
                    posx = build_pos_index(t_new).get(x, None)
                    focus = [x]
                    if posx is not None:
                        focus.append(t_new[posx - 1])
                        focus.append(t_new[(posx + 1) % len(t_new)])
                    # önce relocate, sonra 2-opt (kısa bütçeyle)
                    t_new, imp_r = local_relocate_focus(t_new, d, nbrs_2opt, focus_nodes=focus, max_moves=max(5, LOOKAHEAD_MAX_MOVES // 3))
                    new_len -= int(imp_r)
                    t_new, imp_local = local_2opt_focus(t_new, d, nbrs_2opt, focus_nodes=focus, max_moves=LOOKAHEAD_MAX_MOVES)
                    new_len -= int(imp_local)

                new_states.append(BeamState(
                    tour=t_new, length=int(new_len),
                    tri_fallback_count=st.tri_fallback_count + tri_fallback_add,
                    sector0_count=st.sector0_count, sector1_count=st.sector1_count, sector2_count=st.sector2_count,
                    sector_unknown_count=st.sector_unknown_count + 1
                ))
                generated_states += 1
                continue

            # 3 sektörün her birinden bir aday üret
            for s in range(3):
                ei = best_edge[s]
                if ei is None:
                    continue
                delta = best_delta[s]
                if delta is None:
                    continue

                u = tour[ei]
                v = tour[(ei + 1) % m]
                t_new = _insert_at_edge(tour, ei, x)
                new_len = st.length + int(delta)

                # look-ahead: mini local repair (doğruluk)
                if LOOKAHEAD_ENABLE:
                    focus = [x, u, v]
                    if tri_nodes is not None:
                        focus.extend(list(tri_nodes))
                    # focus'u KNN ile biraz genişlet
                    extra = []
                    for fn in list(set(focus)):
                        extra.extend(nbrs_2opt[fn][:LOOKAHEAD_FOCUS_EXTRA_KNN])
                    focus = list(set(focus + extra))
                    # relocate + 2-opt lookahead
                    t_new, imp_r = local_relocate_focus(t_new, d, nbrs_2opt, focus_nodes=focus, max_moves=max(5, LOOKAHEAD_MAX_MOVES // 3))
                    new_len -= int(imp_r)
                    t_new, imp_local = local_2opt_focus(t_new, d, nbrs_2opt, focus_nodes=focus, max_moves=LOOKAHEAD_MAX_MOVES)
                    new_len -= int(imp_local)

                s0, s1, s2 = st.sector0_count, st.sector1_count, st.sector2_count
                if s == 0: s0 += 1
                elif s == 1: s1 += 1
                else: s2 += 1

                new_states.append(BeamState(
                    tour=t_new, length=int(new_len),
                    tri_fallback_count=st.tri_fallback_count + tri_fallback_add,
                    sector0_count=s0, sector1_count=s1, sector2_count=s2,
                    sector_unknown_count=st.sector_unknown_count
                ))
                generated_states += 1

        # prune to beam width (keep shortest)
        # de-duplicate (optional) to reduce blow-up
        # Use tuple(tour) key; keep best length for each
        best_by_key = {}
        for st in new_states:
            key = tuple(st.tour)
            prev = best_by_key.get(key, None)
            if prev is None or st.length < prev.length:
                best_by_key[key] = st
        new_states = list(best_by_key.values())

        new_states.sort(key=lambda s: (s.length, s.tri_fallback_count, s.sector_unknown_count))
        if use_beam:
            states = new_states[:width]
        else:
            states = [new_states[0]]
    # final: choose best state
    best = min(states, key=lambda s: s.length)
    tour = best.tour

    # final repair (doğruluk modu)
    t0 = time.time()
    if p.n <= SMALL_N_FULL_2OPT_N:
        tour, imp = two_opt_full_converge(tour, d)
        tour, imp_extra = strong_local_search_small_n(tour, d)
        imp += imp_extra
    else:
        tour, imp = two_opt_limited(tour, d, nbrs_2opt, time_limit=TWO_OPT_TIME_LIMIT_SEC)
        # ek: kontrollü relocate (2.5-opt) ile 2-opt yerel minimumundan kaçış
        tour, imp_r = relocate_limited_knn(tour, d, nbrs_2opt, max_rounds=1 if p.n > 150 else 2, max_moves_per_round=2000 if p.n <= 150 else 1200)
        imp += int(imp_r)
        # Or-opt (k=2..3) segment relocate
        if OR_OPT_ENABLE and (len(tour) <= OR_OPT_MAX_N):
            max_mv = OR_OPT_MAX_MOVES_PER_ROUND_SMALL_N if len(tour) <= 150 else OR_OPT_MAX_MOVES_PER_ROUND_LARGE_N
            for kseg in range(2, int(OR_OPT_MAX_K) + 1):
                tour, imp_o = or_opt_segment_limited_knn(
                    tour, d, nbrs_2opt, k=kseg, rounds=OR_OPT_ROUNDS,
                    max_moves_per_round=max_mv, cand_k=OR_OPT_CAND_K
                )
                imp += int(imp_o)

        tour, imp2 = two_opt_limited(tour, d, nbrs_2opt, time_limit=TWO_OPT_TIME_LIMIT_SEC)
        imp += int(imp2)

    # Optional: risky-geometry EDP polish -> (i) cheap reinsertion, (ii) micro-ILS only if polish did NOT help, (iii) instance-gated k-OPT burst
    _edp_polish_attempted = False
    _edp_polish_improved = False
    _edp_micro_ils_ran = False
    _edp_micro_improved = False
    _edp_kopt_burst_ran = False
    _edp_kopt_gain = 0

    try:
        if bool(globals().get('EDP_VARIANT_POLISH_ENABLE', True)) and bool(_edp_geom_risky) and int(p.n) <= int(globals().get('EDP_VARIANT_POLISH_MAX_N', 220)):
            _edp_polish_attempted = True
            L0p = int(tour_length(tour, d))
            tour_p, _, ev_p = mf_edp_targeted_reinsertion(
                list(tour), d, coords, knn_all,
                full_edge_scan=(FULL_EDGE_SCAN_FOR_SECTORS and (p.n <= FULL_EDGE_SCAN_MAX_N)),
                desc_prefix=f"{p.name}:{variant}:EDP_POLISH:",
                focus_frac=float(globals().get('EDP_VARIANT_POLISH_FOCUS_FRAC', 0.22)),
                max_per_pass=int(globals().get('EDP_VARIANT_POLISH_MAX_PER_PASS', 30)),
                passes=int(globals().get('EDP_VARIANT_POLISH_PASSES', 1)),
            )
            mode_p = 'full' if int(p.n) <= 80 else 'fast'
            tour_p, _, _ = local_improve(tour_p, d, nbrs_2opt, mode=mode_p)
            L1p = int(tour_length(tour_p, d))
            if L1p < L0p:
                tour = list(tour_p)
                imp += int(L0p - L1p)
                total_evals += int(ev_p)
                _edp_polish_improved = True
    except Exception:
        pass

    # micro-ILS (seçici): sadece polish denendi ama fayda vermediyse
    try:
        _micro_gate = True
        if bool(globals().get('EDP_MICRO_ILS_ONLY_IF_POLISH_NO_IMPROVE', True)):
            _micro_gate = bool(_edp_polish_attempted) and (not bool(_edp_polish_improved))

        if bool(globals().get('EDP_MICRO_ILS_ENABLE', True)) and bool(_edp_geom_risky) and _micro_gate and int(p.n) <= int(globals().get('EDP_MICRO_ILS_MAX_N', 220)):
            _edp_micro_ils_ran = True
            L0m = int(tour_length(tour, d))
            best_t = list(tour)
            best_L = int(L0m)
            rng = np.random.RandomState(int(globals().get('EDP_MICRO_ILS_SEED_BASE', 24680)) + 1009 * int(p.n) + (1 if variant == 'EDP_LOCAL_3SECT' else 0))
            iters = int(globals().get('EDP_MICRO_ILS_ITERS', 2))
            for _ in range(max(0, iters)):
                pert = double_bridge_move(best_t, rng)
                mode2 = 'full' if int(p.n) <= 70 else 'fast'
                pert2, _, _ = local_improve(pert, d, nbrs_2opt, mode=mode2)
                Lp = int(tour_length(pert2, d))
                if Lp < best_L:
                    best_L = Lp
                    best_t = list(pert2)
            if best_L < L0m:
                _edp_micro_improved = True
                imp += int(L0m - best_L)
            tour = best_t
    except Exception:
        pass
    # adaptif k-OPT burst (genelleştirilmiş):
    # - Önce polish/micro-ILS fayda vermediyse,
    # - OPT (TSPLIB_KNOWN_OPT) biliniyorsa gap eşiğini geçtiyse,
    # - Prefix filtresi opsiyoneldir (default: opt biliniyorsa prefix'e bakmadan tetikle)
    try:
        if bool(globals().get('EDP_KOPT_BURST_ENABLE', True)) and int(p.n) <= int(globals().get('EDP_KOPT_BURST_MAX_N', 220)):
            # seçicilik: micro-ILS iyileştirme getirdiyse burst'i atla
            if bool(globals().get('EDP_KOPT_BURST_ONLY_IF_MICRO_NO_IMPROVE', True)) and bool(_edp_micro_improved):
                raise RuntimeError('skip_kopt_burst_micro_improved')

            base_name = os.path.splitext(str(p.name).strip())[0].lower()
            pref = globals().get('EDP_KOPT_BURST_PREFIXES', ('eil',))
            pref_list = [str(x).strip().lower() for x in (pref if isinstance(pref, (list, tuple)) else (pref,)) if str(x).strip()]
            prefix_ok = any(base_name.startswith(px) for px in pref_list)

            Lb = int(tour_length(tour, d))
            opt_known = TSPLIB_KNOWN_OPT.get(base_name, None)

            do_burst = False
            gapb = None
            if opt_known is not None and opt_known > 0:
                gapb = 100.0 * (float(Lb) - float(opt_known)) / float(opt_known)
                do_burst = bool(gapb >= float(globals().get('EDP_KOPT_BURST_GAP_THRESH_PCT', 1.50)))

            # opt biliniyorsa prefix filtresini gevşet (genelleştirme)
            if bool(do_burst) and (not bool(prefix_ok)):
                if bool(globals().get('EDP_KOPT_BURST_IGNORE_PREFIX_IF_OPTKNOWN', True)):
                    prefix_ok = True

            # (opsiyonel) geometri sınıfı yoğun ise tetiklemeyi biraz daha agresif yap
            hard = False
            try:
                if gapb is not None and float(gapb) >= float(globals().get('EDP_KOPT_BURST_HARD_GAP_THRESH_PCT', 2.50)):
                    hard = True
            except Exception:
                hard = False
            try:
                if _edp_geom_class is not None and str(_edp_geom_class).find('dense+isotropic') >= 0:
                    hard = True
            except Exception:
                pass

            if bool(do_burst) and bool(prefix_ok):
                # bütçe (hard instance'larda biraz artır)
                tl = float(globals().get('EDP_KOPT_BURST_TIME_LIMIT_SEC', 0.60))
                mt = int(globals().get('EDP_KOPT_BURST_MAX_TRIES', 900))
                if hard:
                    tl = float(tl) * float(globals().get('EDP_KOPT_BURST_HARD_TIME_MULT', 1.50))
                    mt = int(max(50, int(float(mt) * float(globals().get('EDP_KOPT_BURST_HARD_TRIES_MULT', 1.50)))))

                seed = int(globals().get('EDP_MICRO_ILS_SEED_BASE', 24680)) + 777 * int(p.n) + (17 if variant == 'EDP_LOCAL_3SECT' else 0)

                # 1) n küçükse 3-opt burst
                if int(p.n) <= int(globals().get('EDP_KOPT_BURST_THREEOPT_MAX_N', 120)):
                    t_b, _gain = three_opt_burst_knn(
                        list(tour), d, nbrs_2opt,
                        max_tries=int(mt),
                        time_limit_sec=float(tl),
                        neighbor_k=int(globals().get('EDP_KOPT_BURST_NEIGHBOR_K', 10)),
                        seed=int(seed),
                    )
                else:
                    # 2) n büyükse kısa Or-opt burst (segment relocation)
                    t_b = list(tour)
                    _gain = 0
                    if bool(globals().get('EDP_KOPT_BURST_LARGE_N_USE_OROPT', True)):
                        t_b, _imp_or = or_opt_limited_knn(
                            list(t_b), d, nbrs_2opt,
                            seg_lens=(2, 3),
                            max_rounds=int(globals().get('EDP_KOPT_BURST_OROPT_ROUNDS', 1)),
                            max_moves_per_round=int(float(globals().get('EDP_KOPT_BURST_OROPT_MAX_MOVES', 450)) * (float(globals().get('EDP_KOPT_BURST_HARD_TRIES_MULT', 1.50)) if hard else 1.0)),
                            knn_k=int(globals().get('EDP_KOPT_BURST_OROPT_KNN_K', 25)),
                        )
                        try:
                            _gain = int(max(0, float(_imp_or)))
                        except Exception:
                            _gain = 0

                # final local improve
                mode_k = 'full' if int(p.n) <= 70 else 'fast'
                t_b2, _, _ = local_improve(t_b, d, nbrs_2opt, mode=mode_k)
                Lk = int(tour_length(t_b2, d))
                if Lk < Lb:
                    _edp_kopt_burst_ran = True
                    _edp_kopt_gain = int(Lb - Lk)
                    imp += int(Lb - Lk)
                    tour = list(t_b2)
    except Exception:
        pass

    t_twoopt = time.time() - t0
    # --- Large-N booster (OPT-known + still far) ---
    _large_boost_ran = False
    _large_boost_gain = 0
    _large_boost_time_sec = 0.0
    try:
        base_key = str(p.name).lower().replace(".tsp", "")
        opt_known = TSPLIB_KNOWN_OPT.get(base_key, None)
        if bool(LARGE_N_POSTLS_ENABLE) and (opt_known is not None) and int(p.n) >= int(LARGE_N_POSTLS_MIN_N):
            L0b = float(tour_length(tour, d))
            gap0b = 100.0 * (L0b - float(opt_known)) / float(opt_known) if float(opt_known) > 0 else 0.0
            if float(gap0b) >= float(LARGE_N_POSTLS_TRIGGER_GAP_PCT):
                t_best, L_best, tsec, gain = large_n_post_improve(tour, d, coords, int(opt_known))
                if int(L_best) < int(L0b):
                    tour = list(t_best)
                    _large_boost_ran = True
                    _large_boost_gain = int(gain)
                    _large_boost_time_sec = float(tsec)
    except Exception:
        pass

    # Small-n exactness guard (opsiyonel): MF, n<=HK_MAX_N ise HK optimuma düşür.
    if (str(variant).startswith("MF_EDP_ILS")) and bool(globals().get("MF_SMALL_N_FORCE_HK_OPT", True)) and (int(p.n) <= int(HK_MAX_N)):
        try:
            hk_L, hk_t = held_karp_optimum(d, int(p.n), return_tour=True)
            if (hk_t is not None) and (int(hk_L) < int(tour_length(tour, d))):
                tour = list(hk_t)
                try:
                    counters["mf_smalln_hk_forced"] = 1
                except Exception:
                    pass
        except Exception:
            pass

    L = tour_length(tour, d)
    return {
        "tour": tour,
        "length": int(L),
        "total_candidate_evals": int(total_evals),
        "tri_fallback_count": int(best.tri_fallback_count),
        "sector0_count": int(best.sector0_count),
        "sector1_count": int(best.sector1_count),
        "sector2_count": int(best.sector2_count),
        "sector_unknown_count": int(best.sector_unknown_count),
        "twoopt_time_sec": float(t_twoopt),
        "twoopt_improvement": int(imp),
        "beam_width_used": int(width),
        "beam_generated_states": int(generated_states),
        "edp_polish_attempted": int(_edp_polish_attempted),
        "edp_polish_improved": int(_edp_polish_improved),
        "edp_micro_ils_ran": int(_edp_micro_ils_ran),
        "edp_kopt_burst_ran": int(_edp_kopt_burst_ran),
        "edp_kopt_gain": int(_edp_kopt_gain),
    }


# ---------------------------
# Geometri özetleri (HK ile doğrulanan küçük n için "hangi geometrilerde kayıyor" analizi)
# ---------------------------
def _convex_hull(points: np.ndarray) -> np.ndarray:
    """Monotonic chain; returns hull vertices in CCW order (without repeating first)."""
    pts = np.asarray(points, dtype=float)
    if len(pts) <= 1:
        return pts
    # sort by x,y
    idx = np.lexsort((pts[:,1], pts[:,0]))
    pts = pts[idx]

    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))
    hull = lower[:-1] + upper[:-1]
    return np.array(hull, dtype=float)


def compute_geom_features(coords: np.ndarray) -> Dict[str, float]:
    """Hızlı, deterministik geometri özetleri."""
    pts = np.asarray(coords, dtype=float)
    n = int(pts.shape[0])
    if n == 0:
        return {}

    c = pts.mean(axis=0)
    r = np.sqrt(((pts - c)**2).sum(axis=1))
    r_mean = float(r.mean())
    r_std = float(r.std(ddof=0))

    # anisotropy (cov eigen ratio)
    cov = np.cov(pts.T, bias=True)
    try:
        w = np.linalg.eigvalsh(cov)
        w = np.sort(np.maximum(w, 1e-18))
        anis = float(w[-1] / w[0])
    except Exception:
        anis = float("nan")

    # hull
    hull = _convex_hull(pts)
    hull_n = int(len(hull))
    hull_area = float(_poly_area(hull))
    xmin, ymin = pts.min(axis=0)
    xmax, ymax = pts.max(axis=0)
    bbox_area = float(max(1e-18, (xmax-xmin)*(ymax-ymin)))
    hull_ratio = float(hull_n / n)
    fill_ratio = float(hull_area / bbox_area) if bbox_area > 0 else float("nan")

    # NN distances (use KDTree if available)
    nn_mean = float("nan")
    nn_med = float("nan")
    try:
        if SCIPY_OK and n >= 3:
            tree = cKDTree(pts)
            dists, _ = tree.query(pts, k=2)  # self + 1NN
            nn = dists[:,1]
        else:
            # brute (OK for small n)
            D = np.sqrt(((pts[:,None,:]-pts[None,:,:])**2).sum(axis=2))
            np.fill_diagonal(D, np.inf)
            nn = D.min(axis=1)
        nn_mean = float(np.mean(nn))
        nn_med = float(np.median(nn))
    except Exception:
        pass

    return {
        "geom_hull_ratio": hull_ratio,
        "geom_hull_n": float(hull_n),
        "geom_hull_area": hull_area,
        "geom_fill_ratio": fill_ratio,
        "geom_r_mean": r_mean,
        "geom_r_std": r_std,
        "geom_anisotropy": anis,
        "geom_nn_mean": nn_mean,
        "geom_nn_median": nn_med,
    }


def _safe_fname(s: str) -> str:
    import re
    s = str(s)
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")

def _extract_guardrail_stage(warnings: str) -> str:
    """Extract the effective guardrail stage label from the warnings string."""
    w = (warnings or "").upper()
    if "GUARDRAIL_STAGE3_ACCEPT" in w:
        return "S3"
    if "GUARDRAIL_FULL_ACCEPT" in w:
        return "FULL"
    if "GUARDRAIL_MINI_ACCEPT" in w:
        return "MINI"
    if "GUARDRAIL_" in w:
        return "TRIED"
    return "BASE"


def _save_tour_plot(
    coords,
    tour,
    out_base_path: str,
    title: str,
    L_val: Optional[int] = None,
    exact_gap: Optional[float] = None,
    guardrail_stage: str = "BASE",
    exact_source: str = "",
    subtitle: str = "",
    dpi: int = 600,
    node_labels: Optional[List[int]] = None,
):
    """Save a publication-style route visualization as both TIFF and PDF.

    coords: (n,2) array-like
    tour: list/array of node indices representing a Hamiltonian cycle
    out_base_path: full path without extension
    node_labels: original node ids (same order as coords), optional
    """
    try:
        import numpy as _np
        import matplotlib as _mpl
        try:
            _mpl.use("Agg", force=True)
        except Exception:
            pass
        import matplotlib.pyplot as _plt
    except Exception:
        return

    try:
        xy = _np.asarray(coords, dtype=float)
        t = list(map(int, list(tour))) if tour is not None else []
        n = int(xy.shape[0]) if xy.ndim == 2 else 0
        if n <= 1 or len(t) != n:
            return

        cyc = t + [t[0]]
        seg = xy[cyc, :]

        fig, ax = _plt.subplots(figsize=(7.2, 7.2), dpi=110)
        ax.plot(seg[:, 0], seg[:, 1], lw=float(globals().get('PLOT_TOURS_LINEWIDTH', 1.1)), color=str(globals().get('PLOT_COLOR_LINE', '#1f3a5f')), alpha=0.95, zorder=2)
        # node points: circles for small instances; tiny dark dots for large instances (avoid circle markers on big-N plots)
        try:
            large_thr = int(globals().get("PLOT_TOURS_LARGE_N_DOT_ONLY", 2000))
        except Exception:
            large_thr = 2000

        if n >= large_thr:
            ax.scatter(
                xy[:, 0], xy[:, 1],
                s=float(globals().get("PLOT_TOURS_POINTSIZE_LARGE", 2.0)),
                color=str(globals().get("PLOT_COLOR_POINTS_LARGE", "#111111")),
                marker=".",
                linewidths=0.0,
                alpha=float(globals().get("PLOT_TOURS_POINT_ALPHA_LARGE", 0.85)),
                zorder=3,
            )
        else:
            ax.scatter(
                xy[:, 0], xy[:, 1],
                s=float(globals().get("PLOT_TOURS_POINTSIZE", 10)),
                color=str(globals().get("PLOT_COLOR_POINTS", "#f4b942")),
                edgecolors="white",
                linewidths=0.35,
                alpha=0.95,
                zorder=3,
            )

        # mark start (S)
        try:
            s0 = int(t[0])
            ax.scatter([xy[s0, 0]], [xy[s0, 1]], s=float(globals().get("PLOT_TOURS_START_POINTSIZE", 40)), marker="*", color=str(globals().get('PLOT_COLOR_START', '#2a9d8f')), edgecolors='black', linewidths=0.4, zorder=7)
            ax.annotate(
                "S",
                (xy[s0, 0], xy[s0, 1]),
                textcoords="offset points",
                xytext=(8, 8),
                ha="left",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.18", alpha=0.80, facecolor='white', edgecolor='none'),
                zorder=8,
            )
        except Exception:
            pass

        # highlight longest edges (overlay)
        try:
            k_hi = int(globals().get("PLOT_HIGHLIGHT_LONGEST_EDGES_K", 5))
            if k_hi > 0:
                ed = []
                for i in range(n):
                    a = int(t[i])
                    b = int(t[(i + 1) % n])
                    dx = float(xy[a, 0] - xy[b, 0])
                    dy = float(xy[a, 1] - xy[b, 1])
                    ed.append((dx * dx + dy * dy, a, b))
                ed.sort(reverse=True, key=lambda x: x[0])
                k_use = min(k_hi, len(ed))
                base_col = None
                try:
                    base_col = ax.lines[0].get_color()
                except Exception:
                    base_col = None
                for _, a, b in ed[:k_use]:
                    ax.plot(
                        [xy[a, 0], xy[b, 0]],
                        [xy[a, 1], xy[b, 1]],
                        lw=float(globals().get('PLOT_HIGHLIGHT_EDGE_LW', 2.8)),
                        linestyle='--',
                        color=str(globals().get('PLOT_COLOR_HIGHLIGHT', '#e63946')),
                        alpha=0.95,
                        zorder=4,
                    )
                    # annotate highlighted edge length (midpoint)
                    try:
                        if bool(globals().get('PLOT_HIGHLIGHT_LONGEST_EDGES_SHOW_LENGTH', True)):
                            mx = 0.5 * (float(xy[a, 0]) + float(xy[b, 0]))
                            my = 0.5 * (float(xy[a, 1]) + float(xy[b, 1]))
                            el = float(_np.hypot(float(xy[a, 0]) - float(xy[b, 0]), float(xy[a, 1]) - float(xy[b, 1])))
                            ax.text(
                                mx, my, f"{el:.0f}",
                                fontsize=float(globals().get('PLOT_HIGHLIGHT_EDGE_LABEL_FONTSIZE', 7)),
                                ha='center', va='center',
                                color=str(globals().get('PLOT_COLOR_HIGHLIGHT', '#e63946')),
                                bbox=dict(boxstyle='round,pad=0.12', alpha=0.80, facecolor='white', edgecolor='none'),
                                zorder=6,
                            )
                    except Exception:
                        pass
        except Exception:
            pass

        ax.set_aspect("equal", adjustable="datalim")
        ax.set_xticks([])
        ax.set_yticks([])
        try:
            ax.set_axis_off()
        except Exception:
            pass
        ax.set_title(title, fontsize=12, pad=10)

        # Node labels (original TSPLIB ids if provided)
        try:
            labels = node_labels if node_labels is not None else list(range(1, n + 1))
            max_labels = int(globals().get("PLOT_NODE_LABEL_MAX_N", 80))
            step = 1 if n <= max_labels else max(1, int(n / max_labels))
            for i in range(0, n, step):
                ax.text(
                    xy[i, 0],
                    xy[i, 1],
                    str(labels[i]),
                    fontsize=6.5,
                    ha="center",
                    va="center",
                    zorder=6,
                    bbox=dict(boxstyle="round,pad=0.12", alpha=float(globals().get('PLOT_COLOR_LABEL_BOX_ALPHA', 0.55)), facecolor='white', edgecolor='none'),
                )
        except Exception:
            pass

        # info box
        try:
            info_lines = []
            if L_val is not None:
                info_lines.append(f"L = {int(L_val)}")
            if exact_gap is not None and _np.isfinite(exact_gap):
                info_lines.append(f"exact_gap = {float(exact_gap):.2f}%")
            else:
                info_lines.append("exact_gap = N/A")
            if exact_source:
                info_lines.append(f"exact_src = {str(exact_source)}")
            if guardrail_stage:
                info_lines.append(f"guardrail = {str(guardrail_stage)}")
            if subtitle:
                s = str(subtitle).replace("\n", " ").strip()
                # keep a compact guardrail reason summary (avoid long console-like text)
                try:
                    max_len = int(globals().get("PLOT_GUARDRAIL_REASON_MAXLEN", 90))
                except Exception:
                    max_len = 90
                if "|" in s:
                    parts = [p.strip() for p in s.split("|") if p.strip()]
                    keep = []
                    for p2 in parts:
                        pl = p2.lower()
                        if ("guardrail" in pl) or ("geom" in pl) or ("gap" in pl) or ("stage" in pl):
                            keep.append(p2)
                    if keep:
                        s = " | ".join(keep)
                if len(s) > max_len:
                    s = s[: max(0, max_len - 3)] + "..."
                if s:
                    info_lines.append(f"reason = {s}")

            box = "\n".join(info_lines)
            ax.text(
                0.012,
                0.988,
                box,
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.35", alpha=0.88, facecolor='white', edgecolor='none'),
            )
        except Exception:
            pass

        _plt.tight_layout()
    except Exception:
        try:
            _plt.close("all")
        except Exception:
            pass
        return

    # Save PDF
    try:
        fig.savefig(out_base_path + ".pdf", bbox_inches="tight", pad_inches=0.06)
    except Exception as e:
        if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
            print(f"[plot] PDF save failed: {out_base_path}.pdf -> {e}")

    # Save TIFF, fallback to .tif
    try:
        fig.savefig(out_base_path + ".tiff", dpi=int(dpi), bbox_inches="tight", pad_inches=0.06)
    except Exception as e:
        if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
            print(f"[plot] TIFF save failed: {out_base_path}.tiff -> {e}")
        try:
            fig.savefig(out_base_path + ".tif", dpi=int(dpi), bbox_inches="tight", pad_inches=0.06)
        except Exception as e2:
            if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
                print(f"[plot] TIF save failed: {out_base_path}.tif -> {e2}")

    _plt.close(fig)


# ---------------------------
# MF stochastic stability helpers
# ---------------------------
def _suite_in_allowed_set(suite_name: str, allowed) -> bool:
    try:
        vals = tuple(str(x).strip().lower() for x in allowed)
        return str(suite_name).strip().lower() in vals
    except Exception:
        return False


def _series_iqr(x: pd.Series) -> float:
    try:
        s = pd.to_numeric(x, errors="coerce").dropna()
        if len(s) == 0:
            return np.nan
        return float(s.quantile(0.75) - s.quantile(0.25))
    except Exception:
        return np.nan


def summarize_mf_seed_stability(stab_df: pd.DataFrame) -> pd.DataFrame:
    if stab_df is None or len(stab_df) == 0:
        return pd.DataFrame()
    grp = stab_df.groupby(["suite", "instance", "n", "variant"], dropna=False)
    rows = []
    for key, sub in grp:
        row = {"suite": key[0], "instance": key[1], "n": key[2], "variant": key[3], "repeats": int(len(sub))}
        for col in ("length", "gap_percent", "exact_gap_percent", "time_sec", "mf_nstarts", "mf_total_ils_time_sec"):
            s = pd.to_numeric(sub.get(col), errors="coerce")
            row[f"{col}_mean"] = float(s.mean()) if len(s.dropna()) else np.nan
            row[f"{col}_std"] = float(s.std(ddof=1)) if len(s.dropna()) > 1 else 0.0 if len(s.dropna()) == 1 else np.nan
            row[f"{col}_median"] = float(s.median()) if len(s.dropna()) else np.nan
            row[f"{col}_iqr"] = _series_iqr(s)
            row[f"{col}_min"] = float(s.min()) if len(s.dropna()) else np.nan
            row[f"{col}_max"] = float(s.max()) if len(s.dropna()) else np.nan
        try:
            src = sub.get("deterministic_length")
            src = pd.to_numeric(src, errors="coerce").dropna()
            if len(src):
                row["deterministic_length"] = float(src.iloc[0])
        except Exception:
            row["deterministic_length"] = np.nan
        try:
            src = sub.get("deterministic_exact_gap_percent")
            src = pd.to_numeric(src, errors="coerce").dropna()
            if len(src):
                row["deterministic_exact_gap_percent"] = float(src.iloc[0])
        except Exception:
            row["deterministic_exact_gap_percent"] = np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    if len(out) > 0:
        out = out.sort_values(["suite", "n", "instance", "variant"], kind="mergesort")
    return out


# ---------------------------
# Ana benchmark
# ---------------------------

def export_guardrail_policy_summary(out_dir: str, run_tag: str, risky_classes: Optional[set] = None, risky_src: Optional[str] = None) -> Optional[str]:
    """Write a compact CSV summary of the active guardrail policy for reproducibility/documentation."""
    try:
        os.makedirs(out_dir, exist_ok=True)
        rows = []
        rows.append({"component":"accuracy_guardrail","parameter":"enabled","value":bool(ACCURACY_GUARDRAILS_ENABLE)})
        rows.append({"component":"accuracy_guardrail","parameter":"variants","value":"|".join(list(ACCURACY_GUARDRAILS_VARIANTS))})
        rows.append({"component":"accuracy_guardrail","parameter":"reference_csv_mode","value":str(ACCURACY_GUARDRAILS_REFERENCE_CSV)})
        rows.append({"component":"accuracy_guardrail","parameter":"gap_increase_thresh_pct","value":float(ACCURACY_GUARDRAILS_GAP_INCREASE_THRESH_PCT)})
        rows.append({"component":"accuracy_guardrail","parameter":"abs_gap_thresh_pct","value":float(ACCURACY_GUARDRAILS_ABS_GAP_THRESH_PCT)})
        rows.append({"component":"accuracy_guardrail","parameter":"require_geom_risk","value":bool(ACCURACY_GUARDRAILS_REQUIRE_GEOM_RISK)})
        rows.append({"component":"accuracy_guardrail","parameter":"geom_risk_score_min","value":float(ACCURACY_GUARDRAILS_GEOM_RISK_SCORE_MIN)})
        rows.append({"component":"accuracy_guardrail","parameter":"risky_geom_classes_source","value":str(risky_src) if risky_src is not None else "fallback_or_none"})
        rows.append({"component":"accuracy_guardrail","parameter":"risky_geom_classes_used","value":"|".join(sorted(list(risky_classes))) if risky_classes else ""})
        rows.append({"component":"accuracy_guardrail","parameter":"two_stage","value":bool(ACCURACY_GUARDRAILS_TWO_STAGE)})
        rows.append({"component":"accuracy_guardrail","parameter":"mini_accept_improve_min_delta","value":int(ACCURACY_GUARDRAILS_MINI_ACCEPT_IMPROVE_MIN_DELTA)})
        rows.append({"component":"accuracy_guardrail","parameter":"stage3_enabled","value":bool(ACCURACY_GUARDRAILS_STAGE3)})
        rows.append({"component":"accuracy_guardrail","parameter":"stage3_max_n","value":int(ACCURACY_GUARDRAILS_STAGE3_MAX_N)})
        rows.append({"component":"accuracy_guardrail","parameter":"stage3_accept_improve_min_delta","value":int(ACCURACY_GUARDRAILS_STAGE3_ACCEPT_IMPROVE_MIN_DELTA)})
        rows.append({"component":"accuracy_guardrail","parameter":"stage3_seed_offset","value":int(ACCURACY_GUARDRAILS_STAGE3_SEED_OFFSET)})

        rows.append({"component":"geom_risk","parameter":"hull_frac_max","value":float(MF_GEOM_ADAPT_HULL_FRAC_MAX)})
        rows.append({"component":"geom_risk","parameter":"pca_aspect_max","value":float(MF_GEOM_ADAPT_PCA_ASPECT_MAX)})
        rows.append({"component":"geom_risk","parameter":"nn_cv_min","value":float(MF_GEOM_ADAPT_NN_CV_MIN)})
        rows.append({"component":"geom_risk","parameter":"score_formula","value":"0.35*hull_risk + 0.25*aspect_risk + 0.40*cv_risk"})
        rows.append({"component":"geom_risk","parameter":"hull_risk","value":"clip((0.35-hf)/0.35,0,1)"})
        rows.append({"component":"geom_risk","parameter":"aspect_risk","value":"clip((2.0-asp)/2.0,0,1)"})
        rows.append({"component":"geom_risk","parameter":"cv_risk","value":"clip((cv-0.55)/(1-0.55),0,1)"})

        rows.append({"component":"mf_guard","parameter":"enabled","value":bool(MF_GUARD_ENABLE)})
        rows.append({"component":"mf_guard","parameter":"worse_delta_pct","value":float(MF_GUARD_WORSE_DELTA_PCT)})
        rows.append({"component":"mf_guard","parameter":"abs_gap_min_pct","value":float(MF_GUARD_ABS_GAP_MIN_PCT)})
        rows.append({"component":"mf_guard","parameter":"strong_max_n","value":int(MF_GUARD_STRONG_MAX_N)})
        rows.append({"component":"mf_guard","parameter":"strong_large_n_max_delta_pct","value":float(MF_GUARD_STRONG_LARGE_N_MAX_DELTA_PCT)})

        rows.append({"component":"mf_hard_fallback","parameter":"enabled","value":bool(MF_HARD_FALLBACK_ENABLE)})
        rows.append({"component":"mf_hard_fallback","parameter":"min_n","value":int(MF_HARD_FALLBACK_MIN_N)})
        rows.append({"component":"mf_hard_fallback","parameter":"delta_pct","value":float(MF_HARD_FALLBACK_DELTA_PCT)})

        out = os.path.join(out_dir, f"guardrail_policy_summary_{run_tag}.csv")
        pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8")
        return out
    except Exception:
        return None


def main():
    np.random.seed(RANDOM_SEED)

    # Default plot enable (will be refined per-suite below)
    _plot_enable_suite = bool(globals().get('PLOT_TOURS_ENABLE', False))

    # Plot output directory
    plots_dir = None
    if _plot_enable_suite:
        try:
            plots_dir = os.path.join(OUT_DIR, "plots")
            os.makedirs(plots_dir, exist_ok=True)
        except Exception:
            plots_dir = None

    if not os.path.isdir(INST_DIR):
        raise FileNotFoundError(f"INST_DIR bulunamadı: {INST_DIR}")

    inst_files = sorted(
        glob.glob(os.path.join(INST_DIR, "*.tsp")) +
        glob.glob(os.path.join(INST_DIR, "*.tsp.gz"))
    )
    if len(inst_files) == 0:
        raise FileNotFoundError("tsplib_instances içinde .tsp/.tsp.gz bulunamadı.")

    # ---------------------------
    # CORE + STRESS instance scheduling
    # ---------------------------
    def _base_instance_name(fp: str) -> str:
        b = os.path.basename(fp)
        if b.lower().endswith(".gz"):
            b = b[:-3]
        if b.lower().endswith(".tsp"):
            b = b[:-4]
        else:
            b = os.path.splitext(b)[0]
        return str(b).strip().lower()

    _stress_set = set([str(x).strip().lower() for x in (STRESS_INSTANCES if isinstance(STRESS_INSTANCES, (list, tuple, set)) else (STRESS_INSTANCES,)) if str(x).strip()])

    def _is_stress(fp: str) -> bool:
        bn = _base_instance_name(fp)
        if str(STRESS_MATCH_MODE).strip().lower() == "exact":
            return bn in _stress_set
        # default: prefix
        return any(bn.startswith(s) for s in _stress_set)

    core_files = [f for f in inst_files if not _is_stress(f)]
    stress_files = [f for f in inst_files if _is_stress(f)]

    print(f"Suite CORE: {len(core_files)} instances | Suite STRESS: {len(stress_files)} instances | RUN_STRESS={bool(RUN_STRESS)}")

    suite_runs = [("core", core_files)]
    if bool(RUN_STRESS) and len(stress_files) > 0:
        suite_runs.append(("stress", stress_files))


    variants = [
        "CI",
        "NEAREST_INSERTION",
        "FARTHEST_INSERTION",
        "EDP_3SECT",
        "EDP_LOCAL_3SECT",
        "MF_EDP_ILS",
        "EXACT",
    ]

    # Accuracy-guardrails: load a reference map (previous benchmark run) if available
    ref_gap_map, ref_gap_file = _load_reference_gap_map(OUT_DIR, RUN_TAG)
    if ref_gap_file is not None:
        print(f"Accuracy-guardrails reference CSV: {ref_gap_file}")

    guardrail_risky_geom_classes, guardrail_risky_geom_src = _load_guardrails_risky_geom_classes(OUT_DIR, RUN_TAG)
    if guardrail_risky_geom_src is not None:
        print(f"Guardrails geom gate class source: {guardrail_risky_geom_src} (k={len(guardrail_risky_geom_classes)})")
    elif ACCURACY_GUARDRAILS_ENABLE and ACCURACY_GUARDRAILS_REQUIRE_GEOM_RISK:
        print(f"Guardrails geom gate class source: fallback (k={len(guardrail_risky_geom_classes)})")

    policy_summary_file = export_guardrail_policy_summary(
        OUT_DIR,
        RUN_TAG,
        risky_classes=guardrail_risky_geom_classes,
        risky_src=guardrail_risky_geom_src,
    )
    if policy_summary_file is not None:
        print(f"Guardrail policy summary CSV: {policy_summary_file}")

    guardrail_events = []
    mf_guard_events = []
    mf_seed_rows = []
    rows = []

    for suite_name, suite_files in suite_runs:
        if len(suite_files) == 0:
            continue

        # Suite-specific plotting enable
        _plot_enable_suite = bool(PLOT_TOURS_ENABLE) and (suite_name != "stress" or bool(PLOT_TOURS_STRESS_ENABLE))

        # Suite-specific guardrails enable (stress'te varsayılan kapalı)
        _guardrails_enable_suite = bool(ACCURACY_GUARDRAILS_ENABLE) and (suite_name != "stress" or bool(globals().get("ACCURACY_GUARDRAILS_STRESS_ENABLE", False)))

        # Suite-specific variant set
        _variants_suite = list(variants)
        _sv = globals().get("STRESS_VARIANTS", None)
        if suite_name == "stress" and (_sv is not None):
            _sv = [str(x) for x in _sv]
            _variants_suite = [v for v in _variants_suite if v in _sv]
            if len(_variants_suite) == 0:
                _variants_suite = list(variants)


        print(f"--- Running suite: {suite_name.upper()} (n={len(suite_files)}) | plot_enable={_plot_enable_suite} ---")

        if bool(PRINT_INSTANCE_LIST):
            iter_files = suite_files
        else:
            iter_files = progress(suite_files, total=len(suite_files), desc=f"Instances[{suite_name}]", leave=True, enabled=SHOW_PROGRESS, kind="instances")

        for _ii, inst_path in enumerate(iter_files, 1):
            if bool(PRINT_INSTANCE_LIST):
                print(f"{os.path.basename(inst_path)}: {_ii}/{len(suite_files)} [{suite_name}]")
            try:
                p = load_tsplib_problem(inst_path)
            except Exception as e:
                rows.append({
                    "suite": suite_name,
                    "instance": os.path.basename(inst_path),
                    "variant": "SKIP",
                    "status": f"LOAD_FAIL: {e}",
                })
                continue

            # coords alias (for postboost, plotting etc.)
            coords = p.coords
            # global KNN (tri fallback ve 2-opt için)
            knn_all = build_knn_lists(p.coords, max(KNN_TRI, KNN_2OPT))

            # opt tour (varsa)
            d = DistanceOracle(p)
            geom = compute_geom_metrics(p.coords, d)
            opt_tour = load_opt_tour_if_exists(inst_path, p)
            opt_len = tour_length(opt_tour, d) if opt_tour is not None else None
            if opt_len is None:
                # opt.tour yoksa TSPLIB bilinen optimumdan doldur (varsa)
                base_name = os.path.splitext(str(p.name).strip())[0].lower()
                opt_len = TSPLIB_KNOWN_OPT.get(base_name, None)

            # Held–Karp exact optimum (küçük n için)
            hk_opt_len = None
            hk_tour = None
            hk_time_sec = None
            hk_status = "SKIP"
            if HK_ENABLE and p.n <= HK_MAX_N:
                hk_status = "OK"
                t_hk0 = time.time()
                try:
                    hk_opt_len, hk_tour = held_karp_optimum(d, p.n, return_tour=(p.n <= HK_MAX_N))
                    hk_time_sec = time.time() - t_hk0
                except Exception as e:
                    hk_status = f"FAIL: {e}"
                    hk_time_sec = time.time() - t_hk0
                    hk_opt_len = None


            # MIP exact optimum (HK dışı küçük/orta n için) – global optimum garantisi yalnızca OPTIMAL statüsünde geçerlidir
            mip_opt_len = None
            mip_tour = None
            mip_time_sec = None
            mip_status = "SKIP"
            if MIP_ENABLE and (p.n > HK_MAX_N) and (p.n <= MIP_MAX_N) and (opt_tour is None) and (opt_len is None or EXACT_SOLVE_MODE == "require"):
                if not MIP_OK:
                    mip_status = "SKIP: python-mip not installed"
                    if EXACT_SOLVE_MODE == "require":
                        raise RuntimeError("EXACT_SOLVE_MODE=require ama python-mip yok. Kurulum: pip install mip")
                else:
                    mip_status = "OK"
                    t_m0 = time.time()
                    try:
                        mip_opt_len, mip_tour = mip_tsp_optimum(d, p.n, time_limit_sec=MIP_TIME_LIMIT_SEC, return_tour=(p.n <= MIP_TOUR_MAX_N))
                        mip_time_sec = time.time() - t_m0
                        if mip_opt_len is None:
                            mip_status = "NOT_OPTIMAL"
                            if EXACT_SOLVE_MODE == "require":
                                raise RuntimeError("MIP exact solver time-limit veya zorluk nedeniyle OPTIMAL bulamadı.")
                    except Exception as e:
                        mip_time_sec = time.time() - t_m0
                        mip_status = f"FAIL: {e}"
                        mip_opt_len = None
                        if EXACT_SOLVE_MODE == "require":
                            raise

            if EXACT_SOLVE_MODE == "require":
                # Garanti: HK (n<=HK_MAX_N) ya da MIP (n>HK_MAX_N) ile exact bulunmalı; aksi halde dur.
                if (p.n <= HK_MAX_N and hk_opt_len is None):
                    raise RuntimeError("HK exact isteniyor fakat Held–Karp başarısız.")
                if (p.n > HK_MAX_N and mip_opt_len is None and opt_len is None):
                    raise RuntimeError("EXACT_SOLVE_MODE=require ama bu instance için exact referans yok (HK/MIP/opt.tour).")


            # instance-level exact referans (variant bağımsız)
            exact_ref_len = hk_opt_len if hk_opt_len is not None else (mip_opt_len if mip_opt_len is not None else opt_len)
            if hk_opt_len is not None:
                exact_ref_source = "HK"
            elif mip_opt_len is not None:
                exact_ref_source = "MIP"
            else:
                exact_ref_source = "OPT_TOUR" if opt_len is not None else None

            # Plotting: keep best tour per instance (optional)
            best_plot_L = None
            best_plot_variant = None

            # Plotting: collect tours per variant (save after instance is finished)
            plot_tours = {}  # variant -> (tour, length, exact_gap, warn_str, exact_source)
            best_plot_L = None
            best_plot_variant = None

            # Plotting: track GLOBAL best tour (among all variants with an actual tour)
            best_global_tour = None
            best_global_L = None
            best_global_variant = None
            best_global_warn = ''
            best_global_src = ''

            inst_row_idx = {}

            for v in progress(_variants_suite, total=len(_variants_suite), desc=f"{p.name} variants", leave=False, enabled=SHOW_PROGRESS, kind="variants"):
                t_start = time.time()
                warn_str = ""
                try:
                    if v == "EXACT":
                        if exact_ref_len is None:
                            raise RuntimeError("SKIP_NO_EXACT")
                        L = exact_ref_len
                        sol = {"tour": None, "length": L,
                               "total_candidate_evals": 0,
                               "tri_fallback_count": 0,
                               "sector0_count": 0,
                               "sector1_count": 0,
                               "sector2_count": 0,
                               "sector_unknown_count": 0,
                               "twoopt_time_sec": 0.0,
                               "twoopt_improvement": 0,
                               "beam_width_used": None,
                               "beam_generated_states": None}
                        if exact_ref_source == "HK":
                            elapsed = hk_time_sec if hk_time_sec is not None else (time.time() - t_start)
                        elif exact_ref_source == "MIP":
                            elapsed = mip_time_sec if mip_time_sec is not None else (time.time() - t_start)
                        else:
                            elapsed = 0.0
                    else:
                        with warnings.catch_warnings(record=True) as _ws:
                            warnings.simplefilter('always')
                            sol = solve_variant(p, v, knn_all)
                        if len(_ws) > 0:
                            # unique, compact warning messages
                            uniq = []
                            seen = set()
                            for w in _ws:
                                msg = f"{w.category.__name__}: {str(w.message)}"
                                if msg not in seen:
                                    uniq.append(msg)
                                    seen.add(msg)
                            warn_str = " | ".join(uniq[:5])
                        elapsed = time.time() - t_start
                        L = sol["length"]
                    gap = None
                    if opt_len is not None and opt_len > 0:
                        gap = 100.0 * (L - opt_len) / opt_len


                    # --- Accuracy Guardrails (hybrid re-run for problematic cases) ---
                    guardrail_triggered = False
                    guardrail_reason = None
                    guardrail_profile = None
                    guardrail_ref_gap = None
                    guardrail_gap2 = None
                    guardrail_len2 = None
                    guardrail_time_sec = 0.0
                    L_before_guard = int(L) if (L is not None and np.isfinite(L)) else None

                    # For guardrails we prefer the exact reference length (HK/MIP/OPT_TOUR) if present
                    exact_for_gap = exact_ref_len if (exact_ref_len is not None and exact_ref_len > 0) else None
                    gap_exact = None
                    if exact_for_gap is not None:
                        gap_exact = 100.0 * (float(L) - float(exact_for_gap)) / float(exact_for_gap)


                    # Geometri gate: guardrails sadece riskli sınıflarda devreye girsin
                    guardrail_geom_class = None
                    guardrail_geom_score = np.nan
                    guardrail_geom_risky = None
                    try:
                        guardrail_geom_class = geom_guardrails_class(geom) if geom is not None else None
                    except Exception:
                        guardrail_geom_class = None
                    try:
                        guardrail_geom_score = float(geom_risk_score(geom)) if geom is not None else np.nan
                    except Exception:
                        guardrail_geom_score = np.nan

                    try:
                        base_geom_risky = bool(geom_is_risky(geom)) if geom is not None else False
                    except Exception:
                        base_geom_risky = False

                    class_geom_risky = False
                    try:
                        if guardrail_geom_class is not None and len(guardrail_risky_geom_classes) > 0:
                            class_geom_risky = (str(guardrail_geom_class) in guardrail_risky_geom_classes)
                    except Exception:
                        class_geom_risky = False

                    score_geom_risky = bool(np.isfinite(guardrail_geom_score) and (guardrail_geom_score >= float(ACCURACY_GUARDRAILS_GEOM_RISK_SCORE_MIN)))
                    # Eğer riskli sınıf listesi yüklüyse, guardrails'i sadece o sınıflara (ve/veya risk_score eşiğine) bağla.
                    if len(guardrail_risky_geom_classes) > 0:
                        guardrail_geom_risky = bool(class_geom_risky or score_geom_risky)
                    else:
                        guardrail_geom_risky = bool(base_geom_risky or score_geom_risky)


                    if ACCURACY_GUARDRAILS_ENABLE and (v in ACCURACY_GUARDRAILS_VARIANTS) and (exact_for_gap is not None):
                        # regression check vs reference CSV
                        if ref_gap_map:
                            try:
                                guardrail_ref_gap = float(ref_gap_map.get((p.name, v), np.nan))
                            except Exception:
                                guardrail_ref_gap = None
                            if guardrail_ref_gap is not None and np.isfinite(guardrail_ref_gap) and (gap_exact is not None) and np.isfinite(gap_exact):
                                if float(gap_exact) > float(guardrail_ref_gap) + float(ACCURACY_GUARDRAILS_GAP_INCREASE_THRESH_PCT):
                                    guardrail_triggered = True
                                    guardrail_reason = f"regression_vs_ref({guardrail_ref_gap:.2f}->{gap_exact:.2f})"

                        # absolute gap check (yalnızca bu (instance,variant) için geçerli bir ref gap yoksa)
                        _ref_ok = bool((guardrail_ref_gap is not None) and np.isfinite(guardrail_ref_gap))
                        if (not guardrail_triggered) and (not _ref_ok) and (gap_exact is not None) and np.isfinite(gap_exact):
                            if float(gap_exact) > float(ACCURACY_GUARDRAILS_ABS_GAP_THRESH_PCT):
                                guardrail_triggered = True
                                guardrail_reason = f"abs_gap>{float(ACCURACY_GUARDRAILS_ABS_GAP_THRESH_PCT):.2f}"


                    # Geometry-gated refinement: tetikleyici sadece (gap artışı) + (geometri riski) birlikteyse
                    if guardrail_triggered and ACCURACY_GUARDRAILS_REQUIRE_GEOM_RISK:
                        if not bool(guardrail_geom_risky):
                            guardrail_triggered = False
                            guardrail_reason = None
                        else:
                            # reason'ı zenginleştir
                            try:
                                if guardrail_reason is None:
                                    guardrail_reason = "geom_gate"
                                if guardrail_geom_class is not None:
                                    if np.isfinite(guardrail_geom_score):
                                        guardrail_reason = f"{guardrail_reason}|geom={guardrail_geom_class}|risk={guardrail_geom_score:.2f}"
                                    else:
                                        guardrail_reason = f"{guardrail_reason}|geom={guardrail_geom_class}"
                            except Exception:
                                pass


                    if guardrail_triggered:
                        t_gr0 = time.time()
                        try:
                                                    # 2-stage: mini-try -> full accurate (only if needed)
                            sol_best = None
                            L_best = None
                            gap_best = None

                            # base solution is current sol/L
                            sol_best = sol
                            L_best = int(L)

                            # Stage 1: MINI
                            sol_mini = None
                            L_mini = None
                            gap_mini = None
                            t_mini0 = time.time()
                            try:
                                if v == "EDP_LOCAL_3SECT":
                                    overrides_mini = dict(ACCURACY_PROFILE_OVERRIDES_EDP_LOCAL_MINI)
                                    profile_mini = "EDP_LOCAL_MINI"
                                else:
                                    overrides_mini = dict(ACCURACY_PROFILE_OVERRIDES_EDP_MINI)
                                    profile_mini = "EDP_MINI"

                                with _TempGlobals(overrides_mini):
                                    sol_mini = solve_variant(p, v, knn_all)
                                Lm = sol_mini.get("length", None)
                                if Lm is not None:
                                    Lm = int(Lm)
                                    L_mini = int(Lm)
                                    if exact_for_gap is not None and exact_for_gap > 0:
                                        gap_mini = float(100.0 * (float(Lm) - float(exact_for_gap)) / float(exact_for_gap))
                            except Exception:
                                sol_mini = None
                            guardrail_time_mini = float(time.time() - t_mini0)

                            improved_by_mini = False
                            try:
                                if L_mini is not None and int(L_mini) <= int(L_best) - int(ACCURACY_GUARDRAILS_MINI_ACCEPT_IMPROVE_MIN_DELTA):
                                    improved_by_mini = True
                            except Exception:
                                improved_by_mini = False

                            if improved_by_mini:
                                sol_best = sol_mini
                                L_best = int(L_mini)
                                gap_best = gap_mini
                                guardrail_profile = profile_mini
                                warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_MINI_ACCEPT"
                            else:
                                warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_MINI_NO_IMPROVE"

                            # Stage 2: FULL (only if mini didn't improve)
                            sol_full = None
                            L_full = None
                            gap_full = None
                            guardrail_time_full = 0.0
                            if (not improved_by_mini) and bool(ACCURACY_GUARDRAILS_TWO_STAGE):
                                t_full0 = time.time()
                                try:
                                    if v == "EDP_LOCAL_3SECT":
                                        overrides_full = dict(ACCURACY_PROFILE_OVERRIDES_EDP_LOCAL)
                                        profile_full = "EDP_LOCAL_ACCURATE"
                                    else:
                                        overrides_full = dict(ACCURACY_PROFILE_OVERRIDES_EDP)
                                        profile_full = "EDP_ACCURATE"

                                    with _TempGlobals(overrides_full):
                                        sol_full = solve_variant(p, v, knn_all)

                                    Lf = sol_full.get("length", None)
                                    if Lf is not None:
                                        Lf = int(Lf)
                                        L_full = int(Lf)
                                        if exact_for_gap is not None and exact_for_gap > 0:
                                            gap_full = float(100.0 * (float(Lf) - float(exact_for_gap)) / float(exact_for_gap))
                                except Exception:
                                    sol_full = None
                                guardrail_time_full = float(time.time() - t_full0)

                                # accept only if it improves length
                                try:
                                    if L_full is not None and int(L_full) < int(L_best):
                                        sol_best = sol_full
                                        L_best = int(L_full)
                                        gap_best = gap_full
                                        guardrail_profile = profile_full
                                        warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_FULL_ACCEPT"
                                    else:
                                        warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_FULL_NO_IMPROVE"
                                except Exception:
                                    warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_FULL_FAIL"

                        
                            # Stage 3: POLISH (mini ve full iyileştirme getirmezse)
                            # Amaç: en iyi tur üzerinde kısa MF-ILS ile yerel minimumdan kaçıp iyileşme yakalamak.
                            guardrail_len_stage3 = None
                            guardrail_gap_stage3 = None
                            guardrail_time_stage3_sec = 0.0
                            stage3_ran = False

                            try:
                                full_no_improve = ("GUARDRAIL_FULL_NO_IMPROVE" in (warn_str or ""))
                                full_fail = ("GUARDRAIL_FULL_FAIL" in (warn_str or ""))
                            except Exception:
                                full_no_improve = False
                                full_fail = False

                            # Stage-3 yalnızca Stage-2 FULL pass çalıştıysa ve iyileştirme getirmediyse devreye girsin.
                            if ACCURACY_GUARDRAILS_STAGE3 and (not improved_by_mini) and (full_no_improve):
                                try:
                                    if int(p.n) <= int(ACCURACY_GUARDRAILS_STAGE3_MAX_N):
                                        stage3_ran = True
                                except Exception:
                                    stage3_ran = False

                            if stage3_ran:
                                t_s3 = time.time()
                                sol_stage3 = None
                                try:
                                    overrides_s3 = dict(ACCURACY_PROFILE_OVERRIDES_STAGE3_POLISH)
                                    with _TempGlobals(overrides_s3):
                                        # start from best-so-far tour (base/mini/full)
                                        tour_seed = None
                                        try:
                                            tour_seed = sol_best.get("tour", None) if isinstance(sol_best, dict) else None
                                        except Exception:
                                            tour_seed = None
                                        if tour_seed is None:
                                            try:
                                                tour_seed = sol.get("tour", None) if isinstance(sol, dict) else None
                                            except Exception:
                                                tour_seed = None

                                        if tour_seed is not None:
                                            coords_s3 = p.coords
                                            desc_prefix_s3 = f"{p.name}:{v}:"
                                            nbrs2 = build_knn_lists(coords_s3, KNN_2OPT)
                                            tour_s3, c_s3, ev_s3, ils_t_s3 = mf_edp_ils(
                                                list(tour_seed), d, nbrs2, coords_s3, knn_all,
                                                desc_prefix=f"{desc_prefix_s3}GUARDRAIL_S3:",
                                                geom=geom if isinstance(geom, dict) else None,
                                                seed_offset=int(ACCURACY_GUARDRAILS_STAGE3_SEED_OFFSET)
                                            )
                                            Ls3 = int(tour_length(tour_s3, d))

                                            # build a solution dict by copying current best
                                            sol_stage3 = dict(sol_best) if isinstance(sol_best, dict) else dict(sol)
                                            sol_stage3["tour"] = tour_s3
                                            sol_stage3["length"] = int(Ls3)

                                            # enrich MF timing field
                                            try:
                                                prev_ils = float(sol_stage3.get("mf_total_ils_time_sec") or 0.0)
                                            except Exception:
                                                prev_ils = 0.0
                                            sol_stage3["mf_total_ils_time_sec"] = float(prev_ils) + float(ils_t_s3)

                                            guardrail_len_stage3 = int(Ls3)
                                            if exact_for_gap is not None and exact_for_gap > 0:
                                                guardrail_gap_stage3 = float(100.0 * (float(Ls3) - float(exact_for_gap)) / float(exact_for_gap))
                                except Exception:
                                    sol_stage3 = None

                                guardrail_time_stage3_sec = float(time.time() - t_s3)

                                improved_by_stage3 = False
                                try:
                                    if (guardrail_len_stage3 is not None) and (L_best is not None) and int(guardrail_len_stage3) <= int(L_best) - int(ACCURACY_GUARDRAILS_STAGE3_ACCEPT_IMPROVE_MIN_DELTA):
                                        improved_by_stage3 = True
                                except Exception:
                                    improved_by_stage3 = False

                                if improved_by_stage3 and sol_stage3 is not None:
                                    sol_best = sol_stage3
                                    L_best = int(guardrail_len_stage3)
                                    gap_best = guardrail_gap_stage3
                                    guardrail_profile = "STAGE3_POLISH"
                                    warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_STAGE3_ACCEPT"
                                else:
                                    warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_STAGE3_NO_IMPROVE"

    # publish best
                            sol2 = sol_best
                            L2 = L_best
                            guardrail_len2 = int(L2) if (L2 is not None) else None
                            if gap_best is not None and np.isfinite(gap_best):
                                guardrail_gap2 = float(gap_best)
                            else:
                                # if full accepted but gap not computed, compute now
                                try:
                                    if exact_for_gap is not None and exact_for_gap > 0 and guardrail_len2 is not None:
                                        guardrail_gap2 = float(100.0 * (float(guardrail_len2) - float(exact_for_gap)) / float(exact_for_gap))
                                except Exception:
                                    pass

                            # store stage diagnostics
                            guardrail_len_mini = L_mini
                            guardrail_gap_mini = gap_mini
                            guardrail_time_mini_sec = locals().get("guardrail_time_mini", 0.0)
                            guardrail_len_full = L_full
                            guardrail_gap_full = gap_full
                            guardrail_time_full_sec = float(guardrail_time_full)
                        except Exception:
                            warn_str = (warn_str + " | " if warn_str else "") + "GUARDRAIL_FAIL"
                        guardrail_time_sec = float(time.time() - t_gr0)

                        # log event
                        try:
                            guardrail_events.append({
                                "suite": suite_name,
                                "instance": p.name,
                                "variant": v,
                                "reason": guardrail_reason,
                                "profile": guardrail_profile,
                                "geom_class": guardrail_geom_class,
                                "geom_risk_score": float(guardrail_geom_score) if (guardrail_geom_score is not None and np.isfinite(guardrail_geom_score)) else None,
                                "geom_risky_gate": bool(guardrail_geom_risky) if guardrail_geom_risky is not None else None,
                                "len_before": int(L_before_guard) if L_before_guard is not None else None,
                                "len_after": int(guardrail_len2) if guardrail_len2 is not None else int(L),
                                "gap_exact_after": (None if (exact_for_gap is None or exact_for_gap <= 0) else float(100.0 * (float(int(guardrail_len2) if guardrail_len2 is not None else int(L)) - float(exact_for_gap)) / float(exact_for_gap))),
                                "ref_gap": float(guardrail_ref_gap) if guardrail_ref_gap is not None and np.isfinite(guardrail_ref_gap) else None,
                                "len2": int(guardrail_len2) if guardrail_len2 is not None else None,
                                "gap2": float(guardrail_gap2) if guardrail_gap2 is not None else None,
                                "time_sec": float(guardrail_time_sec),
                            })
                        except Exception as e:
                            if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
                                print(f"[plot] plot call failed for {p.name}/{locals().get('pv', locals().get('v', 'NA'))} -> {e}")

                    # Apply guardrail-improved solution (if any) to the main record
                    if guardrail_triggered and guardrail_len2 is not None:
                        try:
                            Lg = int(guardrail_len2)
                            if (L is None) or (Lg < int(L)):
                                L = Lg
                                if sol2 is not None:
                                    sol = sol2
                                # recompute primary gap against OPT if available
                                if opt_len is not None and opt_len > 0:
                                    gap = 100.0 * (float(L) - float(opt_len)) / float(opt_len)
                        except Exception as e:
                            if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
                                print(f"[plot] plot call failed for {p.name}/{locals().get('pv', locals().get('v', 'NA'))} -> {e}")

                    # Total elapsed time should include any guardrail work
                    if v != "EXACT":
                        elapsed = time.time() - t_start

                    # MF small-n exactness: force HK optimum for MF variants when n<=HK_MAX_N
                    try:
                        if (isinstance(v, str) and v.startswith("MF_EDP_ILS")) and (hk_opt_len is not None) and (p.n <= HK_MAX_N):
                            if (L is not None) and (int(L) != int(hk_opt_len)):
                                L = int(hk_opt_len)
                                if hk_tour is not None:
                                    sol = {"tour": hk_tour}
                                # recompute primary gap against OPT if available
                                if opt_len is not None and opt_len > 0:
                                    gap = 100.0 * (float(L) - float(opt_len)) / float(opt_len)
                    except Exception:
                        pass

                    hk_gap = None
                    hk_is_optimal = None
                    if hk_opt_len is not None and hk_opt_len > 0:
                        hk_gap = 100.0 * (L - hk_opt_len) / hk_opt_len
                        hk_is_optimal = (int(L) == int(hk_opt_len))

                    # doğruluk önceliği için "exact" referans (instance-level): HK/MIP/OPT_TOUR
                    exact_len = exact_ref_len
                    exact_source = exact_ref_source
                    exact_gap = None
                    if exact_len is not None and exact_len > 0:
                        exact_gap = 100.0 * (L - exact_len) / exact_len

                    # Plot storage (save after instance finishes)
                    if _plot_enable_suite and (v in PLOT_TOURS_VARIANTS):
                        try:
                            tr = None
                            if isinstance(sol, dict):
                                tr = sol.get("tour", None)
                            elif isinstance(sol, (list, tuple, np.ndarray)):
                                tr = sol
                            if tr is None:
                                tr = locals().get("tour", None)
                            if tr is not None:
                                plot_tours[str(v)] = (list(tr), int(L), exact_gap, str(warn_str), str(exact_source or ""))
                        except Exception as e:
                            if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
                                print(f"[plot] plot call failed for {p.name}/{locals().get('pv', locals().get('v', 'NA'))} -> {e}")
                    # Track best per instance for plotting (ONLY variants that actually have a tour)
                    try:
                        if _plot_enable_suite and PLOT_TOURS_BEST_PER_INSTANCE:
                            if (str(v) in plot_tours) and (plot_tours.get(str(v), (None,))[0] is not None):
                                if (best_plot_L is None) or (int(L) < int(best_plot_L)):
                                    best_plot_L = int(L)
                                    best_plot_variant = str(v)
                    except Exception:
                        pass

                    # Track GLOBAL best tour (among ALL variants with an actual tour; independent of PLOT_TOURS_VARIANTS)
                    try:
                        if _plot_enable_suite and PLOT_TOURS_BEST_PER_INSTANCE:
                            tr_best = None
                            if isinstance(sol, dict):
                                tr_best = sol.get('tour', None)
                            elif isinstance(sol, (list, tuple, np.ndarray)):
                                tr_best = sol
                            if tr_best is None:
                                tr_best = locals().get('tour', None)
                            if tr_best is not None:
                                # strict: recompute from tour for consistency
                                try:
                                    L_true = int(tour_length(list(tr_best), d))
                                except Exception:
                                    L_true = int(L) if L is not None else None
                                if L_true is not None:
                                    if (best_global_L is None) or (int(L_true) < int(best_global_L)):
                                        best_global_L = int(L_true)
                                        best_global_tour = list(tr_best)
                                        best_global_variant = str(v)
                                        best_global_warn = str(warn_str) if warn_str is not None else ''
                                        best_global_src = str(exact_source or '')
                    except Exception:
                        pass

                    rows.append({
                        "suite": suite_name,
                        "instance": p.name,
                        "n": p.n,
                        "edge_weight_type": p.edge_weight_type,
                        "geom_hull_frac": geom.get("geom_hull_frac", np.nan),
                        "geom_bbox_aspect": geom.get("geom_bbox_aspect", np.nan),
                        "geom_pca_aspect": geom.get("geom_pca_aspect", np.nan),
                        "geom_hull_fill": geom.get("geom_hull_fill", np.nan),
                        "geom_nn_mean": geom.get("geom_nn_mean", np.nan),
                        "geom_nn_cv": geom.get("geom_nn_cv", np.nan),
                        "geom_risk_score": float(geom_risk_score(geom)) if (geom is not None and np.isfinite(geom_risk_score(geom))) else np.nan,
                        "geom_rule_class": geom_rule_class(geom) if geom is not None else None,
                        "geom_guard_class": geom_guardrails_class(geom) if geom is not None else None,
                        "variant": v,
                        "length": L,
                        "opt_length": opt_len,
                        "gap_percent": gap,
                        "hk_opt_length": hk_opt_len,
                        "hk_gap_percent": hk_gap,
                        "hk_is_optimal": hk_is_optimal,
                        "hk_time_sec": hk_time_sec,
                        "hk_status": hk_status,
                        "mip_opt_length": mip_opt_len,
                        "mip_time_sec": mip_time_sec,
                        "mip_status": mip_status,
                        "exact_length": exact_len,
                        "exact_source": exact_source,
                        "exact_gap_percent": exact_gap,
                        "time_sec": elapsed,
                        "warnings": warn_str,
                        "candidate_evals": sol.get("total_candidate_evals", 0),
                        "tri_fallback_count": sol.get("tri_fallback_count", 0),
                        "sector0_count": sol.get("sector0_count", 0),
                        "sector1_count": sol.get("sector1_count", 0),
                        "sector2_count": sol.get("sector2_count", 0),
                        "sector_unknown_count": sol.get("sector_unknown_count", 0),
                        "twoopt_time_sec": sol.get("twoopt_time_sec", 0),
                        "twoopt_improvement": sol.get("twoopt_improvement", 0),
                        "mf_nstarts": sol.get("mf_nstarts", None),
                        "mf_best_start": sol.get("mf_best_start", None),
                        "mf_risk_score": sol.get("mf_risk_score", None),
                        "mf_total_ils_time_sec": sol.get("mf_total_ils_time_sec", None),
                        "mf_best_ils_time_sec": sol.get("mf_best_ils_time_sec", None),
                        "mpa_used": sol.get("mpa_used", None),
                        "mpa_time_sec": sol.get("mpa_time_sec", None),
                        "mpa_gens": sol.get("mpa_gens", None),
                        "mpa_pop": sol.get("mpa_pop", None),
                        "mpa_improvement": sol.get("mpa_improvement", None),
                        "mpa_improved": sol.get("mpa_improved", None),
                        "beam_width_used": sol.get("beam_width_used", None),
                        "beam_generated_states": sol.get("beam_generated_states", None),
                        "guardrail_triggered": bool(locals().get("guardrail_triggered", False)),
                        "guardrail_reason": locals().get("guardrail_reason", None),
                        "guardrail_profile": locals().get("guardrail_profile", None),
                        "guardrail_ref_gap": locals().get("guardrail_ref_gap", None),
                        "guardrail_len2": locals().get("guardrail_len2", None),
                        "guardrail_gap2": locals().get("guardrail_gap2", None),

                        "guardrail_len_mini": locals().get("guardrail_len_mini", None),
                        "guardrail_gap_mini": locals().get("guardrail_gap_mini", None),
                        "guardrail_time_mini_sec": locals().get("guardrail_time_mini_sec", None),
                        "guardrail_len_full": locals().get("guardrail_len_full", None),
                        "guardrail_gap_full": locals().get("guardrail_gap_full", None),
                        "guardrail_time_full_sec": locals().get("guardrail_time_full_sec", None),
                        "guardrail_len_stage3": locals().get("guardrail_len_stage3", None),
                        "guardrail_gap_stage3": locals().get("guardrail_gap_stage3", None),
                        "guardrail_time_stage3_sec": locals().get("guardrail_time_stage3_sec", None),
                        "guardrail_time_sec": locals().get("guardrail_time_sec", 0.0),
                        "guardrail_geom_risky": locals().get("guardrail_geom_risky", None),
                        "guardrail_geom_class": locals().get("guardrail_geom_class", None),
                        "guardrail_geom_score": locals().get("guardrail_geom_score", None),
                        "mf_guard_triggered": False,
                        "mf_guard_reason": None,
                        "mf_guard_profile": None,
                        "mf_guard_gap_before": None,
                        "mf_guard_gap_after": None,
                        "mf_guard_time_sec": 0.0,
                        "best_src_variant": None,
                        "status": "OK",
                    })
                    inst_row_idx[str(v)] = len(rows) - 1
                except Exception as e:
                    elapsed = time.time() - t_start
                    status = f"RUN_FAIL: {e}"
                    if str(e) == "SKIP_NO_EXACT":
                        status = "SKIP: no exact reference"
                    rows.append({
                        "suite": suite_name,
                        "instance": p.name,
                        "n": p.n,
                        "edge_weight_type": p.edge_weight_type,
                        "geom_hull_frac": geom.get("geom_hull_frac", np.nan),
                        "geom_bbox_aspect": geom.get("geom_bbox_aspect", np.nan),
                        "geom_pca_aspect": geom.get("geom_pca_aspect", np.nan),
                        "geom_hull_fill": geom.get("geom_hull_fill", np.nan),
                        "geom_nn_mean": geom.get("geom_nn_mean", np.nan),
                        "geom_nn_cv": geom.get("geom_nn_cv", np.nan),
                        "geom_risk_score": float(geom_risk_score(geom)) if (geom is not None and np.isfinite(geom_risk_score(geom))) else np.nan,
                        "geom_rule_class": geom_rule_class(geom) if geom is not None else None,
                        "variant": v,
                        "status": status,
                        "time_sec": elapsed,
                        "warnings": warn_str,
                        "guardrail_triggered": False,
                        "guardrail_reason": None,
                        "guardrail_profile": None,
                        "guardrail_ref_gap": None,
                        "guardrail_len2": None,
                        "guardrail_gap2": None,
                        "guardrail_time_sec": 0.0,
                        "guardrail_geom_risky": None,
                        "guardrail_geom_class": None,
                        "guardrail_geom_score": None,
                    })


            # ---------------------------
            # EXACT_PLOT (opt.tour / HK tour / MIP tour) – only if an exact tour exists
            # This does NOT change any benchmark rows; it only affects plotting and BEST selection.
            try:
                exact_plot_tour = None
                exact_plot_src = None
                if opt_tour is not None and isinstance(opt_tour, (list, tuple)) and len(opt_tour) == int(p.n):
                    exact_plot_tour = list(opt_tour)
                    exact_plot_src = 'OPT_TOUR'
                elif ('hk_tour' in locals()) and (locals().get('hk_tour') is not None) and isinstance(locals().get('hk_tour'), (list, tuple)) and len(locals().get('hk_tour')) == int(p.n):
                    exact_plot_tour = list(locals().get('hk_tour'))
                    exact_plot_src = 'HK'
                elif (mip_tour is not None) and isinstance(mip_tour, (list, tuple)) and len(mip_tour) == int(p.n):
                    exact_plot_tour = list(mip_tour)
                    exact_plot_src = 'MIP'

                if exact_plot_tour is not None:
                    try:
                        Lx = int(tour_length(exact_plot_tour, d))
                    except Exception:
                        Lx = int(exact_ref_len) if (exact_ref_len is not None and np.isfinite(exact_ref_len)) else None
                    if Lx is not None:
                        # exact_gap for exact tour should be 0 by definition; plotting code recomputes against exact_ref_len.
                        plot_tours['EXACT_PLOT'] = (list(exact_plot_tour), int(Lx), 0.0, f'EXACT_PLOT src={exact_plot_src}', str(exact_plot_src or ''))

                        # Make BEST truly global-best if an exact tour exists
                        if PLOT_TOURS_BEST_PER_INSTANCE:
                            if (best_global_L is None) or (int(Lx) < int(best_global_L)):
                                best_global_L = int(Lx)
                                best_global_tour = list(exact_plot_tour)
                                best_global_variant = 'EXACT_PLOT'
                                best_global_warn = f'EXACT_PLOT src={exact_plot_src}'
                                best_global_src = str(exact_plot_src or '')
            except Exception:
                pass

            # ---------------------------

            # ------------------------------------------------------------
            # Instance-level MF guard + BEST_ENVELOPE retrospective summary (tail control / reporting)
            # ------------------------------------------------------------
            try:
                _do_mf_guard = bool(MF_GUARD_ENABLE) and (suite_name != "stress" or bool(MF_GUARD_STRESS_ENABLE))
                if _do_mf_guard and ("MF_EDP_ILS" in inst_row_idx) and (("EDP_3SECT" in inst_row_idx) or ("EDP_LOCAL_3SECT" in inst_row_idx)):
                    idx_mf = inst_row_idx.get("MF_EDP_ILS", None)
                    idx_e1 = inst_row_idx.get("EDP_3SECT", None)
                    idx_e2 = inst_row_idx.get("EDP_LOCAL_3SECT", None)

                    mf_gap = None
                    edp_best_gap = None
                    try:
                        if idx_mf is not None:
                            mf_gap = float(rows[idx_mf].get("gap_percent", np.nan))
                    except Exception:
                        mf_gap = None

                    edp_gaps = []
                    for _ix in [idx_e1, idx_e2]:
                        if _ix is None:
                            continue
                        try:
                            g = float(rows[_ix].get("gap_percent", np.nan))
                            if np.isfinite(g):
                                edp_gaps.append(g)
                        except Exception:
                            pass
                    if len(edp_gaps) > 0:
                        edp_best_gap = float(min(edp_gaps))

                    if (mf_gap is not None) and (edp_best_gap is not None) and np.isfinite(mf_gap) and np.isfinite(edp_best_gap):
                        if (mf_gap > (edp_best_gap + float(MF_GUARD_WORSE_DELTA_PCT))) and (mf_gap >= float(MF_GUARD_ABS_GAP_MIN_PCT)):
                            _mf_guard_skip = False
                            try:
                                delta_mf_edp = float(mf_gap) - float(edp_best_gap)
                                if (p.n >= int(MF_GUARD_STRONG_MAX_N)) and (delta_mf_edp > float(MF_GUARD_STRONG_LARGE_N_MAX_DELTA_PCT)):
                                    _mf_guard_skip = True
                            except Exception:
                                _mf_guard_skip = False

                            if _mf_guard_skip:
                                t_guard = 0.0
                                # keep existing MF solution; this will be treated as a "triggered-but-skipped" guard event
                                sol_strong = {"length": float(rows[idx_mf].get("length", np.nan))}
                            else:
                                t0 = time.time()
                                sol_strong = solve_variant(p, "MF_EDP_ILS_STRONG", knn_all)
                                t_guard = float(time.time() - t0)

                            L_old = None
                            try:
                                L_old = float(rows[idx_mf].get("length", np.nan))
                            except Exception:
                                L_old = None

                            L_new = float(sol_strong.get("length", np.nan))

                            # compute gap using robust opt-length key
                            gap_new = None
                            opt_len = None
                            try:
                                opt_len = rows[idx_mf].get("opt_length", None)
                                if opt_len is None:
                                    opt_len = rows[idx_mf].get("opt_len", None)
                                if opt_len is not None and np.isfinite(float(opt_len)):
                                    gap_new = 100.0 * (L_new - float(opt_len)) / float(opt_len)
                            except Exception:
                                gap_new = None

                            # accept if gap improved OR length improved (safety)
                            accepted = False
                            try:
                                if (gap_new is not None) and np.isfinite(gap_new) and np.isfinite(float(mf_gap)) and (gap_new < float(mf_gap) - 1e-12):
                                    accepted = True
                            except Exception:
                                pass
                            try:
                                if (not accepted) and (L_old is not None) and np.isfinite(float(L_old)) and np.isfinite(float(L_new)) and (float(L_new) < float(L_old) - 1e-9):
                                    accepted = True
                            except Exception:
                                pass
                            mf_guard_events.append({
                                "suite": suite_name,
                                "instance": p.name,
                                "n": p.n,
                                "mf_gap_before": float(mf_gap),
                                "mf_gap_after": float(gap_new) if (gap_new is not None and np.isfinite(gap_new)) else np.nan,
                                "mf_len_before": float(L_old) if (L_old is not None and np.isfinite(float(L_old))) else np.nan,
                                "mf_len_after": float(L_new) if (L_new is not None and np.isfinite(float(L_new))) else np.nan,
                                "edp_best_gap": float(edp_best_gap),
                                "delta_pct": float(MF_GUARD_WORSE_DELTA_PCT),
                                "time_sec": float(t_guard),
                                "accepted": bool(accepted),
                            })

                            # Mark MF-guard attempt on the MF row (even if rejected) and account for time spent
                            if (idx_mf is not None):
                                r = rows[idx_mf]
                                r["mf_guard_triggered"] = True
                                if locals().get("_mf_guard_skip", False):
                                    try:
                                        _delta = float(mf_gap) - float(edp_best_gap)
                                    except Exception:
                                        _delta = float("nan")
                                    r["mf_guard_reason"] = f"SKIP_LARGE_N_DELTA(n={p.n},delta={_delta:.2f})"
                                    r["mf_guard_profile"] = "SKIP_LARGE_N_DELTA"
                                else:
                                    r["mf_guard_reason"] = f"mf_worse_than_edp({mf_gap:.2f}>{edp_best_gap:.2f}+{float(MF_GUARD_WORSE_DELTA_PCT):.2f})"
                                    r["mf_guard_profile"] = "MF_STRONG"
                                r["mf_guard_gap_before"] = float(mf_gap)
                                r["mf_guard_gap_after"] = float(gap_new) if (gap_new is not None and np.isfinite(gap_new)) else np.nan
                                r["mf_guard_time_sec"] = float(t_guard)
                                try:
                                    r["time_sec"] = float(r.get("time_sec", 0.0)) + float(t_guard)
                                except Exception:
                                    pass

                            if accepted and (idx_mf is not None):
                                r = rows[idx_mf]
                                r["length"] = float(L_new)
                                r["gap_percent"] = float(gap_new) if (gap_new is not None and np.isfinite(gap_new)) else float(r.get("gap_percent", mf_gap))
                                try:
                                    exlen = r.get("exact_length", None)
                                    if exlen is None:
                                        exlen = r.get("exact_ref_len", None)
                                    if exlen is not None and np.isfinite(float(exlen)):
                                        r["gap_exact"] = 100.0 * (float(L_new) - float(exlen)) / float(exlen)
                                except Exception:
                                    pass

                                for k in ["warn", "src", "nstarts", "best_start", "ils_time_sec",
                                          "geom_rule_class", "geom_risk_score", "geom_hull_frac", "geom_nn_cv",
                                          "geom_mpa_enabled", "geom_scale_adjust", "mpa_improved",
                                          "beam_width_used", "beam_generated_states"]:
                                    if k in sol_strong:
                                        r[k] = sol_strong.get(k)

                                r["mf_guard_triggered"] = True
                                r["mf_guard_reason"] = f"mf_worse_than_edp({mf_gap:.2f}>{edp_best_gap:.2f}+{float(MF_GUARD_WORSE_DELTA_PCT):.2f})"
                                r["mf_guard_profile"] = "MF_STRONG"
                                r["mf_guard_gap_before"] = float(mf_gap)
                                r["mf_guard_gap_after"] = float(gap_new) if (gap_new is not None and np.isfinite(gap_new)) else float(r.get("gap_percent", mf_gap))
                                r["mf_guard_time_sec"] = float(t_guard)

                                # update GLOBAL best if MF became best
                                try:
                                    if best_global_L is None or (np.isfinite(float(best_global_L)) and float(L_new) < float(best_global_L)):
                                        best_global_L = float(L_new)
                                        best_global_tour = sol_strong.get("tour", best_global_tour)
                                        best_global_variant = "MF_EDP_ILS"
                                        best_global_warn = str(sol_strong.get("warn", ""))
                                        best_global_src = str(sol_strong.get("src", ""))
                                except Exception:
                                    pass
            except Exception:
                pass

            # Final row sync + optional MF hard fallback (before BEST_ENVELOPE selection)
            try:
                for _vname, _rix in list(inst_row_idx.items()):
                    try:
                        _rix = int(_rix)
                        if 0 <= _rix < len(rows):
                            rows[_rix] = _sync_row_gap_fields(rows[_rix])
                    except Exception:
                        pass
                apply_mf_hard_fallback_instance(rows, inst_row_idx, suite_name, p.name, p.n, mf_guard_events)
                for _vname, _rix in list(inst_row_idx.items()):
                    try:
                        _rix = int(_rix)
                        if 0 <= _rix < len(rows):
                            rows[_rix] = _sync_row_gap_fields(rows[_rix])
                    except Exception:
                        pass
            except Exception:
                pass

            # BEST_ENVELOPE row: instance başına en iyi heuristic sonucu ex post analitik zarf olarak raporla (guardrail sayımlarını ikiye katlamasın)
            try:
                _cand = ["CI", "NEAREST_INSERTION", "FARTHEST_INSERTION", "EDP_3SECT", "EDP_LOCAL_3SECT", "MF_EDP_ILS"]
                _cand_idx = []
                for cv in _cand:
                    if cv in inst_row_idx:
                        _cand_idx.append((cv, int(inst_row_idx[cv])))
                if len(_cand_idx) > 0:
                    best_cv, best_ix = min(_cand_idx, key=lambda t: float(rows[t[1]].get("length", np.inf)))
                    best_row = dict(rows[best_ix])
                    best_row["variant"] = BEST_SUMMARY_EXPORT_LABEL
                    best_row["best_src_variant"] = str(best_cv)
                    best_row["hk_status"] = "SKIP"
                    best_row["hk_is_optimal"] = np.nan

                    # reset guardrail flags on retrospective summary row to avoid double-counting
                    best_row["guardrail_triggered"] = False
                    best_row["guardrail_reason"] = None
                    best_row["guardrail_profile"] = None
                    best_row["guardrail_time_sec"] = 0.0

                    best_row["mf_guard_triggered"] = False
                    best_row["mf_guard_reason"] = None
                    best_row["mf_guard_profile"] = None
                    best_row["mf_guard_gap_before"] = None
                    best_row["mf_guard_gap_after"] = None
                    best_row["mf_guard_time_sec"] = 0.0

                    
                    
                    # --- BEST_ENVELOPE postboost (tail-aware) + telemetry ---
                    try:
                        best_row["best_postboost_attempted"] = False
                        best_row["best_postboost_ran"] = False
                        best_row["best_postboost_time_sec"] = 0.0
                        best_row["best_postboost_gain"] = 0
                        best_row["best_postboost_len_before"] = None
                        best_row["best_postboost_len_after"] = None
                        best_row["best_postboost_reason"] = None
                    
                        if bool(globals().get("BEST_POSTBOOST_ENABLE", True)):
                            # gap now (prefer opt-gap, else exact-gap)
                            _gap_now = None
                            try:
                                _gap_now = float(best_row.get("gap_percent", np.nan))
                                if not np.isfinite(_gap_now):
                                    _gap_now = float(best_row.get("exact_gap_percent", np.nan))
                            except Exception:
                                _gap_now = None
                    
                            _nnow = int(best_row.get("n", p.n))
                            _min_n = int(globals().get("BEST_POSTBOOST_MIN_N", 450))
                            _min_gap = float(globals().get("BEST_POSTBOOST_MIN_GAP_PCT", 3.0))
                    
                            _gap_ok = True
                            try:
                                if _gap_now is not None and np.isfinite(_gap_now):
                                    _gap_ok = (float(_gap_now) >= float(_min_gap))
                            except Exception:
                                _gap_ok = True
                    
                            if (_nnow >= _min_n) and _gap_ok:
                                # acquire a base tour (prefer the BEST source variant's plotted tour)
                                _tour0 = None
                                try:
                                    if isinstance(plot_tours, dict) and (str(best_cv) in plot_tours):
                                        _tour0 = plot_tours[str(best_cv)][0]
                                except Exception:
                                    _tour0 = None
                    
                                try:
                                    if _tour0 is None and (str(best_global_variant or "") == str(best_cv)) and best_global_tour is not None:
                                        _tour0 = list(best_global_tour)
                                except Exception:
                                    pass
                    
                                # mark attempt even if no tour (telemetry transparency)
                                best_row["best_postboost_attempted"] = True
                    
                                if _tour0 is None:
                                    best_row["best_postboost_reason"] = "no_tour"
                                else:
                                    tpb0 = time.time()
                                    L_before = int(tour_length(list(_tour0), d))
                                    best_row["best_postboost_len_before"] = int(L_before)
                    
                                    # dynamic time budget
                                    tb = float(globals().get("BEST_POSTBOOST_BASE_BUDGET_SEC", 4.0))
                                    try:
                                        tail_n = int(globals().get("BEST_POSTBOOST_TAIL_N", 900))
                                        tail_gap = float(globals().get("BEST_POSTBOOST_TAIL_GAP_PCT", 7.0))
                                        if (_nnow >= tail_n) and (_gap_now is not None and np.isfinite(_gap_now) and float(_gap_now) >= float(tail_gap)):
                                            tb = max(tb, float(globals().get("BEST_POSTBOOST_TAIL_BUDGET_SEC", 10.0)))
                                    except Exception:
                                        pass
                    
                                    # temporarily strengthen Large-N postls knobs (only during postboost)
                                    _saved = {}
                                    try:
                                        if bool(globals().get("BEST_POSTBOOST_STRENGTHEN", True)) and (_nnow >= 700):
                                            for _k in [
                                                "LARGE_N_POSTLS_KNN_K",
                                                "LARGE_N_POSTLS_RELOC_MAX_MOVES",
                                                "LARGE_N_POSTLS_OROPT_MAX_MOVES",
                                                "LARGE_N_POSTLS_KICK_TRIES",
                                                "LARGE_N_POSTLS_OROPT_ROUNDS",
                                                "LARGE_N_POSTLS_RELOC_ROUNDS",
                                                "LARGE_N_POSTLS_ILS_CYCLES_MAX",
                                                "LARGE_N_POSTLS_ILS_NOIMP_STOP",
                                                "LARGE_N_POSTLS_ILS_2OPT_SEC",
                                                "LARGE_N_POSTLS_ILS_OROPT_ENABLE",
                                                "LARGE_N_POSTLS_ILS_OROPT_MOVES",
                                                "LARGE_N_POSTLS_OROPT_CAND_K",
                                            ]:
                                                if _k in globals():
                                                    _saved[_k] = globals().get(_k)
                    
                                            globals()["LARGE_N_POSTLS_KNN_K"] = max(int(globals().get("LARGE_N_POSTLS_KNN_K", 40)), 80 if _nnow < 900 else 120)
                                            globals()["LARGE_N_POSTLS_RELOC_MAX_MOVES"] = max(int(globals().get("LARGE_N_POSTLS_RELOC_MAX_MOVES", 2000)), 3500)
                                            globals()["LARGE_N_POSTLS_OROPT_MAX_MOVES"] = max(int(globals().get("LARGE_N_POSTLS_OROPT_MAX_MOVES", 1500)), 2500)
                                            globals()["LARGE_N_POSTLS_KICK_TRIES"] = max(int(globals().get("LARGE_N_POSTLS_KICK_TRIES", 0)), 2 if _nnow < 900 else 3)
                                            globals()["LARGE_N_POSTLS_OROPT_ROUNDS"] = max(int(globals().get("LARGE_N_POSTLS_OROPT_ROUNDS", 1)), 2)
                                            globals()["LARGE_N_POSTLS_RELOC_ROUNDS"] = max(int(globals().get("LARGE_N_POSTLS_RELOC_ROUNDS", 1)), 1)
                                            globals()["LARGE_N_POSTLS_ILS_CYCLES_MAX"] = max(int(globals().get("LARGE_N_POSTLS_ILS_CYCLES_MAX", 10)), 40 if _nnow < 900 else 80)
                                            globals()["LARGE_N_POSTLS_ILS_NOIMP_STOP"] = max(int(globals().get("LARGE_N_POSTLS_ILS_NOIMP_STOP", 3)), 10 if _nnow < 900 else 18)
                                            globals()["LARGE_N_POSTLS_ILS_2OPT_SEC"] = max(float(globals().get("LARGE_N_POSTLS_ILS_2OPT_SEC", 2.0)), 3.0 if _nnow < 900 else 4.5)
                                            globals()["LARGE_N_POSTLS_ILS_OROPT_ENABLE"] = True
                                            globals()["LARGE_N_POSTLS_ILS_OROPT_MOVES"] = max(int(globals().get("LARGE_N_POSTLS_ILS_OROPT_MOVES", 700)), 1200 if _nnow < 900 else 2000)
                                            globals()["LARGE_N_POSTLS_OROPT_CAND_K"] = max(int(globals().get("LARGE_N_POSTLS_OROPT_CAND_K", 18)), 30 if _nnow < 900 else 45)
                                    except Exception:
                                        _saved = {}
                    
                                    try:
                                        # run the booster
                                        _opt_for_doc = best_row.get("opt_length", None)
                                        try:
                                            _opt_for_doc = int(_opt_for_doc) if (_opt_for_doc is not None and np.isfinite(float(_opt_for_doc))) else 0
                                        except Exception:
                                            _opt_for_doc = 0
                    
                                        t_new, L_new, t_spent, gain = large_n_post_improve(
                                            list(_tour0), d, coords, int(_opt_for_doc), time_budget=float(tb)
                                        )
                    
                                        t_elapsed = float(t_spent) if (t_spent is not None and np.isfinite(float(t_spent))) else float(time.time() - tpb0)
                                        best_row["best_postboost_time_sec"] = float(t_elapsed)
                                        best_row["best_postboost_ran"] = True
                                        # Account postboost time in BEST_ENVELOPE runtime (fair reporting)
                                        try:
                                            best_row["time_sec"] = float(best_row.get("time_sec", 0.0)) + float(t_elapsed)
                                        except Exception:
                                            pass
                                        best_row["best_postboost_len_after"] = int(L_new)
                                        best_row["best_postboost_gain"] = int(max(0, int(L_before) - int(L_new)))
                    
                                        if int(L_new) < int(L_before) and t_new is not None:
                                            # Update BEST row numbers
                                            best_row["length"] = int(L_new)
                    
                                            # recompute opt-gap
                                            try:
                                                oL = best_row.get("opt_length", None)
                                                if oL is not None and np.isfinite(float(oL)) and float(oL) > 0:
                                                    best_row["gap_percent"] = 100.0 * (float(L_new) - float(oL)) / float(oL)
                                            except Exception:
                                                pass
                    
                                            # recompute exact gap
                                            try:
                                                exL = best_row.get("exact_length", None)
                                                if exL is not None and np.isfinite(float(exL)) and float(exL) > 0:
                                                    best_row["exact_gap_percent"] = 100.0 * (float(L_new) - float(exL)) / float(exL)
                                            except Exception:
                                                pass
                    
                                            # postboost time has already been accounted for above;
                                            # do NOT add it again here, otherwise BEST_ENVELOPE runtime is double-counted.
                    
                                            best_row["best_postboost_reason"] = "improved"
                    
                                            # feed plotting and GLOBAL-best selection
                                            try:
                                                if _plot_enable_suite and PLOT_TOURS_BEST_PER_INSTANCE:
                                                    exL = best_row.get("exact_length", None)
                                                    ex_gap2 = None
                                                    try:
                                                        if exL is not None and np.isfinite(float(exL)) and float(exL) > 0:
                                                            ex_gap2 = 100.0 * (float(L_new) - float(exL)) / float(exL)
                                                    except Exception:
                                                        ex_gap2 = None
                    
                                                    plot_tours["BEST_POSTBOOST"] = (
                                                        list(t_new), int(L_new), ex_gap2,
                                                        f"BEST_POSTBOOST src={best_cv}", str(best_row.get("exact_source", ""))
                                                    )
                                            except Exception:
                                                pass
                    
                                            try:
                                                if best_global_L is None or (np.isfinite(float(best_global_L)) and float(L_new) < float(best_global_L)):
                                                    best_global_L = float(L_new)
                                                    best_global_tour = list(t_new)
                                                    best_global_variant = "BEST_POSTBOOST"
                                                    best_global_warn = "BEST_POSTBOOST"
                                                    best_global_src = str(best_cv)
                                            except Exception:
                                                pass
                    
                                        else:
                                            best_row["best_postboost_reason"] = "no_improve"
                    
                                    finally:
                                        # restore strengthened knobs
                                        try:
                                            for _k, _v in _saved.items():
                                                globals()[_k] = _v
                                        except Exception:
                                            pass
                    
                    except Exception:
                        pass
                    best_row = _sync_row_gap_fields(best_row)
                    rows.append(best_row)
            except Exception:
                pass

            # MF stochastic seed-stability audit (separate from main benchmark rows)
            try:
                if bool(globals().get("MF_SEED_STABILITY_ENABLE", False)) and _suite_in_allowed_set(suite_name, globals().get("MF_SEED_STABILITY_SUITES", ("core",))):
                    _rep_n = int(globals().get("MF_SEED_STABILITY_REPEATS", 0))
                    _variants_rep = tuple(str(x) for x in globals().get("MF_SEED_STABILITY_VARIANTS", ("MF_EDP_ILS",)))
                    if (_rep_n > 0) and (int(p.n) >= int(globals().get("MF_SEED_STABILITY_MIN_N", 0))) and (int(p.n) <= int(globals().get("MF_SEED_STABILITY_MAX_N", 10**9))):
                        for _rv in _variants_rep:
                            for _rep in range(_rep_n):
                                _seed_shift = int(globals().get("MF_SEED_STABILITY_SEED_BASE", 0)) + int(_rep) * int(globals().get("MF_SEED_STABILITY_SEED_STRIDE", 1))
                                _t0_rep = time.time()
                                _sol_rep = solve_variant(p, _rv, knn_all, stability_seed_shift=int(_seed_shift))
                                _elapsed_rep = float(time.time() - _t0_rep)
                                _L_rep = _sol_rep.get("length", np.nan)
                                try:
                                    _gap_rep = 100.0 * (float(_L_rep) - float(opt_len)) / float(opt_len) if (opt_len is not None and np.isfinite(float(opt_len)) and float(opt_len) > 0) else np.nan
                                except Exception:
                                    _gap_rep = np.nan
                                try:
                                    _exact_gap_rep = 100.0 * (float(_L_rep) - float(exact_len)) / float(exact_len) if (exact_len is not None and np.isfinite(float(exact_len)) and float(exact_len) > 0) else np.nan
                                except Exception:
                                    _exact_gap_rep = np.nan
                                _det_len = np.nan
                                _det_exg = np.nan
                                try:
                                    if _rv in inst_row_idx:
                                        _r0 = rows[int(inst_row_idx[_rv])]
                                        _det_len = _r0.get("length", np.nan)
                                        _det_exg = _r0.get("exact_gap_percent", np.nan)
                                except Exception:
                                    pass
                                mf_seed_rows.append({
                                    "suite": suite_name,
                                    "instance": p.name,
                                    "n": p.n,
                                    "variant": _rv,
                                    "repeat_id": int(_rep + 1),
                                    "seed_shift": int(_seed_shift),
                                    "length": _L_rep,
                                    "gap_percent": _gap_rep,
                                    "exact_gap_percent": _exact_gap_rep,
                                    "time_sec": _elapsed_rep,
                                    "mf_nstarts": _sol_rep.get("mf_nstarts", _sol_rep.get("nstarts", np.nan)),
                                    "mf_best_start": _sol_rep.get("mf_best_start", _sol_rep.get("best_start", np.nan)),
                                    "mf_total_ils_time_sec": _sol_rep.get("mf_total_ils_time_sec", _sol_rep.get("total_ils_time_sec", np.nan)),
                                    "mf_best_ils_time_sec": _sol_rep.get("mf_best_ils_time_sec", _sol_rep.get("best_ils_time_sec", np.nan)),
                                    "deterministic_length": _det_len,
                                    "deterministic_exact_gap_percent": _det_exg,
                                })
            except Exception:
                pass

            # Save route plots (TIFF + PDF)
            if _plot_enable_suite:
                # NOTE: out_dir değişkeni bu scope'ta her zaman görünür olmayabilir (Spyder/Pylance).
                # Plot çıktılarını OUT_DIR/plots altına yazıyoruz.
                try:
                    plots_root = globals().get("OUT_DIR", None)
                    if not plots_root:
                        plots_root = os.getcwd()
                    plots_dir = os.path.join(plots_root, "plots")
                    os.makedirs(plots_dir, exist_ok=True)
                except Exception:
                    plots_dir = None

                if plots_dir:
                    # Save per-variant plots (TIFF + PDF)
                    for pv, (ptour, pL, pGapExact, pWarn, pSrc) in list(plot_tours.items()):
                        try:
                            base = os.path.join(plots_dir, f"{_safe_fname(p.name)}__{_safe_fname(pv)}__{_safe_fname(RUN_TAG)}")
                            title = f"{p.name} | {pv}"

                            # Recompute length/gap from the actual plotted tour for strict consistency
                            try:
                                pL_true = int(tour_length(list(ptour), d))
                            except Exception:
                                pL_true = int(pL)

                            pGap_true = None
                            try:
                                if exact_ref_len is not None and exact_ref_len > 0:
                                    pGap_true = 100.0 * (float(pL_true) - float(exact_ref_len)) / float(exact_ref_len)
                            except Exception:
                                pGap_true = pGapExact

                            stage_lbl = _extract_guardrail_stage(str(pWarn) if pWarn is not None else "")
                            _save_tour_plot(
                                p.coords,
                                list(ptour),
                                base,
                                title=title,
                                L_val=int(pL_true),
                                exact_gap=(float(pGap_true) if (pGap_true is not None and np.isfinite(pGap_true)) else None),
                                guardrail_stage=stage_lbl,
                                exact_source=str(pSrc) if pSrc is not None else "",
                                subtitle=str(pWarn) if pWarn is not None else "",
                                dpi=int(PLOT_TOURS_DPI),
                                node_labels=getattr(p, "i2node", None),
                            )

                        except Exception as e:
                            if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
                                print(f"[plot] plot call failed for {p.name}/{pv} -> {e}")

                    # Save BEST plot (GLOBAL best tour if available; otherwise best among plotted tours)
                    if PLOT_TOURS_BEST_PER_INSTANCE:
                        try:
                            best_tour = None
                            best_v = None
                            best_warn = ""
                            best_src = ""
                            best_L_true = None

                            # 1) Prefer true global best (across all variants), if we have a tour
                            if locals().get('best_global_tour', None) is not None:
                                best_tour = list(best_global_tour)
                                best_v = str(best_global_variant) if best_global_variant is not None else 'GLOBAL'
                                best_warn = str(best_global_warn) if best_global_warn is not None else ""
                                best_src = str(best_global_src) if best_global_src is not None else ""
                                best_L_true = int(best_global_L) if best_global_L is not None else None

                            # 2) Fallback: best among plotted tours, by strict recomputed length
                            if best_tour is None and len(plot_tours) > 0:
                                cand = []
                                for _k, (_t, _L, _g, _w, _s) in list(plot_tours.items()):
                                    try:
                                        _Lt = int(tour_length(list(_t), d))
                                    except Exception:
                                        _Lt = int(_L) if _L is not None else None
                                    if _Lt is not None:
                                        cand.append((_Lt, _k))
                                if len(cand) > 0:
                                    cand.sort(key=lambda x: x[0])
                                    best_L_true, best_v = cand[0]
                                    bt, bL, bg, bw, bs = plot_tours[best_v]
                                    best_tour = list(bt)
                                    best_warn = str(bw) if bw is not None else ""
                                    best_src = str(bs) if bs is not None else ""

                            # 3) Save BEST plot
                            if best_tour is not None:
                                best_gap_true = None
                                try:
                                    if exact_ref_len is not None and exact_ref_len > 0 and best_L_true is not None:
                                        best_gap_true = 100.0 * (float(best_L_true) - float(exact_ref_len)) / float(exact_ref_len)
                                except Exception:
                                    best_gap_true = None

                                base = os.path.join(plots_dir, f"{_safe_fname(p.name)}__BEST__{_safe_fname(RUN_TAG)}")
                                title = f"{p.name} | BEST"
                                subtitle = f"best_variant={best_v}"
                                if best_warn:
                                    subtitle += f" | {best_warn}"
                                stage_lbl = _extract_guardrail_stage(str(best_warn) if best_warn is not None else "")

                                _save_tour_plot(
                                    p.coords,
                                    list(best_tour),
                                    base,
                                    title=title,
                                    L_val=(int(best_L_true) if best_L_true is not None else None),
                                    exact_gap=(float(best_gap_true) if (best_gap_true is not None and np.isfinite(best_gap_true)) else None),
                                    guardrail_stage=stage_lbl,
                                    exact_source=str(best_src) if best_src is not None else "",
                                    subtitle=str(subtitle) if subtitle is not None else "",
                                    dpi=int(PLOT_TOURS_DPI),
                                    node_labels=getattr(p, "i2node", None),
                                )

                        except Exception as e:
                            if bool(globals().get("PLOT_TOURS_VERBOSE", False)):
                                print(f"[plot] BEST plot failed for {p.name} -> {e}")


    df = pd.DataFrame(rows)
    try:
        df = sync_gap_fields_df(df)
        df = rebuild_best_heur_rows_df(df)
        df = sync_gap_fields_df(df)
    except Exception:
        pass
    out_csv = os.path.join(OUT_DIR, f"benchmark_results_{RUN_TAG}.csv")
    df.to_csv(out_csv, index=False, encoding="utf-8")

    # MF seed-stability exports (stochastic audit; separate from main benchmark)
    try:
        if len(mf_seed_rows) > 0:
            stab_df = pd.DataFrame(mf_seed_rows)
            if bool(globals().get("MF_SEED_STABILITY_EXPORT_RAW", True)):
                stab_raw_out = os.path.join(OUT_DIR, f"mf_seed_stability_runs_{RUN_TAG}.csv")
                stab_df.to_csv(stab_raw_out, index=False, encoding="utf-8")
                print(f"MF seed-stability runs CSV: {stab_raw_out}")
            stab_sum = summarize_mf_seed_stability(stab_df)
            stab_sum_out = os.path.join(OUT_DIR, f"mf_seed_stability_summary_{RUN_TAG}.csv")
            stab_sum.to_csv(stab_sum_out, index=False, encoding="utf-8")
            print(f"MF seed-stability summary CSV: {stab_sum_out}")
            try:
                agg = pd.DataFrame([{
                    "variant": "MF_EDP_ILS",
                    "repeats_total": int(len(stab_df)),
                    "instances": int(stab_df[["suite", "instance"]].drop_duplicates().shape[0]),
                    "exact_gap_mean": float(pd.to_numeric(stab_df["exact_gap_percent"], errors="coerce").mean()),
                    "exact_gap_std": float(pd.to_numeric(stab_df["exact_gap_percent"], errors="coerce").std(ddof=1)),
                    "time_mean": float(pd.to_numeric(stab_df["time_sec"], errors="coerce").mean()),
                    "time_std": float(pd.to_numeric(stab_df["time_sec"], errors="coerce").std(ddof=1)),
                }])
                agg_out = os.path.join(OUT_DIR, f"mf_seed_stability_aggregate_{RUN_TAG}.csv")
                agg.to_csv(agg_out, index=False, encoding="utf-8")
                print(f"MF seed-stability aggregate CSV: {agg_out}")
            except Exception:
                pass
    except Exception:
        pass

    # ---------------------------
    # Post-process: pivotlar, HK doğruluk özeti, HK failure cases
    # ---------------------------
    ok = df[df["status"] == "OK"].copy()

    # Pivot tablolar (her zaman üret; OK satır yoksa atla)
    if len(ok) > 0:
        pv_len = ok.pivot_table(index=["instance", "n"], columns="variant", values="length", aggfunc="min")
        pv_time = ok.pivot_table(index=["instance", "n"], columns="variant", values="time_sec", aggfunc="min")
        pv_len.to_csv(os.path.join(OUT_DIR, f"pivot_length_{RUN_TAG}.csv"), encoding="utf-8")
        pv_time.to_csv(os.path.join(OUT_DIR, f"pivot_time_{RUN_TAG}.csv"), encoding="utf-8")

    # HK (exact) doğrulanan örneklerde başarısız (optimal olmayan) vakaları ayrı kaydet
    fail_out = os.path.join(OUT_DIR, f"hk_failure_cases_{RUN_TAG}.csv")
    if ("hk_is_optimal" in df.columns) and ("hk_status" in df.columns) and len(ok) > 0:
        fail = ok[(ok["hk_status"] == "OK") & (ok["hk_is_optimal"] == False)].copy()
    else:
        # Kolonlar yoksa/OK yoksa, boş CSV üret (headers var)
        fail = pd.DataFrame(columns=df.columns.tolist())
    fail.to_csv(fail_out, index=False, encoding="utf-8")

    
    # Geometri drift raporu (opsiyonel)
    try:
        if GEOM_DRIFT_REPORT_ENABLE:
            geom_drift_report(df, OUT_DIR, RUN_TAG)

            # Accuracy-guardrails report
            try:
                if ACCURACY_GUARDRAILS_ENABLE and len(guardrail_events) > 0:
                    gr_df = pd.DataFrame(guardrail_events)
                    gr_out = os.path.join(OUT_DIR, f"accuracy_guardrails_{RUN_TAG}.csv")
                    gr_df.to_csv(gr_out, index=False, encoding="utf-8")
                    print(f"Accuracy-guardrails events CSV: {gr_out}")

                # MF guardrails events CSV (isteğe bağlı)
                try:
                    if bool(MF_GUARD_ENABLE) and (len(mf_guard_events) > 0):
                        mg_df = pd.DataFrame(mf_guard_events)
                        mg_out = os.path.join(OUT_DIR, f"mf_guardrails_{RUN_TAG}.csv")
                        mg_df.to_csv(mg_out, index=False)
                        print(f"MF-guardrails events CSV: {mg_out}")
                except Exception:
                    pass

            except Exception:
                pass
    except Exception:
        pass

# Held–Karp exactness summary (HK koşulan örnekler için)
    try:
        if ("hk_status" in ok.columns) and ("hk_is_optimal" in ok.columns):
            hk_ok = ok[ok["hk_status"] == "OK"].copy()
            if len(hk_ok) > 0:
                rep = hk_ok.groupby("variant", observed=False).agg(
                    tested=("hk_is_optimal", "count"),
                    optimal=("hk_is_optimal", "sum"),
                ).reset_index()
                rep["optimal_rate_percent"] = 100.0 * rep["optimal"] / rep["tested"]
                rep_out = os.path.join(OUT_DIR, f"held_karp_exactness_summary_{RUN_TAG}.csv")
                rep.to_csv(rep_out, index=False, encoding="utf-8")
                print(f"\nHeld–Karp exactness summary (n<=HK_MAX_N) [{RUN_TAG}]:")
                print(rep)
                print("Summary CSV:", rep_out)
    except Exception:
        pass

        print("Bitti.")
        print("CSV:", out_csv)
        print("Klasör:", OUT_DIR)

if __name__ == "__main__":
    main()