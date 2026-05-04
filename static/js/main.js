// GeoComfortIQ — main.js

document.addEventListener('DOMContentLoaded', () => {

  // ── KPI bar animations on dashboard load ──────────────────────────────────
  document.querySelectorAll('.kpi-bar-fill').forEach(bar => {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = targetWidth; }, 200);
  });

  // ── Navbar active state ───────────────────────────────────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });

});
