"""
Dataset classes.
"""

# Authors: Hubert Banville <hubert.jbanville@gmail.com>
#          Lukas Gemein <l.gemein@gmail.com>
#          Simon Brandt <simonbrandt@protonmail.com>
#          David Sabbagh <dav.sabbagh@gmail.com>
#
# License: BSD (3-clause)

from torch.utils.data import Dataset


class BaseDataset(Dataset):
    """
    A base dataset.

    Parameters
    ----------
    raw: mne.Raw
    info: pandas.DataFrame
        holds additional information about the raw
    """
    def __init__(self, raw, info, target=None):
        self.raw = raw
        # TODO: rename
        self.info = info
        if target is not None:
            assert target in self.info, f"'{target}' not in info"
        self.target = target

    def __getitem__(self, index):
        return self.raw, self.target

    def __len__(self):
        return len(self.raw)


class WindowsDataset(BaseDataset):
    """
    Applies a windower to a base dataset.

    Parameters
    ----------
    windows: ConcatDataset
        windows/supercrops obtained throiugh application of a Windower to a
        BaseDataset
    info: pandas.DataFrame
        hold additional info about the windows
    """
    def __init__(self, windows, info):
        self.windows = windows
        self.info = info

    def __getitem__(self, index):
        target = self.windows.events[:,-1]
        keys = ['i_supercrop_in_trial', 'i_start_in_trial', 'i_stop_in_trial']
        info = self.windows.metadata.iloc[index][keys].to_list()
        return self.windows[index].get_data().squeeze(0), target[index], info

    def __len__(self):
        return len(self.windows.events)