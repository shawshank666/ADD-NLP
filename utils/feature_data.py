from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import lightning as L
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset


DEFAULT_FEATURE_COLUMNS = [
    "frame_subharmonics_ratio",
    "frame_sidebands_ratio",
    "frame_chaos_ratio",
    "frame_frequency_jump_ratio",
    "subharmonics_candidate_count",
    "sidebands_candidate_count",
    "chaos_candidate_count",
    "frequency_jump_candidate_count",
    "voiced_frame_ratio",
    "mean_pitch_voiced",
    "mean_amEnvDep",
    "mean_amMsPurity",
    "mean_HNR",
    "mean_roughness",
    "mean_entropy",
    "mean_subDep",
    "median_pitch_voiced",
    "median_amEnvDep",
    "median_amMsPurity",
    "median_HNR",
    "median_roughness",
    "median_entropy",
    "median_subDep",
]

RESERVED_COLUMNS = {
    "source_audio",
    "relative_audio",
    "status",
    "error",
    "label",
    "target",
    "split",
}


@dataclass(slots=True)
class SplitFrame:
    frame: pd.DataFrame
    features: torch.Tensor
    labels: torch.Tensor


class TabularFeatureDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, features: torch.Tensor, labels: torch.Tensor) -> None:
        if features.ndim != 2:
            raise ValueError(f"Expected 2D features, got shape={tuple(features.shape)}")
        if labels.ndim != 1:
            raise ValueError(f"Expected 1D labels, got shape={tuple(labels.shape)}")
        if len(features) != len(labels):
            raise ValueError("Features and labels must have identical lengths.")
        self._features = features
        self._labels = labels

    def __len__(self) -> int:
        return len(self._labels)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self._features[index], self._labels[index]


class AudioFeatureDataModule(L.LightningDataModule):
    def __init__(
        self,
        train_csv: str,
        val_csv: str | None = None,
        test_csv: str | None = None,
        predict_csv: str | None = None,
        features: Sequence[str] | None = None,
        label_column: str = "label",
        split_column: str = "split",
        train_split: str = "train",
        val_split: str = "val",
        test_split: str = "test",
        positive_labels: Sequence[str] | None = None,
        negative_labels: Sequence[str] | None = None,
        batch_size: int = 64,
        num_workers: int = 4,
        drop_last: bool = False,
        pin_memory: bool = True,
        persistent_workers: bool = True,
        fill_value: float | None = None,
        use_default_feature_set: bool = True,
    ) -> None:
        super().__init__()
        self.train_csv = Path(train_csv).expanduser().resolve()
        self.val_csv = Path(val_csv).expanduser().resolve() if val_csv else None
        self.test_csv = Path(test_csv).expanduser().resolve() if test_csv else None
        self.predict_csv = Path(predict_csv).expanduser().resolve() if predict_csv else None
        self.feature_columns = list(features or [])
        self.label_column = label_column
        self.split_column = split_column
        self.train_split = train_split
        self.val_split = val_split
        self.test_split = test_split
        self.positive_labels = {str(item).strip().lower() for item in (positive_labels or ["fake", "deepfake", "spoof", "1"])}
        self.negative_labels = {str(item).strip().lower() for item in (negative_labels or ["real", "bonafide", "genuine", "0"])}
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.drop_last = drop_last
        self.pin_memory = pin_memory
        self.persistent_workers = persistent_workers and num_workers > 0
        self.fill_value = fill_value
        self.use_default_feature_set = use_default_feature_set

        self.train_set: TabularFeatureDataset | None = None
        self.val_set: TabularFeatureDataset | None = None
        self.test_set: TabularFeatureDataset | None = None
        self.predict_set: TabularFeatureDataset | None = None

        self.feature_mean: torch.Tensor | None = None
        self.feature_std: torch.Tensor | None = None
        self.input_dim: int = 0
        self.class_balance: float | None = None
        self.metadata: dict[str, Any] = {}

    def setup(self, stage: str | None = None) -> None:
        train_frame = self._load_frame(self.train_csv)
        splits = self._resolve_splits(train_frame)

        train_frame = splits[self.train_split]
        val_frame = self._load_optional_split(self.val_csv, splits.get(self.val_split))
        test_frame = self._load_optional_split(self.test_csv, splits.get(self.test_split))
        predict_frame = self._load_predict_frame()

        feature_columns = self._resolve_feature_columns(train_frame)
        train_split = self._frame_to_split(train_frame, feature_columns, fit_statistics=True)
        self.train_set = TabularFeatureDataset(train_split.features, train_split.labels)
        self.input_dim = train_split.features.shape[1]
        self.class_balance = float(train_split.labels.float().mean().item()) if len(train_split.labels) else None

        if val_frame is not None and not val_frame.empty:
            val_split = self._frame_to_split(val_frame, feature_columns, fit_statistics=False)
            self.val_set = TabularFeatureDataset(val_split.features, val_split.labels)
        else:
            self.val_set = None

        if test_frame is not None and not test_frame.empty:
            test_split = self._frame_to_split(test_frame, feature_columns, fit_statistics=False)
            self.test_set = TabularFeatureDataset(test_split.features, test_split.labels)
        else:
            self.test_set = None

        if predict_frame is not None and not predict_frame.empty:
            predict_features = self._transform_features(predict_frame[feature_columns])
            dummy_labels = torch.zeros(len(predict_features), dtype=torch.long)
            self.predict_set = TabularFeatureDataset(predict_features, dummy_labels)
        else:
            self.predict_set = None

        self.metadata = {
            "feature_columns": feature_columns,
            "train_examples": len(train_frame),
            "val_examples": 0 if val_frame is None else len(val_frame),
            "test_examples": 0 if test_frame is None else len(test_frame),
            "predict_examples": 0 if predict_frame is None else len(predict_frame),
        }

    def train_dataloader(self) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
        if self.train_set is None:
            raise RuntimeError("Call setup() before requesting the train dataloader.")
        return self._build_loader(self.train_set, shuffle=True, drop_last=self.drop_last)

    def val_dataloader(self) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
        if self.val_set is None:
            raise RuntimeError("Validation split is not available.")
        return self._build_loader(self.val_set, shuffle=False, drop_last=False)

    def test_dataloader(self) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
        if self.test_set is None:
            raise RuntimeError("Test split is not available.")
        return self._build_loader(self.test_set, shuffle=False, drop_last=False)

    def predict_dataloader(self) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
        if self.predict_set is None:
            raise RuntimeError("Predict split is not available.")
        return self._build_loader(self.predict_set, shuffle=False, drop_last=False)

    def compute_pos_weight(self) -> float | None:
        if self.train_set is None:
            raise RuntimeError("Call setup() before computing class weights.")
        labels = self.train_set._labels.float()
        positives = float(labels.sum().item())
        negatives = float(len(labels) - positives)
        if positives <= 0 or negatives <= 0:
            return None
        return negatives / positives

    def _build_loader(
        self,
        dataset: TabularFeatureDataset,
        *,
        shuffle: bool,
        drop_last: bool,
    ) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=self.persistent_workers,
            drop_last=drop_last,
        )

    def _load_optional_split(
        self,
        csv_path: Path | None,
        inline_frame: pd.DataFrame | None,
    ) -> pd.DataFrame | None:
        if csv_path is not None:
            return self._load_frame(csv_path)
        return inline_frame

    def _load_predict_frame(self) -> pd.DataFrame | None:
        if self.predict_csv is None:
            return None
        return self._load_frame(self.predict_csv)

    def _load_frame(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"CSV file does not exist: {path}")
        frame = pd.read_csv(path)
        if frame.empty:
            raise ValueError(f"CSV file is empty: {path}")
        return frame

    def _resolve_splits(self, frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
        if self.val_csv is not None or self.test_csv is not None:
            return {self.train_split: frame}
        if self.split_column not in frame.columns:
            return {self.train_split: frame}

        normalized_split = frame[self.split_column].astype(str).str.strip().str.lower()
        splits = {
            split_name: frame.loc[normalized_split == split_name].reset_index(drop=True)
            for split_name in {self.train_split, self.val_split, self.test_split}
        }
        if splits.get(self.train_split) is None or splits[self.train_split].empty:
            raise ValueError(
                f"No rows with split='{self.train_split}' were found in {self.train_csv}."
            )
        return splits

    def _resolve_feature_columns(self, frame: pd.DataFrame) -> list[str]:
        if self.feature_columns:
            missing = [column for column in self.feature_columns if column not in frame.columns]
            if missing:
                raise ValueError(f"Missing configured feature columns: {missing}")
            return self.feature_columns

        if self.use_default_feature_set:
            available_default = [column for column in DEFAULT_FEATURE_COLUMNS if column in frame.columns]
            if available_default:
                return available_default

        numeric_columns = []
        for column in frame.columns:
            if column in RESERVED_COLUMNS or column == self.label_column:
                continue
            if pd.api.types.is_numeric_dtype(frame[column]):
                numeric_columns.append(column)

        if not numeric_columns:
            raise ValueError("No numeric feature columns were found in the input CSV.")
        return numeric_columns

    def _frame_to_split(
        self,
        frame: pd.DataFrame,
        feature_columns: Sequence[str],
        *,
        fit_statistics: bool,
    ) -> SplitFrame:
        if self.label_column not in frame.columns:
            raise ValueError(f"Missing label column '{self.label_column}' in dataset.")
        labels = self._encode_labels(frame[self.label_column])
        features = self._transform_features(frame[list(feature_columns)], fit_statistics=fit_statistics)
        return SplitFrame(frame=frame, features=features, labels=labels)

    def _transform_features(
        self,
        frame: pd.DataFrame,
        *,
        fit_statistics: bool = False,
    ) -> torch.Tensor:
        numeric_frame = frame.apply(pd.to_numeric, errors="coerce")
        if fit_statistics:
            fill_values = numeric_frame.median(numeric_only=True)
            if self.fill_value is not None:
                fill_values = fill_values.fillna(self.fill_value)
            numeric_frame = numeric_frame.fillna(fill_values)
            features = torch.tensor(numeric_frame.to_numpy(dtype="float32"), dtype=torch.float32)
            self.feature_mean = features.mean(dim=0)
            self.feature_std = features.std(dim=0).clamp_min(1e-6)
            return (features - self.feature_mean) / self.feature_std

        if self.feature_mean is None or self.feature_std is None:
            raise RuntimeError("Training statistics are not initialized. Run fit setup first.")
        if self.fill_value is not None:
            numeric_frame = numeric_frame.fillna(self.fill_value)
        else:
            numeric_frame = numeric_frame.fillna(numeric_frame.median(numeric_only=True))
        features = torch.tensor(numeric_frame.to_numpy(dtype="float32"), dtype=torch.float32)
        return (features - self.feature_mean) / self.feature_std

    def _encode_labels(self, series: pd.Series) -> torch.Tensor:
        encoded: list[int] = []
        for raw_value in series.tolist():
            if pd.isna(raw_value):
                raise ValueError("Label column contains missing values.")
            if isinstance(raw_value, (int, float)) and raw_value in {0, 1}:
                encoded.append(int(raw_value))
                continue
            value = str(raw_value).strip().lower()
            if value in self.positive_labels:
                encoded.append(1)
            elif value in self.negative_labels:
                encoded.append(0)
            else:
                raise ValueError(
                    "Unsupported label value "
                    f"'{raw_value}'. Configure positive_labels/negative_labels or use numeric 0/1."
                )
        return torch.tensor(encoded, dtype=torch.long)


def collect_feature_columns(frames: Iterable[pd.DataFrame]) -> list[str]:
    shared_columns: set[str] | None = None
    for frame in frames:
        numeric_columns = {
            column
            for column in frame.columns
            if pd.api.types.is_numeric_dtype(frame[column]) and column not in RESERVED_COLUMNS
        }
        shared_columns = numeric_columns if shared_columns is None else shared_columns & numeric_columns
    return sorted(shared_columns or [])