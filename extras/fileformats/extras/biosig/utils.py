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
