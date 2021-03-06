from skorch.callbacks import EpochTimer, BatchScoring, PrintLog
from skorch.utils import train_loss_score, valid_loss_score, noop
from skorch.classifier import NeuralNet
from skorch.classifier import NeuralNetClassifier
import torch
from torch.utils.data.dataloader import DataLoader
import numpy as np


class EEGClassifier(NeuralNetClassifier):
    """Classifier that does not assume softmax activation.
    Calls loss function directly without applying log or anything.
    """

    # pylint: disable=arguments-differ
    def get_loss(self, y_pred, y_true, *args, **kwargs):
        """Return the loss for this batch by calling NeuralNet get_loss.
        Parameters
        ----------
        y_pred : torch tensor
          Predicted target values
        y_true : torch tensor
          True target values.
        X : input data, compatible with skorch.dataset.Dataset
          By default, you should be able to pass:
            * numpy arrays
            * torch tensors
            * pandas DataFrame or Series
            * scipy sparse CSR matrices
            * a dictionary of the former three
            * a list/tuple of the former three
            * a Dataset
          If this doesn't work with your data, you have to pass a
          ``Dataset`` that can deal with the data.
        training : bool (default=False)
          Whether train mode should be used or not.

        """
        return NeuralNet.get_loss(self, y_pred, y_true, *args, **kwargs)

    def get_iterator(self, dataset, training=False, drop_index=True):
        iterator = super().get_iterator(dataset, training=training)
        if drop_index:
            return ThrowAwayIndexLoader(self, iterator)
        else:
            return iterator


    def on_batch_end(self, net, X, y, training=False, **kwargs):
        # If training is false, assume that our loader has indices for this
        # batch
        if not training:
            cbs = self._default_callbacks + self.callbacks
            epoch_cbs = []
            for name, cb in cbs:
                if (cb.__class__.__name__ == 'CroppedTrialEpochScoring') and (
                    hasattr(cb, 'supercrop_inds_')) and (cb.on_train == False):
                    epoch_cbs.append(cb)
            # for trialwise decoding stuffs it might also be we don't have
            # cropped loader, so no indices there
            if len(epoch_cbs) > 0:
                assert hasattr(self, '_last_supercrop_inds')
                for cb in epoch_cbs:
                    cb.supercrop_inds_.append(self._last_supercrop_inds)
                del self._last_supercrop_inds


    def predict_with_supercrop_inds_and_ys(self, dataset):
        preds = []
        i_supercrop_in_trials = []
        i_supercrop_stops = []
        supercrop_ys = []
        for X, y, i in self.get_iterator(dataset, drop_index=False):
            i_supercrop_in_trials.append(i[0].cpu().numpy())
            i_supercrop_stops.append(i[2].cpu().numpy())
            preds.append(self.predict_proba(X))
            supercrop_ys.append(y.cpu().numpy())
        preds = np.concatenate(preds)
        i_supercrop_in_trials = np.concatenate(i_supercrop_in_trials)
        i_supercrop_stops = np.concatenate(i_supercrop_stops)
        supercrop_ys = np.concatenate(supercrop_ys)
        return dict(
            preds=preds, i_supercrop_in_trials=i_supercrop_in_trials,
            i_supercrop_stops=i_supercrop_stops, supercrop_ys=supercrop_ys)


    # Removes default EpochScoring callback computing 'accuracy' to work properly
    # with cropped decoding.
    @property
    def _default_callbacks(self):
        return [
            ("epoch_timer", EpochTimer()),
            (
                "train_loss",
                BatchScoring(
                    train_loss_score,
                    name="train_loss",
                    on_train=True,
                    target_extractor=noop,
                ),
            ),
            (
                "valid_loss",
                BatchScoring(
                    valid_loss_score, name="valid_loss", target_extractor=noop,
                ),
            ),
            ("print_log", PrintLog()),
        ]


class ThrowAwayIndexLoader(object):
    def __init__(self, net, loader):
        self.net = net
        self.loader = loader
        self.last_i = None

    def __iter__(self, ):
        normal_iter = self.loader.__iter__()
        for batch in normal_iter:
            if len(batch) == 3:
                x,y,i = batch
                # Store for scoring callbacks
                self.net._last_supercrop_inds = i
            else:
                x,y = batch

            # TODO: should be on dataset side
            if hasattr(x, 'type'):
                x = x.type(torch.float32)
                y = y.type(torch.int64)
            yield x,y
