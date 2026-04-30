from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import lightning as L
import yaml
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor, ModelCheckpoint
from lightning.pytorch.loggers import CSVLogger


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from model import DeepfakeFeatureClassifier
from utils import AudioFeatureDataModule


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train a Lightning classifier on pre-extracted voice deepfake features."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "feature_deepfake_baseline.yaml",
        help="Path to the YAML training config.",
    )
    return parser


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a mapping, got: {type(config)!r}")
    return config


def build_datamodule(config: dict[str, Any]) -> AudioFeatureDataModule:
    data_config = dict(config.get("data") or {})
    if "train_csv" not in data_config:
        raise ValueError("Config.data.train_csv is required.")
    return AudioFeatureDataModule(**data_config)


def build_model(
    config: dict[str, Any],
    *,
    input_dim: int,
    pos_weight: float | None,
) -> DeepfakeFeatureClassifier:
    model_config = dict(config.get("model") or {})
    configured_pos_weight = model_config.pop("pos_weight", None)
    effective_pos_weight = pos_weight if configured_pos_weight == "auto" else configured_pos_weight
    return DeepfakeFeatureClassifier(
        input_dim=input_dim,
        pos_weight=effective_pos_weight,
        **model_config,
    )


def build_logger(config: dict[str, Any]) -> CSVLogger:
    logging_config = dict(config.get("logging") or {})
    save_dir = Path(logging_config.get("save_dir", REPO_ROOT / "results" / "feature_classifier"))
    experiment_name = str(logging_config.get("experiment_name", "default"))
    version = logging_config.get("version")
    return CSVLogger(save_dir=str(save_dir), name=experiment_name, version=version)


def build_callbacks(config: dict[str, Any], has_validation: bool) -> list[Any]:
    callback_config = dict(config.get("callbacks") or {})
    callbacks: list[Any] = []
    monitor_metric = "val/loss" if has_validation else "train/loss"

    checkpoint_config = dict(callback_config.get("checkpoint") or {})
    if checkpoint_config.get("enabled", True):
        callbacks.append(
            ModelCheckpoint(
                dirpath=checkpoint_config.get("dirpath"),
                filename=checkpoint_config.get("filename", "epoch={epoch:02d}-loss={" + monitor_metric.replace("/", "_") + ":.4f}"),
                monitor=checkpoint_config.get("monitor", monitor_metric if has_validation else None),
                mode=checkpoint_config.get("mode", "min"),
                save_top_k=int(checkpoint_config.get("save_top_k", 1)),
                save_last=bool(checkpoint_config.get("save_last", True)),
            )
        )

    early_stopping_config = dict(callback_config.get("early_stopping") or {})
    if has_validation and early_stopping_config.get("enabled", True):
        callbacks.append(
            EarlyStopping(
                monitor=str(early_stopping_config.get("monitor", monitor_metric)),
                mode=str(early_stopping_config.get("mode", "min")),
                patience=int(early_stopping_config.get("patience", 8)),
                min_delta=float(early_stopping_config.get("min_delta", 0.0)),
            )
        )

    lr_monitor_config = dict(callback_config.get("lr_monitor") or {})
    if lr_monitor_config.get("enabled", True):
        callbacks.append(LearningRateMonitor(logging_interval="epoch"))
    return callbacks


def build_trainer(
    config: dict[str, Any],
    *,
    logger: CSVLogger,
    callbacks: list[Any],
) -> L.Trainer:
    trainer_config = dict(config.get("trainer") or {})
    return L.Trainer(logger=logger, callbacks=callbacks, **trainer_config)


def write_run_artifacts(
    *,
    logger: CSVLogger,
    config: dict[str, Any],
    datamodule: AudioFeatureDataModule,
) -> None:
    log_dir = Path(logger.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    resolved_config_path = log_dir / "resolved_config.yaml"
    with resolved_config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)

    feature_stats = {
        "feature_columns": datamodule.metadata.get("feature_columns", []),
        "feature_mean": [] if datamodule.feature_mean is None else datamodule.feature_mean.tolist(),
        "feature_std": [] if datamodule.feature_std is None else datamodule.feature_std.tolist(),
        "class_balance": datamodule.class_balance,
        "input_dim": datamodule.input_dim,
        "metadata": datamodule.metadata,
    }
    stats_path = log_dir / "feature_stats.json"
    stats_path.write_text(json.dumps(feature_stats, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config(args.config.expanduser().resolve())

    seed = int(config.get("seed", 3407))
    L.seed_everything(seed, workers=True)

    datamodule = build_datamodule(config)
    datamodule.setup(stage="fit")

    model = build_model(
        config,
        input_dim=datamodule.input_dim,
        pos_weight=datamodule.compute_pos_weight(),
    )

    logger = build_logger(config)
    callbacks = build_callbacks(config, has_validation=(datamodule.val_set is not None))
    write_run_artifacts(logger=logger, config=config, datamodule=datamodule)
    trainer = build_trainer(config, logger=logger, callbacks=callbacks)

    trainer.fit(model=model, datamodule=datamodule)

    if config.get("run_test_after_fit", True) and datamodule.test_set is not None:
        trainer.test(model=model, datamodule=datamodule, ckpt_path="best")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())