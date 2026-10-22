"""One forward GRU read over a whole session, with a head for the end and one for the billing mode.

Sessions are padded at the end, which leaves a forward GRU's outputs on the real rows unchanged; the padding is masked
out of both losses."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn
from torch.nn.utils.rnn import pad_sequence

from playend.training.data import BILLING_MODES, Sequence

SESSIONS_PER_STEP = 4
MAX_EPOCHS = 300
PATIENCE = 30
CLIP = 1.0


class EndDetector(nn.Module):
    def __init__(self, inputs: int, hidden: int, dropout: float):
        super().__init__()
        self.gru = nn.GRU(inputs, hidden, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.end = nn.Linear(hidden, 1)
        self.billing = nn.Linear(hidden, len(BILLING_MODES))

    def forward(self, x, state=None):
        out, state = self.gru(x, state)
        out = self.dropout(out)
        return self.end(out).squeeze(-1), self.billing(out), state


@dataclass
class Tensors:
    x: torch.Tensor
    end: torch.Tensor
    usable: torch.Tensor
    billing: torch.Tensor
    real: torch.Tensor  # False on padding


def to_tensors(sequences: list[Sequence], columns: list[int], device: torch.device) -> list[dict]:
    return [
        {
            "x": torch.from_numpy(s.x[:, columns]).to(device),
            "end": torch.from_numpy(s.end.astype(np.float32)).to(device),
            "usable": torch.from_numpy(s.usable.astype(np.float32)).to(device),
            "billing": torch.from_numpy(s.billing).to(device),
        }
        for s in sequences
    ]


def pad(items: list[dict]) -> Tensors:
    real = [torch.ones(len(item["end"]), device=item["end"].device) for item in items]
    return Tensors(
        x=pad_sequence([item["x"] for item in items], batch_first=True),
        end=pad_sequence([item["end"] for item in items], batch_first=True),
        usable=pad_sequence([item["usable"] for item in items], batch_first=True),
        billing=pad_sequence([item["billing"] for item in items], batch_first=True),
        real=pad_sequence(real, batch_first=True),
    )


def class_weights(sequences: list[Sequence]) -> tuple[float, np.ndarray]:
    usable = np.concatenate([s.usable for s in sequences])
    ends = float(np.concatenate([s.end for s in sequences])[usable].sum())
    counts = np.bincount(np.concatenate([s.billing for s in sequences]), minlength=len(BILLING_MODES)).astype(float)
    billing = counts.sum() / np.maximum(counts, 1.0) / len(BILLING_MODES)
    return (usable.sum() - ends) / max(ends, 1.0), billing.astype(np.float32)


def losses(model, batch: Tensors, pos_weight, billing_weight) -> torch.Tensor:
    end_logit, billing_logit, _ = model(batch.x)
    end = nn.functional.binary_cross_entropy_with_logits(end_logit, batch.end, pos_weight=pos_weight, reduction="none")
    end_loss = (end * batch.usable).sum() / batch.usable.sum().clamp(min=1)
    labels = batch.billing.reshape(-1)
    billing = nn.functional.cross_entropy(
        billing_logit.reshape(-1, len(BILLING_MODES)), labels, weight=billing_weight, reduction="none"
    )
    real = batch.real.reshape(-1)
    billing_loss = (billing * real).sum() / (billing_weight[labels] * real).sum().clamp(min=1e-6)
    return end_loss + billing_loss


def batches(lengths: np.ndarray, rng: np.random.Generator) -> list[np.ndarray]:
    """Sessions of similar length together, which saves most of the padding; jitter and order vary by epoch."""
    order = np.argsort(-lengths * rng.uniform(0.8, 1.2, len(lengths)))
    groups = [order[start : start + SESSIONS_PER_STEP] for start in range(0, len(order), SESSIONS_PER_STEP)]
    return [groups[i] for i in rng.permutation(len(groups))]


@dataclass
class Fit:
    state: dict
    best_epoch: int
    curve: list = field(default_factory=list)  # [epoch, training loss, validation loss]


def fit(
    train: list[Sequence],
    valid: list[Sequence] | None,
    columns: list[int],
    config: dict,
    device: str,
    seed: int,
    epochs: int | None = None,
    max_epochs: int = MAX_EPOCHS,
) -> Fit:
    """Early stopping on `valid` when it is given; otherwise exactly `epochs` epochs."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    device = torch.device(device)
    model = EndDetector(len(columns), config["hidden"], config["dropout"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
    ratio, billing = class_weights(train)
    pos_weight = torch.tensor(ratio, dtype=torch.float32, device=device) if config["pos_weight"] else None
    billing_weight = torch.from_numpy(billing).to(device)
    train_items = to_tensors(train, columns, device)
    lengths = np.array([len(item["end"]) for item in train_items])
    valid_batch = pad(to_tensors(valid, columns, device)) if valid else None
    best, best_state, best_epoch, waited, curve = float("inf"), None, 0, 0, []
    for epoch in range(1, (epochs or max_epochs) + 1):
        model.train()
        step_losses = []
        for indices in batches(lengths, rng):
            batch = pad([train_items[i] for i in indices])
            optimizer.zero_grad()
            loss = losses(model, batch, pos_weight, billing_weight)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), CLIP)
            optimizer.step()
            step_losses.append(loss.item())
        if valid_batch is None:
            curve.append([epoch, float(np.mean(step_losses)), None])
            continue
        model.eval()
        with torch.no_grad():
            valid_loss = losses(model, valid_batch, pos_weight, billing_weight).item()
        curve.append([epoch, float(np.mean(step_losses)), valid_loss])
        if valid_loss < best - 1e-5:
            best, best_epoch, waited = valid_loss, epoch, 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            waited += 1
            if waited >= PATIENCE:
                break
    if best_state is None:
        best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        best_epoch = len(curve)
    return Fit(state=best_state, best_epoch=best_epoch, curve=curve)


def predict(state: dict, config: dict, columns: list[int], sequences: list[Sequence], device: str) -> dict:
    """Per session: probability of an end on each row and the most likely billing mode."""
    device = torch.device(device)
    model = EndDetector(len(columns), config["hidden"], config["dropout"]).to(device)
    model.load_state_dict(state)
    model.eval()
    out = {}
    with torch.no_grad():
        for sequence in sequences:
            end_logit, billing_logit, _ = model(torch.from_numpy(sequence.x[:, columns]).to(device)[None])
            out[sequence.session] = (
                torch.sigmoid(end_logit[0]).cpu().numpy().astype(np.float32),
                billing_logit[0].argmax(-1).cpu().numpy().astype(np.int8),
            )
    return out
