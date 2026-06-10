"""1-D U-Net architecture for ECG wave segmentation.

The model takes a single-lead ECG signal and produces a per-sample
classification into {background, P-wave, QRS, T-wave}.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .labels import _CLASS_COUNT


class _ConvBlock(nn.Module):
    """Two 1-D convolutions + BatchNorm + ReLU."""

    def __init__(self, in_ch: int, out_ch: int, kernel_size: int = 7) -> None:
        super().__init__()
        pad = kernel_size // 2
        self.block = nn.Sequential(
            nn.Conv1d(in_ch, out_ch, kernel_size, padding=pad),
            nn.BatchNorm1d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv1d(out_ch, out_ch, kernel_size, padding=pad),
            nn.BatchNorm1d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class UNet1D(nn.Module):
    """Lightweight 1-D U-Net for ECG wave delineation.

    Parameters
    ----------
    in_channels : int
        Number of input channels (1 for single-lead).
    n_classes : int
        Number of output segmentation classes.
    base_filters : int
        Number of filters in the first encoder stage.
    depth : int
        Number of encoder / decoder stages.
    kernel_size : int
        Convolution kernel size.
    """

    def __init__(
        self,
        in_channels: int = 1,
        n_classes: int = _CLASS_COUNT,
        base_filters: int = 32,
        depth: int = 4,
        kernel_size: int = 7,
    ) -> None:
        super().__init__()
        self.depth = depth

        # Encoder
        self.encoders = nn.ModuleList()
        self.pools = nn.ModuleList()
        ch = in_channels
        for i in range(depth):
            out_ch = base_filters * (2 ** i)
            self.encoders.append(_ConvBlock(ch, out_ch, kernel_size))
            self.pools.append(nn.MaxPool1d(2))
            ch = out_ch

        # Bottleneck
        self.bottleneck = _ConvBlock(ch, ch * 2, kernel_size)

        # Decoder
        self.upconvs = nn.ModuleList()
        self.decoders = nn.ModuleList()
        ch = ch * 2
        for i in range(depth - 1, -1, -1):
            out_ch = base_filters * (2 ** i)
            self.upconvs.append(nn.ConvTranspose1d(ch, out_ch, kernel_size=2, stride=2))
            self.decoders.append(_ConvBlock(out_ch * 2, out_ch, kernel_size))
            ch = out_ch

        self.head = nn.Conv1d(ch, n_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        x : torch.Tensor
            Input of shape ``(batch, in_channels, length)``.

        Returns
        -------
        torch.Tensor of shape ``(batch, n_classes, length)``
            Raw logits per sample.
        """
        skips: list[torch.Tensor] = []
        for enc, pool in zip(self.encoders, self.pools):
            x = enc(x)
            skips.append(x)
            x = pool(x)

        x = self.bottleneck(x)

        for up, dec, skip in zip(self.upconvs, self.decoders, reversed(skips)):
            x = up(x)
            # Crop / pad to match skip connection length
            diff = skip.size(2) - x.size(2)
            if diff > 0:
                x = nn.functional.pad(x, (0, diff))
            elif diff < 0:
                x = x[:, :, : skip.size(2)]
            x = torch.cat([x, skip], dim=1)
            x = dec(x)

        return self.head(x)
