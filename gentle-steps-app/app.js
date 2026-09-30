const app = document.getElementById('app');
const toast = document.getElementById('toast');

const STORAGE_KEY = 'gentleStepsEnglish.v2';
const SOURCE_SHA = '1f79edd316f353963ef33bb980843b37f367a0bacb9198bd63e0d221cb8c9ba7';
const PACK_URLS = [
  './content/week-01.json',
  './content/week-02.json',
  './content/week-03.json',
  './content/week-04.json'
];

const FAMILY_ASSET = 'data:image/webp;base64,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';
const CHARACTER_ASSETS = {
  Mimi: '../assets/images/Mimi.png',
  Luli: '../assets/images/Luli.png',
  Dilo: '../assets/images/Dilo.png',
  Alio: '../assets/images/Alio.png',
  Nini: '../assets/images/Nini.png'
};

const FAMILY_PROFILES = [
  { name: 'Mimi', title: 'The Heart and Heroine', image: CHARACTER_ASSETS.Mimi },
  { name: 'Luli', title: 'The Elegant Detective of Holiday Magic', image: CHARACTER_ASSETS.Luli, motto: 'Life is a mystery best solved with style.' },
  { name: 'Dilo', title: 'The Striker With Holiday Swagger', image: CHARACTER_ASSETS.Dilo, motto: 'Glow bold, score big.' },
  { name: 'Alio', title: 'The Chief Holiday Chaos Engineer', image: CHARACTER_ASSETS.Alio, motto: 'Maximum fun, mostly safe...' },
  { name: 'Nini', title: 'The Pocket-Sized Joy Distributor', image: CHARACTER_ASSETS.Nini, motto: 'If it sparkles, she approves.' }
];

const params = new URLSearchParams(window.location.search);
const previewMode = params.get('preview') === '1';

let packs = [];
let days = [];
let currentDay = null;
let state = loadState();

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return {
      completed: Array.isArray(saved.completed)
        ? saved.completed.filter((value) => Number.isInteger(value) && value >= 1 && value <= 24)
        : []
    };
  } catch {
    return { completed: [] };
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2200);
}

function topbar() {
  return '<header class="topbar">' +
    '<div class="brand-lockup">' +
      '<div class="brand-mark" aria-hidden="true">✦</div>' +
      '<div class="brand-text"><strong>24 Gentle Steps to Christmas</strong><span>The Happy-Makers</span></div>' +
    '</div>' +
    '<div class="topbar-actions">' +
      '<button class="ghost-button ghost-button-family" type="button" data-family>Family</button>' +
      '<button class="ghost-button" type="button" data-about>How it works</button>' +
    '</div>' +
  '</header>';
}

function aboutDialog() {
  return '<dialog id="about-dialog">' +
    '<div class="about-sheet">' +
      '<h2>One day. Three shared moments.</h2>' +
      '<p class="about-lead">A Mindful Family Journey of Togetherness, Reflection &amp; the Magic of Christmas.</p>' +
      '<p>Created for real families, <strong>24 Gentle Steps to Christmas</strong> transforms just 10 minutes a day into calm, laughter and meaningful connection.</p>' +
      '<p><strong>No prep. No mess. No glitter required.</strong></p>' +
      '<div class="mini-rituals">' +
        '<div>◌ Mindful Moment</div>' +
        '<div>✦ Fun Spark</div>' +
        '<div>♡ Family Connection</div>' +
      '</div>' +
      '<button class="about-close" type="button" data-close-about>Close</button>' +
    '</div>' +
  '</dialog>';
}

function familyDialog() {
  const cards = FAMILY_PROFILES.map((profile) =>
    '<article class="family-profile">' +
      '<img src="' + profile.image + '" alt="" loading="lazy" />' +
      '<div><h3>' + escapeHtml(profile.name) + '</h3><p>' + escapeHtml(profile.title) + '</p>' +
      (profile.motto ? '<small>“' + escapeHtml(profile.motto) + '”</small>' : '') +
      '</div>' +
    '</article>'
  ).join('');

  return '<dialog id="family-dialog" class="family-dialog">' +
    '<div class="family-sheet">' +
      '<p class="family-eyebrow">Meet the Happy-Makers Family</p>' +
      '<div class="family-group-frame"><img src="' + FAMILY_ASSET + '" alt="The Happy-Makers family" /></div>' +
      '<h2>Your cheerful companions for the journey</h2>' +
      '<p class="family-intro">Full of sparkle, laughter, love and just the right pinch of playful holiday magic. Delightfully imperfect, beautifully lively and wonderfully real.</p>' +
      '<div class="family-profile-grid">' + cards + '</div>' +
      '<button class="about-close" type="button" data-close-family>Back to the journey</button>' +
    '</div>' +
  '</dialog>';
}

function completedCount() {
  return state.completed.length;
}

function getTodayDay() {
  const now = new Date();
  if (now.getMonth() === 11 && now.getDate() >= 1 && now.getDate() <= 24) return now.getDate();
  return null;
}

function isUnlocked(day) {
  if (previewMode) return true;
  const now = new Date();
  if (now.getMonth() === 11 && now.getDate() >= 1 && now.getDate() <= 24) {
    return day <= now.getDate();
  }
  return true;
}

function nextJourneyDay() {
  const today = getTodayDay();
  if (today && isUnlocked(today)) return today;
  return days.find((day) => isUnlocked(day.day) && !state.completed.includes(day.day))?.day || 1;
}

function weekForDay(dayNumber) {
  return packs.find((pack) => pack.days.some((day) => day.day === dayNumber));
}

function renderProgress() {
  const count = completedCount();
  const angle = Math.round((count / 24) * 360);
  return '<section class="progress-card" style="--progress-angle:' + angle + 'deg">' +
    '<div class="progress-orb" aria-hidden="true">' + count + '</div>' +
    '<div class="progress-copy"><strong>Your 24-day journey</strong><span>Progress is saved on this device.</span></div>' +
    '<div class="progress-count">' + count + ' / 24</div>' +
  '</section>';
}

function dayStatus(day) {
  if (state.completed.includes(day)) return 'Done';
  if (!isUnlocked(day)) return 'Dec ' + day;
  if (day === getTodayDay()) return 'Today';
  return 'Open';
}

function renderWeek(pack) {
  const tiles = pack.days.map((day) => {
    const completed = state.completed.includes(day.day);
    const unlocked = isUnlocked(day.day);
    const today = day.day === getTodayDay();
    const className = [
      'day-tile',
      unlocked ? 'available' : 'locked',
      completed ? 'completed' : '',
      today ? 'today' : ''
    ].filter(Boolean).join(' ');

    if (!unlocked) {
      return '<div class="' + className + '" aria-disabled="true">' +
        '<span class="day-number">' + day.day + '</span>' +
        '<span class="day-status">' + dayStatus(day.day) + '</span>' +
      '</div>';
    }

    return '<button class="' + className + '" type="button" data-day="' + day.day + '" aria-label="Day ' + day.day + ' - ' + dayStatus(day.day) + '">' +
      (completed ? '<span class="day-check" aria-hidden="true">✓</span>' : '') +
      '<span class="day-number">' + day.day + '</span>' +
      '<span class="day-status">' + dayStatus(day.day) + '</span>' +
    '</button>';
  }).join('');

  return '<section class="week-block">' +
    '<div class="week-banner"><span class="week-number">Week ' + pack.week + '</span><span class="week-quote">' + escapeHtml(pack.week_quote) + '</span></div>' +
    '<div class="calendar-grid">' + tiles + '</div>' +
  '</section>';
}

function renderHome() {
  currentDay = null;
  document.documentElement.lang = 'en';

  const nextDay = nextJourneyDay();
  app.innerHTML = topbar() +
    '<section class="hero">' +
      '<div class="hero-copy">' +
        '<p class="eyebrow">The Happy-Makers Present</p>' +
        '<h1>24 Gentle Steps to Christmas</h1>' +
        '<p class="hero-subtitle">A Mindful Family Journey of Togetherness, Reflection &amp; the Magic of Christmas</p>' +
        '<div class="hero-meta"><span>10 minutes a day</span><span>24 days</span><span>3 mini-rituals</span></div>' +
        '<div class="hero-actions">' +
          '<button class="primary-cta" type="button" data-start>Open Day ' + nextDay + '</button>' +
          '<button class="secondary-hero-cta" type="button" data-family>Meet the Happy-Makers</button>' +
        '</div>' +
      '</div>' +
      '<div class="hero-visual"><div class="hero-visual-frame">' +
        '<img src="' + FAMILY_ASSET + '" alt="The Happy-Makers family in their purple and gold Christmas world" />' +
      '</div></div>' +
    '</section>' +
    renderProgress() +
    '<section class="ritual-strip" aria-label="Daily ritual">' +
      '<div class="ritual-pill mindful"><span>◌</span><strong>Mindful Moment</strong></div>' +
      '<div class="ritual-pill fun"><span>✦</span><strong>Fun Spark</strong></div>' +
      '<div class="ritual-pill connection"><span>♡</span><strong>Family Connection</strong></div>' +
    '</section>' +
    '<div class="section-heading"><h2>Your Advent journey</h2><p>One day, three shared moments, endless memories.</p></div>' +
    packs.map(renderWeek).join('') +
    '<p class="home-footnote">No prep. No mess. No glitter required.</p>' +
    aboutDialog() +
    familyDialog();

  wireCommon();
  app.querySelector('[data-start]').addEventListener('click', () => renderDay(nextDay));
  app.querySelectorAll('[data-day]').forEach((button) => {
    button.addEventListener('click', () => renderDay(Number(button.dataset.day)));
  });
}

function sectionType(category) {
  if (category === 'Mindful Moment') return 'mindful';
  if (category === 'Fun Spark') return 'fun';
  return 'connection';
}

function bodyClass(text) {
  const trimmed = text.trim();
  if (
    /^Round\b/i.test(trimmed) ||
    /^Final\b/i.test(trimmed) ||
    /^Challenge\b/i.test(trimmed) ||
    /^Gratitude for This Advent$/i.test(trimmed) ||
    /^Wishes for Our Family$/i.test(trimmed) ||
    /^Movement \+Sound \+ Face Examples:$/i.test(trimmed)
  ) return 'body-label';
  return '';
}

function noteOwner(noteLabel) {
  return Object.keys(CHARACTER_ASSETS).find((name) => noteLabel.startsWith(name)) || null;
}

function renderSection(section) {
  const body = section.body.map((paragraph) =>
    '<p class="' + bodyClass(paragraph) + '">' + escapeHtml(paragraph) + '</p>'
  ).join('');
  const owner = noteOwner(section.note_label);
  const avatar = owner
    ? '<img class="character-avatar" src="' + CHARACTER_ASSETS[owner] + '" alt="" loading="lazy" />'
    : '<span class="character-avatar character-avatar-group" aria-hidden="true">✦</span>';

  return '<article class="activity-card" data-type="' + sectionType(section.category) + '">' +
    '<p class="activity-label">' + escapeHtml(section.category) + '</p>' +
    '<h2>' + escapeHtml(section.title) + '</h2>' +
    '<p class="activity-tagline">' + escapeHtml(section.tagline) + '</p>' +
    '<div class="activity-body">' + body + '</div>' +
    '<div class="character-note">' + avatar +
      '<div class="character-note-copy"><strong>' + escapeHtml(section.note_label) + ':</strong><span>' + escapeHtml(section.note) + '</span></div>' +
    '</div>' +
  '</article>';
}

function renderLocked(dayNumber) {
  app.innerHTML = topbar() +
    '<section class="locked-card"><div class="lock-icon">✦</div><h1>Day ' + dayNumber + ' opens December ' + dayNumber + '</h1><p>Your next Gentle Step will be here when its day arrives.</p></section>' +
    '<button class="back-button" type="button" data-home>← All days</button>' +
    aboutDialog() +
    familyDialog();
  wireCommon();
  app.querySelector('[data-home]').addEventListener('click', renderHome);
}

function renderDay(dayNumber) {
  if (!isUnlocked(dayNumber)) {
    currentDay = dayNumber;
    renderLocked(dayNumber);
    return;
  }

  const day = days.find((item) => item.day === dayNumber);
  if (!day) return;
  currentDay = dayNumber;
  const pack = weekForDay(dayNumber);
  const complete = state.completed.includes(dayNumber);

  app.innerHTML = topbar() +
    '<div class="detail-shell">' +
      '<button type="button" class="back-button" data-home>← All 24 days</button>' +
      '<section class="detail-hero">' +
        '<p class="detail-kicker">Week ' + pack.week + ' · Day ' + dayNumber + ' of 24</p>' +
        '<h1>Day ' + dayNumber + '</h1>' +
        '<p class="detail-week">' + escapeHtml(pack.week_quote) + '</p>' +
      '</section>' +
      day.sections.map(renderSection).join('') +
      '<nav class="day-nav" aria-label="Day navigation">' +
        '<button type="button" class="secondary-button" data-prev ' + (dayNumber <= 1 ? 'disabled' : '') + '>← Previous</button>' +
        '<button type="button" class="secondary-button" data-next ' + (dayNumber >= 24 ? 'disabled' : '') + '>Next →</button>' +
      '</nav>' +
      '<div class="detail-actions"><button type="button" class="complete-button ' + (complete ? 'completed' : '') + '" data-complete>' +
        (complete ? 'Completed ✓ · tap to undo' : 'Mark Day ' + dayNumber + ' complete') +
      '</button></div>' +
    '</div>' +
    aboutDialog() +
    familyDialog();

  wireCommon();
  app.querySelector('[data-home]').addEventListener('click', () => {
    renderHome();
    window.scrollTo(0, 0);
  });

  const prev = app.querySelector('[data-prev]');
  const next = app.querySelector('[data-next]');
  if (!prev.disabled) prev.addEventListener('click', () => {
    renderDay(dayNumber - 1);
    window.scrollTo(0, 0);
  });
  if (!next.disabled) next.addEventListener('click', () => {
    renderDay(dayNumber + 1);
    window.scrollTo(0, 0);
  });

  app.querySelector('[data-complete]').addEventListener('click', () => {
    const already = state.completed.includes(dayNumber);
    state.completed = already
      ? state.completed.filter((value) => value !== dayNumber)
      : state.completed.concat(dayNumber).sort((a, b) => a - b);
    saveState();
    showToast(already ? 'Completion removed.' : 'Day ' + dayNumber + ' saved. That is enough for today.');
    renderDay(dayNumber);
  });
}

function wireCommon() {
  const about = app.querySelector('[data-about]');
  const aboutDialogEl = app.querySelector('#about-dialog');
  const closeAbout = app.querySelector('[data-close-about]');
  const familyButtons = app.querySelectorAll('[data-family]');
  const familyDialogEl = app.querySelector('#family-dialog');
  const closeFamily = app.querySelector('[data-close-family]');

  if (about && aboutDialogEl) about.addEventListener('click', () => aboutDialogEl.showModal());
  if (closeAbout && aboutDialogEl) closeAbout.addEventListener('click', () => aboutDialogEl.close());

  if (familyDialogEl) {
    familyButtons.forEach((button) => button.addEventListener('click', () => familyDialogEl.showModal()));
  }
  if (closeFamily && familyDialogEl) closeFamily.addEventListener('click', () => familyDialogEl.close());
}

async function init() {
  try {
    const responses = await Promise.all(PACK_URLS.map((url) => fetch(url, { cache: 'no-store' })));
    if (responses.some((response) => !response.ok)) throw new Error('content request failed');
    packs = await Promise.all(responses.map((response) => response.json()));

    if (packs.some((pack) => pack.source_sha256 !== SOURCE_SHA || pack.canonical_locale !== 'en')) {
      throw new Error('source lock mismatch');
    }

    packs.sort((a, b) => a.week - b.week);
    days = packs.flatMap((pack) => pack.days).sort((a, b) => a.day - b.day);

    const requestedDay = Number(params.get('day'));
    if (Number.isInteger(requestedDay) && requestedDay >= 1 && requestedDay <= 24) renderDay(requestedDay);
    else renderHome();

    if (params.get('family') === '1') {
      requestAnimationFrame(() => {
        const familyDialogEl = app.querySelector('#family-dialog');
        if (familyDialogEl && !familyDialogEl.open) familyDialogEl.showModal();
      });
    }

    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('./service-worker.js').catch(() => {});
    }
  } catch (error) {
    app.innerHTML = '<section class="error-card"><h1>Gentle Steps could not load.</h1><p>' + escapeHtml(String(error.message || error)) + '</p></section>';
  }
}

init();
