import { computed, nextTick } from 'vue';
import { shallowMount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Mock } from 'vitest';

import api from '../../core/api';
import BaseForm from './BaseForm.vue';

vi.mock('../../core/api', () => ({
  default: {
    get: vi.fn()
  }
}));

vi.mock('../../composables/useResponsive', () => ({
  useResponsive: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    isTouchDevice: false,
    formColumns: computed(() => 2),
    touchTargetSize: { minHeight: '32px', minWidth: '32px' }
  })
}));

vi.mock('../../composables/useUnifiedPermissions', () => ({
  useUnifiedPermissions: () => ({
    actionPermissions: computed(() => ({
      showCreateButton: true,
      showSaveButton: true,
      showDiscardButton: true,
      showDeleteButton: true,
      showEditActions: true,
      makeFieldsReadonly: false,
      allowFormSubmission: true
    })),
    canCreate: computed(() => true),
    canWrite: computed(() => true),
    canDelete: computed(() => true),
    getPermissionClasses: vi.fn(() => ''),
    refreshPermissions: vi.fn()
  })
}));

vi.mock('../../composables/useFieldVisibility', () => ({
  useFieldVisibility: () => ({
    isFieldVisible: vi.fn(() => true),
    isFieldReadonly: vi.fn(() => false),
    isFieldRequired: vi.fn(() => false),
    getVisibleFields: vi.fn((fields: string[]) => fields),
    evaluateAllFields: vi.fn(),
    evaluateDomain: vi.fn((domain: any) => Boolean(domain === true)),
    forceLocalEvaluation: vi.fn(),
    resetToBackendEvaluation: vi.fn(),
    fieldStates: computed(() => ({}))
  })
}));

vi.mock('../../composables/useNotifications', () => ({
  useNotifications: () => ({
    add: vi.fn()
  })
}));

vi.mock('../../composables/useDialog', () => ({
  useDialog: () => ({})
}));

const mockedApi = api as unknown as {
  get: Mock;
};

const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

const mountForm = (overrides: any = {}) => {
  return shallowMount(BaseForm, {
    props: {
      modelName: 'test.model',
      formData: {
        id: 1,
        name: 'Test Record',
        stage_id: { id: 2, display_name: 'In Progress' },
        related_count: 0,
        active_count: 3,
        notes: 'Line one\nLine two',
        ...overrides.formData
      },
      metadata: {
        rec_name: 'name',
        status_field: 'stage_id',
        fields: {
          name: { type: 'char', label: 'Name' },
          stage_id: { type: 'many2one', label: 'Stage', relation: 'test.stage' },
          related_count: { type: 'integer', label: 'Related' },
          active_count: { type: 'integer', label: 'Active' },
          notes: { type: 'text', label: 'Notes' }
        },
        views: {
          form: {
            groups: [
              { title: 'Main', fields: ['name', 'notes'] }
            ],
            smart_buttons: [
              { name: 'empty_related', label: 'Related', field: 'related_count', icon: 'Link' },
              { name: 'active_related', label: 'Active', field: 'active_count', icon: 'Link' }
            ],
            header_buttons: []
          }
        },
        ...overrides.metadata
      },
      loading: false,
      currentIndex: 0,
      totalInPage: 1,
      breadcrumbs: [],
      ...overrides.props
    },
    global: {
      stubs: {
        SmartButtons: {
          name: 'SmartButtons',
          props: ['buttons', 'data'],
          template: '<div class="smart-buttons-stub"></div>'
        },
        StatusBar: {
          name: 'StatusBar',
          props: ['stages', 'currentValue', 'readonly'],
          template: '<div class="status-bar-stub"></div>'
        },
        Breadcrumbs: true,
        NotificationBell: true,
        PriorityField: true,
        FormSkeleton: true,
        ResetPasswordModal: true,
        AuditLogSidebar: true,
        AttachmentField: true,
        AttachmentsField: true,
        BooleanField: true,
        DateField: true,
        DateTimeField: true,
        ImageField: true,
        Many2oneField: true,
        Many2manyField: true,
        One2manyField: true,
        PasswordField: true,
        SelectionField: true
      }
    }
  });
};

describe('BaseForm framework metadata rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.get.mockResolvedValue({
      data: {
        items: [
          { id: 3, display_name: 'Done', sequence: 30 },
          { id: 1, display_name: 'Draft', sequence: 10 },
          { id: 2, display_name: 'In Progress', sequence: 20 }
        ]
      }
    });
  });

  it('hides smart buttons whose backend count field is empty', async () => {
    const wrapper = mountForm();
    await nextTick();

    const smartButtons = wrapper.findComponent({ name: 'SmartButtons' });

    expect(smartButtons.props('buttons')).toEqual([
      { name: 'active_related', label: 'Active', field: 'active_count', icon: 'Link' }
    ]);
  });

  it('renders Many2one status fields with loaded relation stages and object current value', async () => {
    const wrapper = mountForm();
    await flushPromises();
    await nextTick();

    const statusBar = wrapper.findComponent({ name: 'StatusBar' });

    expect(mockedApi.get).toHaveBeenCalledWith('/models/test.stage', {
      params: {
        parent_model: 'test.model',
        limit: 500
      }
    });
    expect(statusBar.props('currentValue')).toBe(2);
    expect(statusBar.props('stages')).toEqual([
      { val: 1, label: 'Draft' },
      { val: 2, label: 'In Progress' },
      { val: 3, label: 'Done' }
    ]);
  });
});
