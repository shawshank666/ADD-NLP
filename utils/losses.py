from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as F
from torch import nn


class BinaryFocalLoss(nn.Module):
    def __init__(
        self,
        gamma: float = 2.0,
        alpha: float | None = None,
        pos_weight: float | None = None,
        reduction: Literal["mean", "sum", "none"] = "mean",
    ) -> None:
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction
        self.register_buffer(
            "pos_weight",
            None if pos_weight is None else torch.tensor(float(pos_weight), dtype=torch.float32),
            persistent=False,
        )

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        targets = targets.float()
        bce_loss = F.binary_cross_entropy_with_logits(
            logits,
            targets,
            reduction="none",
            pos_weight=self.pos_weight,
        )
        probabilities = torch.sigmoid(logits)
        pt = torch.where(targets > 0.5, probabilities, 1.0 - probabilities)
        focal_weight = (1.0 - pt).pow(self.gamma)
        if self.alpha is not None:
            alpha_weight = torch.where(targets > 0.5, self.alpha, 1.0 - self.alpha)
            focal_weight = focal_weight * alpha_weight
        loss = focal_weight * bce_loss
        if self.reduction == "sum":
            return loss.sum()
        if self.reduction == "none":
            return loss
        return loss.mean()


def build_binary_loss(
    name: str,
    *,
    pos_weight: float | None = None,
    focal_gamma: float = 2.0,
    focal_alpha: float | None = None,
) -> nn.Module:
    normalized = name.strip().lower()
    if normalized in {"bce", "bcewithlogits", "binary_cross_entropy"}:
        if pos_weight is None:
            return nn.BCEWithLogitsLoss()
        return nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(pos_weight), dtype=torch.float32))
    if normalized == "focal":
        return BinaryFocalLoss(
            gamma=focal_gamma,
            alpha=focal_alpha,
            pos_weight=pos_weight,
        )
    raise ValueError(f"Unsupported loss name: {name}")
