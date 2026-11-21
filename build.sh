#!/bin/bash
# Build OpenNI2 for Apple Silicon Macs with support for the original Orbbec Astra.
# Result: ./dist (NiViewer, SimpleRead, libOpenNI2.dylib, PS1080 driver, libusb)
#
# Needs only Apple's Command Line Tools (xcode-select --install). No Homebrew.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DIST="$ROOT/dist"
# OpenNI2's makefiles and libtool break on paths with spaces (e.g. "My Drive"),
# so compile in a space-free temp folder and only copy the result into dist/.
BUILD="${ASTRA_BUILD_DIR:-/tmp/astra-openni2-build-$(id -u)}"
PREFIX="$BUILD/prefix"

LIBUSB_VER=1.0.30
LIBUSB_SHA256=fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf
OPENNI2_REPO=https://github.com/structureio/OpenNI2.git
OPENNI2_COMMIT=3b787cc8b06e4129d1c5d7daf99e04413ac42266

case "$BUILD" in
  *" "*) echo "ERROR: ASTRA_BUILD_DIR must not contain spaces: $BUILD"; exit 1 ;;
esac

if [ "$(uname -m)" != "arm64" ]; then
  echo "ERROR: this script is for Apple Silicon (arm64) Macs."; exit 1
fi
xcode-select -p >/dev/null 2>&1 || { echo "ERROR: run 'xcode-select --install' first."; exit 1; }

mkdir -p "$BUILD"
cd "$BUILD"

# --- libusb -----------------------------------------------------------------
if [ ! -f "$PREFIX/lib/libusb-1.0.0.dylib" ]; then
  echo "==> Building libusb $LIBUSB_VER"
  TARBALL="libusb-$LIBUSB_VER.tar.bz2"
  [ -f "$TARBALL" ] || curl -fsSLO "https://github.com/libusb/libusb/releases/download/v$LIBUSB_VER/$TARBALL"
  echo "$LIBUSB_SHA256  $TARBALL" | shasum -a 256 -c -
  rm -rf "libusb-$LIBUSB_VER"
  tar xjf "$TARBALL"
  (cd "libusb-$LIBUSB_VER" && ./configure --prefix="$PREFIX" --disable-static >/dev/null \
     && make -j"$(sysctl -n hw.ncpu)" >/dev/null && make install >/dev/null)
fi

# --- OpenNI2 ----------------------------------------------------------------
if [ ! -d OpenNI2 ]; then
  echo "==> Fetching OpenNI2"
  git clone -q "$OPENNI2_REPO" OpenNI2
  git -C OpenNI2 checkout -q "$OPENNI2_COMMIT"
  git -C OpenNI2 apply "$ROOT/patches/openni2-apple-silicon-astra.patch"
fi

echo "==> Building OpenNI2 (takes a few minutes)"
cd OpenNI2
make -j"$(sysctl -n hw.ncpu)" ALLOW_WARNINGS=1 LIBUSB_PREFIX="$PREFIX" \
  ThirdParty/PSCommon/XnLib/Source Source/DepthUtils Source/Core Source/Drivers/PS1080 \
  > "$BUILD/openni2-core.log" 2>&1 || { echo "Build failed, see $BUILD/openni2-core.log"; exit 1; }
make ALLOW_WARNINGS=1 LIBUSB_PREFIX="$PREFIX" Samples/SimpleRead Source/Tools/NiViewer \
  > "$BUILD/openni2-tools.log" 2>&1 || { echo "Build failed, see $BUILD/openni2-tools.log"; exit 1; }

# --- Assemble a self-contained dist/ folder ---------------------------------
echo "==> Assembling dist/"
OUT="$BUILD/OpenNI2/Bin/Arm64-Release"
rm -rf "$DIST"
mkdir -p "$DIST/OpenNI2/Drivers"
cp "$OUT/libOpenNI2.dylib" "$OUT/NiViewer" "$OUT/SimpleRead" "$DIST/"
cp "$OUT/OpenNI2/Drivers/libPS1080.dylib" "$DIST/OpenNI2/Drivers/"
cp "$BUILD/OpenNI2/Config/OpenNI.ini" "$DIST/"
cp "$BUILD/OpenNI2/Config/OpenNI2/Drivers/PS1080.ini" "$DIST/OpenNI2/Drivers/"
cp "$PREFIX/lib/libusb-1.0.0.dylib" "$DIST/"
cp -R "$BUILD/OpenNI2/Include" "$DIST/include"

# The Astra's colour camera sends uncompressed YUV422 over bulk USB; the driver's
# default (compressed YUV422) gives "Image frame is corrupt!" and no colour frames.
awk '/^\[/{s=$0} s=="[Image]" && /^;?InputFormat=/{$0="InputFormat=5"} {print}' \
  "$DIST/OpenNI2/Drivers/PS1080.ini" > "$DIST/PS1080.ini.tmp" && mv "$DIST/PS1080.ini.tmp" "$DIST/OpenNI2/Drivers/PS1080.ini"

# Make the folder relocatable: point everything at libraries next to it.
install_name_tool -id @rpath/libusb-1.0.0.dylib "$DIST/libusb-1.0.0.dylib"
install_name_tool -id @rpath/libOpenNI2.dylib "$DIST/libOpenNI2.dylib"
install_name_tool -change "$PREFIX/lib/libusb-1.0.0.dylib" @loader_path/../../libusb-1.0.0.dylib \
  "$DIST/OpenNI2/Drivers/libPS1080.dylib"
for exe in NiViewer SimpleRead; do
  install_name_tool -change libOpenNI2.dylib @executable_path/libOpenNI2.dylib "$DIST/$exe"
done
# Changing load paths invalidates the signature; re-sign ad hoc so macOS will run them.
for f in "$DIST"/*.dylib "$DIST"/OpenNI2/Drivers/*.dylib "$DIST/NiViewer" "$DIST/SimpleRead"; do
  codesign -f -s - "$f" 2>/dev/null
done

echo
echo "Done. Plug in the Astra and run:"
echo "  $DIST/SimpleRead     (prints the centre depth value)"
echo "  $DIST/NiViewer       (live depth + colour window)"
