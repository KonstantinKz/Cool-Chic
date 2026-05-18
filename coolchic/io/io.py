# Software Name: Cool-Chic
# SPDX-FileCopyrightText: Copyright (c) 2023-2026 Orange
# SPDX-License-Identifier: BSD 3-Clause "New"
#
# This software is distributed under the BSD-3-Clause license.
#
# Authors: see CONTRIBUTORS.md


import os

from coolchic.io.format.chpng import read_7chpng, write_7chpng
from coolchic.io.format.png import read_png, write_png
from coolchic.io.format.ppm import read_ppm, write_ppm
from coolchic.io.format.yuv import read_yuv, write_yuv
from coolchic.io.types import FRAME_DATA_TYPE, POSSIBLE_BITDEPTH
from coolchic.utils.codingstructure import FrameData


def load_frame_data_from_file(file_paths: list[str] | str, idx_display_order: int) -> FrameData:
    """Load the idx_display_order-th frame from a .yuv file or .png file. For the latter,
    idx_display_order must be equal to 0 as there is only one frame in a png.
    Alternatively, accepts a list of 3 PNG paths [diffuse, normal, rm] to load
    a 7-channel texture tensor.

    Args:
        file_paths: Either a single file path (.yuv / .png / .ppm) or a list of
            3 PNG paths [diffuse, normal, rm] for 7-channel texture loading.
        idx_display_order: Index of the frame in display order (ignored for textures).

    Returns:
        FrameData: The loaded frame, wrapped as a FrameData object.
    """
    POSSIBLE_EXT = [".yuv", ".png", ".ppm"]

    if isinstance(file_paths, list):
        frame_data_type: FRAME_DATA_TYPE = "texture"
        data, bitdepth = read_7chpng(file_paths)

    else:
        file_path = file_paths
        assert file_path[-4:] in POSSIBLE_EXT, (
            "The function load_frame_data_from_file() expects a file ending with "
            f"{POSSIBLE_EXT}. Found {file_path}"
        )

        if file_path.endswith(".yuv"):
            bitdepth: POSSIBLE_BITDEPTH = 8 if "_8b" in file_path else 10
            frame_data_type: FRAME_DATA_TYPE = "yuv444" if "444" in file_path else "yuv420"
            data = read_yuv(file_path, idx_display_order, frame_data_type, bitdepth)

        elif file_path.endswith(".png"):
            frame_data_type: FRAME_DATA_TYPE = "rgb"
            data, bitdepth = read_png(file_path)

        elif file_path.endswith(".ppm"):
            frame_data_type: FRAME_DATA_TYPE = "rgb"
            data, bitdepth = read_ppm(file_path)

    return FrameData(bitdepth, frame_data_type, data)


def save_frame_data_to_file(frame_data: FrameData, file_path: str, append: bool = False) -> None:
    """Save the data of a FrameData into a PNG, PPM, YUV, or 7-channel texture.
    For textures (frame_data_type == "texture"), file_path is used as a base path
    and three PNGs are written: <base>_diffuse.png, <base>_normal.png, <base>_rm.png.

    Args:
        frame_data: The data to save.
        file_path:  Absolute path of the output file, or base path for textures.
        append:     Append to an existing YUV file rather than overwriting.
    """

    if frame_data.frame_data_type == "texture":
        write_7chpng(frame_data.data, file_path)
        return

    POSSIBLE_EXT = [".yuv", ".png", ".ppm"]
    cur_extension = os.path.splitext(file_path)[1]
    assert cur_extension in POSSIBLE_EXT, (
        "The function save_frame_data_to_file() expects a file ending with "
        f"{POSSIBLE_EXT}. Found {file_path}"
    )

    if cur_extension == ".png":
        assert frame_data.frame_data_type == "rgb", (
            "The function save_frame_data_to_file() can only save RGB data "
            f"into a PNG file. Found frame_data_type = {frame_data.frame_data_type}."
        )
        assert frame_data.bitdepth == 8, (
            "The function save_frame_data_to_file() can only write 8-bit data "
            f"into a PNG file. Found bitdepth = {frame_data.bitdepth}."
        )
        write_png(frame_data.data, file_path)

    elif cur_extension == ".ppm":
        assert frame_data.frame_data_type == "rgb", (
            "The function save_frame_data_to_file() can only save RGB data "
            f"into a PPM file. Found frame_data_type = {frame_data.frame_data_type}."
        )
        write_ppm(frame_data.data, frame_data.bitdepth, file_path, norm=True)

    elif cur_extension == ".yuv":
        assert frame_data.frame_data_type in ["yuv420", "yuv444"], (
            "The function save_frame_data_to_file() can only save YUV data "
            f"into a YUV file. Found frame_data_type = {frame_data.frame_data_type}."
        )
        write_yuv(
            frame_data.data,
            frame_data.bitdepth,
            frame_data.frame_data_type,
            file_path,
            norm=True,
            append=append,
        )