/* QAKey — query interface */
"use strict";

const questionInput  = document.getElementById("questionInput");
const askBtn         = document.getElementById("askBtn");
const resultPanel    = document.getElementById("resultPanel");
const matchedCard    = document.getElementById("matchedCard");
const feedbackCard   = document.getElementById("feedbackCard");
const noMatchCard    = document.getElementById("noMatchCard");
const confidenceBadge= document.getElementById("confidenceBadge");
const canonicalQ     = document.getElementById("canonicalQuestion");
const answerText     = document.getElementById("answerText");
const noMatchMessage = document.getElementById("noMatchMessage");
const contactRoute   = document.getElementById("contactRoute");
const contactRouteLabel = document.getElementById("contactRouteLabel");
const contactRouteLink  = document.getElementById("contactRouteLink");
const helpfulBtn     = document.getElementById("helpfulBtn");
const notHelpfulBtn  = document.getElementById("notHelpfulBtn");
const feedbackStatus = document.getElementById("feedbackStatus");
const historySection = document.getElementById("historySection");
const historyList    = document.getElementById("historyList");

const history = [];
let currentResult = null;

function confidenceClass(score) {
  if (score >= 0.70) return "confidence-high";
  if (score >= 0.45) return "confidence-medium";
  return "confidence-low";
}

function renderContactRoute(route) {
  if (!route || !route.href || !route.display_text) {
    contactRoute.classList.add("d-none");
    return;
  }

  contactRouteLabel.textContent = route.label || "Contact the team";
  contactRouteLink.textContent = route.display_text;
  contactRouteLink.href = route.href;
  contactRoute.classList.remove("d-none");
}

async function askQuestion(question) {
  if (!question.trim()) return;

  askBtn.disabled = true;
  askBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Searching…';
  feedbackStatus.classList.add("d-none");
  feedbackCard.classList.add("d-none");

  try {
    const res  = await fetch("/api/query", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ question }),
    });
    const data = await res.json();
    currentResult = { ...data, question };

    resultPanel.classList.remove("d-none");

    if (data.matched) {
      const pct = Math.round(data.confidence * 100);

      confidenceBadge.textContent = `${pct}% match`;
      confidenceBadge.className   = `badge bg-white ms-auto ${confidenceClass(data.confidence)}`;

      canonicalQ.textContent = data.canonical_question;
      answerText.innerHTML = data.answer_html || escapeHtml(data.answer);

      matchedCard.classList.remove("d-none");
      noMatchCard.classList.add("d-none");
      contactRoute.classList.add("d-none");
    } else {
      noMatchMessage.textContent = data.answer || NO_MATCH_MESSAGE || "No matching answer found.";
      renderContactRoute(data.human_help);
      noMatchCard.classList.remove("d-none");
      matchedCard.classList.add("d-none");
    }

    feedbackCard.classList.remove("d-none");
    helpfulBtn.disabled = false;
    notHelpfulBtn.disabled = false;
    feedbackStatus.classList.add("d-none");

    // Add to history
    history.unshift({ question, matched: data.matched });
    renderHistory();
  } catch (err) {
    console.error(err);
    resultPanel.classList.remove("d-none");
    noMatchMessage.textContent = "An error occurred. Please try again.";
    contactRoute.classList.add("d-none");
    noMatchCard.classList.remove("d-none");
    matchedCard.classList.add("d-none");
  } finally {
    askBtn.disabled = false;
    askBtn.innerHTML = '<i class="bi bi-search me-1"></i>Ask';
  }
}

async function sendFeedback(helpful) {
  if (!currentResult) return;

  helpfulBtn.disabled = true;
  notHelpfulBtn.disabled = true;

  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: currentResult.question,
        helpful,
        matched: currentResult.matched,
        record_id: currentResult.record_id,
        fallback_type: currentResult.fallback_type,
        confidence: currentResult.confidence,
      }),
    });

    if (!res.ok) {
      throw new Error("feedback request failed");
    }

    feedbackStatus.textContent = helpful
      ? "Thanks. This feedback was recorded."
      : "Thanks. This feedback was recorded for follow-up.";
    feedbackStatus.classList.remove("d-none");
  } catch (err) {
    console.error(err);
    feedbackStatus.textContent = "Unable to record feedback right now.";
    feedbackStatus.classList.remove("d-none");
    helpfulBtn.disabled = false;
    notHelpfulBtn.disabled = false;
  }
}

helpfulBtn.addEventListener("click", () => sendFeedback(true));
notHelpfulBtn.addEventListener("click", () => sendFeedback(false));

function renderHistory() {
  if (history.length === 0) return;
  historySection.classList.remove("d-none");
  historyList.innerHTML = history.slice(0, 8).map(h => `
    <li class="list-group-item list-group-item-action py-1">
      <i class="bi bi-${h.matched ? "check-circle text-success" : "x-circle text-warning"} me-1"></i>
      ${escapeHtml(h.question)}
    </li>
  `).join("");

  // Allow re-asking a history item
  historyList.querySelectorAll("li").forEach((li, i) => {
    li.addEventListener("click", () => {
      questionInput.value = history[i].question;
      askQuestion(history[i].question);
    });
  });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Event listeners
askBtn.addEventListener("click", () => askQuestion(questionInput.value));
questionInput.addEventListener("keydown", e => {
  if (e.key === "Enter") askQuestion(questionInput.value);
});
