from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


TARGET_COLUMNS = (
    "frame_subharmonics_ratio",
    "frame_sidebands_ratio",
)
DEFAULT_FIGURE_STEM = "speaker_ratio_distribution"
SORTED_FIGURE_SUFFIX = "sorted_by_mean"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize speaker-level distributions for frame_subharmonics_ratio and "
            "frame_sidebands_ratio from an analysis CSV."
        )
    )
    parser.add_argument("csv_file", help="Path to the analysis CSV file.")
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional output image path. Defaults to the CSV directory with suffix "
            "'_speaker_ratio_distribution.png'."
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


def load_grouped_metrics(
    csv_path: Path,
    include_non_ok: bool,
) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    grouped_metrics = {column: defaultdict(list) for column in TARGET_COLUMNS}

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, skipinitialspace=True)
        for raw_row in reader:
            row = normalize_row(raw_row)
            status = row.get("status", "")
            if not include_non_ok and status and status.lower() != "ok":
                continue

            speaker_id = extract_speaker_id(row)
            for column in TARGET_COLUMNS:
                value = parse_float(row.get(column, ""))
                if value is not None:
                    grouped_metrics[column][speaker_id].append(value)

    return grouped_metrics["frame_subharmonics_ratio"], grouped_metrics["frame_sidebands_ratio"]


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


def resolve_output_path(csv_path: Path, output_arg: str | None) -> Path:
    if output_arg:
        return Path(output_arg).expanduser().resolve()
    return csv_path.with_name(f"{csv_path.stem}_{DEFAULT_FIGURE_STEM}.png")


def resolve_sorted_output_path(base_output_path: Path) -> Path:
    return base_output_path.with_name(
        f"{base_output_path.stem}_{SORTED_FIGURE_SUFFIX}{base_output_path.suffix}"
    )


def build_figure_title(csv_path: Path, title_prefix: str | None) -> str:
    if title_prefix:
        return f"{title_prefix} Speaker-Level Frame Ratio Distribution"
    return f"{csv_path.stem} Speaker-Level Frame Ratio Distribution"


def render_figure(
    grouped_subharmonics: dict[str, list[float]],
    grouped_sidebands: dict[str, list[float]],
    output_path: Path,
    figure_title: str,
    sort_by_mean: bool,
) -> None:
    speaker_count = max(len(grouped_subharmonics), len(grouped_sidebands), 1)
    figure_width = max(14.0, min(36.0, speaker_count * 0.45 + 4.0))
    figure, axes = plt.subplots(2, 1, figsize=(figure_width, 12), constrained_layout=True)

    draw_distribution_panel(
        axis=axes[0],
        grouped_metric=grouped_subharmonics,
        metric_name="frame_subharmonics_ratio",
        color="#2a9d8f",
        sort_by_mean=sort_by_mean,
        y_limits=(0.0, 0.6),
    )
    draw_distribution_panel(
        axis=axes[1],
        grouped_metric=grouped_sidebands,
        metric_name="frame_sidebands_ratio",
        color="#e76f51",
        sort_by_mean=sort_by_mean,
    )

    figure.suptitle(figure_title, fontsize=16)
    if sort_by_mean:
        subtitle = "Overall first, remaining speakers sorted by per-speaker mean"
    else:
        subtitle = "Overall first, remaining speakers in speaker ID order"
    axes[0].set_title(subtitle)
    axes[1].set_title(subtitle)
    axes[1].set_xlabel("Speaker ID")

    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    args = build_parser().parse_args()
    csv_path = Path(args.csv_file).expanduser().resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    grouped_subharmonics, grouped_sidebands = load_grouped_metrics(
        csv_path=csv_path,
        include_non_ok=args.include_non_ok,
    )

    if not grouped_subharmonics and not grouped_sidebands:
        raise ValueError("No valid metric data found in the CSV file.")

    output_path = resolve_output_path(csv_path, args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_output_path = resolve_sorted_output_path(output_path)
    figure_title = build_figure_title(csv_path, args.title_prefix)

    render_figure(
        grouped_subharmonics=grouped_subharmonics,
        grouped_sidebands=grouped_sidebands,
        output_path=output_path,
        figure_title=figure_title,
        sort_by_mean=False,
    )
    render_figure(
        grouped_subharmonics=grouped_subharmonics,
        grouped_sidebands=grouped_sidebands,
        output_path=sorted_output_path,
        figure_title=f"{figure_title} (Sorted by Speaker Mean)",
        sort_by_mean=True,
    )

    print(f"Saved figure to: {output_path}")
    print(f"Saved figure to: {sorted_output_path}")


if __name__ == "__main__":
    main()