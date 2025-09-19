"""
Functions to help with migration from v020 datasets.
"""

from hdxms_datasets.models import Peptides
from typing import Any
from pathlib import Path


def get_metadata(spec: dict) -> dict[str, Any]:
    try:
        metadata = spec["metadata"]
        return {
            "pH": metadata.get("pH", None),
            "temperature": metadata.get("temperature", None),
            "d_percentage": metadata.get("d_percentage", None),
        }
    except KeyError:
        return {}


def get_peptides(
    spec: dict, data_files: dict, root_dir: Path = Path.cwd(), **kwargs
) -> list[Peptides]:
    """Get peptides from the spec"""

    peptides = []
    for deut_type, p_spec in spec.items():
        data_file = data_files[p_spec["data_file"]]
        p = Peptides(
            data_file=root_dir / data_file["filename"],
            data_format=data_file["format"],
            deuteration_type=deut_type,
            filters=p_spec.get("filters", {}),
            **kwargs,
            **get_metadata(p_spec),
        )

        peptides.append(p)

    return peptides
