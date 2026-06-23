/* Progressive enhancement only — the store works without JS. */
(function () {
  "use strict";

  // Quantity steppers (product detail + cart lines).
  document.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-qty-step]");
    if (!btn) return;
    const wrap = btn.closest("[data-qty]");
    const input = wrap && wrap.querySelector("input");
    if (!input) return;

    const step = parseInt(btn.dataset.qtyStep, 10);
    const min = parseInt(input.min || "1", 10);
    const max = input.max ? parseInt(input.max, 10) : Infinity;
    let value = parseInt(input.value || "1", 10) + step;
    value = Math.max(min, Math.min(max, value));
    input.value = value;

    // Auto-submit cart line updates so the quantity persists immediately.
    if (wrap.dataset.autosubmit === "true") {
      const form = wrap.closest("form");
      if (form) form.requestSubmit();
    }
  });

  // Auto-dismiss flash messages.
  document.querySelectorAll(".alert").forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity .4s ease, transform .4s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-4px)";
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });
})();
