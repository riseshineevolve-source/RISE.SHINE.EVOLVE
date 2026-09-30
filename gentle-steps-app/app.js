const app = document.getElementById('app');
const toast = document.getElementById('toast');

const STORAGE_KEY = 'gentleStepsState.v1';
const AVAILABLE_DAYS = [1, 2, 3];

const ui = {
  en: {
    brand: '24 Gentle Steps',
    brandSub: 'to Christmas',
    eyebrow: 'A family Advent ritual',
    heroTitle: 'A softer way through December.',
    heroSubtitle: 'About 10 minutes. Three small rituals. No prep, no pressure, no perfect-family performance.',
    progressTitle: 'Your December rhythm',
    progressText: 'Completed days stay saved on this device.',
    calendarTitle: 'Your 24 days',
    calendarHint: 'Days 1-3 are live in this production slice.',
    ready: 'Ready',
    done: 'Done',
    locked: 'Soon',
    mindful: 'Mindful Moment',
    fun: 'Fun Spark',
    connection: 'Family Connection',
    homeNote: 'Offline-first: this slice stores language and progress only on this device. No account, social feed, AI or backend.',
    back: 'All days',
    dayOf: 'of 24',
    complete: 'Mark this day complete',
    completed: 'Completed - tap to undo',
    previous: 'Previous day',
    next: 'Next day',
    toastDone: 'Day saved. That is enough for today.',
    toastUndo: 'Completion removed.',
    error: 'The Advent content could not be loaded.'
  },
  'pl-PL': {
    brand: '24 małe kroki',
    brandSub: 'do Świąt',
    eyebrow: 'Rodzinny kalendarz adwentowy',
    heroTitle: 'Grudzień trochę mniej na pełnym gazie.',
    heroSubtitle: 'Około 10 minut. Trzy małe rzeczy. Bez przygotowań, presji i udawania rodziny z reklamy.',
    progressTitle: 'Wasz grudniowy rytm',
    progressText: 'Ukończone dni zostają zapisane na tym urządzeniu.',
    calendarTitle: '24 dni dla Was',
    calendarHint: 'Dni 1-3 są gotowe w tym produkcyjnym wycinku.',
    ready: 'Gotowe',
    done: 'Zrobione',
    locked: 'Wkrótce',
    mindful: 'Spokojna chwila',
    fun: 'Iskra zabawy',
    connection: 'Chwila bliskości',
    homeNote: 'Offline-first: ten wycinek zapisuje język i postęp tylko na tym urządzeniu. Bez konta, feedu, AI i backendu.',
    back: 'Wszystkie dni',
    dayOf: 'z 24',
    complete: 'Oznacz ten dzień jako zrobiony',
    completed: 'Zrobione - dotknij, aby cofnąć',
    previous: 'Poprzedni dzień',
    next: 'Następny dzień',
    toastDone: 'Zapisane. Na dziś naprawdę wystarczy.',
    toastUndo: 'Cofnięto oznaczenie dnia.',
    error: 'Nie udało się wczytać treści kalendarza.'
  }
};

let pack = null;
let currentDay = null;
let state = loadState();

function loadState() {
  const browserLocale = (navigator.language || '').toLowerCase().startsWith('pl') ? 'pl-PL' : 'en';
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return {
      locale: saved.locale === 'pl-PL' ? 'pl-PL' : saved.locale === 'en' ? 'en' : browserLocale,
      completed: Array.isArray(saved.completed) ? saved.completed.filter(Number.isInteger) : []
    };
  } catch {
    return { locale: browserLocale, completed: [] };
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function t(key) {
  return ui[state.locale][key];
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
  showToast.timer = window.setTimeout(function () {
    toast.classList.remove('show');
  }, 2200);
}

function localeButtons() {
  return '<div class="lang-switch" aria-label="Language">' +
    '<button type="button" data-locale="en" aria-pressed="' + (state.locale === 'en') + '">EN</button>' +
    '<button type="button" data-locale="pl-PL" aria-pressed="' + (state.locale === 'pl-PL') + '">PL</button>' +
  '</div>';
}

function topbar() {
  return '<header class="topbar">' +
    '<div class="brand-lockup">' +
      '<div class="brand-mark" aria-hidden="true">✦</div>' +
      '<div class="brand-text"><strong>' + escapeHtml(t('brand')) + '</strong><span>' + escapeHtml(t('brandSub')) + '</span></div>' +
    '</div>' +
    localeButtons() +
  '</header>';
}

function completedCount() {
  return state.completed.filter(function (day) { return day >= 1 && day <= 24; }).length;
}

function progressCard() {
  const count = completedCount();
  const angle = Math.round((count / 24) * 360);
  return '<section class="progress-card" style="--progress-angle:' + angle + 'deg">' +
    '<div class="progress-orb" aria-hidden="true">' + count + '</div>' +
    '<div class="progress-copy"><strong>' + escapeHtml(t('progressTitle')) + '</strong><span>' + escapeHtml(t('progressText')) + '</span></div>' +
    '<div class="progress-count">' + count + ' / 24</div>' +
  '</section>';
}

function renderHome() {
  currentDay = null;
  document.documentElement.lang = state.locale === 'pl-PL' ? 'pl' : 'en';

  let calendar = '';
  for (let day = 1; day <= 24; day += 1) {
    const available = AVAILABLE_DAYS.includes(day);
    const completed = state.completed.includes(day);
    const status = completed ? t('done') : available ? t('ready') : t('locked');
    if (available) {
      calendar += '<button class="day-tile available ' + (completed ? 'completed' : '') + '" type="button" data-day="' + day + '" aria-label="' + escapeHtml((state.locale === 'pl-PL' ? 'Dzień ' : 'Day ') + day + ' - ' + status) + '">' +
        (completed ? '<span class="day-check" aria-hidden="true">✓</span>' : '') +
        '<span class="day-number">' + day + '</span><span class="day-status">' + escapeHtml(status) + '</span></button>';
    } else {
      calendar += '<div class="day-tile locked" aria-disabled="true"><span class="day-number">' + day + '</span><span class="day-status">' + escapeHtml(status) + '</span></div>';
    }
  }

  app.innerHTML = topbar() +
    '<section class="hero">' +
      '<div class="hero-copy">' +
        '<p class="eyebrow">' + escapeHtml(t('eyebrow')) + '</p>' +
        '<h1>' + escapeHtml(t('heroTitle')) + '</h1>' +
        '<p class="hero-subtitle">' + escapeHtml(t('heroSubtitle')) + '</p>' +
      '</div>' +
      '<div class="cover-card"><img src="../assets/images/24%20Gentle%20Steps%20to%20Christmas%20cover.jpg" alt="" /></div>' +
    '</section>' +
    progressCard() +
    '<div class="section-heading"><h2>' + escapeHtml(t('calendarTitle')) + '</h2><p>' + escapeHtml(t('calendarHint')) + '</p></div>' +
    '<section class="calendar-grid" aria-label="' + escapeHtml(t('calendarTitle')) + '">' + calendar + '</section>' +
    '<section class="ritual-strip" aria-label="Daily ritual">' +
      '<div class="ritual-pill">◌<br>' + escapeHtml(t('mindful')) + '</div>' +
      '<div class="ritual-pill">✦<br>' + escapeHtml(t('fun')) + '</div>' +
      '<div class="ritual-pill">♡<br>' + escapeHtml(t('connection')) + '</div>' +
    '</section>' +
    '<p class="home-note">' + escapeHtml(t('homeNote')) + '</p>';

  wireGlobalActions();
  app.querySelectorAll('[data-day]').forEach(function (button) {
    button.addEventListener('click', function () {
      renderDay(Number(button.dataset.day));
    });
  });
}

function sectionLabel(type) {
  if (type === 'mindful') return t('mindful');
  if (type === 'fun') return t('fun');
  return t('connection');
}

function renderSection(section) {
  const body = section.body.map(function (paragraph) {
    return '<p>' + escapeHtml(paragraph) + '</p>';
  }).join('');

  return '<article class="activity-card" data-type="' + escapeHtml(section.type) + '">' +
    '<p class="activity-label">' + escapeHtml(sectionLabel(section.type)) + '</p>' +
    '<h2>' + escapeHtml(section.title) + '</h2>' +
    '<p class="activity-tagline">' + escapeHtml(section.tagline) + '</p>' +
    '<div class="activity-body">' + body + '</div>' +
    '<div class="character-note"><strong>' + escapeHtml(section.note_label) + ':</strong> ' + escapeHtml(section.note) + '</div>' +
  '</article>';
}

function renderDay(dayNumber) {
  const day = pack.days.find(function (item) { return item.day === dayNumber; });
  if (!day) return;

  currentDay = dayNumber;
  document.documentElement.lang = state.locale === 'pl-PL' ? 'pl' : 'en';
  const copy = day.locales[state.locale];
  const complete = state.completed.includes(dayNumber);

  app.innerHTML = topbar() +
    '<div class="detail-shell">' +
      '<button type="button" class="back-button" data-home>← ' + escapeHtml(t('back')) + '</button>' +
      '<section class="detail-hero">' +
        '<p class="detail-kicker">' + escapeHtml(copy.title) + ' · ' + dayNumber + ' ' + escapeHtml(t('dayOf')) + '</p>' +
        '<h1>' + dayNumber + '</h1>' +
        '<p class="detail-intro">' + escapeHtml(copy.intro) + '</p>' +
      '</section>' +
      copy.sections.map(renderSection).join('') +
      '<nav class="day-nav" aria-label="Day navigation">' +
        '<button type="button" class="secondary-button" data-prev ' + (dayNumber <= 1 ? 'disabled' : '') + '>← ' + escapeHtml(t('previous')) + '</button>' +
        '<button type="button" class="secondary-button" data-next ' + (dayNumber >= 3 ? 'disabled' : '') + '>' + escapeHtml(t('next')) + ' →</button>' +
      '</nav>' +
      '<div class="detail-actions"><button type="button" class="primary-button ' + (complete ? 'completed' : '') + '" data-complete>' + escapeHtml(complete ? t('completed') : t('complete')) + '</button></div>' +
    '</div>';

  wireGlobalActions();
  app.querySelector('[data-home]').addEventListener('click', renderHome);

  const prev = app.querySelector('[data-prev]');
  const next = app.querySelector('[data-next]');
  if (!prev.disabled) prev.addEventListener('click', function () { renderDay(dayNumber - 1); window.scrollTo(0, 0); });
  if (!next.disabled) next.addEventListener('click', function () { renderDay(dayNumber + 1); window.scrollTo(0, 0); });

  app.querySelector('[data-complete]').addEventListener('click', function () {
    const exists = state.completed.includes(dayNumber);
    state.completed = exists
      ? state.completed.filter(function (value) { return value !== dayNumber; })
      : state.completed.concat(dayNumber).sort(function (a, b) { return a - b; });
    saveState();
    showToast(exists ? t('toastUndo') : t('toastDone'));
    renderDay(dayNumber);
  });
}

function wireGlobalActions() {
  app.querySelectorAll('[data-locale]').forEach(function (button) {
    button.addEventListener('click', function () {
      state.locale = button.dataset.locale;
      saveState();
      if (currentDay) renderDay(currentDay);
      else renderHome();
    });
  });
}

async function init() {
  try {
    const response = await fetch('./content/days-01-03.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('content request failed');
    pack = await response.json();

    const preview = new URLSearchParams(window.location.search);
    if (preview.get('lang') === 'pl') state.locale = 'pl-PL';
    if (preview.get('lang') === 'en') state.locale = 'en';

    const requestedDay = Number(preview.get('day'));
    if (AVAILABLE_DAYS.includes(requestedDay)) renderDay(requestedDay);
    else renderHome();

    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('./service-worker.js').catch(function () {});
    }
  } catch (error) {
    app.innerHTML = '<section class="error-card"><h1>' + escapeHtml(t('error')) + '</h1><p>' + escapeHtml(String(error.message || error)) + '</p></section>';
  }
}

init();
