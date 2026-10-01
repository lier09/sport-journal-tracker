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

export const getMeta = () => request('/api/meta');
export const getArticles = (params) => request(`/api/articles?${new URLSearchParams(params)}`);
export const getSources = () => request('/api/sources');
export const saveArticleState = (payload) => request('/api/article-state', {
  method: 'POST',
  body: JSON.stringify(payload),
});
