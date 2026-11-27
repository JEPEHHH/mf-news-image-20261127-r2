# World Dispatch — 27 November 2026

One deterministic 1024x1024 poster summing up the world news of Friday,
27 November 2026. Eleven stories: one lead, six illustrated features, four
briefs, and a source footer.

Run with Python 3.13 standard library only:

    MAKEFUN_OUTPUT_DIR=out python3 main.py

The program encodes the PNG itself with zlib and struct. No Pillow, no font
files, no network, no timestamps, no randomness. Two runs yield identical
bytes at out/entry.png. Set MAKEFUN_OUTPUT_DIR to choose the target folder;
the default is /output.

render_colab.py is a thin wrapper for a Colab notebook cell: it renders to
/content and prints the image size and sha256 digest.

MIT licensed, copyright 2026 jepehhh.
