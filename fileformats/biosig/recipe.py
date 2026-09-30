from fileformats.application import Json


class MneAnonymizeRecipe(Json):
    """A JSON file containing the keyword arguments passed to
    `mne.io.anonymize_info <https://mne.tools/stable/generated/mne.io.anonymize_info.html>`__
    when deidentifying a biosignal recording (e.g. ``{"daysback": 365, "keep_his": false}``)
    """
