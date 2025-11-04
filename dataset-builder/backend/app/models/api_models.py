"""API request/response models for the dataset builder."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UploadedFileInfo(BaseModel):
    """Information about an uploaded file."""
    id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    detected_format: Optional[str] = Field(None, description="Auto-detected format")
    confirmed_format: Optional[str] = Field(None, description="User-confirmed format")
    file_type: str = Field(..., description="File type: 'data' or 'structure'")


class ValidationResponse(BaseModel):
    """Response from validation endpoints."""
    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class ProteinIdentifiersData(BaseModel):
    """Protein identifier information."""
    uniprot_accession_number: Optional[str] = None
    uniprot_entry_name: Optional[str] = None
    protein_name: Optional[str] = None


class StructureData(BaseModel):
    """Structure file information."""
    file_id: str
    format: str
    description: Optional[str] = None
    pdb_id: Optional[str] = None
    alphafold_id: Optional[str] = None


class PeptideData(BaseModel):
    """Peptide information for a state."""
    id: str
    data_file_id: str
    data_format: str
    deuteration_type: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    pH: Optional[float] = None
    temperature: Optional[float] = None
    d_percentage: Optional[float] = None
    chain: List[str] = Field(default_factory=list)


class ProteinStateData(BaseModel):
    """Protein state information."""
    sequence: str
    n_term: int
    c_term: int
    mutations: Optional[List[str]] = None
    oligomeric_state: Optional[int] = None
    ligand: Optional[str] = None


class StateData(BaseModel):
    """Complete state information."""
    id: str
    name: str
    description: str = ""
    protein_state: ProteinStateData
    peptides: List[PeptideData] = Field(default_factory=list)


class AuthorData(BaseModel):
    """Author information."""
    name: str
    orcid: Optional[str] = None
    affiliation: Optional[str] = None
    contact_email: Optional[str] = None


class PublicationData(BaseModel):
    """Publication information."""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None


class DataRepositoryData(BaseModel):
    """Data repository information."""
    name: str
    url: Optional[str] = None
    identifier: Optional[str] = None
    doi: Optional[str] = None
    description: Optional[str] = None


class MetadataData(BaseModel):
    """Dataset metadata."""
    authors: List[AuthorData]
    license: str
    publication: Optional[PublicationData] = None
    repository: Optional[DataRepositoryData] = None
    conversion_notes: Optional[str] = None


class DatasetData(BaseModel):
    """Complete dataset information for generation."""
    session_id: str
    protein_identifiers: ProteinIdentifiersData
    structure: StructureData
    states: List[StateData]
    metadata: MetadataData
    description: Optional[str] = None
