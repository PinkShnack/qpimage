import os
from os.path import abspath, dirname
import sys
import tempfile

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import qpimage  # noqa: E402


def test_phase_array():
    size = 200
    phase = np.repeat(np.linspace(0, np.pi, size), size)
    phase = phase.reshape(size, size)
    with qpimage.QPImage(phase, data_type="phase", wavelength=600e-9) as qpi:
        assert np.all(qpi.pha == phase)


def test_file():
    h5file = tempfile.mktemp(suffix=".h5", prefix="qpimage_test_")
    size = 200
    phase = np.repeat(np.linspace(0, np.pi, size), size)
    phase = phase.reshape(size, size)
    # Write data to disk
    with qpimage.QPImage(phase,
                         data_type="phase",
                         hdf5_file=h5file,
                         hdf5_mode="a",
                         ) as qpi:
        p1 = qpi.pha
        a1 = qpi.amp
    # Open data read-only
    qpi2 = qpimage.QPImage(hdf5_file=h5file, hdf5_mode="r")
    assert np.all(p1 == qpi2.pha)
    assert np.all(a1 == qpi2.amp)
    # cleanup
    try:
        os.remove(h5file)
    except:
        pass


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()