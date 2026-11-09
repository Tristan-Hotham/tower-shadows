"""Building and terrain shadows on a grid. For a sun at azimuth A and altitude h, the grid is swept along lines parallel to
the sun's direction (one line per row or column, stepping one cell along the dominant axis, so every cell is visited once);
along each line, starting on the sunny side, the height of the shadow line falls by step * tan(h) per step and is raised
by every surface higher than it. A cell is in shadow when the shadow line above it is higher than the surface there.
Grid: row 0 is the north edge, columns run west to east, north is true north."""
import numpy as np
from numba import njit, prange


@njit(parallel=True, cache=True)
def _sweep(S, dc, dr, dz_step):
    """dc, dr: direction of travel of the shadow (away from the sun) in columns and rows; one of |dc|, |dr| is 1."""
    H, W = S.shape
    out = np.zeros((H, W), np.bool_)
    if abs(dc) >= abs(dr):
        slope = dr / abs(dc); sgn = 1 if dc > 0 else -1
        extra = int(np.ceil(abs(slope) * W)) + 1
        nl = H + 2 * extra
        for li in prange(nl):
            r0 = li - extra
            m = -1e9
            for k in range(W):
                c = k if sgn > 0 else W - 1 - k
                r = int(np.floor(r0 + k * slope + 0.5))
                m -= dz_step
                if r < 0 or r >= H:
                    continue
                v = S[r, c]
                if m > v + 0.05:
                    out[r, c] = True
                if v > m:
                    m = v
    else:
        slope = dc / abs(dr); sgn = 1 if dr > 0 else -1
        extra = int(np.ceil(abs(slope) * H)) + 1
        nl = W + 2 * extra
        for li in prange(nl):
            c0 = li - extra
            m = -1e9
            for k in range(H):
                r = k if sgn > 0 else H - 1 - k
                c = int(np.floor(c0 + k * slope + 0.5))
                m -= dz_step
                if c < 0 or c >= W:
                    continue
                v = S[r, c]
                if m > v + 0.05:
                    out[r, c] = True
                if v > m:
                    m = v
    return out


def shade(S, alt, az, cell):
    """boolean mask of cells in shadow for a sun at apparent altitude alt and azimuth az (degrees from true north)"""
    if alt <= 0:
        return np.ones(S.shape, bool)
    a = np.radians(az)
    dc, dr = -np.sin(a), np.cos(a)            # away from the sun: columns east, rows south
    s = max(abs(dc), abs(dr))
    dc, dr = dc / s, dr / s
    step = cell * np.hypot(dc, dr)
    return _sweep(S.astype(np.float32), dc, dr, step * np.tan(np.radians(alt)))
