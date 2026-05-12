from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .vae import set_torch_seed


@dataclass(frozen=True)
class TimeGANTrainingHistory:
    autoencoder_loss: list[float]
    supervisor_loss: list[float]
    generator_loss: list[float]
    discriminator_loss: list[float]


class RecurrentBlock(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int) -> None:
        super().__init__()
        self.rnn = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.projection = nn.Linear(hidden_dim, output_dim)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        outputs, _ = self.rnn(inputs)
        return self.projection(outputs)


class TimeGAN(nn.Module):
    def __init__(self, n_assets: int, hidden_dim: int, noise_dim: int) -> None:
        super().__init__()
        self.n_assets = n_assets
        self.hidden_dim = hidden_dim
        self.noise_dim = noise_dim

        self.embedder = RecurrentBlock(n_assets, hidden_dim, hidden_dim)
        self.recovery = RecurrentBlock(hidden_dim, hidden_dim, n_assets)
        self.generator = RecurrentBlock(noise_dim, hidden_dim, hidden_dim)
        self.supervisor = RecurrentBlock(hidden_dim, hidden_dim, hidden_dim)
        self.discriminator = nn.Sequential(
            nn.GRU(hidden_dim, hidden_dim, batch_first=True),
            _LastHidden(),
            nn.Linear(hidden_dim, 1),
        )


class _LastHidden(nn.Module):
    def forward(self, gru_output: tuple[torch.Tensor, torch.Tensor]) -> torch.Tensor:
        _, hidden = gru_output
        return hidden[-1]


def _make_loader(windows: np.ndarray, batch_size: int, seed: int) -> DataLoader:
    tensor = torch.from_numpy(windows.astype(np.float32))
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(TensorDataset(tensor), batch_size=batch_size, shuffle=True, generator=generator)


def _noise(batch_size: int, window_size: int, noise_dim: int, device: torch.device) -> torch.Tensor:
    return torch.rand(batch_size, window_size, noise_dim, device=device)


def _sqrt_mse(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return torch.sqrt(nn.functional.mse_loss(prediction, target) + 1e-8)


def fit_timegan(
    train_windows: np.ndarray,
    hidden_dim: int,
    noise_dim: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    gamma: float,
    supervised_weight: float,
    reconstruction_weight: float,
    seed: int,
    device: str | None = None,
) -> tuple[TimeGAN, TimeGANTrainingHistory]:
    set_torch_seed(seed)
    selected_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"Using torch device: {selected_device}")
    _, window_size, n_assets = train_windows.shape
    model = TimeGAN(n_assets=n_assets, hidden_dim=hidden_dim, noise_dim=noise_dim).to(selected_device)
    loader = _make_loader(train_windows, batch_size, seed)

    autoencoder_optimizer = torch.optim.Adam(
        list(model.embedder.parameters()) + list(model.recovery.parameters()),
        lr=learning_rate,
    )
    supervisor_optimizer = torch.optim.Adam(model.supervisor.parameters(), lr=learning_rate)
    generator_optimizer = torch.optim.Adam(
        list(model.generator.parameters()) + list(model.supervisor.parameters()),
        lr=learning_rate,
    )
    discriminator_optimizer = torch.optim.Adam(model.discriminator.parameters(), lr=learning_rate)
    embedder_optimizer = torch.optim.Adam(
        list(model.embedder.parameters()) + list(model.recovery.parameters()),
        lr=learning_rate,
    )

    history = TimeGANTrainingHistory([], [], [], [])

    for _ in range(epochs):
        losses = []
        for (batch,) in loader:
            batch = batch.to(selected_device)
            autoencoder_optimizer.zero_grad(set_to_none=True)
            hidden = model.embedder(batch)
            recovered = model.recovery(hidden)
            loss = reconstruction_weight * _sqrt_mse(recovered, batch)
            loss.backward()
            autoencoder_optimizer.step()
            losses.append(float(loss.detach().cpu()))
        history.autoencoder_loss.append(float(np.mean(losses)))

    for _ in range(epochs):
        losses = []
        for (batch,) in loader:
            batch = batch.to(selected_device)
            supervisor_optimizer.zero_grad(set_to_none=True)
            hidden = model.embedder(batch).detach()
            supervised_loss = nn.functional.mse_loss(hidden[:, 1:, :], model.supervisor(hidden)[:, :-1, :])
            supervised_loss.backward()
            supervisor_optimizer.step()
            losses.append(float(supervised_loss.detach().cpu()))
        history.supervisor_loss.append(float(np.mean(losses)))

    bce = nn.BCEWithLogitsLoss()
    for _ in range(epochs):
        generator_losses = []
        discriminator_losses = []
        for (batch,) in loader:
            batch = batch.to(selected_device)
            current_batch = batch.shape[0]
            real_labels = torch.ones(current_batch, 1, device=selected_device)
            fake_labels = torch.zeros(current_batch, 1, device=selected_device)

            generator_optimizer.zero_grad(set_to_none=True)
            embedder_optimizer.zero_grad(set_to_none=True)
            hidden = model.embedder(batch)
            supervised_hidden = model.supervisor(hidden)
            generated_hidden = model.generator(_noise(current_batch, window_size, noise_dim, selected_device))
            synthetic_hidden = model.supervisor(generated_hidden)
            synthetic_returns = model.recovery(synthetic_hidden)

            adversarial_loss = bce(model.discriminator(synthetic_hidden), real_labels)
            supervised_loss = nn.functional.mse_loss(hidden[:, 1:, :], supervised_hidden[:, :-1, :])
            moment_loss = torch.mean(torch.abs(batch.mean(dim=0) - synthetic_returns.mean(dim=0))) + torch.mean(
                torch.abs(batch.std(dim=0) - synthetic_returns.std(dim=0))
            )
            generator_loss = adversarial_loss + supervised_weight * torch.sqrt(supervised_loss + 1e-8) + moment_loss
            generator_loss.backward()
            generator_optimizer.step()
            generator_losses.append(float(generator_loss.detach().cpu()))

            embedder_optimizer.zero_grad(set_to_none=True)
            hidden = model.embedder(batch)
            recovered = model.recovery(hidden)
            supervised_hidden = model.supervisor(hidden)
            embedder_loss = reconstruction_weight * _sqrt_mse(recovered, batch) + 0.1 * nn.functional.mse_loss(
                hidden[:, 1:, :],
                supervised_hidden[:, :-1, :],
            )
            embedder_loss.backward()
            embedder_optimizer.step()

            discriminator_optimizer.zero_grad(set_to_none=True)
            with torch.no_grad():
                generated_hidden = model.generator(_noise(current_batch, window_size, noise_dim, selected_device))
                synthetic_hidden = model.supervisor(generated_hidden)
            real_loss = bce(model.discriminator(model.embedder(batch).detach()), real_labels)
            fake_loss = bce(model.discriminator(synthetic_hidden.detach()), fake_labels)
            generator_loss_only = bce(model.discriminator(generated_hidden.detach()), fake_labels)
            discriminator_loss = real_loss + fake_loss + gamma * generator_loss_only
            discriminator_loss.backward()
            discriminator_optimizer.step()
            discriminator_losses.append(float(discriminator_loss.detach().cpu()))

        history.generator_loss.append(float(np.mean(generator_losses)))
        history.discriminator_loss.append(float(np.mean(discriminator_losses)))

    return model, history


def sample_timegan(
    model: TimeGAN,
    n_scenarios: int,
    window_size: int,
    seed: int,
    device: str | None = None,
) -> np.ndarray:
    set_torch_seed(seed)
    selected_device = torch.device(device or next(model.parameters()).device)
    model.eval()
    with torch.no_grad():
        generated_hidden = model.generator(_noise(n_scenarios, window_size, model.noise_dim, selected_device))
        synthetic_hidden = model.supervisor(generated_hidden)
        samples = model.recovery(synthetic_hidden).cpu().numpy()
    return samples.astype(np.float32)
