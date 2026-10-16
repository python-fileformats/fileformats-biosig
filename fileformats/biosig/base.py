import os
import typing as ty
from pathlib import Path

from fileformats.core import FileSet, Loaded, extra, staged_out_dir


class Biosig(FileSet):
    """Base class for biophysical time-series recordings"""

    # Whether the files of the format may contain protected health information (PHI).
    # "nested" means that the format's own files don't, but formats nested within it
    # (i.e. returned by its validated properties) may, so deidentifying it deidentifies
    # them (see `deidentify_nested`). Being truthy, it is still treated as holding PHI
    contains_phi: bool | ty.Literal["nested"] = True

    @extra(wrapper=staged_out_dir)
    def deidentify(
        self,
        out_dir: os.PathLike[str],
        recipe: Loaded[FileSet] | None = None,
        **kwargs: ty.Any,
    ) -> ty.Self:
        """
        Deidentifies the dataset by stripping any subject-identifying information from the
        image header. The exact implementation of this method will depend on the
        specific image format and the type of identifying information that is present.

        Implementations are passed a hidden staging directory as `out_dir`, the
        contents of which are only moved into the requested directory once they have
        returned, so they can copy files there and deidentify them in place without
        any risk of partially deidentified files being left in the output if they fail.

        Implementations only need to strip the identifying data -- they don't need to
        track/report what was changed. Callers that need that (e.g. for re-identification
        audit trails) can diff `metadata` before and after calling this method instead,
        since that works uniformly across formats without extra bookkeeping in each
        implementation.

        Parameters
        ----------
        out_dir: PathLike[str]
            The directory where the deidentified dataset should be saved
        recipe: Loaded[FileSet], optional
            A recipe for the deidentification process, loaded from a format that depends
            on the implementation (e.g. `MneAnonymizeRecipe` for formats read with MNE).
            Implementations annotate it with ``Loaded[<recipe format>]``, or ``None`` if
            they don't take a recipe, so callers can find the format to load the recipe
            from with ``find_extra_implementation`` and ``LoadedMarker.from_hint``
            Formats nested within one another are passed the same recipe, so they need
            to be able to read a common recipe format.
        **kwargs: Any
            Additional format-specific keyword arguments (e.g. concurrency options),
            which implementations that don't use them should accept and ignore

        Returns
        -------
        Self
            A new instance of the image with any subject-identifying information stripped from
            the image header.

        Formats whose `contains_phi` is "nested" are deidentified by
        `deidentify_nested` if no implementation is registered for them.
        """
        if self.contains_phi == "nested":
            return self.deidentify_nested(out_dir, recipe=recipe, **kwargs)
        raise NotImplementedError

    def deidentify_nested(
        self,
        out_dir: os.PathLike[str],
        recipe: Loaded[FileSet] | None = None,
        **kwargs: ty.Any,
    ) -> ty.Self:
        """Deidentifies the recordings nested within the fileset (i.e. returned by its
        validated properties) with their own implementations, and copies its remaining
        files unchanged, keeping the same layout (see `FileSet.map_nested`).

        Nested filesets of other types are deidentified too if they have a truthy
        `contains_phi` attribute, which they then need a `deidentify` method for
        (taking the same arguments), so formats from other packages that follow the
        same convention can be nested within each other.

        For use within `deidentify` implementations of formats that contain others,
        which can then deidentify any of the format's own files that may contain PHI
        (e.g. logs) in place in the returned copy. As `deidentify` stages the output
        of its implementations, they are only moved to the requested output directory
        once that is done.

        Parameters
        ----------
        out_dir : PathLike[str]
            the directory to write the deidentified fileset to
        recipe : Loaded[FileSet], optional
            the recipe passed on to the deidentification of each nested fileset
        **kwargs : Any
            passed on to the deidentification of each nested fileset

        Returns
        -------
        Self
            the copy of the fileset with the nested filesets deidentified
        """

        def deidentify(nested: FileSet, dest_dir: Path) -> FileSet | None:
            # Duck-typed, so nested formats from other families that follow the same
            # `contains_phi`/`deidentify` convention (e.g. medical imaging data and
            # biosignals) are also deidentified. One that may contain PHI but doesn't
            # have a `deidentify` method raises, rather than being copied
            if getattr(nested, "contains_phi", False):
                deidentified: FileSet = nested.deidentify(  # type: ignore[attr-defined]
                    dest_dir, recipe=recipe, **kwargs
                )
                return deidentified
            return None  # copied unchanged

        return self.map_nested(out_dir, deidentify)


class Eeg(Biosig):
    """Base class for all Electroencephalography recordings"""

    pass


# ------------------------------
# Base MEG Type (Abstract Class)
# ------------------------------
class Meg(Biosig):
    """
    Base class for MEG data formats
    All specific MEG formats inherit from this class with unified validation logic
    """
