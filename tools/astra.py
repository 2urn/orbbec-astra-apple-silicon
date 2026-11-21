"""Tiny helper for reading the Orbbec Astra from Python via the OpenNI2 build in ../dist.

    from astra import Astra
    with Astra() as cam:
        depth_mm, color_bgr = cam.read()   # numpy arrays (uint16 mm, uint8 BGR)
"""
import os
import numpy as np
from openni import openni2

DIST = os.environ.get(
    "ASTRA_OPENNI2_DIST",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist"),
)


class Astra:
    def __init__(self, width=640, height=480, fps=30, color=True):
        openni2.initialize(os.path.abspath(DIST))
        self.dev = openni2.Device.open_any()
        self.depth = self.dev.create_depth_stream()
        self.depth.set_video_mode(openni2.VideoMode(
            pixelFormat=openni2.PIXEL_FORMAT_DEPTH_1_MM,
            resolutionX=width, resolutionY=height, fps=fps))
        self.depth.start()
        self.color = None
        if color:
            self.color = self.dev.create_color_stream()
            self.color.set_video_mode(openni2.VideoMode(
                pixelFormat=openni2.PIXEL_FORMAT_RGB888,
                resolutionX=width, resolutionY=height, fps=fps))
            self.color.start()
            try:  # line colour up with depth when the firmware supports it
                self.dev.set_image_registration_mode(
                    openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR)
            except Exception:
                pass

    def read_depth(self):
        f = self.depth.read_frame()
        return np.frombuffer(f.get_buffer_as_uint16(), dtype=np.uint16).reshape(
            f.height, f.width).copy()

    def read_color(self):
        f = self.color.read_frame()
        rgb = np.frombuffer(f.get_buffer_as_uint8(), dtype=np.uint8).reshape(
            f.height, f.width, 3)
        return rgb[:, :, ::-1].copy()  # RGB -> BGR for OpenCV

    def read(self):
        return self.read_depth(), (self.read_color() if self.color else None)

    def close(self):
        for s in (self.depth, self.color):
            if s is not None:
                s.stop()
        self.dev.close()
        openni2.unload()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def colorize(depth_mm, near=400, far=4000):
    """Depth in mm -> false-colour BGR image (near = warm, far = cool, 0 = black)."""
    import cv2
    d = np.clip((depth_mm.astype(np.float32) - near) / (far - near), 0, 1)
    img = cv2.applyColorMap((255 - d * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    img[depth_mm == 0] = 0
    return img
