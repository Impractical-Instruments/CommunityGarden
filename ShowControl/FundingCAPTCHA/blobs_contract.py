"""The layout of the blob-records texture: the one place the tracker and the shaders agree on it.

ADR-0022. The "blobs" channel source is BLOB_SLOTS columns x BLOB_ROWS rows of
RGBA32F, read in GLSL with texelFetch(ch, ivec2(slot, row), 0):

  row 0  x0, y0, x1, y1         bounding box, Body UV (y up)
  row 1  cx, cy, vx, vy         centroid (UV) and velocity (UV/s)
  row 2  id, state, age_s, near stable id 1-999, BLOB_* state, seconds in
                                that state, mean Body nearness

A slot keeps its track for the track's whole life. The GLSL side repeats these
numbers (SLOTS in each shader's common.glsl, S_EMPTY..S_LOST or the
equivalents, and shaders/blob_painter.glsl); test_blobs_contract.py fails when
they drift from this file. Changing any value here breaks Setups.
"""
BLOB_SLOTS = 8
BLOB_ROWS  = 3
BLOB_EMPTY, BLOB_TENTATIVE, BLOB_CONFIRMED, BLOB_COASTING, BLOB_LOST = range(5)
