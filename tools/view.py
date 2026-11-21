"""Live depth + colour preview with OpenCV.  Press q or Esc to quit."""
import cv2
from astra import Astra, colorize

with Astra() as cam:
    while True:
        depth, color = cam.read()
        cv2.imshow("Astra depth", colorize(depth))
        if color is not None:
            cv2.imshow("Astra colour", color)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break
cv2.destroyAllWindows()
