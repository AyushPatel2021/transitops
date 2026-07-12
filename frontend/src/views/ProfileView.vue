<template>
  <div class="profile-view">
    <div class="profile-container">
      <!-- Profile Header Card -->
      <div class="profile-header-card">
        <div class="profile-header-content">
          <div class="profile-avatar-section">
            <div class="profile-avatar-container">
              <div class="profile-avatar">
                <img v-if="profileData?.image" :src="profileData.image" alt="Profile" class="avatar-image" />
                <div v-else class="avatar-placeholder">
                  {{ getInitials(profileData?.full_name) }}
                </div>
              </div>
              <!-- Avatar Edit Button Badge -->
              <button 
                type="button" 
                @click="imageInput?.click()" 
                class="avatar-edit-badge"
                title="Edit Profile Picture"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                </svg>
              </button>
              <input
                type="file"
                ref="imageInput"
                @change="handleImageUpload"
                accept="image/*"
                class="image-input"
              />
            </div>
            
            <div class="profile-header-info">
              <h1 class="profile-name">{{ profileData?.full_name || 'Loading...' }}</h1>
              <p class="profile-subtitle">{{ profileData?.role?.name || 'No Role' }}</p>
            </div>
          </div>
          
          <div class="profile-header-actions">
            <button class="btn btn-primary btn-icon" @click="activeTab = 'info'">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Edit Profile
            </button>
          </div>
        </div>
        
        <!-- Tabs -->
        <div class="profile-tabs">
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'overview' }" 
            @click="activeTab = 'overview'"
          >
            Profile Overview
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'info' }" 
            @click="activeTab = 'info'"
          >
            Personal Info
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'security' }" 
            @click="activeTab = 'security'"
          >
            Security
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'preferences' }" 
            @click="activeTab = 'preferences'"
          >
            Preferences
          </button>
        </div>
      </div>

      <!-- Profile Overview Tab -->
      <div v-if="activeTab === 'overview'" class="tab-content-wrapper">
        <div class="content-grid">
          <!-- Personal Information Card -->
          <div class="info-card">
            <div class="card-header">
              <h3 class="card-title">Personal Information</h3>
              <p class="card-subtitle">Update your personal details and public profile info.</p>
            </div>
            <div class="card-content">
              <div class="info-row">
                <span class="info-label">Full Name</span>
                <span class="info-value">{{ profileData?.full_name || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Email Address</span>
                <span class="info-value">{{ profileData?.email || '—' }}</span>
              </div>
            </div>
          </div>

          <!-- Account Details Card -->
          <div class="info-card">
            <div class="card-header">
              <h3 class="card-title">Account Details</h3>
            </div>
            <div class="card-content">
              <div class="info-row">
                <span class="info-label">Role</span>
                <span class="info-value-badge badge-primary">{{ profileData?.role?.name || 'No Role' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Status</span>
                <span class="info-value-badge" :class="profileData?.is_active ? 'badge-success' : 'badge-danger'">
                  {{ profileData?.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <div class="info-row" v-if="profileData?.last_login_at">
                <span class="info-label">Last Login</span>
                <div class="info-value-group">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="info-icon">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                  <span class="info-value">{{ formatDate(profileData.last_login_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Personal Info Tab -->
      <div v-if="activeTab === 'info'" class="tab-content-wrapper">
        <div class="info-card">
          <div class="card-header">
            <h3 class="card-title">Personal Information</h3>
            <p class="card-subtitle">Update your personal details and public profile info.</p>
          </div>
          <form @submit.prevent="updateProfile" class="card-content">
            <div class="form-row">
              <div class="form-group">
                <label for="full_name">Full Name</label>
                <input
                  id="full_name"
                  v-model="profileForm.full_name"
                  type="text"
                  class="form-input"
                  placeholder="Enter your full name"
                  required
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="email">Email Address</label>
                <div class="input-with-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="input-icon">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                  <input
                    id="email"
                    :value="profileData?.email"
                    type="email"
                    class="form-input with-icon"
                    readonly
                    disabled
                  />
                </div>
                <small class="form-help">Email address is managed by administrators</small>
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="profileLoading">
                {{ profileLoading ? 'Updating...' : 'Save Changes' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Security Tab -->
      <div v-if="activeTab === 'security'" class="tab-content-wrapper">
        <div class="info-card">
          <div class="card-header-with-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <div>
              <h3 class="card-title">Password Change</h3>
              <p class="card-subtitle">Ensure your account is using a long, random password to stay secure.</p>
            </div>
          </div>
          
          <form @submit.prevent="changePassword" class="card-content">
            <div class="form-group">
              <label for="current_password">Current Password</label>
              <input
                id="current_password"
                v-model="passwordForm.current_password"
                type="password"
                class="form-input"
                placeholder="••••••••"
                required
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="new_password">New Password</label>
                <input
                  id="new_password"
                  v-model="passwordForm.new_password"
                  type="password"
                  class="form-input"
                  :class="{ 
                    'input-error': passwordForm.new_password && !isPasswordValid,
                    'input-success': passwordForm.new_password && isPasswordValid
                  }"
                  placeholder="••••••••"
                  required
                  @input="validatePassword"
                />
              </div>

              <div class="form-group">
                <label for="confirm_password">Confirm New Password</label>
                <input
                  id="confirm_password"
                  v-model="passwordForm.confirm_password"
                  type="password"
                  class="form-input"
                  :class="{ 
                    'input-error': passwordForm.confirm_password && !passwordsMatch,
                    'input-success': passwordForm.confirm_password && passwordsMatch && isPasswordValid
                  }"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div class="password-hint" v-if="passwordForm.new_password || passwordForm.confirm_password">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              <span>Must be at least 8 characters containing letters and numbers.</span>
            </div>

            <div class="form-actions">
              <button 
                type="submit" 
                class="btn btn-primary" 
                :disabled="passwordLoading || !canSubmitPassword"
              >
                {{ passwordLoading ? 'Updating...' : 'Update Password' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Preferences Tab -->
      <div v-if="activeTab === 'preferences'" class="tab-content-wrapper">
        <div class="info-card">
          <div class="card-header-with-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"/>
            </svg>
            <div>
              <h3 class="card-title">Preferences</h3>
              <p class="card-subtitle">Customize how the application looks and behaves.</p>
            </div>
          </div>
          
          <form @submit.prevent="updatePreferences" class="card-content">
            <div class="preference-item">
              <div class="preference-info">
                <h4 class="preference-title">Notification Toasts</h4>
                <p class="preference-description">Receive pop-up alerts for important updates while you work.</p>
              </div>
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  v-model="preferencesForm.show_notification_toasts"
                  class="toggle-input"
                />
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="preference-section">
              <h4 class="preference-section-title">Theme</h4>
              <p class="preference-section-description">Select your preferred interface appearance.</p>
              
              <div class="theme-options">
                <label class="theme-card" :class="{ active: preferencesForm.theme === 'light' }">
                  <input
                    type="radio"
                    name="theme"
                    value="light"
                    v-model="preferencesForm.theme"
                    class="theme-radio"
                  />
                  <div class="theme-card-content">
                    <div class="theme-preview light-preview">
                      <div class="preview-header">
                        <div class="preview-dot"></div>
                        <div class="preview-dot"></div>
                        <div class="preview-dot"></div>
                      </div>
                      <div class="preview-body">
                        <div class="preview-sidebar">
                          <div class="preview-menu-item"></div>
                          <div class="preview-menu-item"></div>
                          <div class="preview-menu-item active"></div>
                        </div>
                        <div class="preview-content">
                          <div class="preview-line"></div>
                          <div class="preview-line short"></div>
                          <div class="preview-line"></div>
                        </div>
                      </div>
                    </div>
                    <div class="theme-info">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="theme-icon">
                        <circle cx="12" cy="12" r="5"/>
                        <line x1="12" y1="1" x2="12" y2="3"/>
                        <line x1="12" y1="21" x2="12" y2="23"/>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                        <line x1="1" y1="12" x2="3" y2="12"/>
                        <line x1="21" y1="12" x2="23" y2="12"/>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                      </svg>
                      <div class="theme-text">
                        <span class="theme-label">Light Mode</span>
                        <span class="theme-description">Clean and bright interface</span>
                      </div>
                    </div>
                    <svg v-if="preferencesForm.theme === 'light'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="theme-check">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                </label>
                
                <label class="theme-card" :class="{ active: preferencesForm.theme === 'dark' }">
                  <input
                    type="radio"
                    name="theme"
                    value="dark"
                    v-model="preferencesForm.theme"
                    class="theme-radio"
                  />
                  <div class="theme-card-content">
                    <div class="theme-preview dark-preview">
                      <div class="preview-header">
                        <div class="preview-dot"></div>
                        <div class="preview-dot"></div>
                        <div class="preview-dot"></div>
                      </div>
                      <div class="preview-body">
                        <div class="preview-sidebar">
                          <div class="preview-menu-item"></div>
                          <div class="preview-menu-item"></div>
                          <div class="preview-menu-item active"></div>
                        </div>
                        <div class="preview-content">
                          <div class="preview-line"></div>
                          <div class="preview-line short"></div>
                          <div class="preview-line"></div>
                        </div>
                      </div>
                    </div>
                    <div class="theme-info">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="theme-icon">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                      </svg>
                      <div class="theme-text">
                        <span class="theme-label">Dark Mode</span>
                        <span class="theme-description">Easy on the eyes</span>
                      </div>
                    </div>
                    <svg v-if="preferencesForm.theme === 'dark'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="theme-check">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                </label>
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="preferencesLoading">
                {{ preferencesLoading ? 'Updating...' : 'Save Preferences' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import api from '../core/api';
import { useAuth } from '../core/useAuth';
import { useNotifications } from '../composables/useNotifications';
import { formatDateTime } from '../utils/dateUtils';
import { useBreadcrumbs } from '../composables/useBreadcrumbs';

// State
const activeTab = ref('overview');
const profileData = ref<any>(null);
const profileLoading = ref(false);
const passwordLoading = ref(false);
const preferencesLoading = ref(false);
const imageInput = ref<HTMLInputElement | null>(null);

// Auth composable
const { refreshUser, user } = useAuth();

// Notifications composable
const { add: addNotification } = useNotifications();

// Breadcrumbs composable - clear trail on profile page
const { reset: resetBreadcrumbs } = useBreadcrumbs();

// Forms
const profileForm = reactive({
  full_name: ''
});

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
});

const preferencesForm = reactive({
  show_notification_toasts: true,
  theme: 'light'
});

// Password validation state
const passwordValidation = reactive({
  length: false,
  hasLetter: false,
  hasNumber: false
});

// Computed properties for validation
const isPasswordValid = computed(() => {
  return passwordValidation.length && 
         passwordValidation.hasLetter && 
         passwordValidation.hasNumber;
});

const passwordsMatch = computed(() => {
  return passwordForm.new_password === passwordForm.confirm_password;
});

const canSubmitPassword = computed(() => {
  return passwordForm.current_password && 
         isPasswordValid.value && 
         passwordsMatch.value;
});

// Password validation function
const validatePassword = () => {
  const password = passwordForm.new_password;
  
  passwordValidation.length = password.length >= 8;
  passwordValidation.hasLetter = /[A-Za-z]/.test(password);
  passwordValidation.hasNumber = /\d/.test(password);
};

// Methods
const loadProfile = async () => {
  try {
    const response = await api.get('/profile');
    profileData.value = response.data.data;
    
    // Populate form
    profileForm.full_name = profileData.value.full_name;
    
    // Populate preferences form
    if (profileData.value.preferences) {
      preferencesForm.show_notification_toasts = profileData.value.preferences.show_notification_toasts ?? true;
      preferencesForm.theme = profileData.value.preferences.theme ?? 'light';
    }
  } catch (error: any) {
    addNotification({
      title: 'Error',
      message: 'Failed to load profile information',
      type: 'danger',
      sticky: false
    });
  }
};

const updateProfile = async () => {
  profileLoading.value = true;
  try {
    await api.put('/profile', profileForm);
    await loadProfile(); // Reload profile data
    await refreshUser(); // Update sidebar user data
    
    addNotification({
      title: 'Success',
      message: 'Profile updated successfully! 🎉',
      type: 'success',
      sticky: false
    });
  } catch (error: any) {
    addNotification({
      title: 'Error',
      message: error.response?.data?.detail || 'Failed to update profile',
      type: 'danger',
      sticky: false
    });
  } finally {
    profileLoading.value = false;
  }
};

const updatePreferences = async () => {
  preferencesLoading.value = true;
  try {
    await api.put('/profile', {
      preferences: {
        show_notification_toasts: preferencesForm.show_notification_toasts,
        theme: preferencesForm.theme
      }
    });
    await loadProfile(); // Reload profile data
    await refreshUser(); // Update sidebar user data
    
    addNotification({
      title: 'Success',
      message: 'Preferences updated successfully! ⚙️',
      type: 'success',
      sticky: false
    });
  } catch (error: any) {
    addNotification({
      title: 'Error',
      message: error.response?.data?.detail || 'Failed to update preferences',
      type: 'danger',
      sticky: false
    });
  } finally {
    preferencesLoading.value = false;
  }
};

const changePassword = async () => {
  // Frontend validation
  if (!isPasswordValid.value) {
    addNotification({
      title: 'Validation Error',
      message: 'Please ensure your new password meets all requirements',
      type: 'warning',
      sticky: false
    });
    return;
  }

  if (!passwordsMatch.value) {
    addNotification({
      title: 'Validation Error',
      message: 'Passwords do not match',
      type: 'warning',
      sticky: false
    });
    return;
  }

  passwordLoading.value = true;
  try {
    await api.put('/profile/password', passwordForm);
    
    // Clear form
    passwordForm.current_password = '';
    passwordForm.new_password = '';
    passwordForm.confirm_password = '';
    
    // Reset validation state
    passwordValidation.length = false;
    passwordValidation.hasLetter = false;
    passwordValidation.hasNumber = false;
    
    addNotification({
      title: 'Success',
      message: 'Password changed successfully! 🔒',
      type: 'success',
      sticky: false
    });
  } catch (error: any) {
    addNotification({
      title: 'Error',
      message: error.response?.data?.detail || 'Failed to change password',
      type: 'danger',
      sticky: false
    });
  } finally {
    passwordLoading.value = false;
  }
};

const handleImageUpload = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  // Validate file size (2MB max)
  if (file.size > 2 * 1024 * 1024) {
    addNotification({
      title: 'File Size Error',
      message: 'Image size must be less than 2MB',
      type: 'warning',
      sticky: false
    });
    return;
  }

  // Convert to base64
  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const imageData = e.target?.result as string;
      await api.put('/profile/image', { image: imageData });
      await loadProfile(); // Reload to get updated image
      await refreshUser(); // Update sidebar user data
      
      addNotification({
        title: 'Success',
        message: 'Profile image updated successfully! 📸',
        type: 'success',
        sticky: false
      });
    } catch (error: any) {
      addNotification({
        title: 'Error',
        message: 'Failed to update profile image',
        type: 'danger',
        sticky: false
      });
    }
  };
  reader.readAsDataURL(file);
};

const removeImage = async () => {
  try {
    await api.put('/profile/image', { image: null });
    await loadProfile();
    await refreshUser(); // Update sidebar user data
    
    addNotification({
      title: 'Success',
      message: 'Profile image removed successfully! 🗑️',
      type: 'success',
      sticky: false
    });
  } catch (error: any) {
    addNotification({
      title: 'Error',
      message: 'Failed to remove profile image',
      type: 'danger',
      sticky: false
    });
  }
};

const getInitials = (name: string) => {
  if (!name) return '?';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
};

const formatDate = (dateString: string) => {
  try {
    return formatDateTime(dateString);
  } catch {
    return dateString;
  }
};

// Initialize
onMounted(() => {
  // Clear breadcrumb trail when entering profile page
  resetBreadcrumbs();
  loadProfile();
});
</script>

<style lang="scss" scoped>
@use '../styles/variables' as v;

.profile-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: v.$bg-main;
  padding: 2rem;
  overflow-y: auto;
  overflow-x: hidden;
}

.profile-container {
  flex: 0 0 auto;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

// Profile Header Card
.profile-header-card {
  background: v.$white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.profile-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem;
  border-bottom: 1px solid v.$border-light;
}

.profile-avatar-section {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.profile-avatar-container {
  position: relative;
  flex-shrink: 0;
}

.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid v.$border-light;
  background: v.$bg-main;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  font-weight: 600;
  color: v.$text-secondary;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: v.$white;
}

.avatar-edit-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: v.$primary-color;
  color: v.$white;
  border: 3px solid v.$white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: v.$primary-hover;
    transform: scale(1.05);
  }
}

.image-input {
  display: none;
}

.profile-header-info {
  flex: 1;
  min-width: 0;
}

.profile-name {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: v.$text-primary;
  line-height: 1.3;
}

.profile-subtitle {
  margin: 0;
  font-size: 0.9rem;
  color: v.$text-secondary;
}

.profile-header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-primary {
  background: v.$primary-color;
  color: v.$white;

  &:hover:not(:disabled) {
    background: v.$primary-hover;
  }
}

.btn-secondary {
  background: v.$white;
  color: v.$text-primary;
  border: 1.5px solid v.$border-color;

  &:hover:not(:disabled) {
    background: v.$bg-main;
    border-color: v.$text-secondary;
  }
}

.btn-icon {
  svg {
    width: 16px;
    height: 16px;
  }
}

// Tabs
.profile-tabs {
  display: flex;
  padding: 0 2rem;
  gap: 0.5rem;
  background: v.$white;
  border-top: 1px solid v.$border-light;
}

.tab-button {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  color: v.$text-secondary;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  position: relative;

  &:hover {
    color: v.$text-primary;
  }

  &.active {
    color: v.$primary-color;
    border-bottom-color: v.$primary-color;
  }
}

// Tab Content
.tab-content-wrapper {
  padding: 0;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

// Info Cards
.info-card {
  background: v.$white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid v.$border-light;
}

.card-header-with-icon {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid v.$border-light;
}

.card-icon {
  color: v.$primary-color;
  flex-shrink: 0;
}

.card-title {
  margin: 0 0 0.125rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: v.$text-primary;
}

.card-subtitle {
  margin: 0;
  font-size: 0.8rem;
  color: v.$text-secondary;
  line-height: 1.4;
}

.card-content {
  padding: 1.25rem 1.5rem;
}

// Info Rows
.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 0;
  border-bottom: 1px solid v.$border-light;

  &:last-child {
    border-bottom: none;
  }
}

.info-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: v.$text-secondary;
}

.info-value {
  font-size: 0.875rem;
  color: v.$text-primary;
  font-weight: 500;
}

.info-value-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-icon {
  color: v.$text-secondary;
}

.info-value-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  
  &.badge-primary {
    background: rgba(99, 102, 241, 0.1);
    color: v.$primary-color;
  }
  
  &.badge-success {
    background: v.$light-green-bg;
    color: v.$green-text-dark;
  }
  
  &.badge-danger {
    background: v.$error-bg;
    color: v.$error-text;
  }
}

// Forms
.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: v.$text-primary;
  font-size: 0.875rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1.5px solid v.$border-color;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
  background: v.$white;
  color: v.$text-primary;

  &:focus {
    outline: none;
    border-color: v.$primary-color;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }

  &:disabled {
    background: v.$bg-main;
    color: v.$text-disabled;
    cursor: not-allowed;
  }

  &.input-error {
    border-color: v.$red-500;
  }

  &.input-success {
    border-color: v.$green-500;
  }
  
  &.with-icon {
    padding-left: 2.75rem;
  }
}

.input-with-icon {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: v.$text-secondary;
  pointer-events: none;
}

.form-help {
  display: block;
  margin-top: 0.375rem;
  font-size: 0.8rem;
  color: v.$text-secondary;
}

.password-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(99, 102, 241, 0.05);
  border-radius: 8px;
  font-size: 0.8rem;
  color: v.$text-secondary;
  margin-top: 1rem;
  
  svg {
    color: v.$primary-color;
    flex-shrink: 0;
  }
}

.form-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid v.$border-light;
}

// Preferences
.preference-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 0;
  border-bottom: 1px solid v.$border-light;

  &:last-child {
    border-bottom: none;
  }
}

.preference-info {
  flex: 1;
  padding-right: 1rem;
}

.preference-title {
  margin: 0 0 0.125rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
}

.preference-description {
  margin: 0;
  font-size: 0.75rem;
  color: v.$text-secondary;
  line-height: 1.3;
}

.preference-section {
  margin-top: 1rem;
  padding-top: 1rem;
}

.preference-section-title {
  margin: 0 0 0.125rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
}

.preference-section-description {
  margin: 0 0 0.75rem 0;
  font-size: 0.75rem;
  color: v.$text-secondary;
}

// Toggle Switch
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 26px;
  flex-shrink: 0;
}

.toggle-input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: v.$border-color;
  transition: 0.3s;
  border-radius: 26px;

  &:before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 3px;
    bottom: 3px;
    background-color: v.$white;
    transition: 0.3s;
    border-radius: 50%;
  }
}

.toggle-input:checked + .toggle-slider {
  background-color: v.$primary-color;
}

.toggle-input:checked + .toggle-slider:before {
  transform: translateX(22px);
}

// Theme Cards
.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.theme-card {
  cursor: pointer;
  border: 2px solid v.$border-color;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: v.$white;
  overflow: hidden;
  position: relative;
  
  &:hover {
    border-color: v.$primary-color;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    transform: translateY(-2px);
  }
  
  &.active {
    border-color: v.$primary-color;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
    background: rgba(99, 102, 241, 0.02);
  }
}

.theme-radio {
  display: none;
}

.theme-card-content {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 0.75rem;
  position: relative;
}

.theme-preview {
  width: 100%;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid v.$border-light;
  
  &.light-preview {
    background: #f8f9fa;
    
    .preview-header {
      height: 24px;
      background: v.$white;
      border-bottom: 1px solid v.$border-light;
      display: flex;
      align-items: center;
      padding: 0 0.75rem;
      gap: 0.375rem;
      
      .preview-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: v.$border-color;
      }
    }
    
    .preview-body {
      display: flex;
      height: calc(100% - 24px);
      
      .preview-sidebar {
        width: 50px;
        background: #2d3748;
        padding: 0.5rem 0.375rem;
        display: flex;
        flex-direction: column;
        gap: 0.375rem;
        
        .preview-menu-item {
          height: 6px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 2px;
          
          &.active {
            background: v.$primary-color;
          }
        }
      }
      
      .preview-content {
        flex: 1;
        padding: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        
        .preview-line {
          height: 6px;
          background: v.$border-color;
          border-radius: 3px;
          
          &.short {
            width: 60%;
          }
        }
      }
    }
  }
  
  &.dark-preview {
    background: #1a202c;
    
    .preview-header {
      height: 24px;
      background: #2d3748;
      border-bottom: 1px solid #4a5568;
      display: flex;
      align-items: center;
      padding: 0 0.75rem;
      gap: 0.375rem;
      
      .preview-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4a5568;
      }
    }
    
    .preview-body {
      display: flex;
      height: calc(100% - 24px);
      
      .preview-sidebar {
        width: 50px;
        background: #2d3748;
        padding: 0.5rem 0.375rem;
        display: flex;
        flex-direction: column;
        gap: 0.375rem;
        
        .preview-menu-item {
          height: 6px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 2px;
          
          &.active {
            background: v.$primary-color;
          }
        }
      }
      
      .preview-content {
        flex: 1;
        padding: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        
        .preview-line {
          height: 6px;
          background: #4a5568;
          border-radius: 3px;
          
          &.short {
            width: 60%;
          }
        }
      }
    }
  }
}

.theme-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.theme-icon {
  color: v.$text-secondary;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  
  .theme-card.active & {
    color: v.$primary-color;
  }
}

.theme-text {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  flex: 1;
}

.theme-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: v.$text-primary;
}

.theme-description {
  font-size: 0.7rem;
  color: v.$text-secondary;
}

.theme-check {
  position: absolute;
  top: 0.875rem;
  right: 0.875rem;
  color: v.$primary-color;
  background: v.$white;
  border-radius: 50%;
  padding: 2px;
  width: 20px;
  height: 20px;
}

// Responsive
@media (max-width: 768px) {
  .profile-view {
    padding: 1rem;
  }

  .profile-header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 1.5rem;
  }

  .profile-header-actions {
    width: 100%;
    
    .btn {
      flex: 1;
    }
  }

  .profile-tabs {
    overflow-x: auto;
    padding: 0 1rem;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }

  .tab-button {
    white-space: nowrap;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
  
  .theme-options {
    grid-template-columns: 1fr;
  }
}

// Dark Mode Styles
[data-theme="dark"] {
  .profile-view {
    background: #0d1117;
  }

  .profile-header-card {
    background: #161b22;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .profile-header-content {
    border-bottom: 1px solid #30363d;
  }

  .profile-avatar {
    border: 3px solid #30363d;
    background: #0d1117;
  }

  .avatar-placeholder {
    color: #e6edf3;
  }

  .avatar-edit-badge {
    background: #2563eb;
    border: 3px solid #161b22;
    
    &:hover {
      background: #1d4ed8;
    }
  }

  .profile-name {
    color: #e6edf3;
  }

  .profile-subtitle {
    color: #7d8590;
  }

  .btn-primary {
    background: #2563eb;
    
    &:hover:not(:disabled) {
      background: #1d4ed8;
    }
  }

  .btn-secondary {
    background: #161b22;
    color: #e6edf3;
    border: 1.5px solid #30363d;
    
    &:hover:not(:disabled) {
      background: #0d1117;
      border-color: #7d8590;
    }
  }

  .profile-tabs {
    background: #161b22;
    border-top: 1px solid #30363d;
  }

  .tab-button {
    color: #7d8590;
    
    &:hover {
      color: #e6edf3;
    }
    
    &.active {
      color: #58a6ff;
      border-bottom-color: #58a6ff;
    }
  }

  .info-card {
    background: #161b22;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .card-header,
  .card-header-with-icon {
    border-bottom: 1px solid #30363d;
  }

  .card-icon {
    color: #58a6ff;
  }

  .card-title {
    color: #e6edf3;
  }

  .card-subtitle {
    color: #7d8590;
  }

  .info-row {
    border-bottom: 1px solid #30363d;
  }

  .info-label {
    color: #7d8590;
  }

  .info-value {
    color: #e6edf3;
  }

  .info-icon {
    color: #7d8590;
  }

  .info-value-badge {
    &.badge-primary {
      background: rgba(88, 166, 255, 0.15);
      color: #58a6ff;
    }
    
    &.badge-success {
      background: rgba(63, 185, 80, 0.15);
      color: #3fb950;
    }
    
    &.badge-danger {
      background: rgba(248, 81, 73, 0.15);
      color: #f85149;
    }
  }

  .form-group label {
    color: #e6edf3;
  }

  .form-input {
    background: #0d1117;
    border: 1.5px solid #30363d;
    color: #e6edf3;
    
    &::placeholder {
      color: #7d8590;
    }
    
    &:focus {
      border-color: #58a6ff;
      box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
    }
    
    &:disabled {
      background: #161b22;
      color: #484f58;
    }
    
    &.input-error {
      border-color: #f85149;
    }
    
    &.input-success {
      border-color: #3fb950;
    }
  }

  .input-icon {
    color: #7d8590;
  }

  .form-help {
    color: #7d8590;
  }

  .password-hint {
    background: rgba(88, 166, 255, 0.1);
    color: #7d8590;
    
    svg {
      color: #58a6ff;
    }
  }

  .form-actions {
    border-top: 1px solid #30363d;
  }

  .preference-item {
    border-bottom: 1px solid #30363d;
  }

  .preference-title {
    color: #e6edf3;
  }

  .preference-description {
    color: #7d8590;
  }

  .preference-section {
    border-top: none;
  }

  .preference-section-title {
    color: #e6edf3;
  }

  .preference-section-description {
    color: #7d8590;
  }

  .toggle-slider {
    background-color: #30363d;
    
    &:before {
      background-color: #e6edf3;
    }
  }

  .toggle-input:checked + .toggle-slider {
    background-color: #2563eb;
  }

  .theme-card {
    border: 2px solid #30363d;
    background: #161b22;
    
    &:hover {
      border-color: #58a6ff;
      box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2);
    }
    
    &.active {
      border-color: #58a6ff;
      box-shadow: 0 4px 16px rgba(88, 166, 255, 0.25);
      background: rgba(88, 166, 255, 0.05);
    }
  }

  .theme-preview {
    border: 1px solid #30363d;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    
    &.light-preview {
      background: #f8f9fa;
    }
    
    &.dark-preview {
      background: #0d1117;
      
      .preview-header {
        background: #161b22;
        border-bottom: 1px solid #30363d;
        
        .preview-dot {
          background: #30363d;
        }
      }
      
      .preview-body {
        .preview-sidebar {
          background: #161b22;
          
          .preview-menu-item {
            background: rgba(255, 255, 255, 0.1);
            
            &.active {
              background: #58a6ff;
            }
          }
        }
        
        .preview-content {
          .preview-line {
            background: #30363d;
          }
        }
      }
    }
  }

  .theme-icon {
    color: #7d8590;
    
    .theme-card.active & {
      color: #58a6ff;
    }
  }

  .theme-label {
    color: #e6edf3;
  }

  .theme-description {
    color: #7d8590;
  }

  .theme-check {
    color: #58a6ff;
    background: #161b22;
  }
}
</style>