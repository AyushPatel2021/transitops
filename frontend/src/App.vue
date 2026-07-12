<template>
  <router-view />
  
  <!-- Global Dialog Components -->
  <AlertDialog
    :show="alertState.show"
    :title="alertState.title"
    :message="alertState.message"
    :type="alertState.type"
    :confirmText="alertState.confirmText"
    :loading="alertState.loading"
    @confirm="alertState.onConfirm"
    @close="closeAlert"
  />
  
  <ConfirmDialog
    :show="confirmState.show"
    :title="confirmState.title"
    :message="confirmState.message"
    :severity="confirmState.severity"
    :confirmText="confirmState.confirmText"
    :cancelText="confirmState.cancelText"
    :loading="confirmState.loading"
    @confirm="confirmState.onConfirm"
    @cancel="confirmState.onCancel"
    @close="closeConfirm"
  />
  
  <PromptDialog
    :show="promptState.show"
    :title="promptState.title"
    :message="promptState.message"
    :placeholder="promptState.placeholder"
    :defaultValue="promptState.defaultValue"
    :inputType="promptState.inputType"
    :required="promptState.required"
    :confirmText="promptState.confirmText"
    :cancelText="promptState.cancelText"
    :loading="promptState.loading"
    @confirm="promptState.onConfirm"
    @cancel="promptState.onCancel"
    @close="closePrompt"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useUserStore } from './stores/userStore';
import { useDialog } from './composables/useDialog';
import { useTheme } from './composables/useTheme';
import AlertDialog from './components/common/AlertDialog.vue';
import ConfirmDialog from './components/common/ConfirmDialog.vue';
import PromptDialog from './components/common/PromptDialog.vue';

// Initialize user store on app startup
const userStore = useUserStore();

// Initialize theme system
const { initializeTheme } = useTheme();

// Initialize global dialogs
const { alertState, confirmState, promptState, closeAlert, closeConfirm, closePrompt } = useDialog();

onMounted(async () => {
  // Initialize theme system
  initializeTheme();
  
  // Initialize user if we have a token and not already initializing
  if (userStore.token && !userStore.isInitializing) {
    try {
      await userStore.initializeUser();
    } catch (error) {
      // Silent error handling
    }
  }
});
</script>

<style lang="scss">
@use "./styles/base";
</style>
