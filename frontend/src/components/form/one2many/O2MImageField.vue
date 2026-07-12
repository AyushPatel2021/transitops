<template>
  <div class="o2m-image-field">
    <div v-if="!readonly" class="image-upload-wrapper">
      <input
        type="file"
        ref="fileInput"
        @change="handleFileChange"
        accept="image/*"
        class="file-input"
        :disabled="readonly"
      />
      <button 
        v-if="!modelValue"
        @click="triggerFileInput"
        class="upload-btn"
        type="button"
      >
        Upload
      </button>
      <div v-else class="image-preview">
        <img :src="imageUrl" alt="Preview" class="preview-img" />
        <button @click="clearImage" class="clear-btn" type="button" title="Remove">×</button>
      </div>
    </div>
    <div v-else class="o2m-field-readonly">
      <img v-if="modelValue" :src="imageUrl" alt="Image" class="readonly-img" />
      <span v-else>-</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  modelValue: string | null | undefined;
  fieldMeta: any;
  readonly: boolean;
  invalid?: boolean;
}>();

const emit = defineEmits(['update:modelValue', 'focus']);

const fileInput = ref<HTMLInputElement | null>(null);

const imageUrl = computed(() => {
  if (!props.modelValue) return '';
  if (props.modelValue.startsWith('data:')) return props.modelValue;
  if (props.modelValue.startsWith('http')) return props.modelValue;
  return `data:image/png;base64,${props.modelValue}`;
});

const triggerFileInput = () => {
  fileInput.value?.click();
  emit('focus');
};

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const result = e.target?.result as string;
    // Extract base64 data without the data:image/...;base64, prefix
    const base64 = result.split(',')[1];
    emit('update:modelValue', base64);
  };
  reader.readAsDataURL(file);
};

const clearImage = () => {
  emit('update:modelValue', null);
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};
</script>

<style lang="scss" scoped>
@use "sass:color";
@use "../../../styles/variables" as v;

.o2m-image-field {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 4px 8px;
}

.image-upload-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}

.file-input {
  display: none;
}

.upload-btn {
  padding: 4px 12px;
  font-size: 12px;
  background: v.$primary-color;
  color: v.$white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: v.$primary-hover;
  }
}

.image-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.preview-img {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid v.$border-color;
}

.clear-btn {
  background: v.$danger-color;
  color: v.$white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
  transition: all 0.2s;
  
  &:hover {
    filter: brightness(0.9);
  }
}

.o2m-field-readonly {
  padding: 4px 8px;
  color: v.$text-secondary;
  display: flex;
  align-items: center;
}

.readonly-img {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid v.$border-color;
}
</style>
