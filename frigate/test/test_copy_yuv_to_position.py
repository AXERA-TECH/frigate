from unittest import TestCase, main

import cv2
import numpy as np
import av

from frigate.util.image import copy_yuv_to_position


def bgr_to_nv12(frame_bgr: np.ndarray) -> np.ndarray:
    """Convert BGR to NV12 using PyAV (FFmpeg swscale)."""
    # av expects width x height in frame; format bgr24 accepted
    frame = av.VideoFrame.from_ndarray(frame_bgr, format="bgr24")
    nv12 = frame.reformat(format="nv12")
    return nv12.to_ndarray()


class TestCopyYuvToPosition(TestCase):
    def setUp(self):
        self.source_frame_bgr = np.zeros((400, 800, 3), np.uint8)
        self.source_frame_bgr[:] = (0, 0, 255)
        self.source_yuv_frame = bgr_to_nv12(self.source_frame_bgr)
        self.source_channel_dims = None

        self.dest_frame_bgr = np.zeros((400, 800, 3), np.uint8)
        self.dest_frame_bgr[:] = (112, 202, 50)
        self.dest_frame_bgr[100:300, 200:600] = (255, 0, 0)
        self.dest_yuv_frame = bgr_to_nv12(self.dest_frame_bgr)

    def test_clear_position(self):
        copy_yuv_to_position(self.dest_yuv_frame, (100, 100), (100, 100))
        # cv2.imwrite(f"source_frame_yuv.jpg", self.source_yuv_frame)
        # cv2.imwrite(f"dest_frame_yuv.jpg", self.dest_yuv_frame)

    def test_copy_position(self):
        copy_yuv_to_position(
            self.dest_yuv_frame,
            (100, 100),
            (100, 200),
            self.source_yuv_frame,
            self.source_channel_dims,
        )

    # cv2.imwrite(f"source_frame_yuv.jpg", self.source_yuv_frame)
    # cv2.imwrite(f"dest_frame_yuv.jpg", self.dest_yuv_frame)

    def test_copy_position_full_screen(self):
        copy_yuv_to_position(
            self.dest_yuv_frame,
            (0, 0),
            (400, 800),
            self.source_yuv_frame,
            self.source_channel_dims,
        )
        # cv2.imwrite(f"source_frame_yuv.jpg", self.source_yuv_frame)
        # cv2.imwrite(f"dest_frame_yuv.jpg", self.dest_yuv_frame)


if __name__ == "__main__":
    main(verbosity=2)
