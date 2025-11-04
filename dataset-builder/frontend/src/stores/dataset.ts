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

  const canProceed = computed(() => {
    switch (currentStep.value) {
      case 1: // File upload
        return uploadedFiles.value.length > 0
      case 2: // Protein identifiers
        return true // Optional fields
      case 3: // Structure
        return structure.value !== null
      case 4: // States
        return states.value.length > 0 &&
               states.value.every(s => s.peptides.length > 0)
      case 5: // Metadata
        return metadata.value.authors.length > 0 &&
               metadata.value.license !== ''
      default:
        return false
    }
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

  function loadTestData() {
    // Mock session ID
    sessionId.value = 'test-session-' + crypto.randomUUID()

    // Mock uploaded files
    uploadedFiles.value = [
      {
        id: 'file-1',
        filename: 'test_data.csv',
        size: 1024,
        fileType: 'data',
        uploadedAt: new Date().toISOString()
      },
      {
        id: 'file-2',
        filename: 'protein_structure.pdb',
        size: 2048,
        fileType: 'structure',
        uploadedAt: new Date().toISOString()
      }
    ]

    // Mock protein identifiers
    proteinIdentifiers.value = {
      uniprotId: 'P12345',
      name: 'Test Protein',
      organism: 'Homo sapiens'
    }

    // Mock structure
    structure.value = {
      fileId: 'file-2',
      format: 'pdb',
      description: 'Crystal structure of test protein'
    }

    // Mock states with peptides
    const state1Id = crypto.randomUUID()
    const state2Id = crypto.randomUUID()

    states.value = [
      {
        id: state1Id,
        name: 'Apo state',
        description: 'Protein without ligand',
        proteinState: {
          sequence: 'MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL',
          nTerm: 1,
          cTerm: 289
        },
        peptides: [
          {
            id: crypto.randomUUID(),
            dataFileId: 'file-1',
            dataFormat: 'DynamX_v3_state',
            deuterationType: 'partially_deuterated',
            pH: 7.4,
            temperature: 293.15,
            dPercentage: 95.0,
            filters: {},
            chain: ['A']
          }
        ]
      },
      {
        id: state2Id,
        name: 'Holo state',
        description: 'Protein with ligand bound',
        proteinState: {
          sequence: 'MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL',
          nTerm: 1,
          cTerm: 289,
          oligomericState: 2
        },
        peptides: [
          {
            id: crypto.randomUUID(),
            dataFileId: 'file-1',
            dataFormat: 'HDExaminer_v3',
            deuterationType: 'partially_deuterated',
            pH: 7.4,
            temperature: 293.15,
            dPercentage: 95.0,
            filters: {},
            chain: ['A', 'B']
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
