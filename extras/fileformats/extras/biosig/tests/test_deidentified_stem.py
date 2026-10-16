import re
from pathlib import Path

from fileformats.extras.biosig.utils import deidentified_stem


def test_deidentified_stem(tmp_path: Path) -> None:
    named = tmp_path / "Jane_Doe.edf"
    named.write_bytes(b"recording")
    stem = deidentified_stem(named)

    assert re.fullmatch(r"deid-eeg-[0-9a-f]{16}", stem)
    assert "Jane" not in stem
    # Depends only on the contents, so the same recording gets the same name each time
    renamed = tmp_path / "other.edf"
    renamed.write_bytes(b"recording")
    assert deidentified_stem(renamed) == stem
    different = tmp_path / "different.edf"
    different.write_bytes(b"another recording")
    assert deidentified_stem(different) != stem
    assert deidentified_stem(named, prefix="deid-meg").startswith("deid-meg-")
