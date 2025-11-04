"""Validation endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from pathlib import Path
import sys

# Add parent directory to path to import hdxms_datasets
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.models.api_models import (
    ValidationResponse,
    StateData,
    ProteinIdentifiersData,
    MetadataData
)

router = APIRouter()


@router.post("/state", response_model=ValidationResponse)
async def validate_state(state_data: StateData):
    """
    Validate a state configuration.

    This checks if the state data is valid according to the schema.
    """
    errors = []
    warnings = []

    try:
        # Check sequence length matches n_term to c_term
        ps = state_data.protein_state
        expected_length = ps.c_term - ps.n_term + 1
        actual_length = len(ps.sequence)

        if actual_length != expected_length:
            errors.append(
                f"Sequence length ({actual_length}) doesn't match "
                f"N-term({ps.n_term}) to C-term({ps.c_term}): expected {expected_length}"
            )

        # Check if peptides exist
        if not state_data.peptides:
            warnings.append("No peptides defined for this state")

        # Check if oligomeric state is specified
        if ps.oligomeric_state is None:
            warnings.append("No oligomeric state specified (recommended)")

        return ValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    except ValidationError as e:
        return ValidationResponse(
            valid=False,
            errors=[str(err) for err in e.errors()],
            warnings=warnings
        )


@router.post("/protein", response_model=ValidationResponse)
async def validate_protein(protein_data: ProteinIdentifiersData):
    """Validate protein identifier information."""
    warnings = []

    if not protein_data.uniprot_accession_number:
        warnings.append("UniProt accession number not provided (recommended)")

    return ValidationResponse(
        valid=True,
        warnings=warnings
    )


@router.post("/metadata", response_model=ValidationResponse)
async def validate_metadata(metadata: MetadataData):
    """Validate metadata information."""
    errors = []
    warnings = []

    # License is required (enforced by Pydantic)
    if not metadata.license:
        errors.append("License is required")

    # Check if authors provided
    if not metadata.authors:
        errors.append("At least one author is required")

    # Validate ORCID format if provided
    for author in metadata.authors:
        if author.orcid and not _validate_orcid(author.orcid):
            errors.append(f"Invalid ORCID format for {author.name}: {author.orcid}")

    # Validate DOI format if provided
    if metadata.publication and metadata.publication.doi:
        if not _validate_doi(metadata.publication.doi):
            errors.append(f"Invalid DOI format: {metadata.publication.doi}")

    return ValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def _validate_orcid(orcid: str) -> bool:
    """Validate ORCID format: 0000-0000-0000-0000."""
    import re
    pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$'
    return bool(re.match(pattern, orcid))


def _validate_doi(doi: str) -> bool:
    """Validate DOI format."""
    import re
    # Basic DOI pattern
    pattern = r'^10\.\d{4,}/.*$'
    return bool(re.match(pattern, doi))
