<template>
  <div class="o2m-field-wrapper">
    <Many2OneField
      :model-value="parsedValue"
      :options="options"
      :readonly="readonly"
      :invalid="invalid"
      :relation="fieldMeta?.relation"
      :placeholder="fieldMeta?.label || 'Select...'"
      @update:model-value="handleUpdate"
      @focus="$emit('focus')"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import Many2OneField from '../Many2OneField.vue';

const props = defineProps<{
  modelValue: any | null;
  fieldMeta: any;
  readonly?: boolean;
  invalid?: boolean;
  relationOptions?: any[];
  context?: Record<string, any>;
}>();

const emit = defineEmits(['update:modelValue', 'focus']);

// Handle both ID (int) and Object ({id, name}) values
const parsedValue = computed(() => {
  if (props.modelValue && typeof props.modelValue === 'object') {
    return props.modelValue.id;
  }
  return props.modelValue;
});

const localOptions = ref<any[]>([]);

const options = computed(() => {
  const sourceOptions = localOptions.value.length > 0 ? localOptions.value : (props.relationOptions || []);
  const recName = props.fieldMeta?.rec_name || 'display_name';
  return sourceOptions.map(opt => ({
    val: opt.id,
    label: opt[recName] || opt.display_name || opt.name || opt.full_name || opt.subject || `#${opt.id}`
  }));
});

import api from '../../../core/api';
import { DomainEngine } from '../../../core/domain-engine';

const loadOptions = async () => {
  if (!props.fieldMeta?.domain || !props.fieldMeta?.relation) return;
  
  try {
    const domainEngine = new DomainEngine();
    const domain = domainEngine.resolveDomain(props.fieldMeta.domain, props.context || {});
    
    if (domain && domain.length > 0) {
      const resp = await api.get(`/models/${props.fieldMeta.relation}`, {
        params: { domain: JSON.stringify(domain) }
      });
      localOptions.value = resp.data?.items || [];
    }
  } catch (e) {
    // Silently fail
  }
};

onMounted(() => {
  if (props.fieldMeta?.domain) {
    loadOptions();
  }
});

watch(() => props.context, () => {
  if (props.fieldMeta?.domain) {
    loadOptions();
  }
}, { deep: true });

const handleUpdate = (value: any) => {
  emit('update:modelValue', value);
};
</script>

<style scoped>
.o2m-field-wrapper {
  padding: 0 4px; /* Reduced padding */
  position: relative;
  width: 100%;
  min-width: 120px; /* Ensure minimum usable width */
}

/* Override dropdown width to prevent narrow dropdowns */
:deep(.dropdown-list) {
  min-width: 200px !important;
  width: max-content !important;
  max-width: 300px !important;
}

/* Ensure proper spacing for actions */
:deep(.selected-display) {
  width: calc(100% - 60px) !important; /* Reduced reserved space to show more text */
  padding-right: 4px;
}

:deep(.many2one-input) {
  padding-right: 60px; /* Reduced reserved space */
}

/* On hover/focus, we might need more space for actions if they appear, 
   but 60px should be enough for clear + arrow */
</style>
