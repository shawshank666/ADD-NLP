from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


TARGET_COLUMNS = (
    "frame_subharmonics_ratio",
    "frame_sidebands_ratio",
    "frame_frequency_jump_ratio",
    "mean_pitch_voiced",
    "mean_amEnvDep",
    "mean_HNR",
    "mean_roughness",
    "mean_entropy",
    "mean_subDep",
    "median_pitch_voiced",
    "median_amEnvDep",
    "median_HNR",
    "median_roughness",
    "median_entropy",
    "median_subDep",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare speaker-level feature means between two analysis CSV files and "
            "save one correlation scatter plot per selected feature."
        )
    )
    parser.add_argument("--dataset1", type=Path, required=True, help="Path to the first CSV file.")
    parser.add_argument("--dataset2", type=Path, required=True, help="Path to the second CSV file.")
    parser.add_argument(
        "--dataset1-name",
        default=None,
        help="Optional display name for dataset1. Defaults to an inferred dataset name.",
    )
    parser.add_argument(
        "--dataset2-name",
        default=None,
        help="Optional display name for dataset2. Defaults to an inferred dataset name.",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        default=None,
        help="Feature columns to compare. Defaults to a curated feature list.",
    )
    parser.add_argument(
        "--include-non-ok",
        action="store_true",
        help="Include rows whose status is not ok. By default only ok/skipped rows are used.",
    )
    return parser


def normalize_row(raw_row: dict[str, str]) -> dict[str, str]:
    return {(key or "").strip(): (value or "").strip() for key, value in raw_row.items()}


def parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def extract_speaker_from_stem(stem: str) -> str | None:
    normalized_stem = stem.strip()
    if not normalized_stem:
        return None
    normalized_stem = re.sub(
        r"(?:[_-](?:gen|generated|anon|anonymized))+$",
        "",
        normalized_stem,
        flags=re.IGNORECASE,
    )
    match = re.match(r"^([A-Za-z0-9]+?)(?:[_-].+)?$", normalized_stem)
    if match:
        return match.group(1)
    return None


def extract_speaker_id(row: dict[str, str]) -> str:
    relative_audio = row.get("relative_audio", "")
    source_audio = row.get("source_audio", "")

    for audio_path in (relative_audio, source_audio):
        normalized_path = audio_path.replace("\\", "/").strip()
        if not normalized_path:
            continue

        stem_speaker = extract_speaker_from_stem(Path(normalized_path).stem)
        if stem_speaker:
            return stem_speaker

        parts = [part for part in normalized_path.split("/") if part]
        if not normalized_path.startswith("/") and len(parts) >= 2:
            return parts[0]
        if parts:
            return parts[-2] if len(parts) >= 2 else parts[-1]

    return "unknown"


def parse_requested_columns(column_args: list[str] | None) -> list[str]:
    if not column_args:
        return []
    requested_columns: list[str] = []
    for item in column_args:
        for column in item.split(","):
            normalized = column.strip()
            if normalized:
                requested_columns.append(normalized)
    return requested_columns


def load_csv_rows(csv_path: Path, include_non_ok: bool) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames: list[str] = []
    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, skipinitialspace=True)
        fieldnames = [(name or "").strip() for name in (reader.fieldnames or [])]
        for raw_row in reader:
            row = normalize_row(raw_row)
            status = row.get("status", "").lower()
            if not include_non_ok and status not in {"", "ok", "skipped"}:
                continue
            rows.append(row)
    return fieldnames, rows


def resolve_target_columns(
    fieldnames_1: list[str],
    fieldnames_2: list[str],
    rows_1: list[dict[str, str]],
    rows_2: list[dict[str, str]],
    requested_columns: list[str],
) -> list[str]:
    shared_fieldnames = set(fieldnames_1) & set(fieldnames_2)
    if requested_columns:
        missing = [column for column in requested_columns if column not in shared_fieldnames]
        if missing:
            raise ValueError(
                "Requested columns are not shared by both CSV files: " + ", ".join(missing)
            )
        return requested_columns

    available_defaults = []
    for column in TARGET_COLUMNS:
        if column not in shared_fieldnames:
            continue
        if any(parse_float(row.get(column, "")) is not None for row in rows_1) and any(
            parse_float(row.get(column, "")) is not None for row in rows_2
        ):
            available_defaults.append(column)
    if available_defaults:
        return available_defaults

    fallback = []
    for column in sorted(shared_fieldnames):
        if any(parse_float(row.get(column, "")) is not None for row in rows_1) and any(
            parse_float(row.get(column, "")) is not None for row in rows_2
        ):
            fallback.append(column)
    if fallback:
        return fallback
    raise ValueError("No shared numeric columns with valid values were found in both CSV files.")


def aggregate_speaker_means(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    values_by_speaker: dict[str, list[float]] = {}
    for row in rows:
        value = parse_float(row.get(column, ""))
        if value is None:
            continue
        speaker_id = extract_speaker_id(row)
        values_by_speaker.setdefault(speaker_id, []).append(value)
    return {
        speaker_id: float(statistics.fmean(values))
        for speaker_id, values in values_by_speaker.items()
        if values
    }


def infer_dataset_name(path: Path) -> str:
    if path.stem and path.stem.lower() != "audio_stats":
        return path.stem
    if path.parent.name:
        return path.parent.name
    return path.stem or str(path)


def sanitize_metric_name(metric_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", metric_name.strip())


def compute_axis_limits(values_x: np.ndarray, values_y: np.ndarray) -> tuple[tuple[float, float], tuple[float, float]]:
    combined = np.concatenate([values_x, values_y])
    min_value = float(np.min(combined))
    max_value = float(np.max(combined))
    if math.isclose(min_value, max_value):
        padding = max(abs(min_value) * 0.05, 1.0)
    else:
        padding = max((max_value - min_value) * 0.08, 1e-6)
    lower = min_value - padding
    upper = max_value + padding
    return (lower, upper), (lower, upper)


def render_correlation_plot(
    output_path: Path,
    column: str,
    dataset1_name: str,
    dataset2_name: str,
    speaker_values_1: dict[str, float],
    speaker_values_2: dict[str, float],
) -> None:
    shared_speakers = sorted(set(speaker_values_1) & set(speaker_values_2))
    if len(shared_speakers) < 2:
        raise ValueError(
            f"Column '{column}' has fewer than 2 overlapping speakers between the two datasets."
        )

    values_x = np.array([speaker_values_1[speaker] for speaker in shared_speakers], dtype=float)
    values_y = np.array([speaker_values_2[speaker] for speaker in shared_speakers], dtype=float)
    correlation = float(np.corrcoef(values_x, values_y)[0, 1])
    slope, intercept = np.polyfit(values_x, values_y, deg=1)
    fit_x = np.linspace(float(values_x.min()), float(values_x.max()), num=200)
    fit_y = slope * fit_x + intercept

    figure, axis = plt.subplots(1, 1, figsize=(7.5, 6.2), constrained_layout=True)
    axis.scatter(values_x, values_y, s=34, color="#264653", alpha=0.8, edgecolor="white", linewidth=0.35)
    axis.plot(fit_x, fit_y, color="#d1495b", linewidth=2.0, label="Linear fit")
    x_limits, y_limits = compute_axis_limits(values_x, values_y)
    axis.set_xlim(*x_limits)
    axis.set_ylim(*y_limits)
    axis.set_xlabel(dataset1_name)
    axis.set_ylabel(dataset2_name)
    axis.set_title(f"{column} Speaker Mean Correlation")
    axis.grid(True, linestyle="--", linewidth=0.55, alpha=0.35)

    annotation = "\n".join(
        [
            f"shared speakers = {len(shared_speakers)}",
            f"r = {correlation:.4f}",
            f"y = {slope:.4g}x + {intercept:.4g}",
        ]
    )
    axis.text(
        0.02,
        0.98,
        annotation,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#8d99ae", "alpha": 0.92},
    )
    axis.legend(loc="lower right")
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    args = build_parser().parse_args()
    dataset1_path = args.dataset1.expanduser().resolve()
    dataset2_path = args.dataset2.expanduser().resolve()
    if not dataset1_path.is_file():
        raise FileNotFoundError(f"Dataset1 CSV file not found: {dataset1_path}")
    if not dataset2_path.is_file():
        raise FileNotFoundError(f"Dataset2 CSV file not found: {dataset2_path}")

    repo_root = Path(__file__).resolve().parents[2]

    fieldnames_1, rows_1 = load_csv_rows(dataset1_path, include_non_ok=args.include_non_ok)
    fieldnames_2, rows_2 = load_csv_rows(dataset2_path, include_non_ok=args.include_non_ok)
    target_columns = resolve_target_columns(
        fieldnames_1,
        fieldnames_2,
        rows_1,
        rows_2,
        parse_requested_columns(args.columns),
    )

    dataset1_name = args.dataset1_name or infer_dataset_name(dataset1_path)
    dataset2_name = args.dataset2_name or infer_dataset_name(dataset2_path)
    dataset_pair_dir = (
        f"{sanitize_metric_name(dataset1_name)}_vs_{sanitize_metric_name(dataset2_name)}"
    )
    output_dir = repo_root / "results" / "NLPanalysis" / "compare" / dataset_pair_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for column in target_columns:
        speaker_values_1 = aggregate_speaker_means(rows_1, column)
        speaker_values_2 = aggregate_speaker_means(rows_2, column)
        shared_speakers = set(speaker_values_1) & set(speaker_values_2)
        if len(shared_speakers) < 2:
            print(f"Skipping {column}: fewer than 2 overlapping speakers.", flush=True)
            continue

        output_path = output_dir / f"{sanitize_metric_name(column)}.png"
        render_correlation_plot(
            output_path=output_path,
            column=column,
            dataset1_name=dataset1_name,
            dataset2_name=dataset2_name,
            speaker_values_1=speaker_values_1,
            speaker_values_2=speaker_values_2,
        )
        saved_paths.append(output_path)

    if not saved_paths:
        raise ValueError("No plots were generated. Check overlapping speakers and selected columns.")

    print(f"Output directory: {output_dir}", flush=True)
    print("Compared columns: " + ", ".join(target_columns), flush=True)
    for saved_path in saved_paths:
        print(f"Saved figure to: {saved_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())