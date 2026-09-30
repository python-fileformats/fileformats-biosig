"""
Pytest tests for EEG/MEG file format validation and metadata reading.

Test data is downloaded via MNE's dataset utilities and cached for the session.

Authors:
- Miao Cao

Email:
- miaocao@swin.edu.au
"""

import json
import typing as ty

import pytest
from fileformats.core import LoadedMarker, find_extra_implementation

from fileformats.biosig import Biosig, EdfPlus, MneAnonymizeRecipe

# ------------------------------
# EEG: EDF
# ------------------------------


def test_edf_plus_read_metadata(edf_plus_path):
    metadata = EdfPlus(edf_plus_path).metadata
    assert metadata["sfreq"] is not None
    assert "edf_patient_code" in metadata


def test_edf_deidentify_recipe_type():
    """The recipe format can be found from the deidentify implementation signature"""
    impl = find_extra_implementation(Biosig.deidentify, EdfPlus)
    hint = ty.get_type_hints(impl, include_extras=True)["recipe"]
    marker = LoadedMarker.from_hint(hint)
    assert marker is not None and marker.format is MneAnonymizeRecipe


def test_edf_deidentify_with_recipe(edf_plus_path, tmp_path):
    pytest.importorskip("edfio")  # needed by MNE to export EDF
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps({"daysback": 365}))
    recipe = MneAnonymizeRecipe(recipe_path).load()
    deidentified = EdfPlus(edf_plus_path).deidentify(tmp_path / "out", recipe=recipe)
    assert deidentified.fspath.exists()


def test_edf_deidentify_bad_recipe(edf_plus_path, tmp_path):
    with pytest.raises(TypeError, match="JSON object"):
        EdfPlus(edf_plus_path).deidentify(tmp_path, recipe=[1, 2])
