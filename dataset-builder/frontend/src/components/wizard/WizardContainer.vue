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
          completed: store.currentStep > step.number,
          disabled: !canAccessStep(step.number)
        }"
        @click="handleStepClick(step.number)"
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
        v-if="store.currentStep < 5"
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
import Step2ProteinStructure from './steps/Step2ProteinStructure.vue'
import Step3States from './steps/Step3States.vue'
import Step4Metadata from './steps/Step4Metadata.vue'
import Step5Review from './steps/Step5Review.vue'

const store = useDatasetStore()

const steps = [
  { number: 1, label: 'Upload Files' },
  { number: 2, label: 'Protein & Structure' },
  { number: 3, label: 'States' },
  { number: 4, label: 'Metadata' },
  { number: 5, label: 'Review' }
]

const canAccessStep = (stepNumber: number) => {
  return stepNumber <= store.maxAccessibleStep
}

const handleStepClick = (stepNumber: number) => {
  if (canAccessStep(stepNumber)) {
    store.goToStep(stepNumber)
  }
}

const stepComponents = {
  1: Step1FileUpload,
  2: Step2ProteinStructure,
  3: Step3States,
  4: Step4Metadata,
  5: Step5Review
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

.progress-step.disabled {
  cursor: not-allowed;
  opacity: 0.5;
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
