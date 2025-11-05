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
            <strong>Peptide {{ pIndex + 1 }}</strong>
            <button class="danger" @click="store.removePeptide(state.id, peptide.id)">Remove</button>
          </div>

          <div class="form-group">
            <label>Data File *</label>
            <select v-model="peptide.dataFileId">
              <option value="">Select file...</option>
              <option v-for="file in store.dataFiles" :key="file.id" :value="file.id">
                {{ file.filename }}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Format *</label>
              <select v-model="peptide.dataFormat">
                <option value="">Auto-detect</option>
                <option value="DynamX_v3_state">DynamX v3 (State)</option>
                <option value="DynamX_v3_cluster">DynamX v3 (Cluster)</option>
                <option value="HDExaminer_v3">HDExaminer v3</option>
                <option value="OpenHDX">OpenHDX</option>
              </select>
            </div>

            <div class="form-group">
              <label>Deuteration Type *</label>
              <select v-model="peptide.deuterationType">
                <option value="partially_deuterated">Partially Deuterated</option>
                <option value="fully_deuterated">Fully Deuterated</option>
                <option value="non_deuterated">Non-Deuterated</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>pH</label>
              <input v-model.number="peptide.pH" type="number" step="0.1" placeholder="8.0" />
            </div>
            <div class="form-group">
              <label>Temperature (K)</label>
              <input v-model.number="peptide.temperature" type="number" placeholder="303.15" />
            </div>
            <div class="form-group">
              <label>D%</label>
              <input v-model.number="peptide.dPercentage" type="number" placeholder="90.0" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDatasetStore } from '@/stores/dataset'

const store = useDatasetStore()
const collapsedStates = ref<Record<string, boolean>>({})

const toggleState = (stateId: string) => {
  collapsedStates.value[stateId] = !collapsedStates.value[stateId]
}
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
</style>
