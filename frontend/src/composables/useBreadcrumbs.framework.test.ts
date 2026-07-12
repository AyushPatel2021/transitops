import { beforeEach, describe, expect, it } from 'vitest';

import { useBreadcrumbs } from './useBreadcrumbs';

describe('useBreadcrumbs framework navigation state', () => {
  beforeEach(() => {
    sessionStorage.clear();
    useBreadcrumbs().reset();
  });

  it('updates matching list breadcrumbs instead of duplicating query-only changes', () => {
    const breadcrumbs = useBreadcrumbs();

    breadcrumbs.push({
      label: 'Products',
      path: '/models/product.product',
      view: 'list',
      query: { search: 'old' },
      domain: [['active', '=', true]]
    });
    breadcrumbs.push({
      label: 'Products',
      path: '/models/product.product',
      view: 'list',
      query: { search: 'new' },
      domain: [['active', '=', true]]
    });

    expect(breadcrumbs.trail.value).toHaveLength(1);
    expect(breadcrumbs.trail.value[0].query.search).toBe('new');
  });

  it('keeps form records as distinct breadcrumbs and supports sidebar reset requests', () => {
    const breadcrumbs = useBreadcrumbs();

    breadcrumbs.push({ label: 'Products', path: '/models/product.product', view: 'list' });
    breadcrumbs.push({ label: 'A', path: '/models/product.product/1', view: 'form', id: 1 });
    breadcrumbs.push({ label: 'B', path: '/models/product.product/2', view: 'form', id: 2 });

    expect(breadcrumbs.trail.value.map(item => item.label)).toEqual(['Products', 'A', 'B']);

    breadcrumbs.requestReset();

    expect(breadcrumbs.consumeReset()).toBe(true);
    expect(breadcrumbs.trail.value).toEqual([]);
    expect(breadcrumbs.consumeReset()).toBe(false);
  });
});
