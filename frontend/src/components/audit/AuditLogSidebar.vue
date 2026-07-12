<template>
  <!-- Backdrop overlay (when drawer is open) -->
  <div 
    v-if="isExpanded" 
    class="audit-backdrop" 
    @click="toggleDrawer"
  ></div>

  <!-- Collapsed Trigger (when drawer is closed) -->
  <Transition name="slide-trigger">
    <div v-if="!isExpanded" class="audit-trigger" @click="toggleDrawer">
      <div class="audit-trigger-inner">
        <div class="audit-trigger-top">
            <button class="audit-trigger-btn" @click="toggleDrawer" aria-label="Open Audit History">
              <div class="audit-trigger-icon">
                <span class="material-symbols-outlined">history</span>
              </div>
            </button>
        </div>
        
        <div class="audit-trigger-label">
          <span class="audit-trigger-text">AUDIT LOG</span>
        </div>

        <!-- Activity indicators -->
        <div class="audit-activity-dots">
          <!-- Activity dots (indicates many vs few changes) -->
          <div class="audit-dot" v-for="i in 3" :key="i" :class="{ 'audit-dot-active': i === 1 || logs.length > (i * 5) }"></div>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Expanded Drawer (slides in from right) -->
  <Transition name="drawer-slide">
    <aside v-if="isExpanded" class="audit-drawer">
      <!-- Sidebar Header - Clean Redesign -->
      <div class="audit-header">
        <div class="audit-header-content">
          <div class="audit-header-left">
            <span class="material-symbols-outlined audit-icon">history</span>
            <span class="audit-title">Audit History</span>
          </div>
          <div class="audit-header-actions">
            <button class="audit-export-btn" title="Export Logs" @click="exportLogs">
              <span class="material-symbols-outlined">download</span>
              <span>EXPORT</span>
            </button>
          </div>
        </div>
      </div>

    <!-- Loading State -->
    <div v-if="loading" class="audit-loading">
      <div class="audit-spinner"></div>
      <span>ACCESSING LOGS...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="!logs || logs.length === 0" class="audit-empty">
      <span class="material-symbols-outlined audit-empty-icon">history</span>
      <p>NO RECORDS FOUND</p>
    </div>

    <!-- Log List -->
    <div v-else class="audit-log-list cyber-scrollbar">
      <div class="audit-timeline">
        <!-- Timeline line -->
        <div class="audit-timeline-line"></div>

        <!-- Log entries -->
        <div 
          v-for="(log, index) in logs" 
          :key="log.id" 
          class="audit-log-entry"
          :class="{ 'audit-log-latest': index === 0 }"
        >
          <!-- Timeline dot -->
          <div class="audit-timeline-dot" :class="`audit-dot-${log.change_type}`"></div>

          <!-- Log content card -->
          <div class="audit-log-content">
            <!-- For grouped changes (multiple fields) -->
            <template v-if="log.changes_json">
              <!-- Title with Timestamp on the right -->
              <div class="audit-header-row">
                <div class="audit-field-title">Multiple Fields Updated</div>
                <div class="audit-timestamp-compact">
                  <div class="timestamp-date">{{ formatCompactDate(log.changed_at) }}</div>
                  <div class="timestamp-time">{{ formatCompactTime(log.changed_at) }}</div>
                </div>
              </div>
              
              <!-- Activity Line -->
              <div class="audit-activity-line">
                <span class="activity-action">{{ getActionLabel(log.change_type) }} by</span>
                <div class="audit-user-pill" v-if="log.user">
                  <div class="audit-user-mini-avatar">
                    <img v-if="log.user.image" :src="log.user.image" :alt="log.user.name" class="avatar-img" />
                    <img v-else-if="userStore.userData?.id === log.user.id && userStore.userData?.image" 
                         :src="userStore.userData.image" 
                         :alt="log.user.name" 
                         class="avatar-img" />
                    <template v-else>{{ getUserInitials(log.user) }}</template>
                  </div>
                  <span class="audit-user-name">{{ log.user.name || log.user.email }}</span>
                </div>
              </div>

              <!-- Multiple field changes -->
              <div class="audit-change-details">
                <div class="audit-change-card" v-for="(change, idx) in parseChangesJson(log.changes_json)" :key="idx">
                  <div class="grouped-field-label">{{ change.field_label }}</div>
                  <!-- For many2many fields (when old_value is empty and new_value starts with Added/Removed), show inline -->
                  <div v-if="!change.old_value && (change.new_value?.startsWith('Added:') || change.new_value?.startsWith('Removed:'))" class="change-value-inline">
                    {{ change.new_value || '—' }}
                  </div>
                  <!-- For regular fields with FROM and TO -->
                  <template v-else>
                    <div v-if="change.old_value" class="change-value-inline from-value">
                      <span class="inline-label">From:</span> {{ change.old_value }}
                    </div>
                    <div class="change-value-inline to-value">
                      <span class="inline-label">To:</span> {{ change.new_value || '—' }}
                    </div>
                  </template>
                </div>
              </div>
            </template>

            <!-- For single field changes (legacy format) -->
            <template v-else>
              <!-- Field Title with Timestamp on the right -->
              <div class="audit-header-row">
                <div class="audit-field-title">{{ log.field_label || log.field_name }}</div>
                <div class="audit-timestamp-compact">
                  <div class="timestamp-date">{{ formatCompactDate(log.changed_at) }}</div>
                  <div class="timestamp-time">{{ formatCompactTime(log.changed_at) }}</div>
                </div>
              </div>

              <!-- Activity Line -->
              <div class="audit-activity-line">
                <span class="activity-action">{{ getActionLabel(log.change_type) }} by</span>
                <div class="audit-user-pill" v-if="log.user">
                  <div class="audit-user-mini-avatar">
                    <!-- Try log user image, fallback to current user image if IDs match, else initials -->
                    <img v-if="log.user.image" :src="log.user.image" :alt="log.user.name" class="avatar-img" />
                    <img v-else-if="userStore.userData?.id === log.user.id && userStore.userData?.image" 
                         :src="userStore.userData.image" 
                         :alt="log.user.name" 
                         class="avatar-img" />
                    <template v-else>{{ getUserInitials(log.user) }}</template>
                  </div>
                  <span class="audit-user-name">{{ log.user.name || log.user.email }}</span>
                </div>
              </div>

              <!-- Change Detail Card -->
              <div class="audit-change-details" v-if="log.change_type === 'write' || log.change_type === 'create'">
                <div class="audit-change-card">
                  <!-- For many2many fields (when old_value is empty and new_value starts with Added/Removed), show inline -->
                  <div v-if="!log.old_value && (log.new_value?.startsWith('Added:') || log.new_value?.startsWith('Removed:'))" class="change-value-inline">
                    {{ log.new_value || (log.change_type === 'create' ? 'INITIALIZED' : '—') }}
                  </div>
                  <!-- For regular fields with FROM and TO -->
                  <template v-else>
                    <div v-if="log.change_type === 'write' && log.old_value" class="change-value-inline from-value">
                      <span class="inline-label">From:</span> {{ log.old_value }}
                    </div>
                    <div class="change-value-inline to-value">
                      <span class="inline-label">To:</span> {{ log.new_value || (log.change_type === 'create' ? 'INITIALIZED' : '—') }}
                    </div>
                  </template>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer removed as export moved to header -->
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useResponsive } from '@/composables/useResponsive';
import { useUserStore } from '@/stores/userStore';
import api from '../../core/api';

interface AuditLog {
  id: number;
  field_name: string;
  field_label: string;
  old_value: string;
  new_value: string;
  change_type: 'create' | 'write' | 'delete';
  changed_at: string;
  user: {
    id: number;
    name?: string;
    email?: string;
    image?: string;
  } | null;
  changes_json?: string; // JSON string containing multiple field changes
}

interface FieldChange {
  field_name: string;
  field_label: string;
  field_type: string;
  old_value: string;
  new_value: string;
}

interface Props {
  modelName: string;
  recordId: number | null;
  visible?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  visible: true
});

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const { isMobile } = useResponsive();

const logs = ref<AuditLog[]>([]);
const loading = ref(false);
const isExpanded = ref(false);
const userStore = useUserStore();

// Toggle drawer open/close
const toggleDrawer = () => {
  isExpanded.value = !isExpanded.value;
};

// Fetch audit logs
const fetchLogs = async () => {
  if (!props.recordId) {
    logs.value = [];
    return;
  }

  loading.value = true;
  try {
    const response = await api.get(`/models/${props.modelName}/${props.recordId}/audit-logs`);
    logs.value = response.data;
  } catch (error) {
    console.error('Failed to fetch audit logs:', error);
    logs.value = [];
  } finally {
    loading.value = false;
  }
};

// Watch for changes in recordId
watch(() => props.recordId, () => {
  fetchLogs();
}, { immediate: true });

// Format time relative to now
const formatTime = (timestamp: string): string => {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'JUST NOW';
  if (diffMins < 60) return `${diffMins}M AGO`;
  if (diffHours < 24) return `${diffHours}H AGO`;
  if (diffDays < 7) return `${diffDays}D AGO`;
  
  return date.toLocaleDateString();
};

const formatAbsoluteTimestamp = (timestamp: string): string => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  
  const options: Intl.DateTimeFormatOptions = { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric' 
  };
  const datePart = date.toLocaleDateString('en-GB', options);
  
  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  };
  const timePart = date.toLocaleTimeString('en-US', timeOptions).toUpperCase();
  
  return `${datePart} • ${timePart}`;
};

// Format compact date (e.g., "21 Jan")
const formatCompactDate = (timestamp: string): string => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  
  const options: Intl.DateTimeFormatOptions = { 
    day: 'numeric', 
    month: 'short'
  };
  return date.toLocaleDateString('en-GB', options);
};

// Format compact time (e.g., "08:00 PM")
const formatCompactTime = (timestamp: string): string => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  
  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  };
  return date.toLocaleTimeString('en-US', timeOptions).toUpperCase();
};

const getActionLabel = (type: string): string => {
  switch (type) {
    case 'create': return 'Created';
    case 'delete': return 'Deleted';
    default: return 'Updated';
  }
};

// Parse changes JSON for grouped changes
const parseChangesJson = (changesJson: string): FieldChange[] => {
  try {
    return JSON.parse(changesJson);
  } catch (e) {
    console.error('Failed to parse changes JSON:', e);
    return [];
  }
};

// Get user initials
const getUserInitials = (user: AuditLog['user']): string => {
  if (!user) return 'SY';
  
  if (user.name) {
    const parts = user.name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return user.name.substring(0, 2).toUpperCase();
  }
  
  if (user.email) {
    return user.email.substring(0, 2).toUpperCase();
  }
  
  return 'U';
};

// Export logs as JSON
const exportLogs = () => {
  const dataStr = JSON.stringify(logs.value, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `audit-log-${props.modelName}-${props.recordId}.json`;
  link.click();
  URL.revokeObjectURL(url);
};

// Expose refresh method and toggle
defineExpose({
  refresh: fetchLogs,
  toggle: toggleDrawer,
  expand: () => { isExpanded.value = true; },
  collapse: () => { isExpanded.value = false; }
});
</script>

<style scoped lang="scss">
// Cyber Scrollbar
.cyber-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.cyber-scrollbar::-webkit-scrollbar-track {
  background: var(--surface-color);
}
.cyber-scrollbar::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}
.cyber-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--primary-color);
}

// Backdrop overlay
.audit-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 999;
  animation: fadeIn 0.3s ease;
  backdrop-filter: blur(3px);
  cursor: pointer;
}

@keyframes fadeIn {
  from { opacity: 0; backdrop-filter: blur(0px); }
  to { opacity: 1; backdrop-filter: blur(3px); }
}

// Collapsed trigger styles
.audit-trigger {
  position: fixed;
  right: 0;
  top: 50%;
  width: 52px;
  min-height: 280px;
  background: var(--surface-color);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid var(--border-color);
  border-right: none;
  border-radius: 16px 0 0 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 999;
  cursor: pointer;
  box-shadow: var(--shadow-lg);
  
  // INITIAL STATE: Mostly hidden (only the neon edge is visible)
  transform: translateY(-50%) translateX(42px);
  transition: transform 0.8s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.8s ease,
              background-color 0.3s ease,
              border-color 0.3s ease,
              box-shadow 0.3s ease;
  will-change: transform, opacity;
  
  // Left glowing neon edge
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 2px;
    height: 40px;
    background: var(--primary-color);
    border-radius: 0 4px 4px 0;
    box-shadow: 0 0 15px var(--primary-color), 0 0 5px var(--primary-color);
    opacity: 0.6;
    transition: height 0.4s ease, opacity 0.4s ease, width 0.3s ease;
  }

  &:hover {
    transform: translateY(-50%) translateX(0);
    background: var(--surface-highlight);
    border-color: var(--primary-color-alpha);
    box-shadow: var(--shadow-xl);
    
    &::before {
      height: 160px; /* Increased to match the text length */
      width: 4px;
      opacity: 1;
    }

    .audit-trigger-inner {
      opacity: 1;
      transform: translateX(0);
    }
  }
}

.audit-trigger-inner {
  display: grid;
  grid-template-rows: 1fr auto 1fr;
  align-items: center;
  justify-items: center;
  width: 100%;
  height: 280px; 
  opacity: 0;
  transform: translateX(10px);
  transition: opacity 0.4s ease 0.1s, transform 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.1s;
}

.audit-trigger-top {
  grid-row: 1;
  align-self: start;
  padding-top: 24px;
}

.audit-trigger-btn {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
  
  .material-symbols-outlined {
    font-size: 18px;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

.audit-trigger-label {
  grid-row: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.audit-trigger-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  letter-spacing: 0.5em; /* Increased spacing for better look */
  color: var(--text-muted);
  opacity: 0.5;
  user-select: none;
  white-space: nowrap;
  transition: all 0.3s ease;
}

.audit-activity-dots {
  grid-row: 3;
  align-self: end;
  padding-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.audit-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-disabled);
  opacity: 0.6;
  transition: all 0.3s ease;
  
  &.audit-dot-active {
    background: var(--primary-color);
    opacity: 1;
    box-shadow: 0 0 8px var(--primary-color);
  }
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 1; }
}

.slide-trigger-enter-active,
.slide-trigger-leave-active {
  /* Transitions defined on base class */
}

.slide-trigger-enter-from,
.slide-trigger-leave-to {
  transform: translateY(-50%) translateX(100%) !important;
  opacity: 0;
}

// Drawer transition
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  /* Transitions defined on base class */
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(100%) !important;
  opacity: 0;
}

// Expanded drawer styles
.audit-drawer {
  position: fixed;
  right: 0;
  top: 64px; /* Start below the top navbar */
  bottom: 0;
  width: 400px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  border-top: 1px solid var(--border-color); /* Add back top border now that it's not flush */
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  transition: transform 0.7s cubic-bezier(0.16, 1, 0.3, 1), 
              opacity 0.7s ease,
              background-color 0.3s ease, 
              border-color 0.3s ease, 
              box-shadow 0.3s ease;
  will-change: transform, opacity;
}

.audit-header {
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
}

.audit-header-content {
  height: 64px; /* Standard height */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.audit-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.audit-icon {
  font-size: 20px;
  color: var(--primary-color);
}

.audit-title {
  font-size: 15px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.audit-export-btn {
  background: var(--primary-color);
  border: 1px solid var(--primary-color);
  color: white !important;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  
  .material-symbols-outlined {
    font-size: 18px;
  }
  
  &:hover {
    filter: brightness(1.05);
    box-shadow: 0 4px 12px var(--primary-color-alpha);
    transform: translateY(-1px);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.audit-loading,
.audit-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.1em;
  font-size: 12px;
}

.audit-spinner {
  width: 40px;
  height: 40px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.audit-log-list {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-main);
  transition: background-color 0.3s ease;
}

.audit-timeline {
  position: relative;
  padding: 16px 16px;
}

@keyframes timeline-pulse {
  0% { opacity: 0.3; }
  50% { opacity: 0.6; box-shadow: 0 0 10px var(--primary-color-alpha); }
  100% { opacity: 0.3; }
}

.audit-timeline-line {
  position: absolute;
  left: 20px; /* Adjusted to align with 10px dot center (16px padding + 5px to center) */
  top: 16px;
  bottom: 16px;
  width: 2px;
  background: var(--primary-color);
  opacity: 0.3;
  box-shadow: 0 0 8px var(--primary-color-alpha);
  animation: timeline-pulse 4s infinite ease-in-out;
}

.audit-log-entry {
  position: relative;
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  
  &:hover {
    .audit-log-content {
      transform: translateX(4px);
      background: var(--surface-highlight);
      border-color: var(--primary-color-alpha);
      box-shadow: var(--shadow-md);
    }
    
    .audit-timeline-dot {
      border-color: var(--primary-color);
      box-shadow: 0 0 12px var(--primary-color);
      transform: scale(1.15);
    }
  }
}

.audit-timeline-dot {
  position: relative;
  z-index: 10;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 2px;
  flex-shrink: 0;
  background: var(--surface-color);
  border: 2px solid var(--border-color);
  transition: all 0.3s ease;
  
  &.audit-dot-create { border-color: var(--primary-color); background: var(--primary-color); box-shadow: 0 0 8px var(--primary-color-alpha); }
  &.audit-dot-write { border-color: var(--primary-color); }
  &.audit-dot-delete { border-color: var(--danger-color); background: var(--danger-color); }
}

.audit-log-latest .audit-timeline-dot {
  border-color: var(--primary-color);
  background: var(--primary-color);
  box-shadow: 0 0 15px var(--primary-color);
}

.audit-log-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: var(--shadow-sm);
}

.audit-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.audit-field-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  line-height: 1.2;
  flex: 1;
}

.audit-timestamp-compact {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
  flex-shrink: 0;
}

.timestamp-date {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  opacity: 0.7;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.02em;
  line-height: 1.1;
}

.timestamp-time {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  opacity: 0.7;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.02em;
  line-height: 1.1;
}

.grouped-field-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: 'JetBrains Mono', monospace;
}

.audit-activity-line {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.activity-action {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.audit-user-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--bg-tertiary);
  padding: 2px 7px 2px 3px;
  border-radius: 100px;
  border: 1px solid var(--border-color);
}

.audit-user-mini-avatar {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 7px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;

  .avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.audit-user-name {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-primary);
}

.audit-change-details {
  margin-top: 2px;
}

.audit-change-card {
  padding: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* Add spacing between multiple change cards in grouped changes */
.audit-change-details .audit-change-card + .audit-change-card {
  margin-top: 6px;
}

.change-value-inline {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.4;
  white-space: pre-line;
  color: var(--text-primary);
  
  .inline-label {
    font-weight: 700;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.6;
  }
}

.change-value-inline.from-value {
  color: var(--text-muted);
  text-decoration: line-through;
  opacity: 0.7;
  
  .inline-label {
    color: var(--text-muted);
  }
}

.change-value-inline.to-value {
  color: var(--primary-color);
  font-weight: 600;
  
  .inline-label {
    color: var(--primary-color);
    opacity: 1; /* Make it fully visible, same as the value */
  }
  
  [data-theme="dark"] & {
    text-shadow: 0 0 20px var(--primary-color-alpha);
  }
}

.audit-footer {
  border-top: 1px solid var(--border-color);
  padding: 20px;
  background: var(--surface-color);
}

</style>
