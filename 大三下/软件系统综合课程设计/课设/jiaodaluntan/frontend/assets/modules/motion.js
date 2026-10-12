// Product motion layer powered by the npm anime.js package bundled by Vite.
// Keep effects short and transform-based so the forum feels responsive.

const MOTION_QUERY = "(prefers-reduced-motion: reduce)";
let installed = false;
let scrollFrame = 0;
let lastScrollY = 0;
let animeLoader = null;
let feedRevealObserver = null;
let transitioning = false;

function hasDom() {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

function reducedMotion() {
  if (!hasDom()) {
    return true;
  }
  return window.matchMedia?.(MOTION_QUERY).matches ?? false;
}

async function loadAnime() {
  if (!hasDom()) {
    return null;
  }
  if (!animeLoader) {
    animeLoader = import("animejs");
  }
  return animeLoader;
}

function cleanTargetList(nodes, limit = 16) {
  const seen = new Set();
  return Array.from(nodes)
    .filter((node) => {
      if (!node || seen.has(node)) {
        return false;
      }
      seen.add(node);
      return true;
    })
    .slice(0, limit);
}

function isVisibleElement(node) {
  if (!(node instanceof Element)) {
    return false;
  }
  const rect = node.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}

function numericText(value) {
  const text = String(value || "").replace(/[^\d.-]/g, "");
  const number = Number(text);
  return Number.isFinite(number) ? number : null;
}

async function addRipple(target, event) {
  if (!target || target.querySelector(":scope > .motion-ripple")) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  const rect = target.getBoundingClientRect();
  const ripple = document.createElement("span");
  const size = Math.max(rect.width, rect.height) * 1.4;
  ripple.className = "motion-ripple";
  ripple.style.width = `${size}px`;
  ripple.style.height = `${size}px`;
  ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
  ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
  target.appendChild(ripple);
  anime.animate(ripple, {
    scale: [0, 1],
    opacity: [0.22, 0],
    duration: 420,
    ease: "out(3)"
  }).then(() => ripple.remove());
}

function bindPressFeedback() {
  document.addEventListener("pointerdown", async (event) => {
    if (reducedMotion()) {
      return;
    }
    const target = event.target instanceof Element
      ? event.target.closest(".button, .icon-btn, .stat-chip--like, a.tag, .rank-item")
      : null;
    if (!target || target.matches(":disabled") || target.getAttribute("aria-disabled") === "true") {
      return;
    }
    if (target.matches("[data-like-post], [data-favorite]")) {
      return;
    }
    target.classList.add("is-pressing");
    const anime = await loadAnime();
    if (!anime) {
      return;
    }
    anime.animate(target, {
      scale: [0.985, 1],
      duration: 180,
      ease: "out(3)"
    }).then(() => target.classList.remove("is-pressing"));
    if (target.matches(".button, .icon-btn")) {
      addRipple(target, event);
    }
  }, { passive: true });
}

function bindBusinessFeedback() {
  document.addEventListener("click", (event) => {
    if (reducedMotion()) {
      return;
    }
    const target = event.target instanceof Element
      ? event.target.closest("[data-like-post], [data-favorite], [data-check-in], [data-accept-comment], [data-cancel-accept]")
      : null;
    if (!target || target.matches(":disabled") || target.dataset.requesting === "1" || target.getAttribute("aria-busy") === "true") {
      return;
    }
    if (target.matches("[data-like-post], [data-favorite]")) {
      return;
    }
    if (target.matches("[data-check-in]")) {
      floatPoints(target, "+2");
    } else {
      likeBurst(target);
    }
  });
}

function bindTopbarState() {
  const update = () => {
    scrollFrame = 0;
    const currentY = Math.max(0, window.scrollY || 0);
    const topbar = document.querySelector(".topbar");
    const focusedInTopbar = topbar?.contains(document.activeElement);
    const scrollingDown = currentY > lastScrollY + 6;
    const scrollingUp = currentY < lastScrollY - 6;

    document.body.classList.toggle("is-scrolled", currentY > 8);
    document.body.classList.toggle("topbar-compact", currentY > 48);

    if (focusedInTopbar || scrollingUp || currentY < 96) {
      document.body.classList.remove("topbar-hidden");
    } else if (scrollingDown && currentY > 150) {
      document.body.classList.add("topbar-hidden");
    }

    lastScrollY = currentY;
  };
  lastScrollY = Math.max(0, window.scrollY || 0);
  update();
  window.addEventListener("scroll", () => {
    if (!scrollFrame) {
      scrollFrame = requestAnimationFrame(update);
    }
  }, { passive: true });
}

// --- MPA page transitions ---
// Intercept internal link clicks, fade-out the page shell, then navigate.
function bindPageTransitions() {
  if (reducedMotion()) {
    return;
  }

  document.addEventListener("click", (event) => {
    // Only handle primary button, no modifier keys
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    if (event.defaultPrevented) {
      return;
    }

    const anchor = event.target instanceof Element
      ? event.target.closest("a[href]")
      : null;
    if (!anchor) {
      return;
    }
    if (anchor.closest(".admin-dense-shell")) {
      return;
    }

    // Skip non-navigation links
    const href = anchor.getAttribute("href") || "";
    if (!href || href.startsWith("#") || href.startsWith("javascript:") || href.startsWith("mailto:")) {
      return;
    }

    // Skip links that open in new tab or are external
    if (anchor.target === "_blank") {
      return;
    }

    // Skip if same page (just hash change)
    const targetUrl = new URL(href, location.href);
    if (targetUrl.origin !== location.origin) {
      return;
    }
    if (targetUrl.pathname === location.pathname && targetUrl.search === location.search) {
      return;
    }

    // Skip logout buttons
    if (anchor.hasAttribute("data-logout")) {
      return;
    }

    // Prevent default and play transition
    event.preventDefault();
    playPageOut(targetUrl.href);
  }, { capture: true });
}

async function playPageOut(targetUrl) {
  if (transitioning) {
    return;
  }
  transitioning = true;

  const shell = document.querySelector(".page-shell");
  if (!shell) {
    location.href = targetUrl;
    return;
  }

  const anime = await loadAnime();
  if (!anime) {
    location.href = targetUrl;
    return;
  }

  // Show loading bar
  const bar = document.createElement("div");
  bar.className = "page-loading-bar";
  document.body.appendChild(bar);
  requestAnimationFrame(() => bar.classList.add("is-loading"));

  // Fade out the page shell with a smooth downward exit
  const anim = anime.animate(shell, {
    opacity: [1, 0],
    y: [0, -16],
    duration: 220,
    ease: "in(2)"
  });

  await anim.finished;
  location.href = targetUrl;
}

export function resetPageTransitionState() {
  if (!hasDom()) {
    return;
  }
  transitioning = false;
  document.querySelectorAll(".page-loading-bar").forEach((node) => node.remove());
  const shell = document.querySelector(".page-shell");
  if (shell instanceof HTMLElement) {
    shell.style.opacity = "";
    shell.style.transform = "";
    shell.style.translate = "";
  }
  document.documentElement.classList.add("app-ready");
}

export function installMotionSystem() {
  if (installed || !hasDom()) {
    return;
  }
  installed = true;
  document.documentElement.classList.add("motion-ready");
  bindPressFeedback();
  bindBusinessFeedback();
  bindTopbarState();
  bindPageTransitions();
  window.addEventListener("pageshow", resetPageTransitionState);
}

export function applyChromeMotion(root = document) {
  if (reducedMotion()) {
    return;
  }
  const appbar = root.querySelector?.(".appbar");
  if (!appbar) {
    return;
  }
  loadAnime().then((anime) => {
    if (!anime) {
      return;
    }
    anime.animate(appbar, {
      opacity: [0.001, 1],
      y: [-8, 0],
      duration: 260,
      ease: "out(3)"
    });
  });
}

export function applyPageMotion(root = document.querySelector("main")) {
  if (!root || reducedMotion()) {
    return;
  }
  loadAnime().then((anime) => {
    if (!anime) {
      return;
    }

    // Page shell entrance — smooth fade-in with upward slide
    const shell = document.querySelector(".page-shell");
    if (shell) {
      anime.animate(shell, {
        opacity: [0, 1],
        y: [18, 0],
        duration: 320,
        ease: "out(4)"
      });
    }

    const lead = cleanTargetList(root.querySelectorAll(".page-head, .hero, .surface-section, .band"), 4);
    if (lead.length) {
      anime.animate(lead, {
        opacity: [0.001, 1],
        y: [20, 0],
        filter: ["blur(8px)", "blur(0px)"],
        duration: 420,
        delay: anime.stagger(50, { start: 80 }),
        ease: "out(4)"
      });
    }

    const cards = cleanTargetList(root.querySelectorAll(".post-card:not([data-feed-reveal]), .comment-card, .metric-card, .card:not(.post-card)"), 18);
    if (cards.length) {
      anime.animate(cards, {
        opacity: [0.001, 1],
        y: [16, 0],
        duration: 380,
        delay: anime.stagger(32, { start: 120 }),
        ease: "out(4)"
      });
    }

    const smallItems = cleanTargetList(root.querySelectorAll(".rank-item, .section-chips .tag, .inline-tags .tag"), 24);
    if (smallItems.length) {
      anime.animate(smallItems, {
        opacity: [0.001, 1],
        y: [8, 0],
        duration: 280,
        delay: anime.stagger(20, { start: 160 }),
        ease: "out(3)"
      });
    }

    animateWordCloud(anime, root);
    installFeedReveal(root);
    animateEmptyStates(anime, root);
    countUpNumbers(root);
    heatBarsEnter(root);
  });
}

function installFeedReveal(root) {
  if (!hasDom() || reducedMotion()) {
    return;
  }
  const cards = Array.from(root.querySelectorAll?.(".post-card") || [])
    .filter((card) => !card.dataset.feedReveal);
  if (!cards.length) {
    return;
  }
  cards.forEach((card, index) => {
    card.dataset.feedReveal = "pending";
    card.style.setProperty("--feed-reveal-delay", `${Math.min(index, 8) * 46}ms`);
  });

  if (!("IntersectionObserver" in window)) {
    cards.forEach((card) => {
      card.dataset.feedReveal = "visible";
    });
    return;
  }

  if (!feedRevealObserver) {
    feedRevealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        entry.target.dataset.feedReveal = "visible";
        feedRevealObserver.unobserve(entry.target);
      });
    }, {
      rootMargin: "0px 0px -10% 0px",
      threshold: 0.14
    });
  }

  cards.forEach((card) => feedRevealObserver.observe(card));
}

function animateWordCloud(anime, root) {
  const words = cleanTargetList(root.querySelectorAll?.(".swjtu-word, .tag-cloud__chip") || [], 30);
  if (!words.length) {
    return;
  }
  anime.animate(words, {
    opacity: [0.001, 1],
    scale: [0.86, 1],
    y: [10, 0],
    duration: 520,
    delay: anime.stagger(28, { start: 220 }),
    ease: "out(4)"
  });
  anime.animate(words, {
    y: [-3, 3],
    duration: 1900,
    delay: anime.stagger(70),
    alternate: true,
    loop: true,
    ease: "inOut(2)"
  });
}

function animateEmptyStates(anime, root) {
  const emptyIcons = cleanTargetList(root.querySelectorAll?.(".empty-state__emoji, .badge-card__icon") || [], 8);
  if (!emptyIcons.length) {
    return;
  }
  anime.animate(emptyIcons, {
    y: [0, -6, 0],
    duration: 2200,
    delay: anime.stagger(120),
    loop: true,
    ease: "inOut(2)"
  });
}

export async function likeBurst(target) {
  if (!target || reducedMotion()) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  target.classList.add("motion-pop");
  anime.animate(target, {
    scale: [1, 1.08, 1],
    rotate: [0, -3, 0],
    duration: 260,
    ease: "out(4)"
  }).then(() => target.classList.remove("motion-pop"));

  const rect = target.getBoundingClientRect();
  const host = document.createElement("span");
  host.className = "motion-burst";
  host.style.left = `${rect.left + rect.width / 2}px`;
  host.style.top = `${rect.top + rect.height / 2}px`;
  document.body.appendChild(host);

  const particles = Array.from({ length: 7 }, (_, index) => {
    const particle = document.createElement("i");
    const angle = (Math.PI * 2 * index) / 7;
    particle.style.setProperty("--x", `${Math.cos(angle) * 28}px`);
    particle.style.setProperty("--y", `${Math.sin(angle) * 28}px`);
    host.appendChild(particle);
    return particle;
  });

  anime.animate(particles, {
    x: (_, i) => particles[i].style.getPropertyValue("--x"),
    y: (_, i) => particles[i].style.getPropertyValue("--y"),
    scale: [0.7, 1, 0.2],
    opacity: [0, 1, 0],
    duration: 520,
    delay: anime.stagger(18),
    ease: "out(4)"
  }).then(() => host.remove());
}

export async function floatPoints(target, text = "+2") {
  if (!target || reducedMotion()) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  const rect = target.getBoundingClientRect();
  const tip = document.createElement("div");
  tip.className = "float-points";
  tip.textContent = text;
  tip.style.left = `${rect.left + rect.width / 2}px`;
  tip.style.top = `${rect.top + 2}px`;
  document.body.appendChild(tip);
  anime.animate(tip, {
    opacity: [0, 1, 0],
    y: [0, -34],
    scale: [0.82, 1.04, 1],
    duration: 780,
    ease: "out(4)"
  }).then(() => tip.remove());
}

export async function commentEnter(target) {
  if (!target || reducedMotion()) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  anime.animate(target, {
    opacity: [0.001, 1],
    y: [18, 0],
    backgroundColor: ["rgba(0,117,184,.12)", "rgba(255,255,255,.92)"],
    duration: 420,
    ease: "out(4)"
  });
}

export async function publishFlowEnter(root = document) {
  if (!root || reducedMotion()) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  const steps = cleanTargetList(root.querySelectorAll?.(".publish-flow__step") || [], 4);
  const lines = cleanTargetList(root.querySelectorAll?.(".publish-flow__line") || [], 3);
  if (!steps.length) {
    return;
  }
  anime.animate(steps, {
    opacity: [0.001, 1],
    y: [12, 0],
    scale: [0.96, 1],
    duration: 320,
    delay: anime.stagger(80),
    ease: "out(4)"
  });
  if (lines.length) {
    anime.animate(lines, {
      scaleX: [0, 1],
      duration: 360,
      delay: anime.stagger(90, { start: 100 }),
      ease: "out(4)"
    });
  }
}

export async function countUpNumbers(root = document) {
  if (!root || reducedMotion()) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  const nodes = cleanTargetList(root.querySelectorAll?.("[data-count-up], .metric-card__value, .interaction-card strong") || [], 24)
    .filter(isVisibleElement)
    .filter((node) => !node.dataset.counted);
  nodes.forEach((node) => {
    if (!node.dataset.countUp && /[A-Za-z]/.test(String(node.textContent || ""))) {
      return;
    }
    const target = Number(node.dataset.countUp ?? numericText(node.textContent));
    if (!Number.isFinite(target)) {
      return;
    }
    node.dataset.counted = "true";
    const counter = { value: 0 };
    anime.animate(counter, {
      value: target,
      duration: 720,
      ease: "out(4)",
      onUpdate: () => {
        node.textContent = Math.round(counter.value).toLocaleString();
      }
    });
  });
}

export async function heatBarsEnter(root = document) {
  if (!root || reducedMotion()) {
    return;
  }
  const anime = await loadAnime();
  if (!anime) {
    return;
  }
  const bars = cleanTargetList(root.querySelectorAll?.(".dist-row__fill, .trend-bar__fill, .activity-column__fill, .progress span") || [], 28)
    .filter((node) => !node.dataset.motionFilled);
  bars.forEach((bar, index) => {
    const width = bar.style.width || getComputedStyle(bar).width;
    const height = bar.style.height || getComputedStyle(bar).height;
    bar.dataset.motionFilled = "true";
    if (bar.classList.contains("dist-row__fill") || bar.closest(".progress")) {
      anime.animate(bar, {
        scaleX: [0, 1],
        transformOrigin: "0 50%",
        duration: 520,
        delay: Math.min(index * 35, 420),
        ease: "out(4)"
      });
    } else {
      anime.animate(bar, {
        height: ["2px", height],
        duration: 560,
        delay: Math.min(index * 35, 420),
        ease: "out(4)"
      });
      bar.style.height = height;
    }
    if (width) {
      bar.style.width = width;
    }
  });
}

export function buttonLoading(button, text = "处理中") {
  if (!button || button.dataset.motionLoading === "true") {
    return;
  }
  button.dataset.motionLoading = "true";
  button.dataset.oldText = button.textContent || "";
  button.disabled = true;
  button.classList.add("is-loading");
  button.innerHTML = `${text}<span class="loading-dots" aria-hidden="true"><i></i><i></i><i></i></span>`;
  if (reducedMotion()) {
    return;
  }
  loadAnime().then((anime) => {
    if (!anime) {
      return;
    }
    anime.animate(button.querySelectorAll(".loading-dots i"), {
      y: [0, -4, 0],
      delay: anime.stagger(80),
      loop: true,
      duration: 520,
      ease: "inOut(2)"
    });
  });
}

export function buttonReset(button) {
  if (!button) {
    return;
  }
  button.disabled = false;
  button.classList.remove("is-loading");
  button.textContent = button.dataset.oldText || button.textContent || "";
  delete button.dataset.motionLoading;
  delete button.dataset.oldText;
}
