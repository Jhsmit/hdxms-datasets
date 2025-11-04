export interface UploadedFile {
  id: string
  filename: string
  size: number
  detectedFormat: string | null
  fileType: 'data' | 'structure'
}

export interface ProteinIdentifiers {
  uniprotAccessionNumber?: string
  uniprotEntryName?: string
  proteinName?: string
}

export interface StructureData {
  fileId: string
  format: string
  description?: string
  pdbId?: string
  alphafoldId?: string
}

export interface PeptideData {
  id: string
  dataFileId: string
  dataFormat: string
  deuterationType: 'partially_deuterated' | 'fully_deuterated' | 'non_deuterated'
  filters: Record<string, any>
  pH?: number
  temperature?: number
  dPercentage?: number
  chain: string[]
}

export interface ProteinState {
  sequence: string
  nTerm: number
  cTerm: number
  mutations?: string[]
  oligomericState?: number
  ligand?: string
}

export interface StateData {
  id: string
  name: string
  description: string
  proteinState: ProteinState
  peptides: PeptideData[]
}

export interface AuthorData {
  name: string
  orcid?: string
  affiliation?: string
  contactEmail?: string
}

export interface PublicationData {
  title?: string
  authors?: string[]
  journal?: string
  year?: number
  doi?: string
  pmid?: string
  url?: string
}

export interface DataRepositoryData {
  name: string
  url?: string
  identifier?: string
  doi?: string
  description?: string
}

export interface MetadataData {
  authors: AuthorData[]
  license: string
  publication?: PublicationData
  repository?: DataRepositoryData
  conversionNotes?: string
}

export interface ValidationResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
}

export const DEUTERATION_TYPES = [
  { value: 'partially_deuterated', label: 'Partially Deuterated' },
  { value: 'fully_deuterated', label: 'Fully Deuterated' },
  { value: 'non_deuterated', label: 'Non-Deuterated' }
]

export const PEPTIDE_FORMATS = [
  { value: 'DynamX_v3_state', label: 'DynamX v3 (State)' },
  { value: 'DynamX_v3_cluster', label: 'DynamX v3 (Cluster)' },
  { value: 'HDExaminer_v3', label: 'HDExaminer v3' },
  { value: 'OpenHDX', label: 'OpenHDX' }
]

export const STRUCTURE_FORMATS = [
  { value: 'pdb', label: 'PDB' },
  { value: 'cif', label: 'mmCIF' },
  { value: 'bcif', label: 'BinaryCIF' }
]

export const LICENSE_OPTIONS = [
  { value: 'CC0', label: 'CC0 (Public Domain)' },
  { value: 'CC BY 4.0', label: 'CC BY 4.0' },
  { value: 'CC BY-SA 4.0', label: 'CC BY-SA 4.0' },
  { value: 'MIT', label: 'MIT' }
]
