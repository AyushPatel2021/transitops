import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Mock } from 'vitest';

import api from '../core/api';
import { useList } from './useList';

vi.mock('../core/api', () => ({
  default: {
    get: vi.fn()
  }
}));

const mockedApi = api as unknown as {
  get: Mock;
};

describe('useList framework data loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads enhanced metadata and preserves backend search configuration', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        metadata: {
          description: 'Test Models',
          fields: { name: { type: 'char', label: 'Name' } }
        },
        search_config: {
          filters: [{ name: 'active', label: 'Active', default: true }]
        }
      }
    });

    const list = useList('test.model');

    await list.fetchMetadata();

    expect(mockedApi.get).toHaveBeenCalledWith('/models/meta/test.model/enhanced');
    expect(list.metadata.value.search_config.filters[0].name).toBe('active');
  });

  it('builds generic list query params for search, filters, grouping, and paging', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        items: [{ id: 1, name: 'Alpha' }],
        total: 1,
        grouped_results: [{ value: 'Draft', count: 1, items: [] }],
        group_by: 'state'
      }
    });

    const list = useList('test.model');

    await list.fetchItems({
      search: 'alpha',
      searchField: 'name',
      domain: JSON.stringify([['active', '=', true]]),
      filters: ['active'],
      groupBy: 'state',
      limit: 25,
      offset: 50
    });

    const calledUrl = mockedApi.get.mock.calls[0][0];
    const query = new URL(calledUrl, 'http://localhost').searchParams;

    expect(calledUrl.startsWith('/models/test.model?')).toBe(true);
    expect(query.get('search')).toBe('alpha');
    expect(query.get('search_field')).toBe('name');
    expect(query.get('filters')).toBe(JSON.stringify(['active']));
    expect(query.get('groupBy')).toBe('state');
    expect(query.get('limit')).toBe('25');
    expect(query.get('offset')).toBe('50');
    expect(list.items.value).toEqual([{ id: 1, name: 'Alpha' }]);
    expect(list.totalItems.value).toBe(1);
    expect(list.currentGroupBy.value).toBe('state');
  });
});
