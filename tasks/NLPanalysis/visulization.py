from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


TARGET_COLUMNS = (
    "frame_subharmonics_ratio",
    "frame_sidebands_ratio",
    "frame_frequency_jump_ratio"
    "mean_pitch_voiced",
    "mean_amENVdep",
    "mean_HNR",
    "mean_roughness",
    "mean_entropy",
    "mean_subDep",
    "median_pitch_voiced",
    "median_amENVdep",
    "median_HNR",
    "median_roughness",
    "median_entropy",
    "median_subDep",
)
DEFAULT_FIGURE_STEM = ""
SORTED_FIGURE_SUFFIX = "sorted_by_mean"
DEFAULT_OUTPUT_SUFFIX = ".png"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize speaker-level distributions for selected numeric columns "
            "from an analysis CSV."
        )
    )
    parser.add_argument("csv_file", help="Path to the analysis CSV file.")
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional output image path used as the filename base. For multiple "
            "columns, the script appends each column name to this base. Defaults "
            "to the CSV directory with suffix '_speaker_ratio_distribution.png'."
        ),
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        default=None,
        help=(
            "Columns to plot. Accepts repeated names or comma-separated names, "
            "for example: --columns frame_subharmonics_ratio mean_HNR"
        ),
    )
    parser.add_argument(
        "--all-columns",
        action="store_true",
        help=(
            "Plot all numeric columns with at least one valid numeric value in the CSV."
        ),
    )
    parser.add_argument(
        "--title-prefix",
        default=None,
        help="Optional title prefix shown above both subplots.",
    )
    parser.add_argument(
        "--include-non-ok",
        action="store_true",
        help="Include rows whose status is not 'ok'. By default these rows are skipped.",
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

    normalized_stem = re.sub(r"(?:[_-](?:gen|generated|anon|anonymized))+$", "", normalized_stem, flags=re.IGNORECASE)
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


def speaker_sort_key(speaker_id: str) -> tuple[int, str]:
    return (0, f"{int(speaker_id):08d}") if speaker_id.isdigit() else (1, speaker_id)


def parse_requested_columns(column_args: list[str] | None) -> list[str]:
    if not column_args:
        return []

    requested_columns: list[str] = []
    for item in column_args:
        for column in item.split(","):
            normalized_column = column.strip()
            if normalized_column:
                requested_columns.append(normalized_column)
    return requested_columns


def load_csv_rows(
    csv_path: Path,
    include_non_ok: bool,
) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames: list[str] = []
    rows: list[dict[str, str]] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, skipinitialspace=True)
        fieldnames = [(name or "").strip() for name in (reader.fieldnames or [])]
        for raw_row in reader:
            row = normalize_row(raw_row)
            status = row.get("status", "")
            if not include_non_ok and status and status.lower() != "ok":
                continue

            rows.append(row)

    return fieldnames, rows


def discover_numeric_columns(
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> list[str]:
    numeric_columns: list[str] = []
    for column in fieldnames:
        has_numeric_value = False
        for row in rows:
            if parse_float(row.get(column, "")) is not None:
                has_numeric_value = True
                break
        if has_numeric_value:
            numeric_columns.append(column)

    return numeric_columns


def resolve_target_columns(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    requested_columns: list[str],
    all_columns: bool,
) -> list[str]:
    numeric_columns = discover_numeric_columns(fieldnames, rows)
    numeric_column_set = set(numeric_columns)
    fieldname_set = set(fieldnames)

    if all_columns and requested_columns:
        raise ValueError("Use either --columns or --all-columns, not both.")

    if all_columns:
        if not numeric_columns:
            raise ValueError("No numeric columns with valid values were found in the CSV file.")
        return numeric_columns

    if requested_columns:
        missing_columns = [column for column in requested_columns if column not in fieldname_set]
        if missing_columns:
            raise ValueError(
                "Requested columns were not found in the CSV: "
                + ", ".join(missing_columns)
            )

        non_numeric_columns = [column for column in requested_columns if column not in numeric_column_set]
        if non_numeric_columns:
            raise ValueError(
                "Requested columns do not contain plottable numeric values: "
                + ", ".join(non_numeric_columns)
            )
        return requested_columns

    default_columns = [column for column in TARGET_COLUMNS if column in numeric_column_set]
    if default_columns:
        return default_columns
    if numeric_columns:
        return numeric_columns
    raise ValueError("No numeric columns with valid values were found in the CSV file.")


def load_grouped_metrics(
    rows: list[dict[str, str]],
    target_columns: list[str],
) -> dict[str, dict[str, list[float]]]:
    grouped_metrics = {column: defaultdict(list) for column in target_columns}

    for row in rows:
        speaker_id = extract_speaker_id(row)
        for column in target_columns:
            value = parse_float(row.get(column, ""))
            if value is not None:
                grouped_metrics[column][speaker_id].append(value)

    return grouped_metrics


def speaker_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def build_plot_groups(
    grouped_metric: dict[str, list[float]],
    sort_by_mean: bool = False,
) -> tuple[list[str], list[list[float]]]:
    speakers = [speaker for speaker, values in grouped_metric.items() if values]
    if sort_by_mean:
        speakers.sort(key=lambda speaker: (speaker_mean(grouped_metric[speaker]), speaker_sort_key(speaker)))
    else:
        speakers.sort(key=speaker_sort_key)

    labels = ["Overall"] + speakers

    overall_values: list[float] = []
    for speaker in speakers:
        overall_values.extend(grouped_metric[speaker])

    data = [overall_values] + [grouped_metric[speaker] for speaker in speakers]
    return labels, data


def style_violin_parts(parts: dict[str, object], color: str) -> None:
    for body in parts.get("bodies", []):
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.28)


def highlight_overall_group(axis: plt.Axes, violin: dict[str, object], boxplot: dict[str, object]) -> None:
    axis.axvspan(0.5, 1.5, color="#264653", alpha=0.08, zorder=0)

    violin_bodies = violin.get("bodies", [])
    if violin_bodies:
        violin_bodies[0].set_facecolor("#264653")
        violin_bodies[0].set_edgecolor("#264653")
        violin_bodies[0].set_alpha(0.35)

    boxes = boxplot.get("boxes", [])
    if boxes:
        boxes[0].set_facecolor("#f4f1de")
        boxes[0].set_edgecolor("#264653")
        boxes[0].set_linewidth(1.2)


def draw_distribution_panel(
    axis: plt.Axes,
    grouped_metric: dict[str, list[float]],
    metric_name: str,
    color: str,
    sort_by_mean: bool = False,
    y_limits: tuple[float, float] | None = None,
) -> None:
    if not any(grouped_metric.values()):
        axis.text(0.5, 0.5, "No valid data", ha="center", va="center", fontsize=12)
        axis.set_title(metric_name)
        axis.set_xticks([])
        axis.set_yticks([])
        return

    labels, data = build_plot_groups(grouped_metric, sort_by_mean=sort_by_mean)
    positions = list(range(1, len(labels) + 1))

    violin = axis.violinplot(
        data,
        positions=positions,
        widths=0.9,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )
    style_violin_parts(violin, color)

    boxplot = axis.boxplot(
        data,
        positions=positions,
        widths=0.22,
        patch_artist=True,
        showfliers=True,
        boxprops={"facecolor": "white", "edgecolor": "#222222", "linewidth": 1.0},
        medianprops={"color": "#d1495b", "linewidth": 1.4},
        whiskerprops={"color": "#222222", "linewidth": 1.0},
        capprops={"color": "#222222", "linewidth": 1.0},
        flierprops={
            "marker": "o",
            "markersize": 2.6,
            "markerfacecolor": "#222222",
            "markeredgecolor": "none",
            "alpha": 0.4,
        },
    )
    highlight_overall_group(axis, violin, boxplot)

    tick_labels = []
    for label, values in zip(labels, data, strict=True):
        tick_labels.append(f"{label}\n(n={len(values)})")

    axis.set_xticks(positions)
    axis.set_xticklabels(tick_labels, rotation=60, ha="right")
    for index, tick_label in enumerate(axis.get_xticklabels()):
        if index == 0:
            tick_label.set_color("#264653")
            tick_label.set_fontweight("bold")
    axis.set_ylabel(metric_name)
    if y_limits is None:
        axis.set_ylim(-0.02, 1.02)
    else:
        axis.set_ylim(*y_limits)
    axis.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    axis.set_axisbelow(True)


def resolve_output_base(csv_path: Path, output_arg: str | None) -> tuple[Path, str, str]:
    if output_arg:
        output_path = Path(output_arg).expanduser().resolve()
    else:
        output_path = csv_path.with_name(f"{csv_path.stem}_{DEFAULT_FIGURE_STEM}{DEFAULT_OUTPUT_SUFFIX}")

    suffix = output_path.suffix or DEFAULT_OUTPUT_SUFFIX
    return output_path.parent, output_path.stem, suffix


def sanitize_metric_name(metric_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", metric_name.strip())


def resolve_metric_output_path(
    output_dir: Path,
    output_stem: str,
    output_suffix: str,
    metric_name: str,
    sort_by_mean: bool,
) -> Path:
    metric_slug = sanitize_metric_name(metric_name)
    filename = f"{output_stem}_{metric_slug}"
    if sort_by_mean:
        filename = f"{filename}_{SORTED_FIGURE_SUFFIX}"
    return output_dir / f"{filename}{output_suffix}"


def build_figure_title(csv_path: Path, title_prefix: str | None, metric_name: str) -> str:
    if title_prefix:
        return f"{title_prefix} {metric_name} Speaker-Level Distribution"
    return f"{csv_path.stem} {metric_name} Speaker-Level Distribution"


def pick_metric_color(metric_index: int) -> str:
    palette = matplotlib.colormaps["tab20"]
    return matplotlib.colors.to_hex(palette(metric_index % palette.N))


def infer_y_limits(grouped_metric: dict[str, list[float]], metric_name: str) -> tuple[float, float]:
    if metric_name.endswith("_ratio"):
        return (0.0, 1.02)

    all_values = [value for values in grouped_metric.values() for value in values]
    if not all_values:
        return (-0.02, 1.02)

    min_value = min(all_values)
    max_value = max(all_values)
    if math.isclose(min_value, max_value):
        padding = max(abs(min_value) * 0.05, 1.0)
    else:
        padding = max((max_value - min_value) * 0.08, 1e-6)
    return (min_value - padding, max_value + padding)


def annotate_metric_summary(axis: plt.Axes, grouped_metric: dict[str, list[float]]) -> None:
    all_values = [value for values in grouped_metric.values() for value in values]
    if not all_values:
        return

    summary_text = "\n".join(
        [
            f"overall n = {len(all_values)}",
            f"speakers = {sum(1 for values in grouped_metric.values() if values)}",
            f"mean = {statistics.fmean(all_values):.4g}",
            f"median = {statistics.median(all_values):.4g}",
        ]
    )
    axis.text(
        0.015,
        0.98,
        summary_text,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#8d99ae", "alpha": 0.9},
    )


def render_figure(
    grouped_metric: dict[str, list[float]],
    metric_name: str,
    output_path: Path,
    figure_title: str,
    sort_by_mean: bool,
    color: str,
) -> None:
    speaker_count = max(len(grouped_metric), 1)
    figure_width = max(16.0, min(72.0, speaker_count * 0.7 + 6.0))
    figure, axis = plt.subplots(1, 1, figsize=(figure_width, 6.5), constrained_layout=True)

    y_limits = infer_y_limits(grouped_metric, metric_name)

    draw_distribution_panel(
        axis=axis,
        grouped_metric=grouped_metric,
        metric_name=metric_name,
        color=color,
        sort_by_mean=sort_by_mean,
        y_limits=y_limits,
    )
    annotate_metric_summary(axis, grouped_metric)

    figure.suptitle(figure_title, fontsize=16)
    if sort_by_mean:
        subtitle = "Overall first, remaining speakers sorted by per-speaker mean"
    else:
        subtitle = "Overall first, remaining speakers in speaker ID order"
    axis.set_title(subtitle)
    axis.set_xlabel("Speaker ID")

    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    args = build_parser().parse_args()
    csv_path = Path(args.csv_file).expanduser().resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    fieldnames, rows = load_csv_rows(
        csv_path=csv_path,
        include_non_ok=args.include_non_ok,
    )
    requested_columns = parse_requested_columns(args.columns)
    target_columns = resolve_target_columns(
        fieldnames=fieldnames,
        rows=rows,
        requested_columns=requested_columns,
        all_columns=args.all_columns,
    )
    grouped_metrics = load_grouped_metrics(rows=rows, target_columns=target_columns)

    if not grouped_metrics:
        raise ValueError("No valid metric data found in the CSV file.")

    output_dir, output_stem, output_suffix = resolve_output_base(csv_path, args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for metric_index, column in enumerate(target_columns):
        grouped_metric = grouped_metrics.get(column, {})
        if not any(grouped_metric.values()):
            continue

        figure_title = build_figure_title(csv_path, args.title_prefix, column)
        color = pick_metric_color(metric_index)

        output_path = resolve_metric_output_path(
            output_dir=output_dir,
            output_stem=output_stem,
            output_suffix=output_suffix,
            metric_name=column,
            sort_by_mean=False,
        )
        sorted_output_path = resolve_metric_output_path(
            output_dir=output_dir,
            output_stem=output_stem,
            output_suffix=output_suffix,
            metric_name=column,
            sort_by_mean=True,
        )

        render_figure(
            grouped_metric=grouped_metric,
            metric_name=column,
            output_path=output_path,
            figure_title=figure_title,
            sort_by_mean=False,
            color=color,
        )
        render_figure(
            grouped_metric=grouped_metric,
            metric_name=column,
            output_path=sorted_output_path,
            figure_title=f"{figure_title} (Sorted by Speaker Mean)",
            sort_by_mean=True,
            color=color,
        )

        saved_paths.extend([output_path, sorted_output_path])

    if not saved_paths:
        raise ValueError("No selected columns contained plottable numeric data.")

    print("Plotted columns:", ", ".join(target_columns))
    for saved_path in saved_paths:
        print(f"Saved figure to: {saved_path}")


if __name__ == "__main__":
    main()