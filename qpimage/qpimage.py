import h5py
import numpy as np
from skimage.restoration import unwrap_phase

from .image_data import Amplitude, Phase


class QPImage(object):
    def __init__(self, data=None, bg_data=None, data_type="phase",
                 hdf5_file=None, hdf5_mode="a",
                 pixel_size=None, wavelength=None, time=None,
                 ):
        """Quantitative phase image management

        Parameters
        ----------
        data: 2d ndarray (float or complex) or list
            The experimental data (see `data_type`)
        bg_data: 2d ndarray (float or complex), list, or `None`
            The background data (must be same type as `data`)
        data_type: str
            String or comma-separated list of strings indicating
            the order and type of input data. Valid values are
            "field", "phase", "phase,amplitude", or "phase,intensity",
            where the latter two require an indexable object with
            the phase data as first element.
        pixel_size: float
            Pixel size [m]
        time: float
            Time point of data recording [s]
        wavelength: float
            Wavelength of the radiation used [m]

        Properties
        ----------
        meta: dict
            Dictionary holding all meta information such as
            wavelength and sampling
        """
        if hdf5_file is None:
            h5kwargs = {"name": "none.h5",
                        "driver": "core",
                        "backing_store": False,
                        "mode": "a"}
        else:
            h5kwargs = {"name": hdf5_file,
                        "mode": hdf5_mode}
        self.h5 = h5py.File(**h5kwargs)

        for group in ["amplitude", "phase"]:
            if group not in self.h5:
                self.h5.create_group(group)

        self._amp = Amplitude(self.h5["amplitude"])
        self._pha = Phase(self.h5["phase"])

        if data is not None:
            # compute phase and amplitude from input data
            amp, pha = self._get_amp_pha(data=data,
                                         data_type=data_type)
            self._amp["raw"] = amp
            self._pha["raw"] = pha

            # set background data
            self.set_bg_data(bg_data=bg_data,
                             data_type=data_type)
        # set meta data
        if pixel_size:
            self.h5.attrs["pixel_size"] = pixel_size
        if time:
            self.h5.attrs["time"] = time
        if wavelength:
            self.h5.attrs["wavelength"] = wavelength

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.h5.flush()
        self.h5.close()

    def __repr__(self):
        rep = "QPImage, {x}x{y}px".format(x=self._amp.raw.shape[0],
                                          y=self._amp.raw.shape[1],
                                          )
        if "wavelength" in self.h5.attrs:
            wl = self.h5.attrs["wavelength"]
            if wl < 2000e-9 and wl > 10e-9:
                # convenience for light microscopy
                rep += ", λ={:.1f}nm".format(wl * 1e9)
            else:
                rep += ", λ={:.2e}m".format(wl)

        return rep

    def _get_amp_pha(self, data, data_type):
        """Convert input data to phase and amplitude

        Parameters
        ----------
        data: 2d ndarray (float or complex) or list
            The experimental data (see `data_type`)
        data_type: str
            String or comma-separated list of strings indicating
            the order and type of input data. Valid values are
            "field", "phase", "phase,amplitude", or "phase,intensity",
            where the latter two require an indexable object with
            the phase data as first element.

        Returns
        -------
        amp, pha: tuple of (:py:class:`Amplitdue`, :py:class:`Phase`)
        """
        assert data_type in ["field", "phase", "phase,amplitude",
                             "phase,intensity"]
        if data_type == "field":
            amp = np.abs(data)
            pha = unwrap_phase(np.angle(data))
        elif data_type == "phase":
            amp = np.ones_like(data)
            pha = unwrap_phase(data)
        elif data_type == "phase,amplitude":
            pha = unwrap_phase(data[0])
            amp = data[1]
        elif data_type == "phase,intensity":
            pha = unwrap_phase(data[0])
            amp = np.sqrt(data[1])
        return amp, pha

    @property
    def bg_amp(self):
        """Return the background amplitude image"""
        return self._amp.bg

    @property
    def bg_pha(self):
        """Return the background phase image"""
        return self._pha.bg

    @property
    def amp(self):
        """Return the background-corrected amplitude image"""
        return self._amp.image

    @property
    def field(self):
        """Return the background-corrected complex field"""
        return self.amp * np.exp(1j * self.pha)

    @property
    def pha(self):
        """Return the background-corrected phase image"""
        return self._pha.image

    def clear_bg(self, data_names=["amplitude", "phase"], keys=["ramp"]):
        """Clear background correction

        Parameters
        ----------
        names: list of str
            From which type of data to remove the background
            information. The list contains either "amplitude",
            "phase", or both.
        keys: list of str
            Which type of background data to remove. One of
            ["ramp", data"].
        """
        for dn in data_names:
            assert dn in ["amplitude", "phase"]
        for kk in keys:
            assert kk in ["ramp", "data"]
        # Get image data for clearing
        imdats = []
        if "amplitude" in data_names:
            imdats.append(self._amp)
        if "phase" in data_names:
            imdats.append(self._pha)
        assert imdats, "`data_names` must contain 'phase' or 'amplitude'!"
        # Perform clearing of backgrounds
        for imdat in imdats:
            for key in keys:
                imdat.set_bg(None, key)

    def correct_amp(self, method="border"):
        """Perform amplitude background correction
        """

    def correct_pha(self, method="border,sphere-edge"):
        """Perform phase background correction
        """

    def refocus(self, distance, method="helmholtz"):
        """Numerically refocus the current field

        Parameters
        ----------
        distance: float
            Focusing distance [m]
        method: str
            Refocusing method, one of ["helmholtz","fresnel"]

        See Also
        --------
        :py:mod:`nrefocus`: library used for numerical focusing
        """
        # TODO:
        # - Perform refocusing and create new image data instances
        # - Remember old image data instances
        # - Maybe return a new instance of QPImage
        # - Allow autofocusing?

    def set_bg_data(self, bg_data, data_type):
        """Set background amplitude and phase

        Parameters
        ----------
        bg_data: 2d ndarray (float or complex), list, or `None`
            The background data (must be same type as `data`).
            If set to `None`, the background data is reset.
        data_type: str
            String or comma-separated list of strings indicating
            the order and type of input data. Valid values are
            "field", "phase", "phase,amplitude", or "phase,intensity",
            where the latter two require an indexable object with
            the phase data as first element.
        """
        if bg_data is None:
            # Reset phase and amplitude
            amp, pha = None, None
        else:
            # Compute phase and amplitude from data and data_type
            amp, pha = self._get_amp_pha(bg_data, data_type)
        # Set background data
        self._amp.set_bg(amp, key="data")
        self._pha.set_bg(pha, key="data")