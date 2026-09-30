"""
Fileformats extension package: biosignal (EEG/MEG) data types.

Defines and validates EEG/MEG file formats for XNAT Ingest workflows.

Authors:
- Miao Cao

Email:
- miaocao@swin.edu.au
"""

from .base import Biosig, Eeg, Meg
from .edf import (
    Edf,
    EdfPlus,
)
from .recipe import MneAnonymizeRecipe

from ._version import __version__

__all__ = [
    "__version__",
    "Biosig",
    "Eeg",
    "Edf",
    "EdfPlus",
    "Meg",
    "MneAnonymizeRecipe",
]
