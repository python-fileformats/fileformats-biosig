import os
import typing as ty
from pathlib import Path

import mne.export
import mne.io
from fileformats.core import FileSet, Loaded, extra_implementation

from fileformats.biosig import Biosig, Edf, EdfPlus, MneAnonymizeRecipe

from .utils import mne_deidentify


@extra_implementation(FileSet.read_metadata)
def edf_read_metadata(edf: Edf, **kwargs: ty.Any) -> ty.Mapping[str, ty.Any]:
    raw = mne.io.read_raw_edf(edf, preload=False, verbose=False)
    return {
        **raw.info.to_json_dict(),
        **_parse_edf_header(edf),
    }


@extra_implementation(FileSet.read_metadata)
def edf_plus_read_metadata(edf: EdfPlus, **kwargs: ty.Any) -> ty.Mapping[str, ty.Any]:
    raw = mne.io.read_raw_edf(edf, preload=False, verbose=False)
    return {
        **raw.info.to_json_dict(),
        **_parse_edf_header(edf),
    }


@extra_implementation(Biosig.deidentify)
def edf_deidentify(
    edf: Edf,
    out_dir: os.PathLike[str],
    recipe: Loaded[MneAnonymizeRecipe] | None = None,
    **kwargs: ty.Any,
) -> Edf:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = mne.io.read_raw_edf(edf, preload=True, verbose=False)
    raw.info = mne_deidentify(raw, recipe)
    deid_fspath = out_dir / "eeg.edf"
    mne.export.export_raw(deid_fspath, raw, fmt="edf", overwrite=True)
    return type(edf)(deid_fspath)


def _parse_edf_header(path: os.PathLike[str]) -> dict[str, ty.Any]:
    """
    Parse EDF/EDF+ header bytes directly for patient and recording fields
    that MNE may not surface via raw.info.

    Header layout (all ASCII, fixed-width):
      [0:8]    version
      [8:88]   local patient identification  "code sex birthdate name"
      [88:168] local recording identification "Startdate date id technician equipment"
      [168:176] start date DD.MM.YY
      [176:184] start time HH.MM.SS
      [192:236] reserved — contains "EDF+C" or "EDF+D" for EDF+
    """
    with open(path, "rb") as f:
        header = f.read(256)

    lpi = header[8:88].decode("ascii", errors="replace").strip()
    lri = header[88:168].decode("ascii", errors="replace").strip()
    start_date = header[168:176].decode("ascii", errors="replace").strip()
    start_time = header[176:184].decode("ascii", errors="replace").strip()
    reserved = header[192:236].decode("ascii", errors="replace").strip()

    lpi_parts = lpi.split()
    lri_parts = lri.split()

    return {
        "edf_patient_code": lpi_parts[0] if len(lpi_parts) > 0 else None,
        "edf_patient_sex": lpi_parts[1] if len(lpi_parts) > 1 else None,
        "edf_patient_birthdate": lpi_parts[2] if len(lpi_parts) > 2 else None,
        "edf_patient_name": " ".join(lpi_parts[3:]) if len(lpi_parts) > 3 else None,
        "edf_recording_startdate": lri_parts[1] if len(lri_parts) > 1 else None,
        "edf_recording_id": lri_parts[2] if len(lri_parts) > 2 else None,
        "edf_technician": lri_parts[3] if len(lri_parts) > 3 else None,
        "edf_equipment": lri_parts[4] if len(lri_parts) > 4 else None,
        "edf_start_date": start_date,
        "edf_start_time": start_time,
        "edf_subtype": reserved if reserved.startswith("EDF+") else None,
    }
