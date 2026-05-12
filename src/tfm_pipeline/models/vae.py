from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


@dataclass(frozen=True)
class VAETrainingHistory:
    train_loss: list[float]
    train_reconstruction_loss: list[float]
    train_kl_loss: list[float]
    validation_loss: list[float]
    validation_reconstruction_loss: list[float]
    validation_kl_loss: list[float]
    best_epoch: int


class WindowVAE(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 128, latent_dim: int = 16) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.mean = nn.Linear(hidden_dim, latent_dim)
        self.log_variance = nn.Linear(hidden_dim, latent_dim)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def encode(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self.encoder(inputs)
        return self.mean(hidden), self.log_variance(hidden)

    def reparameterize(self, mean: torch.Tensor, log_variance: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * log_variance)
        noise = torch.randn_like(std)
        return mean + noise * std

    def decode(self, latent: torch.Tensor) -> torch.Tensor:
        return self.decoder(latent)

    def forward(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mean, log_variance = self.encode(inputs)
        latent = self.reparameterize(mean, log_variance)
        reconstruction = self.decode(latent)
        return reconstruction, mean, log_variance


def vae_loss_components(
    reconstruction: torch.Tensor,
    inputs: torch.Tensor,
    mean: torch.Tensor,
    log_variance: torch.Tensor,
    beta: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    reconstruction_loss = nn.functional.mse_loss(reconstruction, inputs, reduction="mean")
    kl_loss = -0.5 * torch.mean(1.0 + log_variance - mean.pow(2) - log_variance.exp())
    total_loss = reconstruction_loss + beta * kl_loss
    return total_loss, reconstruction_loss, kl_loss


def set_torch_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except TypeError:
        torch.use_deterministic_algorithms(True)


def flatten_windows(windows: np.ndarray) -> np.ndarray:
    return windows.reshape(windows.shape[0], -1).astype(np.float32)


def fit_vae(
    train_windows: np.ndarray,
    validation_windows: np.ndarray,
    hidden_dim: int,
    latent_dim: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    beta: float,
    seed: int,
    patience: int | None = None,
    device: str | None = None,
) -> tuple[WindowVAE, VAETrainingHistory]:
    set_torch_seed(seed)
    selected_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"Using torch device: {selected_device}")

    train_flat = flatten_windows(train_windows)
    validation_flat = flatten_windows(validation_windows)
    model = WindowVAE(input_dim=train_flat.shape[1], hidden_dim=hidden_dim, latent_dim=latent_dim)
    model.to(selected_device)

    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(train_flat)),
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )
    validation_tensor = torch.from_numpy(validation_flat).to(selected_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    history = VAETrainingHistory(
        train_loss=[],
        train_reconstruction_loss=[],
        train_kl_loss=[],
        validation_loss=[],
        validation_reconstruction_loss=[],
        validation_kl_loss=[],
        best_epoch=0,
    )
    best_validation_loss = float("inf")
    best_state = deepcopy(model.state_dict())
    epochs_without_improvement = 0

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses = []
        epoch_reconstruction_losses = []
        epoch_kl_losses = []
        for (batch,) in train_loader:
            batch = batch.to(selected_device)
            optimizer.zero_grad(set_to_none=True)
            reconstruction, mean, log_variance = model(batch)
            loss, reconstruction_loss, kl_loss = vae_loss_components(reconstruction, batch, mean, log_variance, beta)
            loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.detach().cpu()))
            epoch_reconstruction_losses.append(float(reconstruction_loss.detach().cpu()))
            epoch_kl_losses.append(float(kl_loss.detach().cpu()))

        model.eval()
        with torch.no_grad():
            reconstruction, mean, log_variance = model(validation_tensor)
            validation_loss, validation_reconstruction_loss, validation_kl_loss = vae_loss_components(
                reconstruction,
                validation_tensor,
                mean,
                log_variance,
                beta,
            )

        history.train_loss.append(float(np.mean(epoch_losses)))
        history.train_reconstruction_loss.append(float(np.mean(epoch_reconstruction_losses)))
        history.train_kl_loss.append(float(np.mean(epoch_kl_losses)))
        history.validation_loss.append(float(validation_loss.detach().cpu()))
        history.validation_reconstruction_loss.append(float(validation_reconstruction_loss.detach().cpu()))
        history.validation_kl_loss.append(float(validation_kl_loss.detach().cpu()))

        current_validation_loss = history.validation_loss[-1]
        if current_validation_loss < best_validation_loss:
            best_validation_loss = current_validation_loss
            best_state = deepcopy(model.state_dict())
            history = VAETrainingHistory(
                train_loss=history.train_loss,
                train_reconstruction_loss=history.train_reconstruction_loss,
                train_kl_loss=history.train_kl_loss,
                validation_loss=history.validation_loss,
                validation_reconstruction_loss=history.validation_reconstruction_loss,
                validation_kl_loss=history.validation_kl_loss,
                best_epoch=epoch,
            )
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if patience is not None and epochs_without_improvement >= patience:
            break

    model.load_state_dict(best_state)
    return model, history


def sample_vae(
    model: WindowVAE,
    n_scenarios: int,
    window_size: int,
    n_assets: int,
    seed: int,
    device: str | None = None,
) -> np.ndarray:
    set_torch_seed(seed)
    selected_device = torch.device(device or next(model.parameters()).device)
    model.eval()
    with torch.no_grad():
        latent = torch.randn(n_scenarios, model.latent_dim, device=selected_device)
        samples = model.decode(latent).cpu().numpy()
    return samples.reshape(n_scenarios, window_size, n_assets).astype(np.float32)
