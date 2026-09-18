(function () {
  "use strict";

  var MEASUREMENT_ID = "G-WW6C0S6031";
  var STORAGE_KEY = "rse_analytics_consent_v1";
  var PROD_HOSTS = ["rise-shine-evolve-learning-hub.com", "www.rise-shine-evolve-learning-hub.com"];

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

  // Privacy-first Consent Mode v2 defaults. Marketing consent remains denied.
  window.gtag("consent", "default", {
    analytics_storage: "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    wait_for_update: 500
  });

  window.gtag("set", "ads_data_redaction", true);
  window.gtag("set", "url_passthrough", false);

  var tagLoaded = false;

  function isProduction() {
    return PROD_HOSTS.indexOf(window.location.hostname) !== -1;
  }

  function readChoice() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function saveChoice(choice) {
    try {
      window.localStorage.setItem(STORAGE_KEY, choice);
    } catch (e) {
      // Consent still applies for the current page even when storage is unavailable.
    }
  }

  function loadGoogleTag() {
    if (tagLoaded || !isProduction()) return;
    tagLoaded = true;

    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(MEASUREMENT_ID);
    document.head.appendChild(script);

    window.gtag("js", new Date());
    window.gtag("config", MEASUREMENT_ID, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });
  }

  function applyAnalyticsConsent(granted, persist) {
    window.gtag("consent", "update", {
      analytics_storage: granted ? "granted" : "denied",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied"
    });

    if (persist) saveChoice(granted ? "granted" : "denied");
    if (granted) loadGoogleTag();
  }

  function removeBanner() {
    var banner = document.getElementById("rse-consent-banner");
    if (banner) banner.remove();
  }

  function ensureManageButton() {
    if (document.getElementById("rse-privacy-choices")) return;

    var button = document.createElement("button");
    button.id = "rse-privacy-choices";
    button.type = "button";
    button.textContent = "Privacy choices";
    button.setAttribute("aria-label", "Open analytics privacy choices");
    button.style.cssText = [
      "position:fixed",
      "right:12px",
      "bottom:12px",
      "z-index:2147483646",
      "border:1px solid rgba(255,255,255,.32)",
      "border-radius:999px",
      "padding:8px 12px",
      "background:#111827",
      "color:#fff",
      "font:600 12px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif",
      "box-shadow:0 4px 18px rgba(0,0,0,.28)",
      "cursor:pointer"
    ].join(";");

    button.addEventListener("click", function () {
      showBanner(true);
    });

    document.body.appendChild(button);
  }

  function showBanner(force) {
    if (!force && readChoice()) {
      ensureManageButton();
      return;
    }

    removeBanner();

    var wrap = document.createElement("div");
    wrap.id = "rse-consent-banner";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "true");
    wrap.setAttribute("aria-labelledby", "rse-consent-title");
    wrap.style.cssText = [
      "position:fixed",
      "left:0",
      "right:0",
      "bottom:0",
      "z-index:2147483647",
      "padding:14px",
      "background:rgba(5,5,10,.97)",
      "color:#fff",
      "border-top:1px solid rgba(255,255,255,.22)",
      "box-shadow:0 -10px 30px rgba(0,0,0,.35)",
      "font:400 14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif"
    ].join(";");

    var inner = document.createElement("div");
    inner.style.cssText = "max-width:980px;margin:0 auto;display:grid;gap:12px";

    var title = document.createElement("strong");
    title.id = "rse-consent-title";
    title.textContent = "Analytics privacy";

    var copy = document.createElement("div");
    copy.textContent = "We use Google Analytics only if you allow analytics. It helps us understand which Rise.Shine.Evolve. pages and resources are useful. Advertising storage and ad personalization stay off.";

    var actions = document.createElement("div");
    actions.style.cssText = "display:flex;flex-wrap:wrap;gap:10px";

    function makeButton(label) {
      var button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.style.cssText = [
        "min-height:42px",
        "border:1px solid rgba(255,255,255,.55)",
        "border-radius:999px",
        "padding:9px 16px",
        "background:#111827",
        "color:#fff",
        "font:700 14px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif",
        "cursor:pointer"
      ].join(";");
      return button;
    }

    var reject = makeButton("Reject analytics");
    var accept = makeButton("Allow analytics");

    reject.addEventListener("click", function () {
      applyAnalyticsConsent(false, true);
      removeBanner();
      ensureManageButton();
    });

    accept.addEventListener("click", function () {
      applyAnalyticsConsent(true, true);
      removeBanner();
      ensureManageButton();
    });

    actions.appendChild(reject);
    actions.appendChild(accept);
    inner.appendChild(title);
    inner.appendChild(copy);
    inner.appendChild(actions);
    wrap.appendChild(inner);
    document.body.appendChild(wrap);

    window.setTimeout(function () {
      reject.focus();
    }, 0);
  }

  // Small helper for future custom GA4 events. No event is sent without analytics consent.
  window.rseAnalytics = {
    measurementId: MEASUREMENT_ID,
    track: function (eventName, params) {
      if (readChoice() !== "granted") return false;
      loadGoogleTag();
      window.gtag("event", eventName, params || {});
      return true;
    },
    openPrivacyChoices: function () {
      showBanner(true);
    }
  };

  var choice = readChoice();

  if (choice === "granted") {
    applyAnalyticsConsent(true, false);
  } else if (choice === "denied" || navigator.globalPrivacyControl === true) {
    applyAnalyticsConsent(false, false);
  }

  function initUi() {
    if (!choice && navigator.globalPrivacyControl !== true) {
      showBanner(false);
    } else {
      ensureManageButton();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initUi, { once: true });
  } else {
    initUi();
  }
})();