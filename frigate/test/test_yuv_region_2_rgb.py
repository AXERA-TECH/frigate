from unittest import TestCase, main

import av
import cv2
import numpy as np

from frigate.util.image import yuv_region_2_rgb


class TestYuvRegion2RGB(TestCase):
    def setUp(self):
        self.bgr_frame = np.zeros((100, 200, 3), np.uint8)
        self.bgr_frame[:] = (0, 0, 255)
        self.bgr_frame[5:55, 5:55] = (255, 0, 0)
        # cv2.imwrite(f"bgr_frame.jpg", self.bgr_frame)
        self.yuv_frame = (
            av.VideoFrame.from_ndarray(self.bgr_frame, format="bgr24")
            .reformat(format="nv12")
            .to_ndarray()
        )

    def test_crop_yuv(self):
        cropped = yuv_region_2_rgb(self.yuv_frame, (10, 10, 50, 50))
        # ensure the upper left pixel is blue
        assert np.allclose(cropped[0, 0], [0, 0, 255], atol=5)

    def test_crop_yuv_out_of_bounds(self):
        cropped = yuv_region_2_rgb(self.yuv_frame, (0, 0, 200, 200))
        # cv2.imwrite(f"cropped.jpg", cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
        # ensure the upper left pixel is red
        # allow small noise due to conversion
        assert np.allclose(cropped[0, 0], [255, 0, 0], atol=5)
        # ensure the bottom right is black
        assert np.allclose(cropped[199, 199], [0, 0, 0], atol=5)

    def test_crop_yuv_portrait(self):
        bgr_frame = np.zeros((1920, 1080, 3), np.uint8)
        bgr_frame[:] = (0, 0, 255)
        bgr_frame[5:55, 5:55] = (255, 0, 0)
        # cv2.imwrite(f"bgr_frame.jpg", self.bgr_frame)
        yuv_frame = (
            av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
            .reformat(format="nv12")
            .to_ndarray()
        )

        yuv_region_2_rgb(yuv_frame, (0, 852, 648, 1500))
        # cv2.imwrite(f"cropped.jpg", cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))


if __name__ == "__main__":
    main(verbosity=2)
