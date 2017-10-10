import os
from os.path import abspath, dirname, join
import sys
import tempfile

import h5py
import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import qpimage  # noqa: E402
import qpimage.core  # noqa: E402


def test_qpimage_copy_to_mem():
    h5file = join(dirname(abspath(__file__)), "data/bg_ramp.h5")
    qpi = qpimage.QPImage(h5file=h5file)
    # create an in-memory copy
    qpi2 = qpi.copy()
    assert np.allclose(qpi.pha, qpi2.pha)
    assert qpi.meta == qpi2.meta


def test_qpimage_copy_to_file():
    h5file = join(dirname(abspath(__file__)), "data/bg_ramp.h5")
    qpi = qpimage.QPImage(h5file=h5file)

    tf = tempfile.mktemp(suffix=".h5", prefix="qpimage_test_")
    with qpi.copy(h5file=tf) as qpi2:
        assert np.allclose(qpi.pha, qpi2.pha)
        assert qpi.meta == qpi2.meta
        assert not np.allclose(qpi2.bg_pha, 0)
        qpi2.clear_bg(which_data="phase", keys="fit")
        assert np.allclose(qpi2.bg_pha, 0)

    with qpimage.QPImage(h5file=tf, h5mode="r") as qpi3:
        assert np.allclose(qpi3.bg_pha, 0)

    # override h5 file
    with h5py.File(tf, mode="a") as h54:
        with qpimage.QPImage(h5file=h54) as qpi4:
            assert np.allclose(qpi4.bg_pha, 0)
        qpi.copy(h5file=h54)
        with qpimage.QPImage(h5file=h54) as qpi5:
            assert not np.allclose(qpi5.bg_pha, 0)

    try:
        os.remove(tf)
    except:
        pass


def test_qpimage_copy_method():
    h5file = join(dirname(abspath(__file__)), "data/bg_ramp.h5")
    tf = tempfile.mktemp(suffix=".h5", prefix="qpimage_test_")
    qpimage.core.copyh5(inh5=h5file, outh5=tf)
    qpi1 = qpimage.QPImage(h5file=h5file, h5mode="r")
    qpi2 = qpimage.QPImage(h5file=tf, h5mode="r")
    assert np.allclose(qpi1.pha, qpi2.pha)
    assert qpi1.meta == qpi2.meta

    try:
        os.remove(tf)
    except:
        pass


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
