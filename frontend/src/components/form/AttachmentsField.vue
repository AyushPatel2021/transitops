<template>
  <div class="attachments-field-multiple" :class="{ 'is-readonly': readonly, 'is-invalid': invalid }">
    <!-- File Grid -->
    <div v-if="files.length > 0" class="files-grid">
      <div v-for="file in files" :key="file.id" class="file-card-compact">
        <div class="file-icon-small">
          <component :is="getFileIcon(file.mimetype)" :size="20" />
        </div>
        <div class="file-info-compact">
          <div class="file-name-compact" :title="file.name">{{ file.name }}</div>
          <div class="file-size-compact">{{ formatFileSize(file.file_size) }}</div>
        </div>
        <div class="file-actions-compact">
          <button 
            @click="downloadFile(file)" 
            class="btn-icon-sm" 
            type="button"
            title="Download"
          >
            <Download :size="14" />
          </button>
          <button 
            v-if="!readonly"
            @click="removeFile(file)" 
            class="btn-icon-sm btn-danger" 
            type="button"
            title="Remove"
          >
            <X :size="14" />
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Zone -->
    <div 
      v-if="!readonly && canAddMore"
      class="upload-zone-compact"
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
        multiple
        class="file-input-hidden"
      />
      <Plus :size="24" class="upload-icon-sm" />
      <div class="upload-content">
        <span class="upload-text-sm">Add files</span>
        <div class="upload-constraints-inline">
          <span v-if="metadata?.allowed_types" class="constraint-inline">
            {{ getAllowedTypesText() }}
          </span>
          <span v-if="metadata?.allowed_types" class="constraint-separator">•</span>
          <span class="constraint-inline">
            Max {{ formatFileSize(metadata?.max_size || 10485760) }}
          </span>
          <span v-if="metadata?.max_files" class="constraint-separator">•</span>
          <span v-if="metadata?.max_files" class="constraint-inline">
            Up to {{ metadata.max_files }} files
          </span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="files.length === 0 && readonly" class="empty-state">
      No attachments
    </div>

    <!-- File count info -->
    <div v-if="files.length > 0" class="files-info">
      {{ files.length }} file{{ files.length !== 1 ? 's' : '' }}
      <span v-if="metadata?.max_files"> (max {{ metadata.max_files }})</span>
    </div>

    <!-- Loading overlay -->
    <div v-if="uploading" class="upload-overlay">
      <div class="spinner"></div>
      <span>Uploading {{ uploadProgress }}...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Plus, Download, X, FileText, File, FileImage, FileVideo, FileAudio, FileArchive, FileCode } from 'lucide-vue-next';
import api from '../../core/api';
import { useNotifications } from '../../composables/useNotifications';

const props = defineProps<{
  modelValue: any[];
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
const uploadProgress = ref('');
const files = ref<any[]>([]);

// Load existing attachments
watch(() => props.modelValue, async (newVal) => {
  if (newVal && Array.isArray(newVal) && newVal.length > 0) {
    // Check if we have IDs or full objects
    if (typeof newVal[0] === 'number') {
      // Load attachments by IDs
      try {
        const promises = newVal.map(id => api.get(`/models/ir.attachment/${id}`));
        const responses = await Promise.all(promises);
        files.value = responses.map(r => r.data);
      } catch (error) {
        console.error('Failed to load attachments:', error);
      }
    } else {
      files.value = newVal;
    }
  } else {
    files.value = [];
  }
}, { immediate: true, deep: true });

const acceptTypes = computed(() => {
  if (!props.metadata?.allowed_types) return '*/*';
  return props.metadata.allowed_types.map((t: string) => `.${t}`).join(',');
});

const canAddMore = computed(() => {
  if (!props.metadata?.max_files) return true;
  return files.value.length < props.metadata.max_files;
});

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const selectedFiles = Array.from(target.files || []);
  if (selectedFiles.length > 0) {
    uploadFiles(selectedFiles);
  }
};

const handleDrop = (event: DragEvent) => {
  isDragging.value = false;
  const droppedFiles = Array.from(event.dataTransfer?.files || []);
  if (droppedFiles.length > 0) {
    uploadFiles(droppedFiles);
  }
};

const uploadFiles = async (filesToUpload: File[]) => {
  // Check max files limit
  if (props.metadata?.max_files) {
    const remaining = props.metadata.max_files - files.value.length;
    if (filesToUpload.length > remaining) {
      add({
        type: 'warning',
        message: `Can only add ${remaining} more file(s). Maximum ${props.metadata.max_files} files allowed.`,
        duration: 5000
      });
      filesToUpload = filesToUpload.slice(0, remaining);
    }
  }

  uploading.value = true;
  const uploadedIds: number[] = [];

  for (let i = 0; i < filesToUpload.length; i++) {
    const file = filesToUpload[i];
    uploadProgress.value = `${i + 1}/${filesToUpload.length}`;

    // Validate file size
    if (props.metadata?.max_size && file.size > props.metadata.max_size) {
      add({
        type: 'danger',
        message: `${file.name}: File size exceeds maximum allowed size of ${formatFileSize(props.metadata.max_size)}`,
        duration: 5000
      });
      continue;
    }

    // Validate file type
    if (props.metadata?.allowed_types) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext && !props.metadata.allowed_types.includes(ext)) {
        add({
          type: 'danger',
          message: `${file.name}: File type .${ext} is not allowed`,
          duration: 5000
        });
        continue;
      }
    }

    try {
      // Read file as base64
      const base64 = await readFileAsBase64(file);

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
      files.value.push(response.data);
      uploadedIds.push(response.data.id);
    } catch (error: any) {
      add({
        type: 'danger',
        message: `${file.name}: ${error.response?.data?.detail || 'Upload failed'}`,
        duration: 5000
      });
    }
  }

  uploading.value = false;
  uploadProgress.value = '';

  if (uploadedIds.length > 0) {
    emit('update:modelValue', files.value.map(f => f.id));
    add({
      type: 'success',
      message: `${uploadedIds.length} file(s) uploaded successfully`,
      duration: 3000
    });
  }
};

const readFileAsBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = (e.target?.result as string).split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

const removeFile = async (file: any) => {
  try {
    await api.delete(`/models/ir.attachment/${file.id}`);
    files.value = files.value.filter(f => f.id !== file.id);
    emit('update:modelValue', files.value.map(f => f.id));

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

const downloadFile = (file: any) => {
  if (!file.datas) return;

  const link = document.createElement('a');
  link.href = `data:${file.mimetype};base64,${file.datas}`;
  link.download = file.name;
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
  if (!props.metadata?.allowed_types) return 'All types';
  return props.metadata.allowed_types.map((t: string) => `.${t}`).join(', ');
};
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.attachments-field-multiple {
  position: relative;
  width: 100%;
  
  &.is-invalid {
    .upload-zone-compact {
      border-color: v.$danger-color;
    }
  }
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  width: 100%;
}

.file-card-compact {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  transition: all 0.2s;
  
  &:hover {
    border-color: v.$primary-color;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  }
}

.file-icon-small {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: v.$bg-main;
  border-radius: 6px;
  color: v.$primary-color;
}

.file-info-compact {
  flex: 1;
  min-width: 0;
}

.file-name-compact {
  font-size: 0.8125rem;
  font-weight: 600;
  color: v.$text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size-compact {
  font-size: 0.6875rem;
  color: v.$text-secondary;
  margin-top: 0.125rem;
}

.file-actions-compact {
  display: flex;
  gap: 0.25rem;
}

.btn-icon-sm {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: v.$bg-main;
  border: 1px solid v.$border-color;
  border-radius: 4px;
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

.upload-zone-compact {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1.5rem;
  background: v.$bg-main;
  border: 2px dashed v.$border-color;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 0.75rem;
  width: 100%;
  
  &:hover, &.is-dragging {
    border-color: v.$primary-color;
    background: rgba(v.$primary-color, 0.02);
  }
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.file-input-hidden {
  display: none;
}

.upload-icon-sm {
  color: v.$text-secondary;
}

.upload-text-sm {
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
  margin-top: 0.25rem;
}

.constraint-inline {
  color: v.$text-secondary;
}

.constraint-separator {
  color: v.$text-disabled;
}

.empty-state {
  padding: 1rem;
  text-align: center;
  color: v.$text-secondary;
  font-size: 0.875rem;
  font-style: italic;
  border: 1px solid v.$border-color;
  border-radius: 6px;
  background: v.$bg-main;
}

.files-info {
  font-size: 0.75rem;
  color: v.$text-tertiary;
  margin-top: 0.5rem;
  text-align: center;
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
  border-radius: 6px;
  font-size: 0.875rem;
  color: v.$text-secondary;
  z-index: 10;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid v.$border-color;
  border-top: 3px solid v.$primary-color;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.is-readonly {
  .file-card-compact {
    background: v.$bg-main;
    
    &:hover {
      border-color: v.$border-color;
      box-shadow: none;
    }
  }
}

// Dark mode styles
[data-theme="dark"] {
  .file-card-compact {
    background: #0d1117;
    border-color: #30363d;
    
    &:hover {
      border-color: #58a6ff;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
  }
  
  .file-icon-small {
    background: #161b22;
    color: #58a6ff;
  }
  
  .file-name-compact {
    color: #e6edf3;
  }
  
  .file-size-compact {
    color: #7d8590;
  }
  
  .btn-icon-sm {
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
  
  .upload-zone-compact {
    background: #0d1117;
    border-color: #30363d;
    
    &:hover, &.is-dragging {
      border-color: #58a6ff;
      background: rgba(88, 166, 255, 0.05);
    }
  }
  
  .upload-icon-sm {
    color: #7d8590;
  }
  
  .upload-text-sm {
    color: #e6edf3;
  }
  
  .upload-constraints-inline,
  .constraint-inline {
    color: #7d8590;
  }
  
  .constraint-separator {
    color: #484f58;
  }
  
  .empty-state {
    background: #161b22;
    border-color: #30363d;
    color: #7d8590;
  }
  
  .files-info {
    color: #7d8590;
  }
  
  .upload-overlay {
    background: rgba(13, 17, 23, 0.95);
    color: #7d8590;
  }
  
  .spinner {
    border-color: #30363d;
    border-top-color: #58a6ff;
  }
  
  .is-readonly {
    .file-card-compact {
      background: #161b22;
      
      &:hover {
        border-color: #30363d;
      }
    }
  }
}
</style>
