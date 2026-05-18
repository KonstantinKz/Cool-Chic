import os
from typing import Tuple

import numpy as np
import torch
from einops import rearrange
from PIL import Image
from torch import Tensor
from torchvision.transforms.functional import to_tensor

from coolchic.io.types import POSSIBLE_BITDEPTH


def read_7chpng(file_paths: list[str]) -> Tuple[Tensor, POSSIBLE_BITDEPTH]:
    """Read three PNG textures and pack them into a single 7-channel tensor.

    Channel layout:
        [0:3] Diffuse RGB        (from file_paths[0])
        [3:5] Normal  RG         (from file_paths[1], B dropped)
        [5:6] RM      R          (from file_paths[2])
        [6:7] RM      G or zeros (from file_paths[2] if it has >= 2 channels)

    Args:
        file_paths: [diffuse_path, normal_path, rm_path]

    Returns:
        Image data [1, 7, H, W] in [0., 1.] and the diffuse bitdepth.
    """
    assert len(file_paths) == 3, (
        f"Expected exactly 3 paths [diffuse, normal, rm], got {len(file_paths)}"
    )
    diffuse_path, normal_path, rm_path = file_paths

    for p in file_paths:
        assert os.path.isfile(p), f"No file found at {p}"

    # [1, C, H, W] — C may be 3 or 4 (RGBA), we slice what we need
    diffuse = to_tensor(Image.open(diffuse_path))  # [C, H, W]
    normal  = to_tensor(Image.open(normal_path))
    rm      = to_tensor(Image.open(rm_path))

    diff_rgb = diffuse[:3]                                          # [3, H, W]
    norm_rg  = normal[:2]                                          # [2, H, W]
    rm_r     = rm[0:1]                                             # [1, H, W]
    rm_g     = rm[1:2] if rm.shape[0] >= 2 else torch.zeros_like(rm_r)  # [1, H, W]

    combined = torch.cat([diff_rgb, norm_rg, rm_r, rm_g], dim=0)  # [7, H, W]
    combined = rearrange(combined, "c h w -> 1 c h w")             # [1, 7, H, W]

    return combined, 8


@torch.no_grad()
def write_7chpng(data: Tensor, file_path: str) -> None:
    """Unpack a 7-channel tensor back into three PNG textures.

    Output paths are derived from file_path (extension stripped):
        <base>_diffuse.png  – channels 0-2 (RGB)
        <base>_normal.png   – channels 3-4 (RG) + reconstructed B
        <base>_rm.png       – channels 5-6 (RG, B zeroed)

    Args:
        data:      [1, 7, H, W] in [0., 1.]
        file_path: Base output path; suffixes are appended automatically.
    """
    assert data.ndim == 4 and data.shape[0] == 1 and data.shape[1] == 7, (
        f"Expected [1, 7, H, W], got {tuple(data.shape)}"
    )

    base = os.path.splitext(file_path)[0]
    x = data.squeeze(0).cpu().detach()  # [7, H, W]

    def _save(chw: Tensor, suffix: str) -> None:
        arr = rearrange(chw, "c h w -> h w c")
        arr = np.clip(arr.numpy(), 0.0, 1.0)
        arr = np.round(arr * 255).astype(np.uint8)
        Image.fromarray(arr, mode="RGB").save(f"{base}{suffix}.png")

    # Diffuse
    _save(x[0:3], "_diffuse")

    # Normal: reconstruct B so the map stays on the unit hemisphere
    rg_01     = x[3:5]                                             # [2, H, W] in [0,1]
    rg_signed = rg_01 * 2.0 - 1.0                                 # remap to [-1, 1]
    b_signed  = torch.sqrt((1.0 - rg_signed[0] ** 2 - rg_signed[1] ** 2).clamp(0.0, 1.0))
    b_01      = (b_signed.unsqueeze(0) + 1.0) / 2.0               # back to [0, 1]
    _save(torch.cat([rg_01, b_01], dim=0), "_normal")

    # RM: R=roughness, G=metalness, B=zeros
    H, W  = x.shape[-2], x.shape[-1]
    rm_rgb = torch.cat([x[5:7], torch.zeros(1, H, W)], dim=0)
    _save(rm_rgb, "_rm")