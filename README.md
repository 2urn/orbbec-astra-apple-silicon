# Orbbec Astra on Apple Silicon Macs

**Bring your original Orbbec Astra 3D camera back to life on an M1/M2/M3/M4 Mac. Use it in Resolume, TouchDesigner, MadMapper, OpenCV, Python, browser apps, or your own tools.**

Orbbec no longer supports the original Astra on the Mac. Their current software finds the camera, then ignores it, and their older OpenNI drivers were only released for Windows, Linux and Android. If you own one of these cameras and switched to an Apple Silicon Mac, it has probably been sitting in a drawer.

This project fixes that. It builds the open-source OpenNI2 driver for Apple Silicon with a few small changes so it recognises the Astra. You get live **depth** and **colour** video at 30 frames per second, a viewer app, video feeds for creative software, and simple ways to use the camera in your own code.

---

## Why this matters

Depth cameras like the Astra were made in huge numbers around 2015–2018 for robotics, art installations, research and games. The hardware still works fine: an infrared projector, a depth sensor and a colour camera, all over a single USB cable. What breaks is the software. A company moves on, an operating system changes, and a working device becomes e-waste.

This project shows that a dropped device can often be revived:

- **The device still speaks a language we know.** The Astra's chip uses almost the same protocol as the PrimeSense sensor in the original Microsoft Kinect. That protocol is documented in open-source code (OpenNI2).
- **The fixes were tiny.** Getting it working took four small changes. The driver needed the Astra's USB ID, a fix for how macOS numbers USB ports, a build setting for Apple Silicon, and the right colour format. Each one is described below and in [`patches/`](patches/).
- **Open source made it possible.** Because OpenNI2 is open source, anyone can read it, fix it and rebuild it for a computer that didn't exist when it was written.

If you have another "unsupported" camera, controller or sensor, the same approach often works. Find out what it actually is, find the open-source driver for its family, and make the small changes it needs. Old hardware is cheap, plentiful and often excellent. Keeping it running is good for artists, for schools and labs on a budget, and for the planet.

---

## What you need

- A Mac with Apple Silicon (M1 or newer)
- An **original Orbbec Astra**. On the Mac, Apple menu → About This Mac → More Info → System Report → USB should list it as "ORBBEC Depth Sensor", Product ID `0x0401`.
- Plug it directly into your Mac if you can. Chains of hubs can make the picture choppy, but a small USB-C hub works.
- About 10 minutes and an internet connection for the one-time setup

> **Other Astra models** (Astra S, Astra Pro, Astra Mini…) might work with a one-line change but haven't been tested. If you try one, please open an issue and tell us what happened.

---

## Setup (one time)

1. **Download this project.** On GitHub, click the green **Code** button → **Download ZIP**, then double-click the ZIP to unzip it. Put the folder anywhere you like, for example in Documents.
2. **Double-click `Setup (run first).command`.**
   - macOS may say it *"can't be opened because Apple cannot verify it"*. This happens with every script downloaded from the internet. Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the message. You can also right-click the file and choose **Open**.
   - If your Mac doesn't have Apple's free developer tools yet, a window will offer to install them. Click **Install**, wait for it to finish, then double-click the Setup file again.
3. A Terminal window shows progress. When it says **All set!**, you're done. This takes about 5–10 minutes.

You only do this once.

---

## Using the camera

### See it: `Astra Viewer` app

Double-click **Astra Viewer** to open a live viewer with depth and colour side by side.
- Press number keys to switch views, **p** to show the distance under your mouse, **?** for every key, and **Esc** to quit.
- Drag the app to your Dock for one-click access. Keep the app itself in this folder, because it runs the camera software stored next to it.
- The first time you open it, macOS may block it. Use **System Settings → Privacy & Security → Open Anyway**.
- `Astra Viewer.command` does the same thing in a Terminal window, which shows error messages if something goes wrong.
- Don't drag a box on the picture. The red rectangle is a crop tool the Astra doesn't handle well; it can cause stripes or close the viewer. Press **/** to undo a crop.

### Use it in Resolume, TouchDesigner, MadMapper, VDMX or OBS: `Astra to Syphon.command`

Double-click it and **leave the Terminal window open**. While it runs, three live video feeds appear in any app that supports **Syphon**:

| Feed | What it is | Good for |
|---|---|---|
| **Astra Depth** | Distance shown as colour: warm is near, cool is far | Visual effects, displacement, generative visuals |
| **Astra Colour** | The normal camera picture | Mixing with the depth feed |
| **Astra Mask** | White wherever something is 0.5–1.5 m from the camera, black elsewhere | Silhouettes, cut-outs, using a person as a mask or trigger |

Where to find them:
- **Resolume:** Sources panel → **Syphon** → drag *Astra Depth*, *Astra Mask* or *Astra Colour* onto a clip slot.
- **TouchDesigner:** add a **Syphon Spout In** TOP and pick the feed.
- **MadMapper:** Media → **Syphon**.
- **OBS:** add a **Syphon Client** source.

To stop, close the Terminal window.

**Changing the mask distance or depth style.** Open Terminal, drag `Astra to Syphon.command` into it, add options, then press Return. For example:

```
"/path/to/Astra to Syphon.command" --near 800 --far 2500 --grey
```

- `--near` and `--far` set the mask range in millimetres.
- `--grey` makes the depth feed black-and-white (bright is near) instead of coloured.
- `--no-colour` skips the colour camera.

### Use it in browser apps: `Astra Web Bridge.command`

Double-click it and leave the window open. It streams the camera's depth and colour to web pages and browser apps on this Mac at `ws://localhost:8766`. It's for people building their own browser visuals; see the developer notes below. Only this Mac can connect.

Only one program can use the camera at a time, so quit the Viewer before starting Syphon or the bridge, and the other way round.

---

## For developers

### Python and OpenCV

Setup creates a Python environment in `.venv/` with OpenNI, NumPy, OpenCV, Syphon and websockets. [`tools/astra.py`](tools/astra.py) is a small helper:

```python
from astra import Astra, colorize   # run from the tools/ folder, or add it to sys.path
import cv2

with Astra() as cam:                # 640x480 @ 30 fps; colour is lined up with depth
    while True:
        depth_mm, color_bgr = cam.read()   # numpy: uint16 millimetres, uint8 BGR
        cv2.imshow("depth", colorize(depth_mm))
        cv2.imshow("colour", color_bgr)
        if cv2.waitKey(1) == 27:
            break
```

To try it, run `.venv/bin/python tools/view.py`.

The usual `pip install opencv-python` doesn't include OpenNI support (`cv2.CAP_OPENNI2`), so read frames with `astra.py` and pass the arrays to OpenCV as shown above.

### Browser apps (JavaScript)

[`tools/web_bridge.py`](tools/web_bridge.py) streams frames over a WebSocket on `ws://localhost:8766`, available only to this Mac. Run it with `--web FOLDER` to also serve your own pages on `http://localhost:8765`, and `--full` for 640×480.

Each message is one binary frame:

| Bytes | Content |
|---|---|
| 0–3 | `AST1` |
| 4–5 | width, uint16 little-endian (320 by default; 640 with `--full`) |
| 6–7 | height, uint16 little-endian |
| next `w*h*2` | depth in millimetres, uint16 (0 = no reading) |
| next `w*h*3` | RGB colour, lined up with the depth |

```js
const ws = new WebSocket("ws://localhost:8766");
ws.binaryType = "arraybuffer";
ws.onmessage = ({ data }) => {
  const v = new DataView(data), w = v.getUint16(4, true), h = v.getUint16(6, true);
  const depth = new Uint16Array(data, 8, w * h);           // millimetres
  const rgb = new Uint8Array(data, 8 + w * h * 2, w * h * 3);
  // ...draw it, track hands, trigger sounds...
};
```

To turn depth into 3D points: the Astra's field of view is 58.6° × 45.6°. A pixel `(u, v)` at depth `z` metres sits at `x = (u − w/2)·z/fx`, `y = −(v − h/2)·z/fy`, where `fx = (w/2)/tan(58.6°/2)` and `fy = (h/2)/tan(45.6°/2)`. Pages served from `https://` sites can also connect to `ws://localhost` in Chrome.

### C / C++ and other languages

`dist/` is a self-contained, relocatable OpenNI2 install:
- `libOpenNI2.dylib`
- `OpenNI2/Drivers/libPS1080.dylib`
- a bundled `libusb`

Headers are in `dist/include`. Any program written against the standard OpenNI2 API should work. Point it at `dist/` with `openni::OpenNI::initialize()`, or copy `dist/` next to your app.

### What was changed

The changes are made to [structureio/OpenNI2](https://github.com/structureio/OpenNI2) at commit `3b787cc`, the last upstream OpenNI2 release. See [`patches/openni2-apple-silicon-astra.patch`](patches/openni2-apple-silicon-astra.patch).

1. **`XnDeviceEnumeration.cpp`:** adds the Astra's USB ID `2BC5:0401` to the PS1080 driver's list of supported devices.
2. **`XnLinuxUSB.cpp`:** macOS can report the USB bus number as 0, which the old code treated as invalid. This change lets it open the device.
3. **Build system:** adds an Apple Silicon (`arm64`) platform. The old build only knew Intel Macs and 32-bit ARM.
4. **`glh_linear.h`:** fixes a name clash between an old OpenGL helper and modern C++ headers, so NiViewer compiles.

Also, `build.sh` sets the colour input format to *uncompressed YUV422* (`InputFormat=5` in `PS1080.ini`). The driver's default format produces "Image frame is corrupt!" errors and no colour picture on the Astra.

`build.sh` downloads [libusb](https://libusb.info) 1.0.30 (checksum-verified) and OpenNI2, applies the patch, compiles both, and puts everything in `dist/`. It doesn't need Homebrew or administrator rights, and works from folders whose names contain spaces.

### Tested on

- Original Orbbec Astra: USB `2bc5:0401`, firmware 5.8.22, connected over USB 2.0 through a USB-C hub
- macOS 27 on Apple Silicon, Apple Command Line Tools (clang 21), Python 3.9

---

## Troubleshooting

- **"No device" or "Couldn't open device":**
  - Unplug and replug the camera.
  - Quit any other program using it, such as Orbbec's own viewer.
  - Only one program can use the camera at a time.
- **Choppy or flickering picture:**
  - Connect the camera directly to the Mac, or with fewer hubs in between.
  - Depth cameras can't see glass, mirrors, black velvet or bright sunlight, so those areas appear black.
- **Black patches in the depth image:** these are normal. They're places the infrared pattern can't reach, such as shadows behind objects or surfaces that are too close or too far.
- **Nothing appears in Resolume:** check that the `Astra to Syphon` Terminal window is still open and printing "fps" lines.

## License

The OpenNI2 changes and the scripts in this repository are released under the Apache License 2.0, the same license as OpenNI2 ([LICENSE](LICENSE)). OpenNI2 and libusb are downloaded from their original sources at build time and keep their own licenses. libusb uses LGPL-2.1.

Orbbec and Astra are trademarks of Orbbec Inc. This is an independent community project. It is not affiliated with or endorsed by Orbbec.
