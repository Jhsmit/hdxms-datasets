<template>
  <div id="app">
    <header class="app-header">
      <h1>HDX-MS Dataset Builder</h1>
      <p>Create standardized HDX-MS datasets with ease</p>
      <div v-if="isDev" class="dev-buttons">
        <button
          class="test-data-button"
          @click="loadTestData"
          title="Load test data for development"
        >
          Load Test Data
        </button>
        <button
          class="clear-data-button"
          @click="clearData"
          title="Clear all data"
        >
          Clear Data
        </button>
      </div>
    </header>

    <main class="app-main">
      <WizardContainer />
    </main>

    <footer class="app-footer">
      <p>HDX-MS Dataset Builder v0.1.0</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import WizardContainer from './components/wizard/WizardContainer.vue'
import { useDatasetStore } from './stores/dataset'
import { apiService } from './services/api'

const store = useDatasetStore()

// Check if in development mode
const isDev = computed(() => import.meta.env.DEV)

function loadTestData() {
  if (confirm('This will replace all current data with test data. Continue?')) {
    store.loadTestData()
    console.log('Test data loaded successfully!')
  }
}

function clearData() {
  if (confirm('This will clear all data. Continue?')) {
    store.reset()
    console.log('All data cleared!')
  }
}

onMounted(async () => {
  // Try to load saved draft
  const loaded = store.loadFromLocalStorage()

  if (!loaded || !store.sessionId) {
    // Create new session
    try {
      const sessionId = await apiService.createSession()
      store.sessionId = sessionId
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  // Auto-save every 30 seconds
  setInterval(() => {
    store.saveToLocalStorage()
  }, 30000)

  // Warn before leaving with unsaved changes
  window.addEventListener('beforeunload', (e) => {
    if (store.states.length > 0 || store.uploadedFiles.length > 0) {
      e.preventDefault()
      e.returnValue = ''
    }
  })
})
</script>

<style scoped>
.app-header {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  margin-bottom: 30px;
  position: relative;
}

.app-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.app-header p {
  font-size: 1.2rem;
  opacity: 0.9;
}

.dev-buttons {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
}

.test-data-button,
.clear-data-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.5);
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.test-data-button:hover,
.clear-data-button:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
}

.clear-data-button {
  background: rgba(255, 100, 100, 0.2);
  border-color: rgba(255, 100, 100, 0.5);
}

.clear-data-button:hover {
  background: rgba(255, 100, 100, 0.3);
  border-color: rgba(255, 100, 100, 0.8);
}

.app-main {
  min-height: 500px;
}

.app-footer {
  text-align: center;
  padding: 20px;
  margin-top: 40px;
  color: #666;
  font-size: 0.9rem;
}
</style>
