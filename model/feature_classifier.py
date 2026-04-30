from __future__ import annotations

from collections.abc import Sequence

import lightning as L
import torch
from torch import nn
from torchmetrics import MetricCollection
from torchmetrics.classification import (
    BinaryAUROC,
    BinaryAccuracy,
    BinaryF1Score,
    BinaryPrecision,
    BinaryRecall,
)

from utils.losses import build_binary_loss


class DeepfakeFeatureClassifier(L.LightningModule):
    def __init__(
        self,
        input_dim: int,
        hidden_dims: Sequence[int] = (128, 64),
        dropout: float = 0.2,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        loss_name: str = "bce",
        focal_gamma: float = 2.0,
        focal_alpha: float | None = None,
        pos_weight: float | None = None,
        scheduler_name: str = "none",
        scheduler_t_max: int = 20,
        scheduler_patience: int = 5,
        scheduler_factor: float = 0.5,
    ) -> None:
        super().__init__()
        if input_dim <= 0:
            raise ValueError(f"input_dim must be positive, got {input_dim}")

        self.save_hyperparameters()
        self.network = self._build_network(input_dim=input_dim, hidden_dims=hidden_dims, dropout=dropout)
        self.loss_fn = build_binary_loss(
            loss_name,
            pos_weight=pos_weight,
            focal_gamma=focal_gamma,
            focal_alpha=focal_alpha,
        )
        metrics = MetricCollection(
            {
                "acc": BinaryAccuracy(),
                "f1": BinaryF1Score(),
                "precision": BinaryPrecision(),
                "recall": BinaryRecall(),
                "auroc": BinaryAUROC(),
            }
        )
        self.train_metrics = metrics.clone(prefix="train/")
        self.val_metrics = metrics.clone(prefix="val/")
        self.test_metrics = metrics.clone(prefix="test/")

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)

    def training_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="train")

    def validation_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="val")

    def test_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="test")

    def predict_step(
        self,
        batch: tuple[torch.Tensor, torch.Tensor],
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> dict[str, torch.Tensor]:
        features, _ = batch
        logits = self(features)
        probabilities = torch.sigmoid(logits)
        predictions = (probabilities >= 0.5).long()
        return {
            "logits": logits,
            "probabilities": probabilities,
            "predictions": predictions,
        }

    def configure_optimizers(self) -> dict[str, object] | torch.optim.Optimizer:
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hparams.learning_rate,
            weight_decay=self.hparams.weight_decay,
        )
        scheduler_name = str(self.hparams.scheduler_name).strip().lower()
        if scheduler_name in {"", "none"}:
            return optimizer
        if scheduler_name == "cosine":
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=self.hparams.scheduler_t_max,
            )
            return {"optimizer": optimizer, "lr_scheduler": scheduler}
        if scheduler_name == "plateau":
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer,
                mode="min",
                factor=self.hparams.scheduler_factor,
                patience=self.hparams.scheduler_patience,
            )
            return {
                "optimizer": optimizer,
                "lr_scheduler": {
                    "scheduler": scheduler,
                    "monitor": "val/loss",
                    "interval": "epoch",
                    "frequency": 1,
                },
            }
        raise ValueError(f"Unsupported scheduler_name: {self.hparams.scheduler_name}")

    def _shared_step(self, batch: tuple[torch.Tensor, torch.Tensor], stage: str) -> torch.Tensor:
        features, targets = batch
        logits = self(features)
        targets_float = targets.float()
        loss = self.loss_fn(logits, targets_float)
        probabilities = torch.sigmoid(logits)
        self.log(f"{stage}/loss", loss, prog_bar=(stage != "train"), on_step=False, on_epoch=True)

        metric_collection = self._metric_collection(stage)
        metric_collection.update(probabilities, targets)
        self.log_dict(metric_collection, prog_bar=(stage == "val"), on_step=False, on_epoch=True)
        return loss

    def _metric_collection(self, stage: str) -> MetricCollection:
        if stage == "train":
            return self.train_metrics
        if stage == "val":
            return self.val_metrics
        if stage == "test":
            return self.test_metrics
        raise ValueError(f"Unsupported stage: {stage}")

    @staticmethod
    def _build_network(
        *,
        input_dim: int,
        hidden_dims: Sequence[int],
        dropout: float,
    ) -> nn.Sequential:
        layers: list[nn.Module] = []
        in_features = input_dim
        for hidden_dim in hidden_dims:
            layers.extend(
                [
                    nn.Linear(in_features, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.SiLU(),
                    nn.Dropout(dropout),
                ]
            )
            in_features = hidden_dim
        layers.append(nn.Linear(in_features, 1))
        return nn.Sequential(*layers)