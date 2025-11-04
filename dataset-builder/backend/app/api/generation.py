"""Dataset generation endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import sys
import json
import zipfile
import io
from datetime import datetime

# Add parent directory to path to import hdxms_datasets
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.models.api_models import DatasetData
from app.services import file_manager, session_manager

router = APIRouter()


@router.post("/json")
async def generate_json(dataset: DatasetData):
    """
    Generate the dataset.json file from the provided data.

    Returns the JSON content as a downloadable file.
    """
    try:
        from hdxms_datasets.models import (
            HDXDataSet,
            State,
            Peptides,
            ProteinState,
            Structure,
            ProteinIdentifiers,
            DatasetMetadata,
            Author,
            Publication,
            DataRepository,
            DeuterationType,
            PeptideFormat,
            StructureMapping
        )

        # Get session to access file paths
        session = session_manager.get_session(dataset.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        files = session.get("files", {})

        # Build HDXDataSet from API models
        # Convert states
        states = []
        for state_data in dataset.states:
            # Convert peptides
            peptides = []
            for peptide_data in state_data.peptides:
                file_info = files.get(peptide_data.data_file_id)
                if not file_info:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Data file not found: {peptide_data.data_file_id}"
                    )

                peptide = Peptides(
                    data_file=Path(file_info["path"]),
                    data_format=PeptideFormat(peptide_data.data_format),
                    deuteration_type=DeuterationType(peptide_data.deuteration_type),
                    filters=peptide_data.filters,
                    pH=peptide_data.pH,
                    temperature=peptide_data.temperature,
                    d_percentage=peptide_data.d_percentage,
                    structure_mapping=StructureMapping(chain=peptide_data.chain)
                )
                peptides.append(peptide)

            # Convert protein state
            protein_state = ProteinState(
                sequence=state_data.protein_state.sequence,
                n_term=state_data.protein_state.n_term,
                c_term=state_data.protein_state.c_term,
                mutations=state_data.protein_state.mutations,
                oligomeric_state=state_data.protein_state.oligomeric_state,
                ligand=state_data.protein_state.ligand
            )

            state = State(
                name=state_data.name,
                description=state_data.description,
                peptides=peptides,
                protein_state=protein_state
            )
            states.append(state)

        # Convert structure
        structure_file_info = files.get(dataset.structure.file_id)
        if not structure_file_info:
            raise HTTPException(
                status_code=400,
                detail=f"Structure file not found: {dataset.structure.file_id}"
            )

        structure = Structure(
            data_file=Path(structure_file_info["path"]),
            format=dataset.structure.format,
            description=dataset.structure.description,
            pdb_id=dataset.structure.pdb_id,
            alphafold_id=dataset.structure.alphafold_id
        )

        # Convert protein identifiers
        protein_identifiers = ProteinIdentifiers(
            uniprot_accession_number=dataset.protein_identifiers.uniprot_accession_number,
            uniprot_entry_name=dataset.protein_identifiers.uniprot_entry_name,
            protein_name=dataset.protein_identifiers.protein_name
        )

        # Convert metadata
        authors = [
            Author(
                name=a.name,
                orcid=a.orcid,
                affiliation=a.affiliation,
                contact_email=a.contact_email
            )
            for a in dataset.metadata.authors
        ]

        publication = None
        if dataset.metadata.publication:
            pub = dataset.metadata.publication
            publication = Publication(
                title=pub.title,
                authors=pub.authors,
                journal=pub.journal,
                year=pub.year,
                doi=pub.doi,
                pmid=pub.pmid,
                url=pub.url
            )

        repository = None
        if dataset.metadata.repository:
            repo = dataset.metadata.repository
            repository = DataRepository(
                name=repo.name,
                url=repo.url,
                identifier=repo.identifier,
                doi=repo.doi,
                description=repo.description
            )

        metadata = DatasetMetadata(
            authors=authors,
            license=dataset.metadata.license,
            publication=publication,
            repository=repository,
            conversion_notes=dataset.metadata.conversion_notes,
            created_date=datetime.now()
        )

        # Create HDXDataSet
        hdx_dataset = HDXDataSet(
            description=dataset.description,
            states=states,
            structure=structure,
            protein_identifiers=protein_identifiers,
            metadata=metadata
        )

        # Convert to JSON
        json_str = hdx_dataset.model_dump_json(indent=2)

        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=dataset_{hdx_dataset.hdx_id}.json"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/package")
async def generate_package(dataset: DatasetData):
    """
    Generate a complete dataset package (ZIP with JSON + data files).

    Returns a ZIP file containing:
    - dataset.json (with relative paths)
    - data/ directory with all data files
    """
    try:
        # First generate the JSON (this validates everything)
        # This is a simplified version - in production you'd generate the actual package
        raise HTTPException(
            status_code=501,
            detail="Package generation not yet implemented in MVP"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
