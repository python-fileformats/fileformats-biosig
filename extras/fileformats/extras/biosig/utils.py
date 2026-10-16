import hashlib
import os

import mne
import mne.io
from fileformats.core import Loaded

from fileformats.biosig import MneAnonymizeRecipe


def mne_deidentify(
    raw: mne.io.BaseRaw,
    recipe: Loaded[MneAnonymizeRecipe] | None = None,
) -> mne.Info:
    """Anonymize an MNE Raw object and return the deidentified Info.

    Callers that need to know what was changed (e.g. for a re-identification audit
    trail) should diff `metadata` before and after instead of relying on this
    function to report it, since that works uniformly across formats.
    """
    if recipe is None:
        recipe = {}
    if not isinstance(recipe, dict):
        raise TypeError(
            "MNE anonymization recipe must be a JSON object of keyword arguments to "
            f"mne.io.anonymize_info, not {type(recipe).__name__}"
        )
    return mne.io.anonymize_info(raw.info, verbose=None, **recipe)


def deidentified_stem(data_file: os.PathLike[str], prefix: str = "deid-eeg") -> str:
    """A file stem for a deidentified recording, as the original name may include
    the subject's name. It includes a hash of the recording's data file, so that
    deidentified recordings written to the same directory don't clash and the name
    is the same each time the recording is deidentified. The hash is of the contents
    rather than the original name, which could be recovered from a hash of it by
    hashing candidate names.

    Parameters
    ----------
    data_file : PathLike[str]
        the file the hash is calculated from
    prefix : str, optional
        the start of the stem, by default "deid-eeg"

    Returns
    -------
    str
        the stem, e.g. "deid-eeg-1a2b3c4d5e6f7a8b"
    """
    sha256 = hashlib.sha256()
    with open(data_file, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            sha256.update(chunk)
    return f"{prefix}-{sha256.hexdigest()[:16]}"
