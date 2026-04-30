from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a train/val/test manifest from extracted audio feature CSV files."
    )
    parser.add_argument(
        "--real-csv",
        nargs="+",
        default=[],
        help="One or more audio_stats.csv files for bona fide / real audio.",
    )
    parser.add_argument(
        "--fake-csv",
        nargs="+",
        default=[],
        help="One or more audio_stats.csv files for fake / deepfake audio.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        required=True,
        help="Path to the merged manifest CSV.",
    )
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument(
        "--include-non-ok",
        action="store_true",
        help="Include rows whose status is not ok/skipped.",
    )
    parser.add_argument(
        "--dedupe-by",
        default="source_audio",
        help="Optional column used to drop duplicate rows after concatenation.",
    )
    return parser


def load_labeled_frames(
    paths: list[str],
    *,
    label: str,
    include_non_ok: bool,
) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"CSV file does not exist: {path}")
        frame = pd.read_csv(path)
        if not include_non_ok and "status" in frame.columns:
            allowed_status = frame["status"].astype(str).str.strip().str.lower().isin({"ok", "skipped"})
            frame = frame.loc[allowed_status].copy()
        if frame.empty:
            continue
        frame["label"] = label
        frame["source_csv"] = str(path)
        frames.append(frame)
    return frames


def split_frame(
    frame: pd.DataFrame,
    *,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("Merged feature frame is empty.")
    if val_ratio < 0 or test_ratio < 0 or val_ratio + test_ratio >= 1:
        raise ValueError("val_ratio and test_ratio must be non-negative and sum to less than 1.")

    train_frame = frame.copy()
    val_frame = frame.iloc[0:0].copy()
    test_frame = frame.iloc[0:0].copy()

    if test_ratio > 0:
        train_frame, test_frame = train_test_split(
            train_frame,
            test_size=test_ratio,
            random_state=seed,
            stratify=train_frame["label"],
        )
    if val_ratio > 0:
        adjusted_val_ratio = val_ratio / (1.0 - test_ratio)
        train_frame, val_frame = train_test_split(
            train_frame,
            test_size=adjusted_val_ratio,
            random_state=seed,
            stratify=train_frame["label"],
        )

    train_frame = train_frame.copy()
    val_frame = val_frame.copy()
    test_frame = test_frame.copy()
    train_frame["split"] = "train"
    if not val_frame.empty:
        val_frame["split"] = "val"
    if not test_frame.empty:
        test_frame["split"] = "test"
    return pd.concat([train_frame, val_frame, test_frame], ignore_index=True)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    real_frames = load_labeled_frames(
        args.real_csv,
        label="real",
        include_non_ok=args.include_non_ok,
    )
    fake_frames = load_labeled_frames(
        args.fake_csv,
        label="fake",
        include_non_ok=args.include_non_ok,
    )
    frames = real_frames + fake_frames
    if not frames:
        raise SystemExit("No usable CSV rows were loaded. Provide at least one --real-csv or --fake-csv.")

    merged = pd.concat(frames, ignore_index=True)
    if args.dedupe_by and args.dedupe_by in merged.columns:
        merged = merged.drop_duplicates(subset=[args.dedupe_by]).reset_index(drop=True)

    manifest = split_frame(
        merged,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.output_csv, index=False)

    print(f"Manifest CSV: {args.output_csv}", flush=True)
    print(f"Rows: {len(manifest)}", flush=True)
    print(manifest["split"].value_counts().sort_index().to_string(), flush=True)
    print(manifest["label"].value_counts().sort_index().to_string(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())