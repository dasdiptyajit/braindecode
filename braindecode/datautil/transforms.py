"""Transforms that work on Raw or Epochs objects.
ToDo: should transformer also transform y (e.g. cutting continuous labelled 
      data)?
"""

# Authors: Hubert Banville <hubert.jbanville@gmail.com>
#          Lukas Gemein <l.gemein@gmail.com>
#          Simon Brandt <simonbrandt@protonmail.com>
#          David Sabbagh <dav.sabbagh@gmail.com>
#
# License: BSD (3-clause)

import mne


class FilterRaw(object):
    """Apply mne filter on raw data

    Parameters
    ----------
    mne_filter_kwargs : **kwargs
        kwargs passed to mne.io.Raw.filter
    """

    def __init__(self, **mne_filter_kwargs):
        self.mne_filter_kwargs = mne_filter_kwargs

    def __call__(self, raw):
        """Apply filter
        
        Parameters
        ----------
        raw : mne.io.Raw
            raw data to filter
        """
        return raw.filter(**self.mne_filter_kwargs)


class ZscoreRaw(object):
    """Zscore raw data channel wise
    """

    def __call__(self, raw):
        """Zscore Normalize raw data channel wise

        Parameters
        ----------
        raw : mne.io.Raw
            raw data to normalize

        Returns
        -------
        raw : mne.io.Raw
            normalized raw data

        """
        raw = raw.apply_function(lambda x: x - x.mean())
        return raw.apply_function(lambda x: x / x.std())


class FilterWindow(object):
    """FIR filter for windowed data.

    Parameters
    ----------
    sfreq : int | float
        sampling frequency of data when applying filter
    l_freq : int | float | None
        see mne.filter.create_filter
    h_freq : int | float | None
        see mne.filter.create_filter
    kwargs : **kwargs
        see mne.filter.create_filter
    overlap_kwargs  : **kwargs
        see mne.filter._overlap_add_filter
    """

    def __init__(
        self, sfreq, l_freq=None, h_freq=None, kwargs=None, overlap_kwargs=None
    ):
        if kwargs is None:
            kwargs = dict()
        if overlap_kwargs is None:
            overlap_kwargs = dict()
        self.filter = mne.filter.create_filter(
            None, sfreq, l_freq=l_freq, h_freq=h_freq, method="fir", **kwargs
        )
        self.overlap_kwargs = overlap_kwargs

    def __call__(self, windows):
        return mne.filter._overlap_add_filter(
            windows, self.filter, **self.overlap_kwargs
        )


class ZscoreWindow(object):
    """Zscore windowed data channel wise
    """

    def __call__(self, windows):
        """Zscore Normalize windowed data channel wise

        Parameters
        ----------
        X : ndarray, shape (n_channels, window_size)
            windowed data to normalize

        Returns
        -------
        X : ndarray, shape (n_channels, window_size)
            normalized windowed data

        """
        windows -= windows.mean(axis=-1, keepdims=True)
        return windows / windows.std(axis=-1, keepdims=True)
