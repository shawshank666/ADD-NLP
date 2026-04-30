from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


SUPPORTED_AUDIO_SUFFIXES = (".wav", ".flac", ".mp3", ".ogg", ".m4a")
LABEL_SLUGS = {
    "None": "none",
    "Unvoiced": "unvoiced",
    "Subharmonics": "subharmonics",
    "Sidebands": "sidebands",
    "Chaos": "chaos",
    "Frequency jump": "frequency_jump",
}
LABEL_ORDER = list(LABEL_SLUGS.keys())

AUDIO_STATS_BASE_FIELDS = [
    "source_audio",
    "relative_audio",
    "status",
    "error",
    "duration_ms",
    "frame_count",
    "segment_count",
    "voiced_frame_count",
    "voiced_frame_ratio",
    "dominant_frame_label",
    "dominant_segment_label",
    "subharmonics_candidate_count",
    "sidebands_candidate_count",
    "chaos_candidate_count",
    "frequency_jump_candidate_count",
    "mean_ampl",
    "mean_pitch_voiced",
    "mean_amEnvDep",
    "mean_amMsPurity",
    "mean_HNR",
    "mean_roughness",
    "mean_entropy",
    "mean_subDep",
    "median_ampl",
    "median_pitch_voiced",
    "median_amEnvDep",
    "median_amMsPurity",
    "median_HNR",
    "median_roughness",
    "median_entropy",
    "median_subDep",
]
AUDIO_STATS_INT_FIELDS = {
    "frame_count",
    "segment_count",
    "voiced_frame_count",
    "subharmonics_candidate_count",
    "sidebands_candidate_count",
    "chaos_candidate_count",
    "frequency_jump_candidate_count",
}
AUDIO_STATS_FLOAT_FIELDS = {
    "duration_ms",
    "voiced_frame_ratio",
    "mean_ampl",
    "mean_pitch_voiced",
    "mean_amEnvDep",
    "mean_amMsPurity",
    "mean_HNR",
    "mean_roughness",
    "mean_entropy",
    "mean_subDep",
    "median_ampl",
    "median_pitch_voiced",
    "median_amEnvDep",
    "median_amMsPurity",
    "median_HNR",
    "median_roughness",
    "median_entropy",
    "median_subDep",
}


R_ANALYSIS_SCRIPT = r'''
options(warn = 1)
suppressPackageStartupMessages(library(soundgen))

args <- commandArgs(trailingOnly = TRUE)

input_path <- args[[1]]
frames_csv <- args[[2]]
window_length <- as.numeric(args[[3]])
step_size <- as.numeric(args[[4]])
am_low <- as.numeric(args[[5]])
am_high <- as.numeric(args[[6]])
jump_thres <- as.numeric(args[[7]])
jump_window <- as.numeric(args[[8]])
subdep_thres <- as.numeric(args[[9]])
amenv_thres <- as.numeric(args[[10]])
amms_thres <- as.numeric(args[[11]])
hnr_thres <- as.numeric(args[[12]])
roughness_thres <- as.numeric(args[[13]])
entropy_thres <- as.numeric(args[[14]])

analysis <- analyze(
  input_path,
  windowLength = window_length,
  step = step_size,
  silence = 0,
  amRange = c(am_low, am_high),
  roughness = list(
    msType = '1D',
    windowLength = 25,
    step = 0.25,
    amRes = NULL,
    roughRange = NULL,
    roughMean = 100,
    roughSD = 8
  ),
  formants = 0,
  novelty = NULL,
  loudness = NULL
)

detailed <- analysis$detailed
if (is.null(detailed) || nrow(detailed) == 0) {
  stop('analyze() returned no frame-level output for the input audio.')
}

if (!('time' %in% names(detailed))) {
  stop('analyze() output does not contain a time column.')
}

if (!('voiced' %in% names(detailed))) detailed$voiced <- FALSE
if (!('ampl' %in% names(detailed))) detailed$ampl <- NA_real_
if (!('pitch' %in% names(detailed))) detailed$pitch <- NA_real_
if (!('amEnvDep' %in% names(detailed))) detailed$amEnvDep <- NA_real_
if (!('amMsPurity' %in% names(detailed))) detailed$amMsPurity <- NA_real_
if (!('HNR' %in% names(detailed))) detailed$HNR <- NA_real_
if (!('roughness' %in% names(detailed))) detailed$roughness <- NA_real_
if (!('entropy' %in% names(detailed))) detailed$entropy <- NA_real_
if (!('subDep' %in% names(detailed))) detailed$subDep <- NA_real_

step_ms <- step_size
if (nrow(detailed) >= 2) {
  step_ms <- detailed$time[2] - detailed$time[1]
}

frame_start_ms <- pmax(0, detailed$time - step_ms)
frame_end_ms <- detailed$time

jump_candidate <- rep(FALSE, nrow(detailed))
if (sum(is.finite(detailed$pitch)) >= 3) {
  jumps <- soundgen:::findJumps(
    pitch = detailed$pitch,
    step = step_ms,
    jumpThres = jump_thres,
    jumpWindow = jump_window
  )
  if (length(jumps) == nrow(detailed)) {
    jump_candidate <- as.logical(jumps)
  }
}

subharmonics_candidate <- !is.na(detailed$subDep) & detailed$subDep >= subdep_thres
sidebands_candidate <-
  (!is.na(detailed$amEnvDep) & detailed$amEnvDep >= amenv_thres) |
  (!is.na(detailed$amMsPurity) & detailed$amMsPurity >= amms_thres)
chaos_candidate <-
  (!is.na(detailed$HNR) & detailed$HNR <= hnr_thres) &
  (
    (!is.na(detailed$roughness) & detailed$roughness >= roughness_thres) |
    (!is.na(detailed$entropy) & detailed$entropy >= entropy_thres)
  )

heuristic_label <- rep('None', nrow(detailed))
unvoiced_idx <- is.na(detailed$voiced) | !detailed$voiced
heuristic_label[unvoiced_idx] <- 'Unvoiced'
heuristic_label[chaos_candidate & !unvoiced_idx] <- 'Chaos'
heuristic_label[sidebands_candidate & !unvoiced_idx] <- 'Sidebands'
heuristic_label[jump_candidate & !unvoiced_idx] <- 'Frequency jump'
heuristic_label[subharmonics_candidate & !unvoiced_idx] <- 'Subharmonics'

out <- data.frame(
  frame_index = seq_len(nrow(detailed)),
  time_start_ms = frame_start_ms,
  time_end_ms = frame_end_ms,
  voiced = detailed$voiced,
  ampl = detailed$ampl,
  pitch = detailed$pitch,
  amEnvDep = detailed$amEnvDep,
  amMsPurity = detailed$amMsPurity,
  HNR = detailed$HNR,
  roughness = detailed$roughness,
  entropy = detailed$entropy,
  subDep = detailed$subDep,
  subharmonics_candidate = subharmonics_candidate,
  sidebands_candidate = sidebands_candidate,
  chaos_candidate = chaos_candidate,
  frequency_jump_candidate = jump_candidate,
  heuristic_label = heuristic_label,
  stringsAsFactors = FALSE
)

write.csv(out, frames_csv, row.names = FALSE)
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run heuristic NLP analysis for one audio file or a whole directory tree. "
            "Batch mode stores one CSV row per audio by default."
        )
    )
    parser.add_argument("audio", help="Path to an input audio file or dataset directory.")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Directory used to store output files. Defaults to VoiceDeepfake/results.",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help=(
            "Optional output prefix. For a single file it changes the file stem; "
            "for a directory it changes the batch CSV and summary file names."
        ),
    )
    parser.add_argument(
        "--extensions",
        default=",".join(SUPPORTED_AUDIO_SUFFIXES),
        help="Comma-separated audio suffixes for directory scans, for example .wav,.flac",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of files to process when the input is a directory.",
    )
    parser.add_argument(
        "--keep-detailed-files",
        action="store_true",
        help=(
            "In batch mode also persist per-audio frame, segment, and markdown files. "
            "By default batch mode only writes one consolidated CSV and one batch summary."
        ),
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help=(
            "In batch mode, skip items already recorded in the consolidated stats CSV. "
            "When used with --keep-detailed-files, detailed outputs can also be reused."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on the first file that fails during batch processing.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help=(
            "Number of audio files to analyze in parallel during batch processing. "
            "Use 1 for sequential mode."
        ),
    )
    parser.add_argument("--window-length", type=float, default=50.0)
    parser.add_argument("--step", type=float, default=25.0)
    parser.add_argument("--am-low", type=float, default=40.0)
    parser.add_argument("--am-high", type=float, default=150.0)
    parser.add_argument("--jump-thres", type=float, default=14.0)
    parser.add_argument("--jump-window", type=float, default=100.0)
    parser.add_argument("--subdep-thres", type=float, default=0.12)
    parser.add_argument("--amenv-thres", type=float, default=0.18)
    parser.add_argument("--amms-thres", type=float, default=0.18)
    parser.add_argument("--hnr-thres", type=float, default=5.0)
    parser.add_argument("--roughness-thres", type=float, default=25.0)
    parser.add_argument("--entropy-thres", type=float, default=0.7)
    return parser


def ensure_rscript() -> str:
    rscript_path = shutil.which("Rscript")
    if rscript_path is None:
        raise SystemExit(
            "Rscript is not available. Activate the conda environment with R and soundgen first."
        )
    return rscript_path


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "t", "1"}


def parse_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    text = str(value).strip()
    if text == "" or text.upper() == "NA":
        return None
    return float(text)


def parse_extensions(text: str) -> tuple[str, ...]:
    items = []
    for raw_item in text.split(","):
        item = raw_item.strip().lower()
        if not item:
            continue
        if not item.startswith("."):
            item = f".{item}"
        items.append(item)
    return tuple(dict.fromkeys(items)) or SUPPORTED_AUDIO_SUFFIXES


def iter_audio_files(root: Path, suffixes: tuple[str, ...], limit: int | None) -> list[Path]:
    files: list[Path] = []
    for current_root, _, filenames in os.walk(root, followlinks=True):
        current_root_path = Path(current_root)
        for filename in filenames:
            path = current_root_path / filename
            if path.suffix.lower() in suffixes:
                files.append(path)
    files.sort()
    if limit is not None:
        files = files[:limit]
    return files


def load_frames_csv(path: Path) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            frames.append(
                {
                    "frame_index": int(float(row["frame_index"])),
                    "time_start_ms": parse_float(row["time_start_ms"]) or 0.0,
                    "time_end_ms": parse_float(row["time_end_ms"]) or 0.0,
                    "voiced": parse_bool(row["voiced"]),
                    "ampl": parse_float(row["ampl"]),
                    "pitch": parse_float(row["pitch"]),
                    "amEnvDep": parse_float(row["amEnvDep"]),
                    "amMsPurity": parse_float(row["amMsPurity"]),
                    "HNR": parse_float(row["HNR"]),
                    "roughness": parse_float(row["roughness"]),
                    "entropy": parse_float(row["entropy"]),
                    "subDep": parse_float(row["subDep"]),
                    "subharmonics_candidate": parse_bool(row["subharmonics_candidate"]),
                    "sidebands_candidate": parse_bool(row["sidebands_candidate"]),
                    "chaos_candidate": parse_bool(row["chaos_candidate"]),
                    "frequency_jump_candidate": parse_bool(row["frequency_jump_candidate"]),
                    "heuristic_label": row["heuristic_label"],
                }
            )
    return frames


def build_segments(frames: list[dict[str, Any]], gap_tolerance_ms: float) -> list[dict[str, Any]]:
    if not frames:
        return []

    segments: list[dict[str, Any]] = []
    current = {
        "label": frames[0]["heuristic_label"],
        "start_ms": frames[0]["time_start_ms"],
        "end_ms": frames[0]["time_end_ms"],
        "frame_count": 1,
    }

    for frame in frames[1:]:
        same_label = frame["heuristic_label"] == current["label"]
        contiguous = frame["time_start_ms"] <= current["end_ms"] + gap_tolerance_ms
        if same_label and contiguous:
            current["end_ms"] = frame["time_end_ms"]
            current["frame_count"] += 1
            continue

        current["duration_ms"] = current["end_ms"] - current["start_ms"]
        segments.append(current)
        current = {
            "label": frame["heuristic_label"],
            "start_ms": frame["time_start_ms"],
            "end_ms": frame["time_end_ms"],
            "frame_count": 1,
        }

    current["duration_ms"] = current["end_ms"] - current["start_ms"]
    segments.append(current)
    return segments


def write_segments_csv(path: Path, segments: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["label", "start_ms", "end_ms", "duration_ms", "frame_count"],
        )
        writer.writeheader()
        writer.writerows(segments)


def format_ms(ms: float) -> str:
    seconds = max(ms, 0.0) / 1000.0
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    if minutes:
        return f"{minutes}m {remainder:.2f}s"
    return f"{remainder:.2f}s"


def safe_mean(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None and math.isfinite(value)]
    if not filtered:
        return None
    return float(statistics.fmean(filtered))


def safe_median(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None and math.isfinite(value)]
    if not filtered:
        return None
    return float(statistics.median(filtered))


def count_true(frames: list[dict[str, Any]], key: str) -> int:
    return sum(1 for frame in frames if frame.get(key))


def dominant_label(counter: Counter[str]) -> str:
    if not counter:
        return ""
    return max(counter.items(), key=lambda item: item[1])[0]


def build_summary_markdown(
    audio_path: Path,
    frames_path: Path,
    segments_path: Path,
    frames: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    args: argparse.Namespace,
) -> str:
    label_counts = Counter(frame["heuristic_label"] for frame in frames)
    segment_counts = Counter(segment["label"] for segment in segments)
    total_duration_ms = frames[-1]["time_end_ms"] if frames else 0.0
    top_segments = sorted(segments, key=lambda item: item["duration_ms"], reverse=True)[:10]

    lines = [
        "# NLP Analysis Test Report",
        "",
        "## Input",
        "",
        f"- Audio: {audio_path}",
        f"- Approximate duration: {format_ms(total_duration_ms)}",
        f"- Frame count: {len(frames)}",
        f"- Segment count: {len(segments)}",
        "",
        "## Heuristic Settings",
        "",
        f"- window_length: {args.window_length}",
        f"- step: {args.step}",
        f"- am_range: [{args.am_low}, {args.am_high}]",
        f"- jump_thres: {args.jump_thres}",
        f"- jump_window: {args.jump_window}",
        f"- subdep_thres: {args.subdep_thres}",
        f"- amenv_thres: {args.amenv_thres}",
        f"- amms_thres: {args.amms_thres}",
        f"- hnr_thres: {args.hnr_thres}",
        f"- roughness_thres: {args.roughness_thres}",
        f"- entropy_thres: {args.entropy_thres}",
        "",
        "## Frame Label Counts",
        "",
    ]

    for label, count in sorted(label_counts.items()):
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Segment Counts", ""])
    for label, count in sorted(segment_counts.items()):
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Longest Segments", ""])
    if top_segments:
        for segment in top_segments:
            lines.append(
                "- "
                f"{segment['label']}: {segment['start_ms']:.1f} ms -> {segment['end_ms']:.1f} ms "
                f"({format_ms(segment['duration_ms'])}, {segment['frame_count']} frames)"
            )
    else:
        lines.append("- No segments were generated.")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Frames CSV: {frames_path}",
            f"- Segments CSV: {segments_path}",
            "",
            "## Notes",
            "",
            "- heuristic_label is a rule-based candidate label, not a manually verified final annotation.",
            "- This task depends on Rscript and the R package soundgen.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_r_analysis(args: argparse.Namespace, audio_path: Path, frames_path: Path) -> None:
    rscript_path = ensure_rscript()
    with tempfile.NamedTemporaryFile("w", suffix=".R", encoding="utf-8", delete=False) as handle:
        handle.write(R_ANALYSIS_SCRIPT)
        script_path = Path(handle.name)

    prepared_audio_path = audio_path
    temp_audio_path: Path | None = None
    if audio_path.suffix.lower() not in {".wav", ".mp3"}:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise RuntimeError(
                f"ffmpeg is required to convert {audio_path.suffix} inputs into wav for R analysis."
            )
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            temp_audio_path = Path(handle.name)
        convert = subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(audio_path),
                "-acodec",
                "pcm_s16le",
                str(temp_audio_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if convert.returncode != 0:
            temp_audio_path.unlink(missing_ok=True)
            message = convert.stderr.strip() or convert.stdout.strip() or "Unknown ffmpeg error"
            raise RuntimeError(f"Audio conversion failed: {message}")
        prepared_audio_path = temp_audio_path

    command = [
        rscript_path,
        str(script_path),
        str(prepared_audio_path),
        str(frames_path),
        str(args.window_length),
        str(args.step),
        str(args.am_low),
        str(args.am_high),
        str(args.jump_thres),
        str(args.jump_window),
        str(args.subdep_thres),
        str(args.amenv_thres),
        str(args.amms_thres),
        str(args.hnr_thres),
        str(args.roughness_thres),
        str(args.entropy_thres),
    ]

    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    finally:
        script_path.unlink(missing_ok=True)
        if temp_audio_path is not None:
            temp_audio_path.unlink(missing_ok=True)

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Unknown R error"
        raise RuntimeError(f"R analysis failed: {message}")


def make_output_paths(results_dir: Path, prefix: str) -> tuple[Path, Path, Path]:
    frames_path = results_dir / f"{prefix}_nlp_frames.csv"
    segments_path = results_dir / f"{prefix}_nlp_segments.csv"
    summary_path = results_dir / f"{prefix}_nlp_summary.md"
    return frames_path, segments_path, summary_path


def build_audio_stats_fieldnames() -> list[str]:
    label_fields = []
    for label in LABEL_ORDER:
        slug = LABEL_SLUGS[label]
        label_fields.extend(
            [f"frame_{slug}_count", f"frame_{slug}_ratio", f"segment_{slug}_count"]
        )
    return AUDIO_STATS_BASE_FIELDS + label_fields


AUDIO_STATS_FIELDNAMES = build_audio_stats_fieldnames()
for label in LABEL_ORDER:
    slug = LABEL_SLUGS[label]
    AUDIO_STATS_INT_FIELDS.update({f"frame_{slug}_count", f"segment_{slug}_count"})
    AUDIO_STATS_FLOAT_FIELDS.add(f"frame_{slug}_ratio")


def build_audio_stats_row(
    audio_path: Path,
    relative_audio: str,
    frames: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    status: str,
    error: str = "",
) -> dict[str, Any]:
    frame_counts = Counter(frame["heuristic_label"] for frame in frames)
    segment_counts = Counter(segment["label"] for segment in segments)
    frame_count = len(frames)
    segment_count = len(segments)
    duration_ms = frames[-1]["time_end_ms"] if frames else 0.0
    voiced_frame_count = sum(1 for frame in frames if frame["voiced"])

    row: dict[str, Any] = {
        "source_audio": str(audio_path),
        "relative_audio": relative_audio,
        "status": status,
        "error": error,
        "duration_ms": duration_ms,
        "frame_count": frame_count,
        "segment_count": segment_count,
        "voiced_frame_count": voiced_frame_count,
        "voiced_frame_ratio": (voiced_frame_count / frame_count) if frame_count else 0.0,
        "dominant_frame_label": dominant_label(frame_counts),
        "dominant_segment_label": dominant_label(segment_counts),
        "subharmonics_candidate_count": count_true(frames, "subharmonics_candidate"),
        "sidebands_candidate_count": count_true(frames, "sidebands_candidate"),
        "chaos_candidate_count": count_true(frames, "chaos_candidate"),
        "frequency_jump_candidate_count": count_true(frames, "frequency_jump_candidate"),
        "mean_ampl": safe_mean([frame["ampl"] for frame in frames]),
        "mean_pitch_voiced": safe_mean([frame["pitch"] for frame in frames if frame["voiced"]]),
        "mean_amEnvDep": safe_mean([frame["amEnvDep"] for frame in frames]),
        "mean_amMsPurity": safe_mean([frame["amMsPurity"] for frame in frames]),
        "mean_HNR": safe_mean([frame["HNR"] for frame in frames]),
        "mean_roughness": safe_mean([frame["roughness"] for frame in frames]),
        "mean_entropy": safe_mean([frame["entropy"] for frame in frames]),
        "mean_subDep": safe_mean([frame["subDep"] for frame in frames]),
        "median_ampl": safe_median([frame["ampl"] for frame in frames]),
        "median_pitch_voiced": safe_median([frame["pitch"] for frame in frames if frame["voiced"]]),
        "median_amEnvDep": safe_median([frame["amEnvDep"] for frame in frames]),
        "median_amMsPurity": safe_median([frame["amMsPurity"] for frame in frames]),
        "median_HNR": safe_median([frame["HNR"] for frame in frames]),
        "median_roughness": safe_median([frame["roughness"] for frame in frames]),
        "median_entropy": safe_median([frame["entropy"] for frame in frames]),
        "median_subDep": safe_median([frame["subDep"] for frame in frames]),
    }

    for label in LABEL_ORDER:
        slug = LABEL_SLUGS[label]
        frame_label_count = frame_counts.get(label, 0)
        segment_label_count = segment_counts.get(label, 0)
        row[f"frame_{slug}_count"] = frame_label_count
        row[f"frame_{slug}_ratio"] = (frame_label_count / frame_count) if frame_count else 0.0
        row[f"segment_{slug}_count"] = segment_label_count
    return row


def analyze_audio(
    args: argparse.Namespace,
    audio_path: Path,
    relative_audio: str,
    detailed_dir: Path | None,
) -> dict[str, Any]:
    if detailed_dir is not None:
        detailed_dir.mkdir(parents=True, exist_ok=True)
        frames_path, segments_path, summary_path = make_output_paths(detailed_dir, audio_path.stem)
        if args.skip_existing and frames_path.exists() and segments_path.exists() and summary_path.exists():
            frames = load_frames_csv(frames_path)
            segments = load_segments_csv(segments_path)
            return build_audio_stats_row(audio_path, relative_audio, frames, segments, status="skipped")
    else:
        frames_temp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        frames_temp.close()
        frames_path = Path(frames_temp.name)
        segments_path = Path(tempfile.mkstemp(suffix=".csv")[1])
        summary_path = Path(tempfile.mkstemp(suffix=".md")[1])

    try:
        run_r_analysis(args, audio_path, frames_path)
        frames = load_frames_csv(frames_path)
        segments = build_segments(frames, gap_tolerance_ms=max(args.step * 0.5, 1.0))
        write_segments_csv(segments_path, segments)
        if detailed_dir is not None:
            summary = build_summary_markdown(
                audio_path=audio_path,
                frames_path=frames_path,
                segments_path=segments_path,
                frames=frames,
                segments=segments,
                args=args,
            )
            summary_path.write_text(summary, encoding="utf-8")
        return build_audio_stats_row(audio_path, relative_audio, frames, segments, status="ok")
    finally:
        if detailed_dir is None:
            frames_path.unlink(missing_ok=True)
            segments_path.unlink(missing_ok=True)
            summary_path.unlink(missing_ok=True)


def build_failed_row(audio_path: Path, relative_audio: str, error: str) -> dict[str, Any]:
    row = {
        "source_audio": str(audio_path),
        "relative_audio": relative_audio,
        "status": "failed",
        "error": error,
        "duration_ms": 0.0,
        "frame_count": 0,
        "segment_count": 0,
        "voiced_frame_count": 0,
        "voiced_frame_ratio": 0.0,
        "dominant_frame_label": "",
        "dominant_segment_label": "",
        "subharmonics_candidate_count": 0,
        "sidebands_candidate_count": 0,
        "chaos_candidate_count": 0,
        "frequency_jump_candidate_count": 0,
        "mean_ampl": None,
        "mean_pitch_voiced": None,
        "mean_amEnvDep": None,
        "mean_amMsPurity": None,
        "mean_HNR": None,
        "mean_roughness": None,
        "mean_entropy": None,
        "mean_subDep": None,
        "median_ampl": None,
        "median_pitch_voiced": None,
        "median_amEnvDep": None,
        "median_amMsPurity": None,
        "median_HNR": None,
        "median_roughness": None,
        "median_entropy": None,
        "median_subDep": None,
    }
    for label in LABEL_ORDER:
        slug = LABEL_SLUGS[label]
        row[f"frame_{slug}_count"] = 0
        row[f"frame_{slug}_ratio"] = 0.0
        row[f"segment_{slug}_count"] = 0
    return row


def run_batch_job(
    args: argparse.Namespace,
    audio_path: Path,
    relative_audio: str,
    detailed_dir: Path | None,
) -> dict[str, Any]:
    return analyze_audio(args, audio_path, relative_audio, detailed_dir)


def load_segments_csv(path: Path) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            segments.append(
                {
                    "label": row["label"],
                    "start_ms": parse_float(row["start_ms"]) or 0.0,
                    "end_ms": parse_float(row["end_ms"]) or 0.0,
                    "duration_ms": parse_float(row["duration_ms"]) or 0.0,
                    "frame_count": int(float(row["frame_count"])),
                }
            )
    return segments


def load_audio_stats_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            # Be tolerant of legacy CSVs whose headers/values include padding spaces.
            normalized_row = {
                (key.strip() if isinstance(key, str) else key): (
                    value.strip() if isinstance(value, str) else value
                )
                for key, value in raw_row.items()
            }
            row: dict[str, Any] = {}
            for field in AUDIO_STATS_FIELDNAMES:
                value = normalized_row.get(field, "")
                if field in {"source_audio", "relative_audio", "status", "error"}:
                    row[field] = value or ""
                elif field in {"dominant_frame_label", "dominant_segment_label"}:
                    row[field] = value or ""
                elif field in AUDIO_STATS_INT_FIELDS:
                    row[field] = int(float(value)) if value not in {"", None} else 0
                elif field in AUDIO_STATS_FLOAT_FIELDS:
                    row[field] = parse_float(value)
                else:
                    row[field] = value
            rows.append(row)
    return rows


def append_audio_stats_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIO_STATS_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def write_audio_stats_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIO_STATS_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_batch_summary_markdown(
    input_dir: Path,
    stats_csv_path: Path,
    rows: list[dict[str, Any]],
    suffixes: tuple[str, ...],
) -> str:
    ok_rows = [row for row in rows if row["status"] in {"ok", "skipped"}]
    failed_rows = [row for row in rows if row["status"] == "failed"]

    frame_counter: Counter[str] = Counter()
    segment_counter: Counter[str] = Counter()
    total_duration_ms = 0.0
    for row in ok_rows:
        total_duration_ms += float(row.get("duration_ms") or 0.0)
        for label in LABEL_ORDER:
            slug = LABEL_SLUGS[label]
            frame_counter[label] += int(row.get(f"frame_{slug}_count") or 0)
            segment_counter[label] += int(row.get(f"segment_{slug}_count") or 0)

    lines = [
        "# Batch NLP Analysis Report",
        "",
        "## Batch Info",
        "",
        f"- Input directory: {input_dir}",
        f"- Stats CSV: {stats_csv_path}",
        f"- Audio suffixes: {', '.join(suffixes)}",
        f"- Files discovered: {len(rows)}",
        f"- Successful or reused: {len(ok_rows)}",
        f"- Failed: {len(failed_rows)}",
        f"- Approximate analyzed duration: {format_ms(total_duration_ms)}",
        "",
        "## Aggregate Frame Labels",
        "",
    ]

    if frame_counter:
        for label, count in frame_counter.items():
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- No successful frame outputs.")

    lines.extend(["", "## Aggregate Segment Labels", ""])
    if segment_counter:
        for label, count in segment_counter.items():
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- No successful segment outputs.")

    lines.extend(["", "## Failures", ""])
    if failed_rows:
        for row in failed_rows[:20]:
            lines.append(f"- {row['relative_audio']}: {row['error']}")
        if len(failed_rows) > 20:
            lines.append(f"- Additional failures omitted: {len(failed_rows) - 20}")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def resolve_batch_results_dir(
    base_results_dir: Path,
    batch_name: str,
    explicit_results_dir: bool,
) -> Path:
    if explicit_results_dir:
        return base_results_dir
    return base_results_dir / "NLPanalysis" / batch_name


def process_batch(
    args: argparse.Namespace,
    input_dir: Path,
    results_dir: Path,
    explicit_results_dir: bool,
) -> int:
    suffixes = parse_extensions(args.extensions)
    audio_files = iter_audio_files(input_dir, suffixes=suffixes, limit=args.limit)
    if not audio_files:
        raise SystemExit(
            f"No audio files found under {input_dir} for suffixes: {', '.join(suffixes)}"
        )

    batch_name = args.prefix or input_dir.name
    batch_results_dir = resolve_batch_results_dir(results_dir, batch_name, explicit_results_dir)
    batch_results_dir.mkdir(parents=True, exist_ok=True)
    stats_csv_path = batch_results_dir / "audio_stats.csv"
    batch_summary_path = batch_results_dir / "batch_summary.md"
    detailed_root = batch_results_dir / "details" if args.keep_detailed_files else None
    ordered_relatives = [audio_path.relative_to(input_dir).as_posix() for audio_path in audio_files]

    existing_rows_by_relative: dict[str, dict[str, Any]] = {}
    if args.skip_existing and stats_csv_path.exists():
        for row in load_audio_stats_csv(stats_csv_path):
            relative_audio = str(row.get("relative_audio") or "").strip()
            if relative_audio:
                existing_rows_by_relative[relative_audio] = row
        if existing_rows_by_relative:
            print(
                f"Resuming from existing stats CSV: {stats_csv_path} "
                f"({len(existing_rows_by_relative)} recorded items)"
            , flush=True)
    elif stats_csv_path.exists():
        stats_csv_path.unlink(missing_ok=True)

    jobs = []
    for index, audio_path in enumerate(audio_files, start=1):
        relative_audio_path = audio_path.relative_to(input_dir)
        relative_audio = relative_audio_path.as_posix()
        if args.skip_existing and relative_audio in existing_rows_by_relative:
            continue
        detailed_dir = detailed_root / relative_audio_path.parent if detailed_root is not None else None
        pending_slot = len(jobs)
        jobs.append((pending_slot, index, audio_path, relative_audio, detailed_dir))

    rows: list[dict[str, Any] | None] = [None] * len(jobs)
    max_workers = max(1, args.jobs)
    newly_written_count = 0

    if not jobs:
        final_rows = [
            existing_rows_by_relative[relative_audio]
            for relative_audio in ordered_relatives
            if relative_audio in existing_rows_by_relative
        ]
        batch_summary = build_batch_summary_markdown(input_dir, stats_csv_path, final_rows, suffixes)
        batch_summary_path.write_text(batch_summary, encoding="utf-8")
        failed_count = sum(row["status"] == "failed" for row in final_rows)
        print(f"Audio stats CSV: {stats_csv_path}", flush=True)
        print(f"Batch summary MD: {batch_summary_path}", flush=True)
        print(
            f"All discovered files were already recorded in the stats CSV: {len(final_rows)} items reused."
        , flush=True)
        return 0 if failed_count == 0 else 1

    if max_workers == 1:
        for pending_slot, index, audio_path, relative_audio, detailed_dir in jobs:
            print(f"[{index}/{len(audio_files)}] {relative_audio}", flush=True)
            try:
                row = run_batch_job(args, audio_path, relative_audio, detailed_dir)
                print(f"  {row['status'].upper()}", flush=True)
            except Exception as exc:
                row = build_failed_row(audio_path, relative_audio, str(exc))
                print(f"  FAILED: {exc}", flush=True)
                rows[pending_slot] = row
                if args.fail_fast:
                    break
            rows[pending_slot] = row
            append_audio_stats_row(stats_csv_path, row)
            newly_written_count += 1
    else:
        print(
            f"Running batch analysis with {max_workers} parallel jobs on CPU "
            f"(host cores: {os.cpu_count() or 'unknown'})."
        , flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(run_batch_job, args, audio_path, relative_audio, detailed_dir): (
                    pending_slot,
                    index,
                    audio_path,
                    relative_audio,
                )
                for pending_slot, index, audio_path, relative_audio, detailed_dir in jobs
            }
            for future in concurrent.futures.as_completed(future_to_job):
                pending_slot, index, audio_path, relative_audio = future_to_job[future]
                try:
                    row = future.result()
                    print(f"[{index}/{len(audio_files)}] {relative_audio}", flush=True)
                    print(f"  {row['status'].upper()}", flush=True)
                except Exception as exc:
                    row = build_failed_row(audio_path, relative_audio, str(exc))
                    print(f"[{index}/{len(audio_files)}] {relative_audio}", flush=True)
                    print(f"  FAILED: {exc}", flush=True)
                    if args.fail_fast:
                        for pending_future in future_to_job:
                            pending_future.cancel()
                        rows[pending_slot] = row
                        append_audio_stats_row(stats_csv_path, row)
                        newly_written_count += 1
                        break
                rows[pending_slot] = row
                append_audio_stats_row(stats_csv_path, row)
                newly_written_count += 1

    new_rows = [row for row in rows if row is not None]
    final_rows_by_relative = dict(existing_rows_by_relative)
    for row in new_rows:
        final_rows_by_relative[row["relative_audio"]] = row

    final_rows = [
        final_rows_by_relative[relative_audio]
        for relative_audio in ordered_relatives
        if relative_audio in final_rows_by_relative
    ]
    extra_relatives = sorted(
        relative_audio
        for relative_audio in final_rows_by_relative
        if relative_audio not in set(ordered_relatives)
    )
    final_rows.extend(final_rows_by_relative[relative_audio] for relative_audio in extra_relatives)

    write_audio_stats_csv(stats_csv_path, final_rows)
    batch_summary = build_batch_summary_markdown(input_dir, stats_csv_path, final_rows, suffixes)
    batch_summary_path.write_text(batch_summary, encoding="utf-8")

    ok_count = sum(row["status"] in {"ok", "skipped"} for row in final_rows)
    failed_count = sum(row["status"] == "failed" for row in final_rows)
    reused_count = len(existing_rows_by_relative)
    print(f"Audio stats CSV: {stats_csv_path}", flush=True)
    print(f"Batch summary MD: {batch_summary_path}", flush=True)
    print(
        f"Discovered files: {len(audio_files)} | Newly processed this run: {newly_written_count} | "
        f"Reused from prior CSV: {reused_count}"
    , flush=True)
    print(f"Successful or reused: {ok_count} | Failed: {failed_count}", flush=True)
    return 0 if failed_count == 0 else 1


def process_single(args: argparse.Namespace, input_path: Path, results_dir: Path) -> int:
    prefix = args.prefix or input_path.stem
    frames_path, segments_path, summary_path = make_output_paths(results_dir, prefix)
    run_r_analysis(args, input_path, frames_path)
    frames = load_frames_csv(frames_path)
    segments = build_segments(frames, gap_tolerance_ms=max(args.step * 0.5, 1.0))
    write_segments_csv(segments_path, segments)
    summary = build_summary_markdown(
        audio_path=input_path,
        frames_path=frames_path,
        segments_path=segments_path,
        frames=frames,
        segments=segments,
        args=args,
    )
    summary_path.write_text(summary, encoding="utf-8")
    print(f"Frames CSV: {frames_path}", flush=True)
    print(f"Segments CSV: {segments_path}", flush=True)
    print(f"Summary MD: {summary_path}", flush=True)
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.audio).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input path does not exist: {input_path}")

    repo_root = Path(__file__).resolve().parents[1]
    explicit_results_dir = args.results_dir is not None
    results_dir = (
        Path(args.results_dir).expanduser().resolve() if args.results_dir else repo_root / "results"
    )
    results_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_dir():
        return process_batch(args, input_path, results_dir, explicit_results_dir)
    return process_single(args, input_path, results_dir)


if __name__ == "__main__":
    sys.exit(main())