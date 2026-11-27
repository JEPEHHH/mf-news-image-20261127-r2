"""Colab cell wrapper: render the poster into /content and report its digest."""

import hashlib
import os

import main


def colab_render():
    target, data = main.render("/content")
    with open(target, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    print("%s: %d bytes" % (os.path.basename(target), len(data)))
    print("sha256: %s" % digest)
    return target


if __name__ == "__main__":
    colab_render()
