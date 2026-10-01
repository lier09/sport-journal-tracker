async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `请求失败 (${response.status})`);
  }
  return response.json();
}

const browserStateMode = import.meta.env.VITE_BROWSER_READING_STATE === '1';
const readingStateKey = 'sport-journal-tracker-reading-state-v1';

function readBrowserStates() {
  try { return JSON.parse(localStorage.getItem(readingStateKey) || '{}'); }
  catch { return {}; }
}

export const getMeta = () => request('/api/meta');
export async function getArticles(params) {
  if (!browserStateMode) return request(`/api/articles?${new URLSearchParams(params)}`);
  const query = new URLSearchParams(params);
  const requestedStatus = query.get('status') || '';
  const requestedFavorites = query.get('favorites') === '1';
  query.delete('status');
  query.delete('favorites');
  if (requestedStatus || requestedFavorites) query.set('limit', '100');
  const result = await request(`/api/articles?${query}`);
  const states = readBrowserStates();
  let items = (result.items || []).map((row) => ({
    ...row,
    ...(states[row.article_key] || {}),
    favorite: Number((states[row.article_key]?.favorite ?? row.favorite) || 0),
  }));
  if (requestedStatus) items = items.filter((row) => row.status === requestedStatus);
  if (requestedFavorites) items = items.filter((row) => row.favorite);
  return { ...result, items, total: requestedStatus || requestedFavorites ? items.length : result.total };
}
export const getSources = () => request('/api/sources');
export async function saveArticleState(payload) {
  if (browserStateMode) {
    const states = readBrowserStates();
    states[payload.article_key] = {
      status: payload.status,
      favorite: Number(Boolean(payload.favorite)),
      user_notes: payload.user_notes || '',
      personal_tags: payload.personal_tags || '',
    };
    localStorage.setItem(readingStateKey, JSON.stringify(states));
    return { ok: true };
  }
  return request('/api/article-state', { method: 'POST', body: JSON.stringify(payload) });
}
