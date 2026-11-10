/* =====================================================================
   Cursor spotlight for cards  (Chamunda Cab)
   - Works on any element with .golden-glow-card (or .glow-card).
   - Injects <div class="glow-spot"> on first hover, so it also covers cards
     that are rendered later by JS (fleet) and cloned carousel slides.
   - Writes --mx / --my (px, relative to the card) once per animation frame.
   - Desktop pointers only; disabled for touch and prefers-reduced-motion.
   ===================================================================== */
(function () {
  'use strict';
  if (!window.matchMedia) return;
  if (!matchMedia('(hover:hover) and (pointer:fine)').matches) return;
  if (matchMedia('(prefers-reduced-motion:reduce)').matches) return;

  var SEL = '.golden-glow-card, .glow-card';
  var card = null, px = 0, py = 0, raf = 0;

  function getSpot(c) {
    var s = c.querySelector(':scope > .glow-spot');
    if (!s) {
      s = document.createElement('div');
      s.className = 'glow-spot';
      s.setAttribute('aria-hidden', 'true');
      s.style.opacity = '0';           // start hidden so the first hover still fades in
      c.insertBefore(s, c.firstChild);
      void s.offsetWidth;              // commit opacity:0, then let CSS (:hover) take over
      s.style.opacity = '';
    }
    return s;
  }

  function paint() {
    raf = 0;
    if (!card) return;
    var r = card.getBoundingClientRect();           // one read, then two writes
    card.style.setProperty('--mx', (px - r.left).toFixed(1) + 'px');
    card.style.setProperty('--my', (py - r.top).toFixed(1) + 'px');
  }

  document.addEventListener('mousemove', function (e) {
    var c = e.target.closest ? e.target.closest(SEL) : null;
    if (c !== card) { card = c; if (c) getSpot(c); }
    if (!c) return;
    px = e.clientX; py = e.clientY;
    if (!raf) raf = requestAnimationFrame(paint);
  }, { passive: true });

  document.addEventListener('mouseleave', function () { card = null; }, { passive: true });
})();
