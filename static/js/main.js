/* IT Travel — кичинекей интерактивдүүлүк (китепканасыз) */
(function () {
  "use strict";

  // --- Жүктөлбөй калган сүрөттүн ордуна заглушка (бөтөн сайттардын сүрөттөрү үчүн) ---
  const fallback = window.PLACEHOLDER_IMG;
  const useFallback = (img) => {
    if (!fallback || img.dataset.fallback) return;
    img.dataset.fallback = "1";
    img.classList.add("is-fallback");
    img.src = fallback;
  };
  document.addEventListener("error", (e) => {
    if (e.target && e.target.tagName === "IMG") useFallback(e.target);
  }, true);
  document.querySelectorAll("img").forEach((img) => {
    if (img.complete && img.naturalWidth === 0 && img.src) useFallback(img);
  });
  // Фон-сүрөттөр (баннерлер) үчүн да ошол эле текшерүү
  document.querySelectorAll(".banner[style*='background-image']").forEach((el) => {
    const m = /url\(['"]?([^'")]+)['"]?\)/.exec(el.style.backgroundImage);
    if (!m || !fallback) return;
    const probe = new Image();
    probe.onerror = () => { el.style.backgroundImage = `url('${fallback}')`; };
    probe.src = m[1];
  });

  // --- Караңгы / жарык тема (тандоо эсте калат) ---
  const root = document.documentElement;
  const themeBtn = document.getElementById("theme-toggle");
  const setIcon = () => {
    if (themeBtn) themeBtn.innerHTML = root.dataset.theme === "dark"
      ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
  };
  setIcon();
  themeBtn && themeBtn.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) { /* storage жок */ }
    setIcon();
  });

  // --- Мобилдик меню ---
  const burger = document.getElementById("burger");
  const nav = document.getElementById("nav");
  burger && burger.addEventListener("click", () => nav.classList.toggle("is-open"));

  // --- Билдирүүлөр (toast) өзү жабылат ---
  document.querySelectorAll(".toast").forEach((toast) => {
    const close = () => toast.remove();
    toast.querySelector(".toast__close").addEventListener("click", close);
    setTimeout(close, 6000);
  });

  // --- Ырастоо сураган формалар ---
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // --- Скроллдо пайда болуу анимациясы ---
  const revealItems = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("is-visible"); io.unobserve(entry.target); }
      });
    }, { threshold: 0.15 });
    revealItems.forEach((el) => io.observe(el));
  } else {
    revealItems.forEach((el) => el.classList.add("is-visible"));
  }

  // --- Галерея: сүрөттү чоңойтуп көрүү ---
  document.querySelectorAll("[data-lightbox] a").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const box = document.createElement("div");
      box.className = "lightbox";
      box.innerHTML = `<img src="${link.href}" alt="">`;
      const close = () => { box.remove(); document.removeEventListener("keydown", onKey); };
      const onKey = (ev) => { if (ev.key === "Escape") close(); };
      box.addEventListener("click", close);
      document.addEventListener("keydown", onKey);
      document.body.appendChild(box);
    });
  });

  // --- ♥ Сактоо: бетти жаңыртпай ---
  document.querySelectorAll("form[data-fav]").forEach((favForm) => {
    favForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = favForm.querySelector(".fav-btn");
      try {
        const res = await fetch(favForm.action, {
          method: "POST",
          body: new FormData(favForm),
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!res.ok) throw new Error(res.status);
        const { saved } = await res.json();
        btn.classList.toggle("is-active", saved);
        btn.setAttribute("aria-pressed", saved);
        btn.innerHTML = `<i class="fa-${saved ? "solid" : "regular"} fa-heart"></i>`;
      } catch (err) {
        favForm.submit(); // JS иштебесе — кадимки форма
      }
    });
  });

  // --- Брондоо: бааны серверден эсептеп көрсөтүү ---
  const form = document.getElementById("booking-form");
  const totalEl = document.getElementById("total-price");
  if (form && totalEl && form.dataset.priceUrl) {
    const fmt = new Intl.NumberFormat("ru-RU");
    let timer;
    const update = () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        const val = (name, def) => {
          const el = form.querySelector(`[name="${name}"]`);
          return el && el.value !== "" ? el.value : def;
        };
        const params = new URLSearchParams({
          adults: val("adults", 1), children: val("children", 0), hotel: val("hotel", ""),
          promo_code: val("promo_code", ""),
        });
        try {
          const res = await fetch(`${form.dataset.priceUrl}?${params}`);
          if (!res.ok) return;
          const data = await res.json();
          totalEl.textContent = fmt.format(data.total);
          const row = document.getElementById("discount-row");
          if (row) {
            row.hidden = !data.discount;
            document.getElementById("discount-value").textContent = fmt.format(data.discount);
          }
        } catch (e) { /* тармак катасы — эски баа калат */ }
      }, 200);
    };
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    update();
  }
})();
