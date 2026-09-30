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
    '<button class="ghost-button" type="button" data-about>How it works</button>' +
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
        '<button class="primary-cta" type="button" data-start>Open Day ' + nextDay + '</button>' +
      '</div>' +
      '<div class="hero-visual"><div class="hero-visual-frame">' +
        '<img src="../assets/images/24%20Gentle%20Steps%20to%20Christmas%20cover.jpg" alt="24 Gentle Steps to Christmas cover" />' +
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
    aboutDialog();

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

function renderSection(section) {
  const body = section.body.map((paragraph) =>
    '<p class="' + bodyClass(paragraph) + '">' + escapeHtml(paragraph) + '</p>'
  ).join('');

  return '<article class="activity-card" data-type="' + sectionType(section.category) + '">' +
    '<p class="activity-label">' + escapeHtml(section.category) + '</p>' +
    '<h2>' + escapeHtml(section.title) + '</h2>' +
    '<p class="activity-tagline">' + escapeHtml(section.tagline) + '</p>' +
    '<div class="activity-body">' + body + '</div>' +
    '<div class="character-note"><strong>' + escapeHtml(section.note_label) + ':</strong> ' + escapeHtml(section.note) +
      '<span class="source-page">Final paperback source · page ' + section.page + '</span>' +
    '</div>' +
  '</article>';
}

function renderLocked(dayNumber) {
  app.innerHTML = topbar() +
    '<section class="locked-card"><div class="lock-icon">✦</div><h1>Day ' + dayNumber + ' opens December ' + dayNumber + '</h1><p>Your next Gentle Step will be here when its day arrives.</p></section>' +
    '<button class="back-button" type="button" data-home>← All days</button>' +
    aboutDialog();
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
    aboutDialog();

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
  const dialog = app.querySelector('#about-dialog');
  const close = app.querySelector('[data-close-about]');
  if (about && dialog) about.addEventListener('click', () => dialog.showModal());
  if (close && dialog) close.addEventListener('click', () => dialog.close());
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

    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('./service-worker.js').catch(() => {});
    }
  } catch (error) {
    app.innerHTML = '<section class="error-card"><h1>Gentle Steps could not load.</h1><p>' + escapeHtml(String(error.message || error)) + '</p></section>';
  }
}

init();
