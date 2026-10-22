/* =====================================================================
   LIVE CUSTOMER REVIEWS  -  ultra-compact horizontal slider (homepage)
   Vanilla JS, no dependencies. Loaded with <script src="reviews.js" defer>.

   What it does
   - Single-row, fixed-height slider (CSS scroll-snap): touch swipe on phones,
     mouse drag on desktop, left/right arrow buttons, arrow keys
   - AUTO-SCROLL: advances one card every 4 s; pauses on hover / keyboard focus /
     open dialogs / hidden tab / off-screen; any arrow click resets the 4 s timer
   - INFINITE LOOP: after the last card it glides on to the first one (and the left
     arrow wraps from the first card to the last) with no visible rewind
   - "Write a Review" modal (native <dialog>) with validation + spam guards
   - A new review is PREPENDED to the front of the slider and glides into view
   - Header rating + review count are recalculated from the cards in the slider
   - Long reviews are clamped to 3 lines (so every card has the same height);
     a "Read more" link opens the full text in a dialog
   - Visitor reviews are kept in this browser (localStorage) so they survive reload
   - Optional: POST every new review to YOUR endpoint (see REVIEW_ENDPOINT)

   SEO note: the reviews + JSON-LD that Google reads are the ones written into
   the HTML. Reviews submitted by visitors are NOT added to the JSON-LD
   automatically - that keeps unmoderated text out of your structured data.
   ===================================================================== */
(function () {
  'use strict';

  /* ----- Settings you can change ----- */
  var REVIEW_ENDPOINT = '';      // e.g. a Formspree / Google Apps Script / your own API URL. Leave '' to keep reviews local only.
  var AUTO_MS         = 4000;    // auto-scroll interval (milliseconds)
  var STORAGE_KEY     = 'cc_reviews_v1';
  var MAX_LOCAL       = 50;      // max reviews remembered per browser
  var BASE_RATING     = 4.9;     // published average shown in the badge + JSON-LD (the 6 hardcoded cards)
  var THEMES          = 6;       // number of card colour themes (gold / cyan / mint / pink / violet / orange) - see data-theme in style.css
  var COOLDOWN_MS     = 60000;   // one submission per minute per browser

  var root = document.getElementById('reviews');
  if (!root) return;

  var track     = root.querySelector('.rv-track');
  var slider    = root.querySelector('.rv-slider');
  var prevBtn   = root.querySelector('[data-rv-prev]');
  var nextBtn   = root.querySelector('[data-rv-next]');
  var bar       = root.querySelector('.rv-progress');
  var barThumb  = bar ? bar.querySelector('span') : null;
  var openBtns  = root.querySelectorAll('[data-rv-open]');
  var dialog    = root.querySelector('.rv-modal:not(.rv-read)');
  var readDlg   = root.querySelector('.rv-read');
  var form      = root.querySelector('.rv-form');
  var toast     = root.querySelector('.rv-toast');
  var ratingBox = root.querySelector('.rv-rating');
  var avgEl     = root.querySelector('.rv-avg');
  var countEl   = root.querySelector('.rv-count-n');
  var countLbl  = root.querySelector('.rv-count-l');
  var rateText  = root.querySelector('.rv-rate-text');
  var commentEl = form.elements.comment;
  var counterEl = root.querySelector('.rv-counter');

  var toastTimer = null;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var SMOOTH = reduceMotion ? 'auto' : 'smooth';
  var SVG_NS = 'http://www.w3.org/2000/svg';

  /* ---------- helpers ---------- */
  function cards() { return Array.prototype.slice.call(track.querySelectorAll('.rv-card:not(.rv-clone)')); }
  function ratingOf(card) { return parseInt(card.getAttribute('data-rating'), 10) || 0; }

  function clean(str, max) {
    // strip control chars, collapse whitespace, cap length
    return String(str || '').replace(/[\u0000-\u001F\u007F]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max);
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;   // textContent => user text can never inject HTML
    return n;
  }

  function makeStars(n) {
    var wrap = el('span', 'rv-stars');
    wrap.setAttribute('role', 'img');
    wrap.setAttribute('aria-label', n + ' out of 5 stars');
    for (var i = 1; i <= 5; i++) {
      var svg = document.createElementNS(SVG_NS, 'svg');
      svg.setAttribute('aria-hidden', 'true');
      if (i > n) svg.setAttribute('class', 'rv-off');
      var use = document.createElementNS(SVG_NS, 'use');
      use.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#rv-star');
      use.setAttribute('href', '#rv-star');
      svg.appendChild(use);
      wrap.appendChild(svg);
    }
    return wrap;
  }

  function initials(name) {
    var parts = name.split(' ').filter(Boolean);
    var s = (parts[0] ? parts[0].charAt(0) : '') + (parts[1] ? parts[1].charAt(0) : '');
    return (s || '?').toUpperCase();
  }

  function today() {
    var d = new Date();
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }

  function fmtDate(iso) {
    try {
      return new Date(iso + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch (e) { return iso; }
  }

  // next colour theme in the 1 > 2 > ... > 6 > 1 cycle, always different from the card it will sit next to
  function nextTheme() {
    var first = track.querySelector('.rv-card:not(.rv-clone)');
    var t = first ? parseInt(first.getAttribute('data-theme'), 10) || 0 : 0;
    return (t % THEMES) + 1;
  }

  /* ---------- build one review card (used for visitor-submitted reviews) ---------- */
  function buildCard(r, isNew) {
    var li = el('li', 'rv-card' + (isNew ? ' rv-card--new' : ''));
    li.setAttribute('data-rating', r.rating);
    li.setAttribute('data-source', 'local');
    li.setAttribute('data-theme', String(r.theme >= 1 && r.theme <= THEMES ? r.theme : 1));

    var row = el('div', 'rv-rate-row');
    row.appendChild(makeStars(r.rating));
    var time = el('time', 'rv-date', fmtDate(r.date));
    time.setAttribute('datetime', r.date);
    row.appendChild(time);

    var body = el('p', 'rv-body', r.comment);

    var top = el('div', 'rv-top');
    var av = el('div', 'rv-avatar', initials(r.name));
    av.setAttribute('aria-hidden', 'true');
    var who = el('div', 'rv-who');
    var name = el('cite', 'rv-name');
    name.appendChild(document.createTextNode(r.name + ' '));
    name.appendChild(el('span', 'rv-badge rv-badge--new', isNew ? 'Just now' : 'Your review'));
    who.appendChild(name);
    who.appendChild(el('div', 'rv-route', r.route));
    top.appendChild(av);
    top.appendChild(who);

    li.appendChild(row);
    li.appendChild(body);
    li.appendChild(top);
    ensureReadMore(li);
    return li;
  }

  /* ---------- "Read more": cards are a fixed height, so long text is clamped ---------- */
  function ensureReadMore(card) {
    if (card.querySelector('.rv-readmore')) return;
    var body = card.querySelector('.rv-body');
    if (!body) return;
    var btn = el('button', 'rv-readmore', 'Read more');
    btn.type = 'button';
    btn.setAttribute('aria-haspopup', 'dialog');
    body.parentNode.insertBefore(btn, body.nextSibling);
  }

  function markTruncation(card) {
    var body = card.querySelector('.rv-body');
    if (!body) return;
    // line-clamped box: scrollHeight is the full text, clientHeight is the 3 visible lines
    card.classList.toggle('is-trunc', body.scrollHeight > body.clientHeight + 1);
  }

  function markAll() { cards().forEach(markTruncation); }

  var resizeTimer = null;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(refresh, 150);
  });

  // re-measure truncation, rebuild the loop copies (the number of cards per view may have changed), redraw arrows/progress
  function refresh() { markAll(); rebuildClones(); updateNav(); }

  /* ---------- slider: step size, arrows, progress bar ---------- */
  function step() {
    var c = track.querySelector('.rv-card');
    if (!c) return 0;
    var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    return c.getBoundingClientRect().width + gap;
  }

  function maxScroll() { return Math.max(0, track.scrollWidth - track.clientWidth); }

  function scrollToLeft(left) {
    track.scrollTo({ left: Math.min(Math.max(0, left), maxScroll()), behavior: SMOOTH });
  }
  function scrollToIndex(i) {
    var s = step();
    if (s) scrollToLeft(i * s);
  }

  /* ---------- infinite loop ----------
     The first few cards are copied to the END of the track (class .rv-clone, hidden from
     screen readers and not clickable). Sliding "next" from the last real card lands on those
     copies, which look exactly like the start. Once the slide has settled we silently jump back
     to the real first card, so the visitor never sees a rewind. "Previous" on the first card
     does the same trick in reverse. */
  var looping = false;
  var touching = false;                 // a finger is on the slider (touch devices)

  function loopWidth() { return cards().length * step(); }

  function jumpTo(left) {               // instant, invisible reposition (no smooth animation)
    track.classList.add('is-jump');
    track.scrollLeft = left;
    void track.offsetWidth;             // flush layout before animation is switched back on
    track.classList.remove('is-jump');
  }

  function normalize() {                // standing on the copies? -> hop to the identical real cards
    if (!looping) return;
    var lw = loopWidth();
    if (track.scrollLeft >= lw - 2) jumpTo(track.scrollLeft - lw);
  }

  function rebuildClones() {
    normalize();
    Array.prototype.slice.call(track.querySelectorAll('.rv-clone')).forEach(function (c) { track.removeChild(c); });
    looping = false;
    var real = cards(), s = step();
    if (!s || real.length < 2) return;
    var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    if (real.length * s - gap <= track.clientWidth + 2) return;      // everything already fits: nothing to scroll or loop
    var per = parseFloat(getComputedStyle(track).getPropertyValue('--per')) || 1;
    var need = Math.min(real.length, Math.ceil(per));                // enough copies to fill the last view
    for (var i = 0; i < need; i++) {
      var c = real[i].cloneNode(true);
      c.classList.add('rv-clone');
      c.setAttribute('aria-hidden', 'true');
      c.setAttribute('inert', '');
      c.style.animation = 'none';                                    // never replay the "new review" animation on a copy
      track.appendChild(c);
    }
    looping = true;
  }

  function drawBar(thumbW, progress) {
    if (!bar || !barThumb) return;
    bar.classList.remove('is-hidden');
    barThumb.style.width = (thumbW * 100) + '%';
    barThumb.style.transform = 'translateX(' + (bar.clientWidth * (1 - thumbW) * progress) + 'px)';
  }

  var navQueued = false;
  function updateNav() {
    navQueued = false;
    var x = track.scrollLeft;
    if (looping) {                                                   // endless: arrows are never disabled
      if (prevBtn) prevBtn.disabled = false;
      if (nextBtn) nextBtn.disabled = false;
      var s = step(), n = cards().length, span = (n - 1) * s;
      drawBar(Math.max(Math.min(1, track.clientWidth / (n * s)), 0.08), span > 0 ? Math.min(1, Math.max(0, x / span)) : 0);
      return;
    }
    var max = maxScroll();
    if (prevBtn) prevBtn.disabled = x <= 2;
    if (nextBtn) nextBtn.disabled = x >= max - 2;
    if (bar && barThumb) {
      if (max > 2) drawBar(Math.max(track.clientWidth / track.scrollWidth, 0.08), x / max);
      else bar.classList.add('is-hidden');
    }
  }
  function queueNav() {
    if (navQueued) return;
    navQueued = true;
    requestAnimationFrame(updateNav);
  }

  /* One step left (-1) or right (+1). fromTimer=true when called by the auto-scroll. */
  function go(dir, fromTimer) {
    var s = step();
    if (!s) return;
    if (!fromTimer) resetAuto();                                     // a manual click restarts the 4 s countdown
    if (!looping) { scrollToIndex(Math.round(track.scrollLeft / s) + dir); return; }
    normalize();
    var idx = Math.round(track.scrollLeft / s);
    if (dir < 0 && idx <= 0) { jumpTo(loopWidth()); idx = cards().length; }   // wrap backwards: start on the copy of card 1
    scrollToIndex(idx + dir);
  }

  // once a slide has settled, hop off the copies (debounced: scroll events stream while it animates)
  var settleTimer = null;
  function settle() {
    if (touching || (drag && drag.moved)) return;
    normalize();
  }
  track.addEventListener('scroll', function () {
    queueNav();
    clearTimeout(settleTimer);
    settleTimer = setTimeout(settle, 120);
  }, { passive: true });
  if (prevBtn) prevBtn.addEventListener('click', function () { go(-1); });
  if (nextBtn) nextBtn.addEventListener('click', function () { go(1); });

  // keyboard: left / right arrows while the slider has focus
  track.addEventListener('keydown', function (e) {
    if (e.target !== track) return;                  // don't hijack keys while a "Read more" button is focused
    if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
    else if (e.key === 'Home') { e.preventDefault(); resetAuto(); scrollToIndex(0); }
    else if (e.key === 'End') { e.preventDefault(); resetAuto(); scrollToIndex(cards().length - 1); }
  });

  /* ---------- mouse drag-to-scroll (touch already scrolls natively) ---------- */
  var drag = null;
  var suppressClick = false;

  track.addEventListener('pointerdown', function (e) {
    if (e.pointerType !== 'mouse' || e.button !== 0) return;
    drag = { x: e.clientX, left: track.scrollLeft, moved: false, id: e.pointerId };
  });
  track.addEventListener('pointermove', function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x;
    if (!drag.moved) {
      if (Math.abs(dx) < 6) return;                 // below threshold it is still a click
      drag.moved = true;
      track.classList.add('is-drag');                // disables snapping while dragging
      try { track.setPointerCapture(drag.id); } catch (err) { /* ignore */ }
    }
    track.scrollLeft = drag.left - dx;
  });
  function endDrag() {
    if (!drag) return;
    var moved = drag.moved;
    drag = null;
    if (!moved) return;
    track.classList.remove('is-drag');
    suppressClick = true;                            // the mouse-up after a drag must not "click" a button
    setTimeout(function () { suppressClick = false; }, 0);
    scrollToIndex(Math.round(track.scrollLeft / (step() || 1)));   // settle on the nearest card
    resetAuto();
  }
  track.addEventListener('pointerup', endDrag);
  track.addEventListener('pointercancel', endDrag);
  track.addEventListener('click', function (e) {
    if (suppressClick) { e.preventDefault(); e.stopPropagation(); }
  }, true);
  track.addEventListener('dragstart', function (e) { e.preventDefault(); });

  /* ---------- AUTO-SCROLL ----------
     One setInterval ticks every AUTO_MS. A tick only moves the slider when nothing is
     "holding" it: mouse hovering the cards, keyboard focus inside the slider, a finger on it,
     a drag in progress, an open dialog, a hidden tab or the slider being scrolled out of view.
     resetAuto() restarts the full countdown (used after arrow clicks, drags, leaving hover...). */
  var autoTimer = null;
  var hovering = false, focused = false, inView = true;

  function canAuto() {
    return looping && !hovering && !focused && !touching && !(drag && drag.moved) && inView &&
           !document.hidden && !(dialog && dialog.open) && !(readDlg && readDlg.open);
  }
  function stopAuto() { if (autoTimer) { clearInterval(autoTimer); autoTimer = null; } }
  function startAuto() {
    stopAuto();
    if (reduceMotion) return;                         // respect "reduce motion": no self-moving content
    autoTimer = setInterval(function () { if (canAuto()) go(1, true); }, AUTO_MS);
  }
  function resetAuto() { startAuto(); }

  // hover pause (mouse / pen only; touch has its own handlers below)
  slider.addEventListener('pointerenter', function (e) { if (e.pointerType !== 'touch') hovering = true; });
  slider.addEventListener('pointerleave', function (e) {
    if (e.pointerType === 'touch') return;
    hovering = false;
    resetAuto();                                      // resume with a fresh 4 s countdown
  });

  // keyboard focus pause (only real keyboard focus, so a mouse click on the track doesn't freeze it)
  slider.addEventListener('focusin', function (e) {
    var kb = true;
    try { kb = e.target.matches(':focus-visible'); } catch (err) { /* old browser: treat as keyboard */ }
    if (kb) focused = true;
  });
  slider.addEventListener('focusout', function () { focused = false; resetAuto(); });

  // touch: hold while a finger is down, resume after it lifts
  track.addEventListener('touchstart', function () { touching = true; }, { passive: true });
  function touchDone() { touching = false; resetAuto(); setTimeout(settle, 150); }
  track.addEventListener('touchend', touchDone, { passive: true });
  track.addEventListener('touchcancel', touchDone, { passive: true });
  track.addEventListener('wheel', resetAuto, { passive: true });   // trackpad / shift-wheel scrolling counts as interaction

  // pause while the tab is hidden or the slider is off-screen
  document.addEventListener('visibilitychange', function () { if (!document.hidden) resetAuto(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      var v = entries[0].isIntersecting;
      if (v && !inView) resetAuto();
      inView = v;
    }, { threshold: 0.25 }).observe(slider);
  }

  /* ---------- header rating + count (computed from the cards in the slider) ---------- */
  function updateSummary() {
    var all = cards();
    var total = all.length;
    // published cards count at BASE_RATING (4.9); each visitor review is blended in on top
    var pub = 0, sum = 0;
    all.forEach(function (c) {
      if (c.getAttribute('data-source') === 'published') { pub++; sum += BASE_RATING; }
      else sum += ratingOf(c);
    });
    var avg = total ? sum / total : 0;
    var avgTxt = total ? avg.toFixed(1) : '–';
    avgEl.textContent = avgTxt;
    countEl.textContent = total;
    if (countLbl) countLbl.textContent = total === 1 ? 'review' : 'reviews';
    if (ratingBox) ratingBox.setAttribute('aria-label', total
      ? 'Rated ' + avgTxt + ' out of 5 from ' + total + (total === 1 ? ' review' : ' reviews')
      : 'No reviews yet');
  }

  /* ---------- local persistence ---------- */
  function loadLocal() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) { return []; }
  }
  function saveLocal(arr) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(arr.slice(0, MAX_LOCAL))); } catch (e) { /* private mode etc. */ }
  }
  function lastSubmitAt() {
    try { return parseInt(localStorage.getItem(STORAGE_KEY + '_t'), 10) || 0; } catch (e) { return 0; }
  }
  function markSubmit() {
    try { localStorage.setItem(STORAGE_KEY + '_t', String(Date.now())); } catch (e) { /* ignore */ }
  }

  // give the published cards their "Read more" button
  cards().forEach(ensureReadMore);

  // restore this visitor's earlier reviews (newest first, at the front of the slider)
  loadLocal().slice().reverse().forEach(function (r) {
    if (!r || !r.name || !r.comment || !(r.rating >= 1 && r.rating <= 5)) return;
    track.insertBefore(buildCard({
      name: clean(r.name, 60), route: clean(r.route, 80), rating: r.rating,
      comment: clean(r.comment, 600), date: /^\d{4}-\d{2}-\d{2}$/.test(r.date) ? r.date : today(),
      theme: r.theme || nextTheme()
    }, false), track.firstChild);
  });

  /* ---------- LIVE INSERT: prepend a new card and glide to it ---------- */
  function prependCard(card) {
    normalize();                                     // not standing on the loop copies while we insert
    var before = track.scrollLeft;
    track.classList.add('is-jump');                  // instant, invisible reposition ...
    track.insertBefore(card, track.firstChild);
    track.scrollLeft = before + step();              // ... so the current view does not jump
    void track.offsetWidth;                          // flush layout
    track.classList.remove('is-jump');
    markTruncation(card);
    rebuildClones();                                 // the copies at the end must now start with the NEW card
    track.scrollTo({ left: 0, behavior: SMOOTH });   // ... then animate to the new card at the front
    updateNav();
    resetAuto();
  }

  /* ---------- toast ---------- */
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('rv-show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('rv-show'); }, 4200);
  }

  /* ---------- dialogs (native <dialog>) ---------- */
  var lastOpener = null;
  function openDlg(d, opener) {
    lastOpener = opener || null;
    if (typeof d.showModal === 'function') d.showModal(); else d.setAttribute('open', '');
  }
  function closeDlg(d) {
    if (typeof d.close === 'function') d.close(); else d.removeAttribute('open');
  }
  [dialog, readDlg].forEach(function (d) {
    if (!d) return;
    d.addEventListener('close', function () {
      if (lastOpener && document.contains(lastOpener)) lastOpener.focus();
      resetAuto();
    });
    // click on the dark backdrop closes the dialog
    d.addEventListener('click', function (e) { if (e.target === d) closeDlg(d); });
    d.querySelectorAll('[data-rv-close]').forEach(function (b) {
      b.addEventListener('click', function () { closeDlg(d); });
    });
  });

  openBtns.forEach(function (b) {
    b.addEventListener('click', function (e) {
      openDlg(dialog, e.currentTarget);
      var first = form.elements.name;
      if (first) setTimeout(function () { first.focus(); }, 30);
    });
  });

  /* "Read more" -> full review dialog (event delegation: also works for cards added later) */
  track.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.rv-readmore') : null;
    if (!btn || !readDlg) return;
    var card = btn.closest('.rv-card');
    if (!card) return;
    var rateBox = readDlg.querySelector('.rv-read-rate');
    var whoBox  = readDlg.querySelector('.rv-read-who');
    rateBox.textContent = '';
    whoBox.textContent = '';
    var row = card.querySelector('.rv-rate-row');
    var top = card.querySelector('.rv-top');
    if (row) { Array.prototype.forEach.call(row.children, function (n) { rateBox.appendChild(n.cloneNode(true)); }); }
    if (top) { var t = top.cloneNode(true); whoBox.appendChild(t); }
    readDlg.querySelector('.rv-read-body').textContent = card.querySelector('.rv-body').textContent;
    openDlg(readDlg, btn);
  });

  /* live star label + character counter */
  var LABELS = { 1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very good', 5: 'Excellent' };
  form.querySelectorAll('input[name="rating"]').forEach(function (r) {
    r.addEventListener('change', function () {
      rateText.textContent = LABELS[r.value] || '';
      setInvalid('rating', false);
    });
  });
  commentEl.addEventListener('input', function () { counterEl.textContent = commentEl.value.length + ' / 600'; });

  function setInvalid(field, bad) {
    var box = form.querySelector('[data-field="' + field + '"]');
    if (box) box.classList.toggle('rv-invalid', !!bad);
  }

  /* ---------- submit ---------- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // spam guard 1: hidden field real people never fill
    if (form.elements.website && form.elements.website.value) { closeDlg(dialog); return; }

    var name    = clean(form.elements.name.value, 60);
    var route   = clean(form.elements.route.value, 80);
    var comment = clean(commentEl.value, 600);
    var checked = form.querySelector('input[name="rating"]:checked');
    var rating  = checked ? parseInt(checked.value, 10) : 0;

    var okName = name.length >= 2;
    var okRoute = route.length >= 3;
    var okRating = rating >= 1 && rating <= 5;
    var okComment = comment.length >= 10;
    setInvalid('name', !okName);
    setInvalid('route', !okRoute);
    setInvalid('rating', !okRating);
    setInvalid('comment', !okComment);
    if (!(okName && okRoute && okRating && okComment)) {
      var firstBad = form.querySelector('.rv-invalid input, .rv-invalid textarea');
      if (firstBad) firstBad.focus();
      return;
    }

    // spam guard 2: one review per minute per browser
    var wait = COOLDOWN_MS - (Date.now() - lastSubmitAt());
    if (wait > 0) { showToast('Please wait ' + Math.ceil(wait / 1000) + ' seconds before posting another review.'); return; }

    var review = { name: name, route: route, rating: rating, comment: comment, date: today(), theme: nextTheme() };

    // 1) show it instantly at the FRONT of the slider
    prependCard(buildCard(review, true));
    updateSummary();

    // 2) remember it in this browser
    var saved = loadLocal();
    saved.unshift(review);
    saveLocal(saved);
    markSubmit();

    // 3) optionally send it to your server for moderation
    if (REVIEW_ENDPOINT) {
      try {
        fetch(REVIEW_ENDPOINT, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, keepalive: true,
          body: JSON.stringify({ name: name, route: route, rating: rating, comment: comment, page: location.href, submittedAt: new Date().toISOString() })
        }).catch(function () { /* review is still shown locally */ });
      } catch (err) { /* ignore */ }
    }

    // 4) tidy up
    form.reset();
    rateText.textContent = '';
    counterEl.textContent = '0 / 600';
    lastOpener = null;                                // don't pull focus back to the button; the user wants to see the card
    closeDlg(dialog);
    showToast('Thank you! Your review is now live.');
    // bring the slider into view if the form was opened while it was off-screen
    var r = root.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) {
      root.scrollIntoView({ block: 'center', behavior: SMOOTH });
    }
  });

  /* ---------- init ---------- */
  updateSummary();
  refresh();
  startAuto();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(refresh);              // text re-wraps once web fonts load
  }
  window.addEventListener('load', refresh);
})();
