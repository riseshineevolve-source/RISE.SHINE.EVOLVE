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

const FAMILY_ASSET = './brand/concepts/splash-v2-city-family.webp';
const CHARACTER_NAMES = ['Mimi', 'Luli', 'Dilo', 'Alio', 'Nini'];

const FAMILY_PROFILES = [
  { name: 'Mimi', title: 'The Heart and Heroine' },
  { name: 'Luli', title: 'The Elegant Detective of Holiday Magic', motto: 'Life is a mystery best solved with style.' },
  { name: 'Dilo', title: 'The Striker With Holiday Swagger', motto: 'Glow bold, score big.' },
  { name: 'Alio', title: 'The Chief Holiday Chaos Engineer', motto: 'Maximum fun, mostly safe...' },
  { name: 'Nini', title: 'The Pocket-Sized Joy Distributor', motto: 'If it sparkles, she approves.' }
];

function characterPortrait(name, extraClass = '') {
  const safeName = CHARACTER_NAMES.includes(name) ? name.toLowerCase() : 'group';
  return '<span class="character-portrait portrait-' + safeName + ' ' + extraClass + '" role="img" aria-label="' + escapeHtml(name) + '"></span>';
}

const params = new URLSearchParams(window.location.search);
const previewMode = params.get('preview') === '1';
const REMINDER_STORAGE_KEY = 'gentleStepsReminder.v1';
const REMINDER_NOTIFICATION_BASE_ID = 2400;

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

function nativeReminderPlugin() {
  return window.Capacitor?.Plugins?.LocalNotifications || null;
}

function reminderDialog() {
  if (!nativeReminderPlugin()) return '';
  const saved = localStorage.getItem(REMINDER_STORAGE_KEY) || '18:30';
  return '<dialog id="reminder-dialog" class="reminder-dialog" aria-labelledby="reminder-title">' +
    '<div class="reminder-sheet">' +
      '<p class="family-eyebrow">Gentle reminder</p>' +
      '<h2 id="reminder-title">Choose your daily Advent time</h2>' +
      '<p>A small local reminder on this device only. No account, cloud sync or push server.</p>' +
      '<label class="reminder-time-label" for="reminder-time">Daily reminder</label>' +
      '<input id="reminder-time" class="reminder-time" type="time" value="' + escapeHtml(saved) + '" />' +
      '<div class="reminder-actions">' +
        '<button class="about-close" type="button" data-save-reminder>Save reminder</button>' +
        '<button class="reminder-cancel" type="button" data-cancel-reminder>Turn reminder off</button>' +
        '<button class="reminder-dismiss" type="button" data-close-reminder>Cancel</button>' +
      '</div>' +
    '</div>' +
  '</dialog>';
}

async function scheduleDailyReminder(time) {
  const plugin = nativeReminderPlugin();
  if (!plugin) return false;

  let permission = await plugin.checkPermissions();
  if (permission.display !== 'granted') {
    permission = await plugin.requestPermissions();
  }
  if (permission.display !== 'granted') {
    showToast('Notifications are off in device settings.');
    return false;
  }

  const [hour, minute] = time.split(':').map(Number);
  const ids = Array.from({ length: 24 }, (_, index) => ({ id: REMINDER_NOTIFICATION_BASE_ID + index + 1 }));
  await plugin.cancel({ notifications: ids });

  const now = new Date();
  let seasonYear = now.getFullYear();
  if (now.getMonth() === 11 && now.getDate() > 24) seasonYear += 1;

  const notifications = [];
  for (let day = 1; day <= 24; day += 1) {
    const at = new Date(seasonYear, 11, day, hour, minute, 0, 0);
    if (at <= now) continue;
    notifications.push({
      id: REMINDER_NOTIFICATION_BASE_ID + day,
      title: 'Day ' + day + ' • Your Gentle Step is waiting ✦',
      body: 'About 10 minutes for today’s Mindful Moment, Fun Spark and Family Connection.',
      schedule: { at, allowWhileIdle: true },
      autoCancel: true,
      extra: { day }
    });
  }

  if (notifications.length === 0) {
    seasonYear += 1;
    for (let day = 1; day <= 24; day += 1) {
      notifications.push({
        id: REMINDER_NOTIFICATION_BASE_ID + day,
        title: 'Day ' + day + ' • Your Gentle Step is waiting ✦',
        body: 'About 10 minutes for today’s Mindful Moment, Fun Spark and Family Connection.',
        schedule: { at: new Date(seasonYear, 11, day, hour, minute, 0, 0), allowWhileIdle: true },
        autoCancel: true,
        extra: { day }
      });
    }
  }

  await plugin.schedule({ notifications });
  localStorage.setItem(REMINDER_STORAGE_KEY, time);
  showToast('Advent reminders saved for ' + time + '.');
  return true;
}

async function cancelDailyReminder() {
  const plugin = nativeReminderPlugin();
  if (!plugin) return;
  const ids = Array.from({ length: 24 }, (_, index) => ({ id: REMINDER_NOTIFICATION_BASE_ID + index + 1 }));
  await plugin.cancel({ notifications: ids });
  localStorage.removeItem(REMINDER_STORAGE_KEY);
  showToast('Daily reminder turned off.');
}

function topbar() {
  return '<header class="topbar">' +
    '<div class="brand-lockup">' +
      '<div class="brand-mark" aria-hidden="true">✦</div>' +
      '<div class="brand-text"><strong>24 Gentle Steps to Christmas</strong><span>The Happy-Makers</span></div>' +
    '</div>' +
    '<div class="topbar-actions">' +
      '<button class="ghost-button ghost-button-family" type="button" data-family>Family</button>' +
      (nativeReminderPlugin() ? '<button class="ghost-button" type="button" data-reminder>Reminder</button>' : '') +
      '<button class="ghost-button" type="button" data-about>How it works</button>' +
    '</div>' +
  '</header>';
}

function aboutDialog() {
  return '<dialog id="about-dialog" aria-labelledby="about-title">' +
    '<div class="about-sheet">' +
      '<h2 id="about-title">One day. Three shared moments.</h2>' +
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
      characterPortrait(profile.name, 'family-profile-avatar') +
      '<div><h3>' + escapeHtml(profile.name) + '</h3><p>' + escapeHtml(profile.title) + '</p>' +
      (profile.motto ? '<small>“' + escapeHtml(profile.motto) + '”</small>' : '') +
      '</div>' +
    '</article>'
  ).join('');

  return '<dialog id="family-dialog" class="family-dialog" aria-labelledby="family-title">' +
    '<div class="family-sheet">' +
      '<p class="family-eyebrow">Meet the Happy-Makers Family</p>' +
      '<div class="family-group-frame"><img src="' + FAMILY_ASSET + '" alt="The Happy-Makers family" loading="lazy" decoding="async" /></div>' +
      '<h2 id="family-title">Your cheerful companions for the journey</h2>' +
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
  return '<section class="progress-card" aria-label="' + count + ' of 24 days completed" style="--progress-angle:' + angle + 'deg">' +
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
      return '<div class="' + className + '" aria-disabled="true" aria-label="Day ' + day.day + ' - opens December ' + day.day + '">' +
        '<span class="day-number">' + day.day + '</span>' +
        '<span class="day-status">' + dayStatus(day.day) + '</span>' +
      '</div>';
    }

    return '<button class="' + className + '" type="button" data-day="' + day.day + '" aria-label="Day ' + day.day + ' - ' + dayStatus(day.day) + '"' + (today ? ' aria-current="date"' : '') + '>' +
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
        '<img src="' + FAMILY_ASSET + '" alt="The Happy-Makers family in their purple and gold Christmas world" fetchpriority="high" decoding="async" />' +
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
    familyDialog() +
    reminderDialog();

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
  return CHARACTER_NAMES.find((name) => noteLabel.startsWith(name)) || null;
}

function renderSection(section) {
  const body = section.body.map((paragraph) =>
    '<p class="' + bodyClass(paragraph) + '">' + escapeHtml(paragraph) + '</p>'
  ).join('');
  const owner = noteOwner(section.note_label);
  const avatar = owner
    ? characterPortrait(owner, 'character-avatar')
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
    familyDialog() +
    reminderDialog();
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
    familyDialog() +
    reminderDialog();

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
  const reminderButton = app.querySelector('[data-reminder]');
  const reminderDialogEl = app.querySelector('#reminder-dialog');
  const closeReminder = app.querySelector('[data-close-reminder]');
  const saveReminder = app.querySelector('[data-save-reminder]');
  const cancelReminder = app.querySelector('[data-cancel-reminder]');

  if (about && aboutDialogEl) about.addEventListener('click', () => aboutDialogEl.showModal());
  if (closeAbout && aboutDialogEl) closeAbout.addEventListener('click', () => aboutDialogEl.close());

  if (familyDialogEl) {
    familyButtons.forEach((button) => button.addEventListener('click', () => familyDialogEl.showModal()));
  }
  if (closeFamily && familyDialogEl) closeFamily.addEventListener('click', () => familyDialogEl.close());

  if (reminderButton && reminderDialogEl) reminderButton.addEventListener('click', () => reminderDialogEl.showModal());
  if (closeReminder && reminderDialogEl) closeReminder.addEventListener('click', () => reminderDialogEl.close());
  if (saveReminder && reminderDialogEl) saveReminder.addEventListener('click', async () => {
    const time = reminderDialogEl.querySelector('#reminder-time')?.value;
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time || '')) {
      showToast('Choose a valid reminder time.');
      return;
    }
    if (await scheduleDailyReminder(time)) reminderDialogEl.close();
  });
  if (cancelReminder && reminderDialogEl) cancelReminder.addEventListener('click', async () => {
    await cancelDailyReminder();
    reminderDialogEl.close();
  });
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
