/* QAKey — query interface */
"use strict";

const questionInput  = document.getElementById("questionInput");
const askBtn         = document.getElementById("askBtn");
const resultPanel    = document.getElementById("resultPanel");
const matchedCard    = document.getElementById("matchedCard");
const noMatchCard    = document.getElementById("noMatchCard");
const confidenceBadge= document.getElementById("confidenceBadge");
const canonicalQ     = document.getElementById("canonicalQuestion");
const answerText     = document.getElementById("answerText");
const noMatchMessage = document.getElementById("noMatchMessage");
const historySection = document.getElementById("historySection");
const historyList    = document.getElementById("historyList");

const history = [];

function confidenceClass(score) {
  if (score >= 0.70) return "confidence-high";
  if (score >= 0.45) return "confidence-medium";
  return "confidence-low";
}

async function askQuestion(question) {
  if (!question.trim()) return;

  askBtn.disabled = true;
  askBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Searching…';

  try {
    const res  = await fetch("/api/query", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ question }),
    });
    const data = await res.json();

    resultPanel.classList.remove("d-none");

    if (data.matched) {
      const pct = Math.round(data.confidence * 100);

      confidenceBadge.textContent = `${pct}% match`;
      confidenceBadge.className   = `badge bg-white ms-auto ${confidenceClass(data.confidence)}`;

      canonicalQ.textContent = data.canonical_question;
      answerText.innerHTML = data.answer_html || escapeHtml(data.answer);

      matchedCard.classList.remove("d-none");
      noMatchCard.classList.add("d-none");
    } else {
      noMatchMessage.textContent = NO_MATCH_MESSAGE || "No matching answer found.";
      noMatchCard.classList.remove("d-none");
      matchedCard.classList.add("d-none");
    }

    // Add to history
    history.unshift({ question, matched: data.matched });
    renderHistory();
  } catch (err) {
    console.error(err);
    resultPanel.classList.remove("d-none");
    noMatchMessage.textContent = "An error occurred. Please try again.";
    noMatchCard.classList.remove("d-none");
    matchedCard.classList.add("d-none");
  } finally {
    askBtn.disabled = false;
    askBtn.innerHTML = '<i class="bi bi-search me-1"></i>Ask';
  }
}

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
