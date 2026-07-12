import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Mock } from 'vitest';

import api from '../core/api';
import { useForm } from './useForm';

vi.mock('../core/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}));

vi.mock('./useNotifications', () => ({
  useNotifications: () => ({
    add: vi.fn()
  })
}));

vi.mock('./useErrorHandler', () => ({
  useErrorHandler: () => ({
    handleApiError: vi.fn()
  })
}));

vi.mock('../stores/userStore', () => ({
  useUserStore: () => ({
    userData: null,
    refreshUserData: vi.fn()
  })
}));

const mockedApi = api as unknown as {
  get: Mock;
  post: Mock;
  put: Mock;
  delete: Mock;
};

describe('useForm framework record lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads metadata defaults and keeps sequence defaults display-only until save', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        metadata: {
          fields: {
            name: { type: 'char', default: 'Draft' },
            code: { type: 'char', readonly: true, default: 'New' },
            active: { type: 'boolean', default: true }
          }
        }
      }
    });

    const form = useForm('test.model');

    await form.fetchMetadata();

    expect(mockedApi.get).toHaveBeenCalledWith('/models/meta/test.model/enhanced');
    expect(form.formData.name).toBe('Draft');
    expect(form.formData.code).toBeNull();
    expect(form.formData.active).toBe(true);
  });

  it('creates, updates, and deletes records through generic model endpoints', async () => {
    mockedApi.post.mockResolvedValueOnce({
      data: { id: 10, name: 'Created', code: 'TST-001' }
    });
    mockedApi.put.mockResolvedValueOnce({
      data: { id: 10, name: 'Updated', code: 'TST-001' }
    });
    mockedApi.delete.mockResolvedValueOnce({ data: {} });

    const form = useForm('test.model');
    form.metadata.value = {
      fields: {
        code: { type: 'char', readonly: true, default: 'New' }
      }
    };
    form.formData.name = 'Created';
    form.formData.code = null;

    await form.save();

    expect(mockedApi.post).toHaveBeenCalledWith('/models/test.model', expect.objectContaining({
      name: 'Created',
      code: 'New'
    }));
    expect(form.formData.id).toBe(10);
    expect(form.formData.code).toBe('TST-001');

    form.formData.name = 'Updated';
    await form.save();

    expect(mockedApi.put).toHaveBeenCalledWith('/models/test.model/10', expect.objectContaining({
      id: 10,
      name: 'Updated'
    }));

    await form.deleteRecord(10);

    expect(mockedApi.delete).toHaveBeenCalledWith('/models/test.model/10');
  });
});
