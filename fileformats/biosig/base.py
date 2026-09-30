import os
import typing as ty

from fileformats.core import FileSet, Loaded, extra


class Biosig(FileSet):
    """Base class for biophysical time-series recordings"""

    @extra
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
        **kwargs: Any
            Additional format-specific keyword arguments (e.g. concurrency options),
            which implementations that don't use them should accept and ignore

        Returns
        -------
        Self
            A new instance of the image with any subject-identifying information stripped from
            the image header.
        """
        raise NotImplementedError


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
