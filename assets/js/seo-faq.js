// /assets/js/seo-faq.js
(function () {
  function normalizeText(str) {
    if (!str) return "";
    return String(str)
      .replace(/[“”]/g, '"')
      .replace(/[‘’]/g, "'")
      .trim();
  }

  function getCanonicalUrl() {
    const canonical = document.querySelector('link[rel="canonical"]');
    return canonical && canonical.href ? canonical.href : location.href;
  }

  function getPathKey() {
    let p = window.location.pathname || "/";
    if (!p.startsWith("/")) p = "/" + p;
    if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
    return p;
  }

  const FAQ_BY_PATH = {
    "/kids": {
      title: "FAQ",
      questions: [
        { q: "Is this only about emotions?", a: "No—this hub includes emotions, but also routines, habits, confidence, friendship, and screen time balance." },
        { q: "What’s the best place to start?", a: "Start with World 01 for core coping skills and big feelings. Then move to World 02 for habits, routines, and digital life." },
        { q: "How do busy families use this?", a: "Pick one short resource, try one idea today, and repeat for a week. Small steps beat long lectures." }
      ]
    },
    "/teenagers": {
      title: "FAQ",
      questions: [
        { q: "What does this hub help with?", a: "It’s a practical starting point for teen-focused themes: emotions under pressure, digital balance, communication, routines, motivation, and confidence." },
        { q: "How can families start today?", a: "Pick one focus area for the week, use one short daily check-in question, and review after 7 days." },
        { q: "Is this a full program?", a: "Think of it as a hub: quick tools, simple prompts, and recommended resources you can use in real life." }
      ]
    },
    "/library/world-01": {
      title: "FAQ",
      questions: [
        { q: "How long does it take to use each story?", a: "Each level is designed to be read quickly, followed by a short Neuro-Coaching Console section you can talk about in a couple of minutes." },
        { q: "Is this a workbook or a storybook?", a: "It reads like funny stories, but each level includes a simple brain explanation and a practical cheat code you can try right away." },
        { q: "What skills does World 01 cover?", a: "World 01 includes kid-friendly tools for after-school crashes, empathy, handling mistakes, curiosity vs boredom, anger tools, growth mindset, friendship skills, self-care, and energy basics." }
      ]
    },
    "/library/world-02": {
      title: "FAQ",
      questions: [
        { q: "What is World 02 about?", a: "World 02 is advanced training for modern family life: screen balance, routines, habits, listening, teamwork, and critical thinking." },
        { q: "Do we need a lot of time?", a: "No. Read one short level, check the Neuro-Coaching Console, then try one simple cheat code in real life." },
        { q: "Does it include screen time tools?", a: "Yes. World 02 includes levels focused on screen balance and dopamine burnout in a kid-friendly way." }
      ]
    },
    "/library/confident-adventure": {
      title: "FAQ",
      questions: [
        { q: "Is this a storybook?", a: "It’s a guided 31-day adventure with daily prompts designed to build confidence, mindfulness, and growth mindset." },
        { q: "How long does it take each day?", a: "Just a few minutes. Most families do one page a day and pick one tiny action to practice." },
        { q: "Who is it for?", a: "Kids who need support with confidence, mindset, and big feelings—and parents who want a simple daily routine that actually sticks." }
      ]
    },
    "/library/christmas-book": {
      title: "FAQ",
      questions: [
        { q: "What is this Christmas book for?", a: "It’s a practical holiday companion to help families create calmer routines and meaningful connection moments in December." },
        { q: "Do we need to do everything?", a: "No—pick what fits your family. The goal is less pressure and more real connection." },
        { q: "Who is it best for?", a: "Busy families who want simple traditions, calmer days, and ‘we’ll remember this’ moments—without perfection." }
      ]
    },
    "/adults": {
      title: "FAQ",
      questions: [
        {
          q: "What is the Adults Hub for?",
          a: "Practical tools for adult life: stress, routines, mindset, and calmer daily choices—built for busy schedules."
        },
        {
          q: "Do I need lots of time?",
          a: "No. Start with one small habit or prompt and repeat it for a week. Consistency beats big plans."
        },
        {
          q: "Where should I start?",
          a: "Pick one pain point (stress, routines, focus) and begin with the simplest tool you will actually use today."
        }
      ]
    },
    "/gifts": {
      title: "FAQ",
      questions: [
        {
          q: "What are the Gifts?",
          a: "Quick printable tools and mini-activities you can use right away to support calm, connection, and better routines."
        },
        {
          q: "Are these free?",
          a: "Some gifts are free and some are paid—each one is designed to be simple, fast, and usable in real life."
        },
        {
          q: "How do we use them as a family?",
          a: "Pick one gift, try it today, and keep it visible (fridge, desk, bedtime spot). Small tools work best when they’re easy to grab."
        }
      ]
    },
    "/gifts/family-motto": {
      title: "FAQ",
      questions: [
        {
          q: "What are Family Motto Cards?",
          a: "Simple phrases you choose as a family to guide daily moments—like a shared reminder during chaos."
        },
        {
          q: "How do we use them?",
          a: "Pick one motto for the week, say it together, and place it where everyone will see it."
        },
        {
          q: "Why does this help?",
          a: "One clear phrase reduces arguing and helps everyone reset faster—especially during transitions and tough moments."
        }
      ]
    },
    "/gifts/calm-energy": {
      title: "FAQ",
      questions: [
        {
          q: "What are Calm vs Energy Cards?",
          a: "A quick way to help kids notice whether they need calm or healthy energy—so you can choose the right reset."
        },
        {
          q: "How do we use them?",
          a: "Point to a card in the moment and choose a matching action: calm-down, move-your-body, or recharge."
        },
        {
          q: "Is energy bad?",
          a: "No. The goal is to guide it. Kids can be high-energy and still make good choices."
        }
      ]
    },
    "/gifts/word-search": {
      title: "FAQ",
      questions: [
        {
          q: "What is the Word Search gift?",
          a: "A simple, screen-free activity for focus and fun—great for boredom moments and calm downtime."
        },
        {
          q: "When should we use it?",
          a: "After school, travel, waiting rooms, rainy days, or anytime you need a quick reset without a fight."
        },
        {
          q: "Is it kid-friendly?",
          a: "Yes. It’s made to be easy to start and satisfying to finish."
        }
      ]
    },
    "/gifts/word-search-studio": {
      title: "FAQ",
      questions: [
        {
          q: "What is Word Search Studio?",
          a: "A simple way to create custom word searches—so kids stay engaged with topics they actually like."
        },
        {
          q: "How do families use it?",
          a: "Pick a theme, generate a puzzle, then use it as a quick, screen-free focus activity."
        },
        {
          q: "Why do custom puzzles help?",
          a: "Kids cooperate more when the activity feels like it was made for them."
        }
      ]
    },
    "/library": {
      title: "FAQ",
      questions: [
        { q: "Where should we start?", a: "Start with World 01 for core coping skills and big feelings. Then move to World 02 for habits, routines, and the digital world." },
        { q: "Are these long books?", a: "They’re designed for busy families: short levels, simple explanations, and quick tools you can use right away." },
        { q: "Do I need to buy everything?", a: "No. Start with one book that matches your biggest pain point, then build your toolkit over time." }
      ]
    }
  };

  function getFAQForThisPage() {
    const key = getPathKey();
    return FAQ_BY_PATH[key] || null;
  }

  function buildFAQSchema(faq) {
    const canonical = getCanonicalUrl();
    const normalizedCanonical = canonical.replace(/\/?$/, "/");
    const id = normalizedCanonical + "#faq";
    const questions = (faq.questions || []).map((item) => ({
      "@type": "Question",
      name: normalizeText(item.q),
      acceptedAnswer: {
        "@type": "Answer",
        text: normalizeText(item.a)
      }
    }));

    return {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "@id": id,
      mainEntityOfPage: { "@id": normalizedCanonical + "#webpage" },
      mainEntity: questions
    };
  }

  function injectFAQSchema(schemaObj) {
    const existing = document.getElementById("faq-jsonld");
    if (existing) existing.remove();

    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.id = "faq-jsonld";
    script.textContent = JSON.stringify(schemaObj);
    document.head.appendChild(script);
  }

  function renderFAQHtml(faq) {
    const container = document.querySelector("[data-faq-container]") || document.getElementById("faq");
    if (!container) return;

    const title = normalizeText(faq.title || "FAQ");
    const items = faq.questions || [];

    container.innerHTML = "";

    const heading = document.createElement("h2");
    heading.textContent = title;
    container.appendChild(heading);

    items.forEach((item) => {
      const q = normalizeText(item.q);
      const a = normalizeText(item.a);

      const details = document.createElement("details");
      details.className = "faq-item";

      const summary = document.createElement("summary");
      const strong = document.createElement("strong");
      strong.textContent = q;
      summary.appendChild(strong);

      const answer = document.createElement("p");
      answer.textContent = a;

      details.appendChild(summary);
      details.appendChild(answer);
      container.appendChild(details);
    });
  }

  function init() {
    const faq = getFAQForThisPage();
    if (!faq || !Array.isArray(faq.questions) || faq.questions.length === 0) return;

    renderFAQHtml(faq);
    injectFAQSchema(buildFAQSchema(faq));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
