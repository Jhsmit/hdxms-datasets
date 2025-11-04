<template>
  <div class="wizard-container card">
    <!-- Progress bar -->
    <div class="wizard-progress">
      <div
        v-for="step in steps"
        :key="step.number"
        class="progress-step"
        :class="{
          active: store.currentStep === step.number,
          completed: store.currentStep > step.number
        }"
        @click="store.goToStep(step.number)"
      >
        <div class="step-number">{{ step.number }}</div>
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- Step content -->
    <div class="wizard-content">
      <component :is="currentStepComponent" />
    </div>

    <!-- Navigation -->
    <div class="wizard-navigation">
      <button
        class="secondary"
        @click="store.prevStep()"
        :disabled="store.currentStep === 1"
      >
        Previous
      </button>

      <button
        v-if="store.currentStep < 6"
        class="primary"
        @click="store.nextStep()"
        :disabled="!store.canProceed"
      >
        Next
      </button>

      <button
        v-else
        class="primary"
        @click="handleGenerate"
        :disabled="!store.isComplete"
      >
        Generate Dataset
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDatasetStore } from '@/stores/dataset'
import Step1FileUpload from './steps/Step1FileUpload.vue'
import Step2ProteinInfo from './steps/Step2ProteinInfo.vue'
import Step3Structure from './steps/Step3Structure.vue'
import Step4States from './steps/Step4States.vue'
import Step5Metadata from './steps/Step5Metadata.vue'
import Step6Review from './steps/Step6Review.vue'

const store = useDatasetStore()

const steps = [
  { number: 1, label: 'Upload Files' },
  { number: 2, label: 'Protein Info' },
  { number: 3, label: 'Structure' },
  { number: 4, label: 'States' },
  { number: 5, label: 'Metadata' },
  { number: 6, label: 'Review' }
]

const stepComponents = {
  1: Step1FileUpload,
  2: Step2ProteinInfo,
  3: Step3Structure,
  4: Step4States,
  5: Step5Metadata,
  6: Step6Review
}

const currentStepComponent = computed(() => {
  return stepComponents[store.currentStep as keyof typeof stepComponents]
})

const handleGenerate = () => {
  // This will be handled in Step6Review
  console.log('Generate dataset')
}
</script>

<style scoped>
.wizard-container {
  max-width: 900px;
  margin: 0 auto;
}

.wizard-progress {
  display: flex;
  justify-content: space-between;
  margin-bottom: 40px;
  padding: 0 20px;
}

.progress-step {
  flex: 1;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.progress-step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 20px;
  width: 100%;
  height: 2px;
  background: #ddd;
  z-index: -1;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ddd;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  font-weight: bold;
  transition: all 0.3s;
}

.progress-step.active .step-number {
  background: #007bff;
  color: white;
  transform: scale(1.2);
}

.progress-step.completed .step-number {
  background: #28a745;
  color: white;
}

.step-label {
  font-size: 12px;
  color: #666;
}

.progress-step.active .step-label {
  color: #007bff;
  font-weight: bold;
}

.wizard-content {
  min-height: 400px;
  margin-bottom: 30px;
}

.wizard-navigation {
  display: flex;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid #ddd;
}
</style>
