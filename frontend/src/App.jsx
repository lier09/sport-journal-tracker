import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowDownWideNarrow, ArrowUpRight, BookMarked, BookOpen, Bookmark, CalendarDays,
  Check, ChevronDown, ChevronLeft, ChevronRight, CircleCheck, Clipboard, Database,
  ExternalLink, FileDown, Filter, Heart, Layers3, ListChecks, Menu, Search, Settings2,
  Tag, X,
} from 'lucide-react';
import { getArticles, getMeta, getSources, saveArticleState } from './api';

const NAV = [
  { label: '文献流', icon: BookOpen },
  { label: '今日文献', icon: CalendarDays },
  { label: '期刊库', icon: Layers3 },
  { label: '专题', icon: Tag },
  { label: '阅读队列', icon: ListChecks },
  { label: '数据源', icon: Database },
];
const STATUSES = ['未读', '待读', '阅读中', '已读', '精读', '已引用', '不相关'];

function shortDate(value) {
  if (!value) return '日期暂缺';
  const d = new Date(`${value}T00:00:00`);
  return Number.isNaN(d.getTime()) ? value : new Intl.DateTimeFormat('zh-CN', { month: 'short', day: 'numeric' }).format(d);
}

function formatAuthors(value) {
  const authors = String(value || '').split(';').map((name) => name.trim()).filter(Boolean);
  return authors.length > 4 ? `${authors.slice(0, 3).join(' · ')} · 等` : authors.join(' · ');
}

function topicList(value) {
  return String(value || '').split(';').map((item) => item.trim()).filter(Boolean);
}

function sourceStatus(row) {
  return ['yes', 'true', '1'].includes(String(row.official_source_verified || '').toLowerCase());
}

function App() {
  const [meta, setMeta] = useState(null);
  const [view, setView] = useState('文献流');
  const [selectedDate, setSelectedDate] = useState('');
  const [articles, setArticles] = useState([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState(null);
  const [sources, setSources] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [group, setGroup] = useState('');
  const [journal, setJournal] = useState('');
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [journalSearch, setJournalSearch] = useState('');
  const [mobileReader, setMobileReader] = useState(false);
  const [notice, setNotice] = useState('');

  const refreshMeta = useCallback(async () => {
    try {
      const nextMeta = await getMeta();
      setMeta(nextMeta);
      setSelectedDate((current) => current || nextMeta.latest_date);
    } catch (err) {
      setError(`连接本地文献库失败：${err.message}`);
    }
  }, []);

  useEffect(() => { refreshMeta(); }, [refreshMeta]);

  const groups = useMemo(() => [...new Set((meta?.journals || []).map((item) => item.collection_group).filter(Boolean))].sort(), [meta]);
  const articlesParams = useMemo(() => {
    if (!selectedDate) return null;
    const end = selectedDate;
    const start = view === '文献流' || view === '阅读队列'
      ? new Date(new Date(`${end}T00:00:00`).getTime() - (view === '阅读队列' ? 89 : 6) * 86_400_000).toISOString().slice(0, 10)
      : end;
    return {
      start, end, limit: view === '阅读队列' ? 100 : 40,
      q: query, journal, group, topic, status,
      favorites: favoritesOnly ? '1' : '',
    };
  }, [selectedDate, view, query, journal, group, topic, status, favoritesOnly]);

  const loadArticles = useCallback(async () => {
    if (!articlesParams || view === '期刊库' || view === '数据源') return;
    setBusy(true);
    setError('');
    try {
      const result = await getArticles(articlesParams);
      let rows = result.items || [];
      if (view === '阅读队列') rows = rows.filter((row) => row.favorite || ['待读', '阅读中', '精读', '已引用'].includes(row.status));
      setArticles(rows);
      setTotal(view === '阅读队列' ? rows.length : result.total || 0);
      setSelected((current) => rows.find((row) => row.article_id === current?.article_id) || rows[0] || null);
    } catch (err) {
      setError(`读取文献失败：${err.message}`);
    } finally {
      setBusy(false);
    }
  }, [articlesParams, view]);

  useEffect(() => { loadArticles(); }, [loadArticles]);

  useEffect(() => {
    if (view !== '数据源') return;
    getSources().then(setSources).catch((err) => setError(`读取数据源状态失败：${err.message}`));
  }, [view]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(''), 2400);
    return () => clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    const onShortcut = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        const input = document.getElementById('global-search');
        if (input) { event.preventDefault(); input.focus(); }
      }
    };
    window.addEventListener('keydown', onShortcut);
    return () => window.removeEventListener('keydown', onShortcut);
  }, []);

  const chooseView = (next) => {
    setView(next);
    document.body.classList.remove('nav-open');
    setMobileReader(false);
    setError('');
    if (next !== '专题') setTopic('');
    if (next !== '阅读队列') { setStatus(''); setFavoritesOnly(false); }
  };

  const saveState = async (row, patch) => {
    if (!row) return;
    const payload = {
      doi: row.doi,
      title_hash: row.title_hash,
      journal_name: row.journal_name,
      status: patch.status ?? row.status ?? '未读',
      favorite: patch.favorite ?? Boolean(row.favorite),
      user_notes: patch.user_notes ?? row.user_notes ?? '',
      personal_tags: patch.personal_tags ?? row.personal_tags ?? '',
    };
    try {
      await saveArticleState(payload);
      const update = (item) => item.article_id === row.article_id ? { ...item, ...payload, favorite: Number(payload.favorite) } : item;
      setArticles((rows) => rows.map(update));
      setSelected((current) => current?.article_id === row.article_id ? { ...current, ...payload, favorite: Number(payload.favorite) } : current);
      setNotice('阅读信息已保存在本机');
    } catch (err) {
      setError(`保存失败：${err.message}`);
    }
  };

  const toggleFavorite = (row) => saveState(row, { favorite: !Boolean(row.favorite) });
  const markRead = (row) => saveState(row, { status: row.status === '已读' ? '未读' : '已读' });

  const exportCsv = () => {
    const columns = ['first_seen_date', 'publication_date', 'journal_name', 'title', 'authors', 'doi', 'url', 'topics', 'status', 'favorite'];
    const quote = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
    const csv = [columns.join(','), ...articles.map((row) => columns.map((key) => quote(row[key])).join(','))].join('\r\n');
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }));
    link.download = `sport-literature-${selectedDate || 'export'}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const displayedArticles = articles;
  const title = view === '文献流' ? (selectedDate === new Date().toISOString().slice(0, 10) ? '今日新发现' : '最近收录') : view;
  const journalRows = (meta?.journals || []).filter((row) => {
    const q = journalSearch.trim().toLowerCase();
    return (!group || row.collection_group === group) && (!q || `${row.journal_name} ${row.domain} ${row.collection_group}`.toLowerCase().includes(q));
  });
  const topicCounts = useMemo(() => {
    const counts = new Map();
    for (const row of articles) for (const label of topicList(row.topics)) counts.set(label, (counts.get(label) || 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [articles]);

  if (!meta) return <div className="boot-screen"><div className="boot-mark"><BookOpen size={25} /></div><p>{error || '正在连接本机文献库…'}</p>{error && <button className="button button-outline" onClick={refreshMeta}>重新连接</button>}</div>;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><BookOpen size={21} strokeWidth={1.8} /></span><span>运动科学文献台</span></div>
        <div className="nav-caption">阅读空间</div>
        <nav className="primary-nav" aria-label="主导航">
          {NAV.map(({ label, icon: Icon }) => (
            <button key={label} className={`nav-item ${view === label ? 'active' : ''}`} onClick={() => chooseView(label)} aria-label={label} title={label} aria-current={view === label ? 'page' : undefined}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-rule" />
        <div className="sidebar-meta"><span className="status-dot" />本机阅读模式</div>
        <div className="sidebar-footer">
          <div className="avatar">研</div>
          <div className="profile-copy"><strong>研究者</strong><span>私人阅读数据仅保存在本机</span></div>
          <button className="icon-button quiet" aria-label="导出当前文献" title="导出当前文献" onClick={exportCsv}><FileDown size={17} /></button>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <button className="mobile-menu icon-button" aria-label="打开导航" onClick={() => document.body.classList.toggle('nav-open')}><Menu size={20} /></button>
          <div className="breadcrumbs"><span>文献工作台</span><ChevronRight size={14} /><strong>{title}</strong></div>
          <div className="topbar-actions">
            <span className="local-indicator"><span className="status-dot" />本机数据</span>
            <button className="icon-button" title="导出当前结果" aria-label="导出当前结果" onClick={exportCsv}><FileDown size={18} /></button>
            <button className="icon-button" title="刷新" aria-label="刷新" onClick={() => { refreshMeta(); loadArticles(); }}><Settings2 size={18} /></button>
          </div>
        </header>

        <section className="page-heading">
          <div className="heading-main">
            <div>
              <h1>{title}</h1>
              <p>{view === '文献流' ? '把新研究放在一起，按方向筛选，再直接进入阅读。' : view === '今日文献' ? '查看所选日期首次收录的研究。' : view === '期刊库' ? '按研究方向浏览正在追踪的期刊与来源状态。' : view === '专题' ? '从主题线索快速找到相关的新研究。' : view === '阅读队列' ? '你标记待读、精读或收藏的文献。' : '查看目录覆盖、来源核验和最近抓取记录。'}</p>
            </div>
            {view !== '期刊库' && view !== '数据源' && <div className="date-control"><CalendarDays size={16} /><input aria-label="首次收录日期" type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} /><button className="icon-button mini" aria-label="前一天" onClick={() => setSelectedDate((day) => shiftDay(day, -1))}><ChevronLeft size={16} /></button><button className="icon-button mini" aria-label="后一天" onClick={() => setSelectedDate((day) => shiftDay(day, 1))}><ChevronRight size={16} /></button></div>}
          </div>
          <div className="summary-strip">
            <div><span>当前结果</span><strong>{total.toLocaleString('zh-CN')}</strong><small>篇文献</small></div>
            <div><span>追踪期刊</span><strong>{meta.journals.length.toLocaleString('zh-CN')}</strong><small>本</small></div>
            <div><span>最新收录</span><strong className="summary-date">{shortDate(meta.latest_date)}</strong><small>{meta.latest_date}</small></div>
          </div>
        </section>

        {(view === '文献流' || view === '今日文献' || view === '阅读队列' || view === '专题') && (
          <section className="filterbar" aria-label="文献筛选">
            <label className="search-box"><Search size={17} /><input id="global-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索题名、作者、期刊或摘要" aria-label="搜索题名、作者、期刊或摘要" /><kbd>Ctrl K</kbd></label>
            <label className="filter-control"><span className="sr-only">研究方向</span><Filter size={15} /><select value={group} onChange={(event) => { setGroup(event.target.value); setJournal(''); }}><option value="">全部方向</option>{groups.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={13} /></label>
            <label className="filter-control journal-filter"><span className="sr-only">期刊</span><select value={journal} onChange={(event) => setJournal(event.target.value)}><option value="">全部期刊</option>{(meta.journals || []).map((item) => <option key={item.journal_name}>{item.journal_name}</option>)}</select><ChevronDown size={13} /></label>
            {view === '专题' && <label className="filter-control"><Tag size={15} /><select value={topic} onChange={(event) => setTopic(event.target.value)}><option value="">选择专题</option>{meta.topics.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={13} /></label>}
            {view === '阅读队列' && <label className="filter-control"><span className="sr-only">阅读状态</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">全部状态</option>{STATUSES.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={13} /></label>}
            <label className={`favorite-filter ${favoritesOnly ? 'selected' : ''}`}><input type="checkbox" checked={favoritesOnly} onChange={(event) => setFavoritesOnly(event.target.checked)} /><Heart size={15} fill={favoritesOnly ? 'currentColor' : 'none'} />收藏</label>
            <span className="sort-indicator"><ArrowDownWideNarrow size={16} /><span>最新收录</span></span>
          </section>
        )}

        {error && <div className="inline-error" role="alert"><span>{error}</span><button onClick={() => { setError(''); loadArticles(); }}>重试</button></div>}

        <div className={`content-layout ${view === '期刊库' || view === '数据源' ? 'single-content' : ''}`}>
          {view === '期刊库' && (
            <section className="library-view">
              <div className="library-toolbar">
                <label className="search-box"><Search size={17} /><input value={journalSearch} onChange={(event) => setJournalSearch(event.target.value)} placeholder="搜索期刊或研究方向" aria-label="搜索期刊或研究方向" /></label>
                <label className="filter-control"><span className="sr-only">研究方向</span><Filter size={15} /><select value={group} onChange={(event) => setGroup(event.target.value)}><option value="">全部方向</option>{groups.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={13} /></label>
                <span className="result-count">{journalRows.length} / {meta.journals.length} 本期刊</span>
              </div>
              <div className="journal-table-wrap"><table className="journal-table"><thead><tr><th>期刊</th><th>研究方向</th><th>细分主题</th><th>策略</th><th>来源核验</th></tr></thead><tbody>
                {journalRows.map((item) => {
                  const verified = item.source_verified === true || ['yes', 'true', '1'].includes(String(item.official_source_verified || '').toLowerCase());
                  return <tr key={item.journal_name}><td className="journal-name-cell">{item.journal_name}<small>{[item.issn && `ISSN ${item.issn}`, item.eissn && `eISSN ${item.eissn}`].filter(Boolean).join(' · ') || 'ISSN 暂缺'}</small></td><td>{item.collection_group || '—'}</td><td>{item.domain || '—'}</td><td><span className="plain-tag">{item.collection_mode === 'keyword_filter' ? '相关性筛选' : '按刊检索'}</span></td><td><span className={`source-state ${verified ? 'verified' : 'pending'}`}><span />{verified ? '出版社源已核验' : '数据库兜底'}</span></td></tr>;
                })}
              </tbody></table></div>
            </section>
          )}

          {view === '数据源' && <SourceView data={sources} journals={meta.journals} />}

          {view === '专题' && !topic && (
            <aside className="topic-rail"><div className="rail-heading"><div><h2>主题线索</h2><p>当前结果中的专题分布</p></div><Tag size={18} /></div>
              {topicCounts.length ? topicCounts.map(([name, count]) => <button key={name} className="topic-row" onClick={() => setTopic(name)}><span>{name.replaceAll('_', ' ')}</span><strong>{count}</strong></button>) : <div className="empty-message">当前结果还没有专题命中。</div>}
            </aside>
          )}

          {!['期刊库', '数据源'].includes(view) && (view !== '专题' || topic) && (
            <>
              <section className="article-column" aria-label="文献列表">
                <div className="list-toolbar">
                  <div className="list-tabs"><button className="selected">{view === '阅读队列' ? '阅读清单' : view === '专题' ? topic.replaceAll('_', ' ') : '最新收录'}</button><button onClick={() => chooseView('期刊库')}>浏览期刊</button></div>
                  <span className="list-count">{busy ? '正在更新…' : `${total} 篇`}</span>
                </div>
                <div className="article-list" aria-busy={busy}>
                  {displayedArticles.map((row, index) => <ArticleRow key={row.article_id} row={row} index={index} selected={selected?.article_id === row.article_id} onSelect={() => { setSelected(row); setMobileReader(true); }} onFavorite={() => toggleFavorite(row)} />)}
                  {!busy && displayedArticles.length === 0 && <div className="empty-state"><Search size={21} /><strong>{view === '阅读队列' ? '阅读清单还是空的' : '没有找到匹配的文献'}</strong><p>{view === '阅读队列' ? '在论文条目上点书签，或把状态改为待读，即可加入清单。' : '试试放宽日期、清除某个筛选条件，或换一个关键词。'}</p><button className="button button-outline" onClick={() => { setQuery(''); setTopic(''); setJournal(''); setGroup(''); setStatus(''); setFavoritesOnly(false); }}>清除筛选</button></div>}
                </div>
                  {total > articles.length && <button className="load-more" onClick={async () => { try { const more = await getArticles({ ...articlesParams, limit: 40, offset: articles.length }); setArticles((current) => [...current, ...more.items]); } catch (err) { setError(err.message); } }}>加载更多文献 <ChevronDown size={15} /></button>}
              </section>
              <ReaderPane row={selected} onSave={saveState} onFavorite={toggleFavorite} onRead={markRead} onClose={() => setMobileReader(false)} mobileOpen={mobileReader} />
            </>
          )}
        </div>
      </main>
      {notice && <div className="toast" role="status"><Check size={16} />{notice}</div>}
    </div>
  );
}

function shiftDay(value, delta) {
  if (!value) return value;
  const day = new Date(`${value}T00:00:00`);
  day.setDate(day.getDate() + delta);
  return day.toISOString().slice(0, 10);
}

function ArticleRow({ row, index, selected, onSelect, onFavorite }) {
  const tags = topicList(row.topics);
  return (
    <article className={`article-row ${selected ? 'selected' : ''}`} onClick={onSelect} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(); } }} tabIndex={0} aria-label={`${row.title}, ${row.journal_name}`} aria-current={selected ? 'true' : undefined}>
      <div className="row-index">{String(index + 1).padStart(2, '0')}</div>
      <div className="row-content">
        <div className="row-journal">{row.journal_name}<span>{row.collection_group}</span></div>
        <h2>{row.title}</h2>
        <p className="row-authors">{formatAuthors(row.authors) || '作者信息暂缺'}</p>
        <p className="row-abstract">{row.abstract || '暂无摘要。打开原文或 DOI 页面查看研究详情。'}</p>
        <div className="row-tags">{tags.slice(0, 4).map((tag) => <span key={tag}>{tag.replaceAll('_', ' ')}</span>)}</div>
      </div>
      <div className="row-side"><time dateTime={row.first_seen_date}>{shortDate(row.first_seen_date)}</time><button className={`bookmark-button ${row.favorite ? 'saved' : ''}`} aria-label={row.favorite ? '取消收藏' : '收藏文献'} title={row.favorite ? '取消收藏' : '收藏文献'} onClick={(event) => { event.stopPropagation(); onFavorite(); }}>{row.favorite ? <BookMarked size={18} /> : <Bookmark size={18} />}</button><span className={`read-dot status-${row.status === '已读' ? 'read' : row.status === '精读' ? 'deep' : 'new'}`} title={`阅读状态：${row.status}`} /></div>
    </article>
  );
}

function ReaderPane({ row, onSave, onFavorite, onRead, onClose, mobileOpen }) {
  if (!row) return <aside className={`reader-pane reader-empty ${mobileOpen ? 'mobile-open' : ''}`}><div className="reader-empty-mark"><BookOpen size={24} /></div><strong>选择一篇文献开始阅读</strong><p>从列表中选择条目，这里会显示摘要、主题与阅读操作。</p></aside>;
  const tags = topicList(row.topics);
  return (
    <aside className={`reader-pane ${mobileOpen ? 'mobile-open' : ''}`} aria-label="文献详情">
      <div className="reader-toolbar"><span><span className="status-dot" />文献详情</span><button className="icon-button mobile-close" onClick={onClose} aria-label="关闭阅读窗"><X size={19} /></button><span className="reader-position">{row.status || '未读'}</span></div>
      <div className="reader-scroll">
        <div className="reader-journal">{row.journal_name}<span>{row.collection_group || '运动科学'}</span></div>
        <h2 className="reader-title">{row.title}</h2>
        <dl className="metadata-list">
          <div><dt>首次收录</dt><dd>{row.first_seen_date || '暂缺'}</dd></div>
          <div><dt>发表日期</dt><dd>{row.publication_date || '暂缺'}</dd></div>
          <div><dt>作者</dt><dd>{formatAuthors(row.authors) || '暂缺'}</dd></div>
          {row.doi && <div><dt>DOI</dt><dd><a href={`https://doi.org/${row.doi}`} target="_blank" rel="noreferrer">{row.doi}<ArrowUpRight size={13} /></a></dd></div>}
        </dl>
        <section className="reader-section"><div className="reader-section-heading"><h3>摘要</h3><span>{row.abstract ? '来源记录' : '暂缺'}</span></div><p className="reader-abstract">{row.abstract || '当前数据库尚无该文献的摘要。可以通过 DOI 或原文链接查看出版方页面。'}</p></section>
        <section className="reader-section"><div className="reader-section-heading"><h3>专题标签</h3><span>{tags.length}</span></div><div className="detail-tags">{tags.length ? tags.map((tag) => <span key={tag}>{tag.replaceAll('_', ' ')}</span>) : <span className="no-tag">暂无命中标签</span>}</div></section>
        <section className="reader-section reader-personal"><div className="reader-section-heading"><h3>个人阅读</h3><span>仅保存在本机</span></div>
          <label className="personal-field">阅读状态<select value={row.status || '未读'} onChange={(event) => onSave(row, { status: event.target.value })}>{STATUSES.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="personal-field">我的标签<input key={`${row.article_id}-tags`} defaultValue={row.personal_tags || ''} placeholder="例如：精读、训练监控" onBlur={(event) => { if (event.target.value !== (row.personal_tags || '')) onSave(row, { personal_tags: event.target.value }); }} /></label>
          <label className="personal-field">阅读笔记<textarea key={`${row.article_id}-notes`} defaultValue={row.user_notes || ''} placeholder="记录研究设计、主要发现或对实践的启发…" rows={3} onBlur={(event) => { if (event.target.value !== (row.user_notes || '')) onSave(row, { user_notes: event.target.value }); }} /></label>
        </section>
      </div>
      <div className="reader-actions"><a className="button button-primary" href={row.fulltext_url || row.url || (row.doi ? `https://doi.org/${row.doi}` : '#')} target="_blank" rel="noreferrer"><ExternalLink size={16} />查看原文</a><button className={`button button-outline ${row.favorite ? 'is-saved' : ''}`} onClick={() => onFavorite(row)}><Bookmark size={16} />{row.favorite ? '已收藏' : '收藏'}</button><button className={`button button-outline ${row.status === '已读' ? 'is-saved' : ''}`} onClick={() => onRead(row)}><CircleCheck size={16} />{row.status === '已读' ? '已读' : '标记已读'}</button></div>
    </aside>
  );
}

function SourceView({ data, journals }) {
  if (!data) return <section className="source-view"><div className="loading-line" /><div className="loading-line short" /></section>;
  const verified = data.registry.filter(sourceStatus).length;
  const expanded = data.registry.length - verified;
  return <section className="source-view">
    <div className="source-summary"><div><span>期刊目录</span><strong>{journals.length}</strong><small>本</small></div><div><span>出版社源已核验</span><strong>{verified}</strong><small>本</small></div><div><span>数据库兜底</span><strong>{expanded}</strong><small>本</small></div></div>
    <div className="source-intro"><div className="source-icon"><Database size={20} /></div><div><h2>来源覆盖与核验</h2><p>未核验出版社接口的期刊仍通过 Crossref / PubMed 等数据库检索；状态会明确显示，不会被算作官方订阅源。</p></div></div>
    <div className="source-run"><div><span className="source-run-label">最近一次抓取</span><strong>{data.latest_run?.run_date || '暂无抓取记录'}</strong></div><span className={`run-badge ${data.latest_run?.status === 'error' ? 'error' : ''}`}><span />{data.latest_run?.status || '等待运行'}</span></div>
    {data.errors?.length > 0 && <div className="error-list"><h3>近期异常</h3>{data.errors.slice(0, 8).map((item, index) => <div className="error-row" key={`${item.created_at}-${index}`}><span>{item.journal_name}</span><span>{item.source}</span><small>{item.error_message}</small></div>)}</div>}
    <h3 className="directory-title">期刊来源目录 <span>{data.registry.length} 本</span></h3>
    <div className="journal-table-wrap"><table className="journal-table"><thead><tr><th>期刊</th><th>方向</th><th>来源状态</th><th>后续动作</th></tr></thead><tbody>{data.registry.map((row) => <tr key={row.journal_name}><td className="journal-name-cell">{row.journal_name}</td><td>{row.collection_group || row.domain || '—'}</td><td><span className={`source-state ${sourceStatus(row) ? 'verified' : 'pending'}`}><span />{sourceStatus(row) ? '出版社源已核验' : 'Crossref / PubMed 兜底'}</span></td><td>{row.next_action || '按现有来源采集'}</td></tr>)}</tbody></table></div>
  </section>;
}

export default App;
