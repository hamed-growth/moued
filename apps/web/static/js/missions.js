const page = document.querySelector('.path-page');
if (page) {
  const today = document.getElementById('today');
  const days = document.getElementById('path-days');
  const sheet = document.getElementById('mission-sheet');
  const toast = document.getElementById('path-toast');
  const backToday = document.getElementById('back-today');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let activeNode = null;
  let busy = false;

  const stateText = { available: 'آمادهٔ انجام', not_open: 'هنوز باز نشده', missed: 'از دست رفت', pending: 'در انتظار تأیید', approved: 'تأیید شد', rejected: 'دوباره تلاش کن', locked: 'این مأموریت در روز خودش باز می‌شود' };
  const digits = text => String(text).replace(/\d/g, digit => '۰۱۲۳۴۵۶۷۸۹'[Number(digit)]);
  document.querySelectorAll('[data-count]').forEach(el => { el.textContent = digits(el.dataset.count); });
  function flash(message) { toast.textContent = message; toast.hidden = false; setTimeout(() => { toast.hidden = true; }, 3500); }
  function csrf() { return document.cookie.split('; ').find(value => value.startsWith('csrftoken='))?.split('=')[1] || ''; }

  function openSheet(node) {
    activeNode = node;
    const state = node.dataset.state;
    document.getElementById('sheet-title').textContent = node.dataset.title;
    document.getElementById('sheet-description').textContent = node.dataset.description || 'این مأموریت را انجام بده و مسیرت را ادامه بده.';
    document.getElementById('sheet-time').textContent = node.dataset.time;
    document.getElementById('sheet-points').textContent = `+${digits(node.dataset.points)} امتیاز`;
    document.getElementById('sheet-status').textContent = stateText[state];
    const action = document.getElementById('sheet-action');
    action.disabled = node.dataset.canSubmit !== 'true';
    action.textContent = node.dataset.canSubmit === 'true' ? 'انجام دادم' : stateText[state];
    sheet.showModal();
  }
  days.addEventListener('click', event => {
    const node = event.target.closest('.path-node');
    if (node) openSheet(node);
  });
  sheet.querySelector('[data-sheet-close]').addEventListener('click', () => sheet.close());
  sheet.addEventListener('click', event => { if (event.target === sheet) sheet.close(); });
  sheet.addEventListener('close', () => activeNode?.focus());
  let touchY = 0;
  sheet.addEventListener('touchstart', event => { touchY = event.touches[0].clientY; }, { passive: true });
  sheet.addEventListener('touchend', event => { if (event.changedTouches[0].clientY - touchY > 100) sheet.close(); }, { passive: true });

  document.getElementById('sheet-action').addEventListener('click', async event => {
    if (!activeNode || busy || activeNode.dataset.canSubmit !== 'true') return;
    busy = true;
    const button = event.currentTarget;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    button.textContent = 'در حال ثبت…';
    try {
      const response = await fetch(`/missions/${activeNode.dataset.missionId}/request/`, {
        method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
        body: new URLSearchParams({ note: '' }),
      });
      if (response.status === 401 || response.redirected) { location.href = `${page.dataset.loginUrl}?next=${encodeURIComponent(location.pathname)}`; return; }
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.message || 'ثبت انجام نشد. دوباره تلاش کن.');
      activeNode.dataset.state = 'pending';
      activeNode.dataset.canSubmit = 'false';
      activeNode.closest('.path-item').className = 'path-item path-item--pending';
      activeNode.querySelector('.path-node__meta').textContent = 'در انتظار تأیید';
      activeNode.querySelector('use').setAttribute('href', '#icon-clock');
      activeNode.setAttribute('aria-label', `${activeNode.dataset.title}، در انتظار تأیید، ${digits(activeNode.dataset.points)} امتیاز`);
      const pending = document.querySelector('[data-pending]');
      pending.dataset.count = String(Number(pending.dataset.count) + Number(activeNode.dataset.points));
      pending.textContent = digits(pending.dataset.count);
      sheet.close(); flash('ثبت شد؛ در انتظار تأیید مدیر است.');
    } catch (error) { flash(error instanceof TypeError ? 'ارتباط برقرار نشد. اینترنتت را بررسی کن و دوباره تلاش کن.' : error.message); button.disabled = false; button.textContent = 'انجام دادم'; }
    finally { busy = false; button.removeAttribute('aria-busy'); }
  });

  if (today) {
    requestAnimationFrame(() => today.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' }));
    new IntersectionObserver(entries => { backToday.hidden = entries[0].isIntersecting; }).observe(today);
    backToday.addEventListener('click', () => today.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' }));
  }
  let ticking = false;
  addEventListener('scroll', () => { if (ticking) return; ticking = true; requestAnimationFrame(() => { document.getElementById('path-header').dataset.compact = scrollY > 60; ticking = false; }); }, { passive: true });

  const loading = { before: false, after: false };
  const finished = { before: false, after: false };
  async function load(direction) {
    if (loading[direction] || finished[direction]) return;
    const sections = days.querySelectorAll('.mission-day');
    if (!sections.length) return;
    const anchor = direction === 'before' ? sections[0].dataset.day : sections[sections.length - 1].dataset.day;
    loading[direction] = true;
    const edge = document.getElementById(direction === 'before' ? 'path-top' : 'path-bottom');
    edge.classList.add('path-sentinel--loading');
    edge.setAttribute('role', 'status');
    edge.setAttribute('aria-label', 'در حال بارگذاری روزها');
    try {
      const response = await fetch(`/missions/days/?${direction}=${anchor}&count=3`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (response.status === 401 || response.redirected) { location.href = `${page.dataset.loginUrl}?next=${encodeURIComponent(location.pathname)}`; return; }
      if (!response.ok) throw new Error('روزهای بیشتر بارگذاری نشد.');
      const html = await response.text();
      if (!html.trim()) {
        finished[direction] = true;
        observer.unobserve(edge);
        edge.classList.add('path-sentinel--end');
        edge.textContent = direction === 'before' ? 'اینجا شروع مسیر توست' : 'مأموریت‌های بعدی به‌زودی';
        return;
      }
      const previous = document.documentElement.scrollHeight;
      days.insertAdjacentHTML(direction === 'before' ? 'afterbegin' : 'beforeend', html);
      if (direction === 'before') scrollBy(0, document.documentElement.scrollHeight - previous);
    } catch (error) { flash(error instanceof TypeError ? 'ارتباط برقرار نشد. اینترنتت را بررسی کن و دوباره تلاش کن.' : error.message); }
    finally { loading[direction] = false; edge.classList.remove('path-sentinel--loading'); edge.removeAttribute('role'); edge.removeAttribute('aria-label'); }
  }
  const observer = new IntersectionObserver(entries => { for (const entry of entries) if (entry.isIntersecting) load(entry.target.id === 'path-top' ? 'before' : 'after'); }, { rootMargin: '200px' });
  observer.observe(document.getElementById('path-top'));
  observer.observe(document.getElementById('path-bottom'));
}
