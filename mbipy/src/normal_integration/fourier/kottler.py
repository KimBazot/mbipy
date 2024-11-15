"""Normal integration using the method of Kottler et al.

Kottler, C., David, C., Pfeiffer, F. & Bunk, O. A two-directional approach for
grating based differential phase contrast imaging using hard x-rays 2007.
"""

from __future__ import annotations

__all__ = ("kottler",)


from typing import TYPE_CHECKING

from mbipy.src.normal_integration.padding import antisym
from mbipy.src.normal_integration.utils import check_shapes, get_dfts
from mbipy.src.utils import array_namespace, setitem

if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import NDArray


def kottler(
    gy: NDArray[floating],
    gx: NDArray[floating],
    pad: str | None = None,
    workers: int | None = None,
) -> NDArray[floating]:
    """Integrate the normal field using the method of Kottler et al.

    Parameters
    ----------
    gy : NDArray[floating]
        Component of the normal field in the vertical direction.
    gx : NDArray[floating]
        Component of the normal field in the horizontal direction.
    pad : str | None, optional
        padding of the , by default None
    workers : int | None, optional
        _description_, by default None

    Returns
    -------
    NDArray[floating]
        _description_

    Raises
    ------
    ValueError
        if pad is not None or "antisym"

    """
    # TODO(nin17): docstring
    xp = array_namespace(gy, gx)
    dtype = xp.result_type(gy, gx)
    if not xp.isdtype(dtype, "real floating"):
        msg = "Input arrays must be real-valued."
        raise ValueError(msg)
    fft2, ifft2 = get_dfts(xp)
    y, x = check_shapes(gx, gy)

    if pad == "antisym":
        gy, gx = antisym(gy=gy, gx=gx)
    elif pad is None:
        pass
    else:
        msg = f"Invalid value for pad: {pad}"
        raise ValueError(msg)

    fx = xp.astype(xp.fft.fftfreq(2 * x if pad else x), dtype, copy=False)
    fy = xp.astype(xp.fft.fftfreq(2 * y if pad else y)[:, None], dtype, copy=False)
    f_num = fft2(gx + 1j * gy, axes=(-2, -1), workers=workers)
    f_den = 1j * 2.0 * xp.pi * (fx + 1j * fy)
    # avoid division by zero warning
    f_den = setitem(f_den, (..., 0, 0), 1.0, xp)
    f_phase = f_num / f_den
    f_phase = setitem(f_phase, (..., 0, 0), 0.0, xp)

    return ifft2(f_phase, axes=(-2, -1), workers=workers).real[..., :y, :x]
