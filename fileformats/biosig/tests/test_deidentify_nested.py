import os
import typing as ty
from pathlib import Path

import pytest
from fileformats.core import (
    extra,
    extra_implementation,
    staged_out_dir,
    validated_property,
)
from fileformats.generic import Directory, File

from fileformats.biosig import Biosig


class Recording(File, Biosig):
    ext = ".rec"


class Unsupported(File, Biosig):
    """Contains PHI but has no deidentify implementation"""

    ext = ".unsupported"


class Session(Directory, Biosig):
    contains_phi = "nested"

    @validated_property
    def recordings(self) -> list[Recording]:
        return [Recording(p) for p in sorted(self.fspath.glob("*.rec"))]

    @validated_property
    def unsupported(self) -> list[Unsupported]:
        return [Unsupported(p) for p in sorted(self.fspath.glob("*.unsupported"))]


class Study(Directory, Biosig):
    """A container with a log file of its own that may contain PHI"""

    @validated_property
    def sessions(self) -> dict[str, Session]:
        return {p.name: Session(p) for p in sorted(self.fspath.glob("ses-*"))}

    @property
    def log_file(self) -> File:
        return File(self.fspath / "log.txt")


@extra_implementation(Biosig.deidentify)
def recording_deidentify(
    recording: Recording,
    out_dir: os.PathLike[str],
    recipe: None = None,
    **kwargs: ty.Any,
) -> Recording:
    out_path = Path(out_dir) / recording.fspath.name
    out_path.write_text("deidentified")
    return Recording(out_path)


@extra_implementation(Biosig.deidentify)
def study_deidentify(
    study: Study,
    out_dir: os.PathLike[str],
    recipe: None = None,
    fail: bool = False,
    **kwargs: ty.Any,
) -> Study:
    deidentified = study.deidentify_nested(out_dir, recipe=recipe, **kwargs)
    if fail:
        raise RuntimeError("deidentification failed")
    deidentified.log_file.fspath.write_text("deidentified")
    return deidentified


def _make_study(root: Path) -> Study:
    study = root / "study"
    for ses in ("ses-1", "ses-2"):
        (study / ses).mkdir(parents=True)
        (study / ses / "eeg.rec").write_text("Jane Doe")
        (study / ses / "notes.txt").write_text("notes")
    (study / "log.txt").write_text("Jane Doe")
    return Study(study)


def test_deidentify_nested(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    study = _make_study(tmp_path / "in")
    deidentified = study.deidentify(out_dir)

    assert isinstance(deidentified, Study)
    assert deidentified.fspath == out_dir / "study"
    # Keys use "/" separators on all platforms (incl. Windows)
    assert {
        p.relative_to(out_dir).as_posix(): p.read_text()
        for p in deidentified.all_file_paths()
    } == {
        "study/log.txt": "deidentified",
        "study/ses-1/eeg.rec": "deidentified",
        "study/ses-1/notes.txt": "notes",
        "study/ses-2/eeg.rec": "deidentified",
        "study/ses-2/notes.txt": "notes",
    }
    # the originals are left untouched and the staging directories are cleaned up
    assert study.log_file.fspath.read_text() == "Jane Doe"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["in", "out"]


def test_deidentify_failure_leaves_nothing(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    with pytest.raises(RuntimeError, match="deidentification failed"):
        _make_study(tmp_path / "in").deidentify(out_dir, fail=True)
    assert not out_dir.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["in"]


def test_deidentify_without_implementation_leaves_nothing(tmp_path: Path) -> None:
    study = _make_study(tmp_path / "in")
    (study.fspath / "ses-1" / "x.unsupported").write_text("Jane Doe")
    out_dir = tmp_path / "out"
    with pytest.raises(NotImplementedError):
        Study(study.fspath).deidentify(out_dir)
    assert not out_dir.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["in"]


def test_contains_phi_nested_is_truthy() -> None:
    assert Session.contains_phi


class OtherFamily(File):
    """A format from another package with its own, separate, `deidentify` hook that
    follows the same convention"""

    ext = ".other"
    contains_phi = True

    @extra(wrapper=staged_out_dir)
    def deidentify(
        self, out_dir: os.PathLike[str], recipe: None = None, **kwargs: ty.Any
    ) -> "OtherFamily":
        raise NotImplementedError


@extra_implementation(OtherFamily.deidentify)
def other_family_deidentify(
    other: OtherFamily, out_dir: os.PathLike[str], recipe: None = None, **kwargs: ty.Any
) -> OtherFamily:
    out_path = Path(out_dir) / other.fspath.name
    out_path.write_text("deidentified by other family")
    return OtherFamily(out_path)


class ClaimsPhi(File):
    """A format that may contain PHI but has no `deidentify` method"""

    ext = ".claims"
    contains_phi = True


class Mixed(Directory, Biosig):
    contains_phi = "nested"

    @validated_property
    def others(self) -> list[OtherFamily]:
        return [OtherFamily(p) for p in sorted(self.fspath.glob("*.other"))]

    @validated_property
    def claims(self) -> list[ClaimsPhi]:
        return [ClaimsPhi(p) for p in sorted(self.fspath.glob("*.claims"))]


def test_deidentify_nested_other_family(tmp_path: Path) -> None:
    mixed = tmp_path / "in" / "mixed"
    mixed.mkdir(parents=True)
    (mixed / "a.other").write_text("Jane Doe")
    (mixed / "notes.txt").write_text("notes")
    deidentified = Mixed(mixed).deidentify(tmp_path / "out")
    assert (deidentified.fspath / "a.other").read_text() == (
        "deidentified by other family"
    )
    assert (deidentified.fspath / "notes.txt").read_text() == "notes"


def test_deidentify_nested_phi_without_deidentify_raises(tmp_path: Path) -> None:
    mixed = tmp_path / "in" / "mixed"
    mixed.mkdir(parents=True)
    (mixed / "a.claims").write_text("Jane Doe")
    with pytest.raises(AttributeError, match="deidentify"):
        Mixed(mixed).deidentify(tmp_path / "out")
    assert not (tmp_path / "out").exists()
