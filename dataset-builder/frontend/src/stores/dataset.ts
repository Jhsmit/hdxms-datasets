import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  UploadedFile,
  ProteinIdentifiers,
  StructureData,
  StateData,
  MetadataData,
  PeptideData,
  ProteinState
} from '@/types/dataset'

export const useDatasetStore = defineStore('dataset', () => {
  // State
  const sessionId = ref<string>('')
  const currentStep = ref<number>(1)
  const uploadedFiles = ref<UploadedFile[]>([])
  const proteinIdentifiers = ref<ProteinIdentifiers>({})
  const structure = ref<StructureData | null>(null)
  const states = ref<StateData[]>([])
  const metadata = ref<MetadataData>({
    authors: [],
    license: 'CC0'
  })
  const datasetDescription = ref<string>('')

  // Getters
  const dataFiles = computed(() =>
    uploadedFiles.value.filter(f => f.fileType === 'data')
  )

  const structureFiles = computed(() =>
    uploadedFiles.value.filter(f => f.fileType === 'structure')
  )

  const maxAccessibleStep = computed(() => {
    // Step 1 is always accessible
    let maxStep = 1

    // Step 2 requires data and structure files
    if (dataFiles.value.length === 0 || structureFiles.value.length === 0) return maxStep
    maxStep = 2

    // Step 3 requires protein identifiers (optional, always allow)
    maxStep = 3

    // Step 4 requires structure to be defined
    if (structure.value === null) return maxStep
    maxStep = 4

    // Step 5 requires states with peptides
    const hasValidStates = states.value.length > 0 &&
                          states.value.every((s: StateData) => s.peptides.length > 0)
    if (!hasValidStates) return maxStep
    maxStep = 5

    // Step 6 requires metadata
    const hasValidMetadata = metadata.value.authors.length > 0 &&
                            metadata.value.license !== ''
    if (!hasValidMetadata) return maxStep
    maxStep = 6

    return maxStep
  })

  const canProceed = computed(() => {
    return currentStep.value < maxAccessibleStep.value
  })

  const isComplete = computed(() => {
    return uploadedFiles.value.length > 0 &&
      structure.value !== null &&
      states.value.length > 0 &&
      metadata.value.authors.length > 0 &&
      metadata.value.license !== ''
  })

  // Actions
  function nextStep() {
    if (canProceed.value && currentStep.value < 6) {
      currentStep.value++
    }
  }

  function prevStep() {
    if (currentStep.value > 1) {
      currentStep.value--
    }
  }

  function goToStep(step: number) {
    if (step >= 1 && step <= 6) {
      currentStep.value = step
    }
  }

  function addUploadedFile(file: UploadedFile) {
    uploadedFiles.value.push(file)
  }

  function removeUploadedFile(fileId: string) {
    uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== fileId)
  }

  function addState() {
    const newState: StateData = {
      id: crypto.randomUUID(),
      name: `State ${states.value.length + 1}`,
      description: '',
      proteinState: {
        sequence: '',
        nTerm: 1,
        cTerm: 1
      },
      peptides: []
    }
    states.value.push(newState)
  }

  function removeState(stateId: string) {
    states.value = states.value.filter(s => s.id !== stateId)
  }

  function updateState(stateId: string, updates: Partial<StateData>) {
    const index = states.value.findIndex(s => s.id === stateId)
    if (index !== -1) {
      states.value[index] = { ...states.value[index], ...updates }
    }
  }

  function addPeptide(stateId: string) {
    const state = states.value.find(s => s.id === stateId)
    if (state) {
      const newPeptide: PeptideData = {
        id: crypto.randomUUID(),
        dataFileId: '',
        dataFormat: '',
        deuterationType: 'partially_deuterated',
        filters: {},
        chain: []
      }
      state.peptides.push(newPeptide)
    }
  }

  function removePeptide(stateId: string, peptideId: string) {
    const state = states.value.find(s => s.id === stateId)
    if (state) {
      state.peptides = state.peptides.filter(p => p.id !== peptideId)
    }
  }

  function updatePeptide(stateId: string, peptideId: string, updates: Partial<PeptideData>) {
    const state = states.value.find(s => s.id === stateId)
    if (state) {
      const peptideIndex = state.peptides.findIndex(p => p.id === peptideId)
      if (peptideIndex !== -1) {
        state.peptides[peptideIndex] = { ...state.peptides[peptideIndex], ...updates }
      }
    }
  }

  function addAuthor() {
    metadata.value.authors.push({
      name: '',
      orcid: '',
      affiliation: ''
    })
  }

  function removeAuthor(index: number) {
    metadata.value.authors.splice(index, 1)
  }

  function reset() {
    sessionId.value = ''
    currentStep.value = 1
    uploadedFiles.value = []
    proteinIdentifiers.value = {}
    structure.value = null
    states.value = []
    metadata.value = {
      authors: [],
      license: 'CC0'
    }
    datasetDescription.value = ''
  }

  // Load/Save from localStorage
  function saveToLocalStorage() {
    const data = {
      sessionId: sessionId.value,
      currentStep: currentStep.value,
      uploadedFiles: uploadedFiles.value,
      proteinIdentifiers: proteinIdentifiers.value,
      structure: structure.value,
      states: states.value,
      metadata: metadata.value,
      datasetDescription: datasetDescription.value
    }
    localStorage.setItem('hdxms-builder-draft', JSON.stringify(data))
  }

  function loadFromLocalStorage() {
    const saved = localStorage.getItem('hdxms-builder-draft')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        sessionId.value = data.sessionId || ''
        currentStep.value = data.currentStep || 1
        uploadedFiles.value = data.uploadedFiles || []
        proteinIdentifiers.value = data.proteinIdentifiers || {}
        structure.value = data.structure || null
        states.value = data.states || []
        metadata.value = data.metadata || { authors: [], license: 'CC0' }
        datasetDescription.value = data.datasetDescription || ''
        return true
      } catch (e) {
        console.error('Failed to load draft:', e)
        return false
      }
    }
    return false
  }

  async function uploadTestFile(
    url: string,
    filename: string,
    mimeType: string,
    fileType: 'data' | 'structure'
  // @ts-ignore - False positive: ES2020 includes Promise support
  ): Promise<boolean> {
    try {
      const response = await fetch(url)
      if (!response.ok) throw new Error(`Failed to fetch ${filename}`)

      const blob = await response.blob()
      const file = new File([blob], filename, { type: mimeType })

      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId.value)
      formData.append('file_type', fileType)

      const uploadResponse = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData
      })

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text()
        throw new Error(errorText)
      }

      const backendResponse = await uploadResponse.json()
      console.log(`${filename} uploaded successfully:`, backendResponse)

      // Transform backend response (snake_case) to frontend format (camelCase)
      addUploadedFile({
        id: backendResponse.id,
        filename: backendResponse.filename,
        size: backendResponse.size,
        detectedFormat: backendResponse.detected_format,
        confirmedFormat: backendResponse.confirmed_format,
        fileType: backendResponse.file_type
      })

      return true
    } catch (error) {
      console.error(`Failed to upload ${filename}:`, error)
      alert(`Error uploading ${filename}: ${error}`)
      return false
    }
  }

  // @ts-ignore - False positive: ES2020 includes Promise support
  async function loadTestData() {
    // Clear existing data first
    uploadedFiles.value = []
    states.value = []

    // Create a new session via the backend
    try {
      const sessionResponse = await fetch('/api/files/session', { method: 'POST' })
      if (!sessionResponse.ok) throw new Error('Failed to create session')

      const sessionData = await sessionResponse.json()
      sessionId.value = sessionData.session_id
      console.log('Created session:', sessionId.value)
    } catch (error) {
      console.error('Failed to create session:', error)
      return
    }

    // Upload test files
    const csvUploaded = await uploadTestFile(
      '/test-data/ecSecB_apo.csv',
      'ecSecB_apo.csv',
      'text/csv',
      'data'
    )
    if (!csvUploaded) return

    const pdbUploaded = await uploadTestFile(
      '/test-data/SecB_structure.pdb',
      'SecB_structure.pdb',
      'chemical/x-pdb',
      'structure'
    )
    if (!pdbUploaded) return

    // Get the uploaded data file
    const dataFile = uploadedFiles.value.find(f => f.fileType === 'data')
    const dataFileId = dataFile?.id || ''
    const detectedFormat = dataFile?.detectedFormat || dataFile?.confirmedFormat || ''

    // Mock protein identifiers
    proteinIdentifiers.value = {
      uniprotId: 'P0AG86',
      name: 'SecB',
      organism: 'Escherichia coli'
    }

    // Mock structure
    structure.value = {
      fileId: uploadedFiles.value.find(f => f.fileType === 'structure')?.id || '',
      format: 'pdb',
      description: 'Crystal structure of SecB'
    }

    // Mock states with peptides
    const state1Id = crypto.randomUUID()

    states.value = [
      {
        id: state1Id,
        name: 'SecB WT apo',
        description: 'Wild-type SecB in apo state',
        proteinState: {
          sequence: 'MSEQNNTEMTFQIQRIYTKDISFEAPNAPHVFQKDWQPEVKLDLDTASSQLADDVYEVVLRVTVTASLGEETAFLCEVQQGGIFSIAGIEGTQMAHCLGAYCPNILFPYARECITSMVSRGTFPQLNLAPVNFDALFMNYLQQQAGEGTEEHQDA',
          nTerm: 1,
          cTerm: 155
        },
        peptides: [
          {
            id: crypto.randomUUID(),
            dataFileId: dataFileId,
            dataFormat: detectedFormat,
            deuterationType: 'partially_deuterated',
            pH: 7.5,
            temperature: 293.15,
            dPercentage: 95.0,
            filters: { state: 'SecB WT apo' },
            chain: ['A']
          }
        ]
      }
    ]

    // Mock metadata
    metadata.value = {
      authors: [
        {
          name: 'John Doe',
          orcid: '0000-0001-2345-6789',
          affiliation: 'Test University'
        },
        {
          name: 'Jane Smith',
          orcid: '0000-0002-3456-7890',
          affiliation: 'Research Institute'
        }
      ],
      license: 'CC-BY-4.0',
      title: 'Test HDX-MS Dataset',
      description: 'This is a test dataset for development purposes',
      keywords: ['HDX-MS', 'protein dynamics', 'test']
    }

    datasetDescription.value = 'Comprehensive HDX-MS analysis of test protein in apo and holo states'
  }

  return {
    // State
    sessionId,
    currentStep,
    uploadedFiles,
    proteinIdentifiers,
    structure,
    states,
    metadata,
    datasetDescription,

    // Getters
    dataFiles,
    structureFiles,
    maxAccessibleStep,
    canProceed,
    isComplete,

    // Actions
    nextStep,
    prevStep,
    goToStep,
    addUploadedFile,
    removeUploadedFile,
    addState,
    removeState,
    updateState,
    addPeptide,
    removePeptide,
    updatePeptide,
    addAuthor,
    removeAuthor,
    reset,
    saveToLocalStorage,
    loadFromLocalStorage,
    loadTestData
  }
})
