"""Send the Astra to Resolume, MadMapper, TouchDesigner, VDMX, OBS (with the Syphon
plugin) etc. as live Syphon video sources:

    "Astra Depth"   false-colour depth      (or grey with --grey)
    "Astra Colour"  the RGB camera
    "Astra Mask"    white where something is between --near and --far, black elsewhere

Usage:  python syphon_out.py [--near 500] [--far 1500] [--grey] [--no-colour]
Press Ctrl+C to stop.
"""
import argparse
import time

import cv2
import numpy as np
import syphon
from syphon.utils.numpy import copy_image_to_mtl_texture
from syphon.utils.raw import create_mtl_texture
from Foundation import NSDate, NSRunLoop

from astra import Astra, colorize

ap = argparse.ArgumentParser()
ap.add_argument("--near", type=int, default=500, help="mask: nearest distance in mm")
ap.add_argument("--far", type=int, default=1500, help="mask: furthest distance in mm")
ap.add_argument("--grey", action="store_true", help="depth as greyscale instead of colour")
ap.add_argument("--no-colour", action="store_true", help="don't send the RGB camera")
args = ap.parse_args()


class Out:
    def __init__(self, name, w, h):
        self.server = syphon.SyphonMetalServer(name)
        self.tex = create_mtl_texture(self.server.device, w, h)

    def send(self, bgr_or_grey):
        img = bgr_or_grey
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        copy_image_to_mtl_texture(np.ascontiguousarray(img), self.tex)
        self.server.publish_frame_texture(self.tex)

    def stop(self):
        self.server.stop()


with Astra(color=not args.no_colour) as cam:
    depth, color = cam.read()
    h, w = depth.shape
    outs = {"depth": Out("Astra Depth", w, h), "mask": Out("Astra Mask", w, h)}
    if color is not None:
        outs["colour"] = Out("Astra Colour", color.shape[1], color.shape[0])
    print("Publishing Syphon sources:", ", ".join(
        "Astra " + k.capitalize() for k in outs), "- press Ctrl+C to stop.")
    frames, t0 = 0, time.time()
    try:
        while True:
            if args.grey:
                # near = bright, far = dark, no reading = black
                d = 255 - np.clip(depth / 4000.0 * 255, 0, 255).astype(np.uint8)
                d[depth == 0] = 0
                outs["depth"].send(d)
            else:
                outs["depth"].send(colorize(depth))
            mask = ((depth >= args.near) & (depth <= args.far)).astype(np.uint8) * 255
            outs["mask"].send(cv2.medianBlur(mask, 5))
            if color is not None:
                outs["colour"].send(color)
            # Let macOS deliver Syphon's discovery messages, so apps like Resolume
            # can find these sources even if they were opened after this script.
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.001))
            frames += 1
            if time.time() - t0 >= 5:
                print(f"{frames / (time.time() - t0):.1f} fps")
                frames, t0 = 0, time.time()
            depth, color = cam.read()
    except KeyboardInterrupt:
        pass
    finally:
        for o in outs.values():
            o.stop()
