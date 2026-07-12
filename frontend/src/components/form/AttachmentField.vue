<template>
  <div class="attachment-field-single" :class="{ 'is-readonly': readonly, 'is-invalid': invalid }">
    <!-- File Card (when file exists) -->
    <div v-if="currentFile" class="file-card">
      <div class="file-icon">
        <component :is="getFileIcon(currentFile.mimetype)" :size="32" />
      </div>
      <div class="file-info">
        <div class="file-name" :title="currentFile.name">{{ currentFile.name }}</div>
        <div class="file-meta">{{ formatFileSize(currentFile.file_size) }}</div>
      </div>
      <div class="file-actions">
        <button 
          v-if="!readonly"
          @click="downloadFile" 
          class="btn-icon" 
          type="button"
          title="Download"
        >
          <Download :size="16" />
        </button>
        <button 
          v-if="!readonly"
          @click="removeFile" 
          class="btn-icon btn-danger" 
          type="button"
          title="Remove"
        >
          <Trash2 :size="16" />
        </button>
      </div>
    </div>

    <!-- Upload Zone (when no file) -->
    <div 
      v-else-if="!readonly"
      class="upload-zone"
      :class="{ 'is-dragging': isDragging }"
      @click="triggerFileInput"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInput"
        type="file"
        @change="handleFileSelect"
        :accept="acceptTypes"
        class="file-input-hidden"
      />
      <Upload :size="32" class="upload-icon" />
      <div class="upload-text">
        <span class="upload-primary">Click to upload or drag and drop</span>
      </div>
      <div class="upload-constraints-inline">
        <span v-if="metadata?.allowed_types" class="constraint-inline">
          {{ getAllowedTypesText() }}
        </span>
        <span v-if="metadata?.allowed_types" class="constraint-separator">•</span>
        <span class="constraint-inline">
          Max {{ formatFileSize(metadata?.max_size || 10485760) }}
        </span>
      </div>
    </div>

    <!-- Readonly empty state -->
    <div v-else class="empty-state">
      No attachment
    </div>

    <!-- Loading overlay -->
    <div v-if="uploading" class="upload-overlay">
      <div class="spinner"></div>
      <span>Uploading...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Upload, Download, Trash2, FileText, File, FileImage, FileVideo, FileAudio, FileArchive, FileCode } from 'lucide-vue-next';
import api from '../../core/api';
import { useNotifications } from '../../composables/useNotifications';

const props = defineProps<{
  modelValue: any;
  metadata: any;
  readonly: boolean;
  invalid: boolean;
  context?: Record<string, any>;
}>();

const emit = defineEmits(['update:modelValue']);
const { add } = useNotifications();

const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
const uploading = ref(false);
const currentFile = ref<any>(null);

// Load existing attachment
watch(() => props.modelValue, async (newVal) => {
  if (newVal && typeof newVal === 'number') {
    // Load attachment by ID
    try {
      const response = await api.get(`/models/ir.attachment/${newVal}`);
      currentFile.value = response.data;
    } catch (error) {
      console.error('Failed to load attachment:', error);
    }
  } else if (newVal && typeof newVal === 'object') {
    currentFile.value = newVal;
  } else {
    currentFile.value = null;
  }
}, { immediate: true });

const acceptTypes = computed(() => {
  if (!props.metadata?.allowed_types) return '*/*';
  return props.metadata.allowed_types.map((t: string) => `.${t}`).join(',');
});

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    uploadFile(file);
  }
};

const handleDrop = (event: DragEvent) => {
  isDragging.value = false;
  const file = event.dataTransfer?.files[0];
  if (file) {
    uploadFile(file);
  }
};

const uploadFile = async (file: File) => {
  // Validate file size
  if (props.metadata?.max_size && file.size > props.metadata.max_size) {
    add({
      type: 'danger',
      message: `File size exceeds maximum allowed size of ${formatFileSize(props.metadata.max_size)}`,
      duration: 5000
    });
    return;
  }

  // Validate file type
  if (props.metadata?.allowed_types) {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext && !props.metadata.allowed_types.includes(ext)) {
      add({
        type: 'danger',
        message: `File type .${ext} is not allowed. Allowed types: ${props.metadata.allowed_types.join(', ')}`,
        duration: 5000
      });
      return;
    }
  }

  uploading.value = true;

  try {
    // Read file as base64
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64 = (e.target?.result as string).split(',')[1];

      // Create attachment record
      const attachmentData = {
        name: file.name,
        datas: base64,
        file_size: file.size,
        mimetype: file.type,
        res_model: props.context?.model || '',
        res_id: props.context?.id || 0,
        res_field: props.metadata?.name || ''
      };

      const response = await api.post('/models/ir.attachment', attachmentData);
      currentFile.value = response.data;
      emit('update:modelValue', response.data.id);

      add({
        type: 'success',
        message: 'File uploaded successfully',
        duration: 3000
      });
    };

    reader.readAsDataURL(file);
  } catch (error: any) {
    add({
      type: 'danger',
      message: error.response?.data?.detail || 'Failed to upload file',
      duration: 5000
    });
  } finally {
    uploading.value = false;
  }
};

const removeFile = async () => {
  if (!currentFile.value) return;

  try {
    await api.delete(`/models/ir.attachment/${currentFile.value.id}`);
    currentFile.value = null;
    emit('update:modelValue', null);

    add({
      type: 'success',
      message: 'File removed',
      duration: 3000
    });
  } catch (error: any) {
    add({
      type: 'danger',
      message: error.response?.data?.detail || 'Failed to remove file',
      duration: 5000
    });
  }
};

const downloadFile = () => {
  if (!currentFile.value?.datas) return;

  const link = document.createElement('a');
  link.href = `data:${currentFile.value.mimetype};base64,${currentFile.value.datas}`;
  link.download = currentFile.value.name;
  link.click();
};

const getFileIcon = (mimetype: string) => {
  if (!mimetype) return FileText;
  if (mimetype.startsWith('image/')) return FileImage;
  if (mimetype.startsWith('video/')) return FileVideo;
  if (mimetype.startsWith('audio/')) return FileAudio;
  if (mimetype.includes('zip') || mimetype.includes('rar') || mimetype.includes('tar')) return FileArchive;
  if (mimetype.includes('javascript') || mimetype.includes('python') || mimetype.includes('java')) return FileCode;
  if (mimetype.includes('pdf')) return FileText;
  return File;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

const getAllowedTypesText = (): string => {
  if (!props.metadata?.allowed_types) return '';
  return props.metadata.allowed_types.map((t: string) => `.${t}`).join(', ');
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.attachment-field-single {
  position: relative;
  
  &.is-invalid {
    .upload-zone {
      border-color: v.$danger-color;
    }
  }
}

.file-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 8px;
  transition: all 0.2s;
  
  &:hover {
    border-color: v.$primary-color;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
}

// Dark mode file card
[data-theme="dark"] .file-card {
  background: #0d1117;
  border-color: #30363d;
  
  &:hover {
    border-color: #58a6ff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}

.file-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: v.$bg-main;
  border-radius: 8px;
  color: v.$primary-color;
}

// Dark mode file icon
[data-theme="dark"] .file-icon {
  background: #161b22;
  color: #58a6ff;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 0.75rem;
  color: v.$text-secondary;
  margin-top: 0.25rem;
}

// Dark mode file info
[data-theme="dark"] {
  .file-name {
    color: #e6edf3;
  }
  
  .file-meta {
    color: #7d8590;
  }
}

.file-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: v.$bg-main;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  color: v.$text-secondary;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: v.$white;
    border-color: v.$primary-color;
    color: v.$primary-color;
  }
  
  &.btn-danger:hover {
    border-color: v.$danger-color;
    color: v.$danger-color;
    background: rgba(v.$danger-color, 0.05);
  }
}

// Dark mode button icon
[data-theme="dark"] .btn-icon {
  background: #161b22;
  border-color: #30363d;
  color: #7d8590;
  
  &:hover {
    background: #0d1117;
    border-color: #58a6ff;
    color: #58a6ff;
  }
  
  &.btn-danger:hover {
    border-color: #f85149;
    color: #f85149;
    background: rgba(248, 81, 73, 0.1);
  }
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: v.$bg-main;
  border: 2px dashed v.$border-color;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover, &.is-dragging {
    border-color: v.$primary-color;
    background: rgba(v.$primary-color, 0.02);
  }
}

// Dark mode upload zone
[data-theme="dark"] .upload-zone {
  background: #0d1117;
  border-color: #30363d;
  
  &:hover, &.is-dragging {
    border-color: #58a6ff;
    background: rgba(88, 166, 255, 0.05);
  }
}

.file-input-hidden {
  display: none;
}

.upload-icon {
  color: v.$text-secondary;
  margin-bottom: 0.75rem;
}

.upload-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.upload-primary {
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
}

.upload-constraints-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: v.$text-secondary;
}

.constraint-inline {
  color: v.$text-secondary;
}

.constraint-separator {
  color: v.$text-disabled;
}

// Dark mode upload text
[data-theme="dark"] {
  .upload-icon {
    color: #7d8590;
  }
  
  .upload-primary {
    color: #e6edf3;
  }
  
  .upload-constraints-inline,
  .constraint-inline {
    color: #7d8590;
  }
  
  .constraint-separator {
    color: #484f58;
  }
}

.empty-state {
  padding: 1rem;
  text-align: center;
  color: v.$text-secondary;
  font-size: 0.875rem;
  font-style: italic;
}

.upload-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  font-size: 0.875rem;
  color: v.$text-secondary;
}

// Dark mode upload overlay
[data-theme="dark"] .upload-overlay {
  background: rgba(13, 17, 23, 0.95);
  color: #7d8590;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid v.$border-color;
  border-top: 3px solid v.$primary-color;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

// Dark mode spinner
[data-theme="dark"] .spinner {
  border-color: #30363d;
  border-top-color: #58a6ff;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.is-readonly {
  .file-card {
    background: v.$bg-main;
    cursor: default;
    
    &:hover {
      border-color: v.$border-color;
      box-shadow: none;
    }
  }
}

// Dark mode readonly
[data-theme="dark"] .is-readonly {
  .file-card {
    background: #161b22;
    
    &:hover {
      border-color: #30363d;
    }
  }
}
</style>
