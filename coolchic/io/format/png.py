# Software Name: Cool-Chic
# SPDX-FileCopyrightText: Copyright (c) 2023-2025 Orange
# SPDX-License-Identifier: BSD 3-Clause "New"
#
# This software is distributed under the BSD-3-Clause license.
#
# Authors: see CONTRIBUTORS.md


import os
from typing import Tuple

import numpy as np
import torch
from einops import rearrange
from PIL import Image
from torch import Tensor
from torchvision.transforms.functional import to_tensor

from coolchic.io.types import POSSIBLE_BITDEPTH

def _open_as_float(path: str) -> Tensor:
    """Open a PNG and return a float32 [C, H, W] tensor in [0, 1],
    handling both 8-bit (mode RGB/L/RGBA) and 16-bit (mode I/I;16) correctly.
    """
    img = Image.open(path)

    if img.mode == "I":
        # 16-bit grayscale: PIL stores as int32, normalize by 2^16 - 1
        arr = np.array(img, dtype=np.float32) / 65535.0          # [H, W]
        arr = arr[:, :, np.newaxis]                               # [H, W, 1]
        return torch.from_numpy(arr).permute(2, 0, 1)            # [1, H, W]

    elif img.mode == "I;16":
        arr = np.frombuffer(img.tobytes(), dtype=np.uint16)
        arr = arr.reshape(img.size[1], img.size[0]).astype(np.float32) / 65535.0
        arr = arr[:, :, np.newaxis]
        return torch.from_numpy(arr).permute(2, 0, 1)            # [1, H, W]

    else:
        # 8-bit: RGB, RGBA, L — to_tensor handles these correctly
        return to_tensor(img)                                     # [C, H, W]

def read_png(file_path: str) -> Tuple[Tensor, POSSIBLE_BITDEPTH]:
    """Read a PNG file

    Args:
        file_path: Path of the png file to read.

    Returns:
        Image data [1, 3, H, W] in [0., 1.] and its bitdepth.
    """

    assert os.path.isfile(file_path), f"No file found at {file_path}"

    data = _open_as_float(file_path)
    data = rearrange(data, "c h w -> 1 c h w")

    # Bitdepth is always 8 when we read PNG through PIL?
    bitdepth = 8

    return data[:,:3, :, :], bitdepth


@torch.no_grad()
def write_png(data: Tensor, file_path: str) -> None:
    """Save an image x into a PNG file.

    Args:
        x: Image to be saved
        file_path: Where to save the PNG files
    """
    data = rearrange(data, "1 c h w -> h w c", c=3)

    assert len(data.shape) == 3 and data.shape[-1] == 3, (
        f"Data shape must be [H, W, 3], found {data.shape}"
    )

    data = np.clip(data.cpu().detach().numpy(), 0.0, 1.0)
    data = np.round(data * 255).astype(np.uint8)

    im = Image.fromarray(data, mode="RGB")
    im.save(file_path)
