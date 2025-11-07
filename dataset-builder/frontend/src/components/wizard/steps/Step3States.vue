<template>
  <div class="step-content">
    <div class="step-header">
      <div>
        <h2>Step 3: Define States</h2>
        <p>Define protein states and their peptides</p>
      </div>
      <button class="primary" @click="store.addState()">+ Add State</button>
    </div>

    <div v-if="store.states.length === 0" class="warning">
      No states defined yet. Click "Add State" to get started.
    </div>

    <div v-for="(state, index) in store.states" :key="state.id" class="state-card card">
      <div class="state-header">
        <div class="state-header-left">
          <button class="collapse-button" @click="toggleState(state.id)">
            {{ collapsedStates[state.id] ? '▶' : '▼' }}
          </button>
          <h3>State {{ index + 1 }}{{ state.name ? `: ${state.name}` : '' }}</h3>
        </div>
        <button class="danger" @click="store.removeState(state.id)">Remove</button>
      </div>

      <div v-show="!collapsedStates[state.id]" class="state-content">
        <div class="form-group">
          <label>State Name *</label>
          <input v-model="state.name" type="text" placeholder="e.g., Apo state" />
        </div>

        <div class="form-group">
          <label>Description</label>
          <textarea v-model="state.description" rows="2" />
        </div>

        <h4>Protein State</h4>

        <div class="form-group">
          <label>Sequence *</label>
          <textarea v-model="state.proteinState.sequence" rows="3" placeholder="Amino acid sequence" />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>N-terminus *</label>
            <input v-model.number="state.proteinState.nTerm" type="number" min="1" />
          </div>
          <div class="form-group">
            <label>C-terminus *</label>
            <input v-model.number="state.proteinState.cTerm" type="number" min="1" />
          </div>
          <div class="form-group">
            <label>Oligomeric State</label>
            <input v-model.number="state.proteinState.oligomericState" type="number" min="1" />
          </div>
        </div>

        <h4>Peptides</h4>
        <button class="secondary" @click="store.addPeptide(state.id)">+ Add Peptide</button>

        <div v-if="state.peptides.length === 0" class="warning">
          No peptides defined. Add at least one peptide.
        </div>

        <div v-for="(peptide, pIndex) in state.peptides" :key="peptide.id" class="peptide-card">
          <div class="peptide-header">
            <strong>Peptides {{ pIndex + 1 }}</strong>
            <button class="danger" @click="store.removePeptide(state.id, peptide.id)">Remove</button>
          </div>

          <div class="form-group">
            <label>Data File *</label>
            <div class="file-select-with-badge">
              <select v-model="peptide.dataFileId">
                <option value="">Select file...</option>
                <option v-for="file in store.dataFiles" :key="file.id" :value="file.id">
                  {{ file.filename }}
                </option>
              </select>
              <span v-if="getSelectedFileFormat(peptide.dataFileId)" class="badge">
                {{ getSelectedFileFormat(peptide.dataFileId) }}
              </span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Deuteration Type *</label>
              <select v-model="peptide.deuterationType">
                <option value="partially_deuterated">Partially Deuterated</option>
                <option value="fully_deuterated">Fully Deuterated</option>
                <option value="non_deuterated">Non-Deuterated</option>
              </select>
            </div>

            <div class="form-group">
              <label>Structure Mapping (Optional)</label>
              <select
                v-model="peptide.structureMappingId"
                :disabled="store.structureMappings.length === 0"
              >
                <option :value="undefined">None</option>
                <option
                  v-for="mapping in store.structureMappings"
                  :key="mapping.id"
                  :value="mapping.id"
                >
                  {{ mapping.name }}
                </option>
              </select>
              <span v-if="store.structureMappings.length === 0" class="hint">
                No structure mappings defined. Add mappings in Step 2 if needed.
              </span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>pH read</label>
              <input v-model.number="peptide.pH" type="number" placeholder="8.0" />
            </div>
            <div class="form-group">
              <label>Temperature (K)</label>
              <input v-model.number="peptide.temperature" type="number" placeholder="303.15" />
            </div>
            <div class="form-group">
              <label>Percentage D</label>
              <input v-model.number="peptide.dPercentage" type="number" placeholder="90.0" />
            </div>
          </div>

          <!-- Filter Section -->
          <div v-if="shouldShowFilters(peptide)" class="filters-section">
            <h5>Data Filters</h5>
            <p class="filter-hint">
              Select which rows from the data file to include based on column values
            </p>
            <div
              v-for="columnName in getFilterColumnsForPeptide(peptide)"
              :key="columnName"
              class="filter-item"
            >
              <FilterSelector
                :label="columnName"
                :options="getOptionsForColumn(peptide, columnName)"
                :model-value="getPeptideFilterValues(peptide, columnName)"
                @update:model-value="(values) => updatePeptideFilter(state.id, peptide.id, columnName, values)"
              />
            </div>
            <div v-if="loadingFilters[peptide.id]" class="loading-hint">
              Loading filter options...
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDatasetStore } from '@/stores/dataset'
import FilterSelector from '@/components/wizard/FilterSelector.vue'
import { getFilterColumns, fetchFilterOptions, hasFilters } from '@/utils/formatFilters'

const store = useDatasetStore()
const collapsedStates = ref<Record<string, boolean>>({})

// Store filter options for each peptide: peptideId -> { columnName: string[] }
const filterOptionsCache = ref<Record<string, Record<string, string[]>>>({})

// Track loading state for each peptide
const loadingFilters = ref<Record<string, boolean>>({})

// Track which peptides we've loaded options for (to avoid re-triggering on unrelated changes)
const loadedPeptideFiles = ref<Record<string, string>>({})

const toggleState = (stateId: string) => {
  collapsedStates.value[stateId] = !collapsedStates.value[stateId]
}

const getSelectedFileFormat = (fileId: string): string | null => {
  if (!fileId) return null
  const file = store.dataFiles.find((f) => f.id === fileId)
  return file?.detectedFormat || null
}

const getFilterColumnsForPeptide = (peptide: any) => {
  const format = getSelectedFileFormat(peptide.dataFileId)
  return getFilterColumns(format)
}

const getOptionsForColumn = (peptide: any, columnName: string): string[] => {
  const options = filterOptionsCache.value[peptide.id]?.[columnName] || []
  return options
}

const updatePeptideFilter = async (
  stateId: string,
  peptideId: string,
  columnName: string,
  values: string[]
) => {
  const state = store.states.find((s) => s.id === stateId)
  if (state) {
    const peptide = state.peptides.find((p) => p.id === peptideId)
    if (peptide) {
      // Update the filters object
      const updatedFilters = { ...peptide.filters, [columnName]: values }
      store.updatePeptide(stateId, peptideId, { filters: updatedFilters })

      // Refresh filter options with cascading behavior
      await loadFilterOptions(peptide)
    }
  }
}

const getPeptideFilterValues = (peptide: any, columnName: string): string[] => {
  return peptide.filters?.[columnName] || []
}

const shouldShowFilters = (peptide: any) => {
  const format = getSelectedFileFormat(peptide.dataFileId)
  return format && hasFilters(format)
}

const loadFilterOptions = async (peptide: any) => {
  if (!peptide.dataFileId || !store.sessionId) return

  const format = getSelectedFileFormat(peptide.dataFileId)
  if (!format || !hasFilters(format)) return

  loadingFilters.value[peptide.id] = true

  try {
    // Fetch filter options considering current filter selections
    const options = await fetchFilterOptions(store.sessionId, peptide.dataFileId, peptide.filters || {})
    console.log('Fetched filter options for peptide', peptide.id, options, peptide, peptide.filters)
    filterOptionsCache.value[peptide.id] = options
    // Track that we've loaded options for this peptide's file
    loadedPeptideFiles.value[peptide.id] = peptide.dataFileId
  } catch (error) {
    console.error('Failed to load filter options:', error)
    // Keep existing options on error
  } finally {
    loadingFilters.value[peptide.id] = false
  }
}

// Watch for changes to peptides and load filter options only when dataFileId changes
watch(
  () => store.states,
  (newStates) => {
    newStates.forEach((state) => {
      state.peptides.forEach((peptide) => {
        // Only load if:
        // 1. Peptide has a dataFileId
        // 2. AND we haven't loaded options for this peptide yet
        // 3. OR the dataFileId has changed from what we previously loaded
        if (
          peptide.dataFileId &&
          loadedPeptideFiles.value[peptide.id] !== peptide.dataFileId
        ) {
          loadFilterOptions(peptide)
        }
      })
    })
  },
  { deep: true, immediate: true }
)
</script>

<style scoped>
.step-content {
  padding: 20px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.step-header h2 {
  margin: 0 0 5px 0;
}

.step-header p {
  margin: 0;
}

.state-card {
  margin: 20px 0;
  padding: 20px;
  border-left: 4px solid #007bff;
}

.state-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.state-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.collapse-button {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 5px 10px;
  color: #007bff;
  transition: transform 0.2s;
}

.collapse-button:hover {
  background: #f0f0f0;
  border-radius: 4px;
}

.state-content {
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.peptide-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
}

.peptide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

h4 {
  margin: 20px 0 10px 0;
  color: #007bff;
}

.hint {
  display: block;
  margin-top: 5px;
  color: #6c757d;
  font-size: 12px;
  font-style: italic;
}

select:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

.file-select-with-badge {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-select-with-badge select {
  flex: 1;
}

.badge {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.filters-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #dee2e6;
}

.filters-section h5 {
  margin: 0 0 5px 0;
  color: #495057;
  font-size: 14px;
  font-weight: 600;
}

.filter-hint {
  margin: 0 0 15px 0;
  color: #6c757d;
  font-size: 12px;
  font-style: italic;
}

.filter-item {
  margin-bottom: 10px;
}

.loading-hint {
  margin-top: 10px;
  padding: 8px 12px;
  background: #f0f8ff;
  border: 1px solid #b3d9ff;
  border-radius: 4px;
  color: #0066cc;
  font-size: 12px;
  font-style: italic;
  text-align: center;
}
</style>
