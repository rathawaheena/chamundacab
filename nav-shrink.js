/* Shrinking sticky navbar: toggles .scrolled on .site-nav.
   Two thresholds (hysteresis) + requestAnimationFrame = no flicker near the trigger point. */
(function () {
  var nav = document.querySelector('.site-nav');
  if (!nav) return;
  var ON = 40, OFF = 10, ticking = false;

  function update() {
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    if (y > ON) nav.classList.add('scrolled');
    else if (y < OFF) nav.classList.remove('scrolled');
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  update();
})();
