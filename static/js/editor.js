/* QAKey — content editor */
"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let records = [];
let pendingDeleteId = null;
let importPreviewRecords = [];
let recordSearch = "";
let statusFilter = "All";
let expandedRecordId = null;
let undoStack = [];
let hasUnpublishedChanges = false;
let feedbackAlerts = [];

const editModal   = new bootstrap.Modal(document.getElementById("editModal"));
const deleteModal = new bootstrap.Modal(document.getElementById("deleteModal"));
const bulkImportModal = new bootstrap.Modal(document.getElementById("bulkImportModal"));

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    if (body instanceof FormData) {
      opts.body = body;
    } else {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(path, opts);
  const payload = res.status === 204 ? null : await res.json();
  if (!res.ok) {
    throw new Error((payload && payload.error) || `Request failed with ${res.status}`);
  }
  return payload;
}

// ---------------------------------------------------------------------------
// Load and render records
// ---------------------------------------------------------------------------
async function loadRecords() {
  try {
    records = await api("GET", "/api/records");
    undoStack = [];
    setDirty(false);
    renderUndoState();
    renderTable();
    renderWorkspaceSummary();
    await loadFeedbackAlerts();
  } catch (e) {
    showBanner("danger", "Failed to load records: " + e.message);
  }
}

function statusBadge(status) {
  const map = { Active: "success", Draft: "secondary", Inactive: "danger" };
  const cls = map[status] || "secondary";
  return `<span class="badge bg-${cls}">${escHtml(status)}</span>`;
}

function renderTable() {
  const tbody = document.getElementById("recordsTbody");
  const visibleRecords = getVisibleRecords();

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">
      No records yet. Click <strong>New Record</strong> to add one.
    </td></tr>`;
    return;
  }

  if (visibleRecords.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">
      No records match the current filters.
    </td></tr>`;
    return;
  }

  tbody.innerHTML = visibleRecords.map(r => `
    <tr data-id="${escHtml(r.id)}">
      <td class="font-monospace small text-muted" title="${escHtml(r.id)}">${escHtml(r.id)}</td>
      <td class="truncate" title="${escHtml(r.canonical_question)}">${escHtml(r.canonical_question)}</td>
      <td class="truncate text-muted" title="${escHtml((r.alternate_phrasings||[]).join('\n'))}">
        ${escHtml((r.alternate_phrasings || []).join(", ") || "—")}
      </td>
      <td class="truncate" title="${escHtml(r.answer)}">${escHtml(r.answer)}</td>
      <td>${statusBadge(r.status)}</td>
      <td class="text-muted small">${escHtml(r.contributor || "—")}</td>
      <td class="text-muted small">${escHtml(r.reviewer || "—")}</td>
      <td class="text-center small text-muted">${escHtml(String(r.version || 1))}</td>
      <td>
        <button class="btn btn-sm btn-outline-secondary inspect-btn me-1" title="Inspect record">
          <i class="bi bi-eye-fill"></i>
        </button>
        <button class="btn btn-sm btn-outline-primary edit-btn me-1" title="Edit">
          <i class="bi bi-pencil-fill"></i>
        </button>
        ${r.status !== "Inactive" ? `
        <button class="btn btn-sm btn-outline-warning sunset-btn me-1" title="Sunset to inactive">
          <i class="bi bi-moon-stars-fill"></i>
        </button>` : ""}
        <button class="btn btn-sm btn-outline-danger delete-btn" title="Delete">
          <i class="bi bi-trash-fill"></i>
        </button>
      </td>
    </tr>
    ${expandedRecordId === r.id ? `
    <tr class="record-detail-row" data-detail-id="${escHtml(r.id)}">
      <td colspan="9" class="record-detail-cell p-0">
        <div class="p-3 p-lg-4">
          <div class="row g-3">
            <div class="col-lg-7">
              <div class="small text-uppercase fw-semibold text-muted mb-2">Approved answer</div>
              <div class="rendered-answer record-detail-answer border rounded editor-surface p-3">${escHtml(r.answer)}</div>
            </div>
            <div class="col-lg-5">
              <div class="small text-uppercase fw-semibold text-muted mb-2">Record metadata</div>
              <div class="border rounded editor-surface p-3 small">
                <div class="mb-2"><strong>Status:</strong> ${escHtml(r.status)}</div>
                <div class="mb-2"><strong>Contributor:</strong> ${escHtml(r.contributor || "—")}</div>
                <div class="mb-2"><strong>Reviewer:</strong> ${escHtml(r.reviewer || "—")}</div>
                <div class="mb-2"><strong>Tags:</strong> ${escHtml((r.tags || []).join(", ") || "—")}</div>
                <div><strong>Alternates:</strong><br>${escHtml((r.alternate_phrasings || []).join("\n") || "—")}</div>
              </div>
            </div>
          </div>
        </div>
      </td>
    </tr>` : ""}
  `).join("");

  tbody.querySelectorAll(".inspect-btn").forEach(btn => {
    const id = btn.closest("tr").dataset.id;
    btn.addEventListener("click", () => toggleRecordInspection(id));
  });

  tbody.querySelectorAll(".edit-btn").forEach(btn => {
    const id = btn.closest("tr").dataset.id;
    btn.addEventListener("click", () => openEditModal(id));
  });

  tbody.querySelectorAll(".delete-btn").forEach(btn => {
    const id = btn.closest("tr").dataset.id;
    btn.addEventListener("click", () => openDeleteModal(id));
  });

  tbody.querySelectorAll(".sunset-btn").forEach(btn => {
    const id = btn.closest("tr").dataset.id;
    btn.addEventListener("click", () => sunsetRecord(id));
  });

  renderWorkspaceSummary();
  renderNeedsReviewQueue();
}

function toggleRecordInspection(id) {
  expandedRecordId = expandedRecordId === id ? null : id;
  renderTable();
}

function getVisibleRecords() {
  return records.filter(record => {
    if (statusFilter !== "All" && record.status !== statusFilter) {
      return false;
    }

    if (!recordSearch) {
      return true;
    }

    const haystack = [
      record.id,
      record.canonical_question,
      record.answer,
      record.contributor,
      record.reviewer,
      ...(record.tags || []),
      ...(record.alternate_phrasings || []),
    ]
      .join("\n")
      .toLowerCase();

    return haystack.includes(recordSearch);
  });
}

function renderWorkspaceSummary() {
  const total = records.length;
  const active = records.filter(record => record.status === "Active").length;
  const draft = records.filter(record => record.status === "Draft").length;
  const inactive = records.filter(record => record.status === "Inactive").length;
  const visible = getVisibleRecords().length;

  document.getElementById("statTotal").textContent = String(total);
  document.getElementById("statActive").textContent = String(active);
  document.getElementById("statDraft").textContent = String(draft);
  document.getElementById("statInactive").textContent = String(inactive);

  const summary = document.getElementById("recordsSummary");
  summary.textContent = `${visible} visible of ${total} total record(s)`;
}

function cloneRecord(record) {
  return JSON.parse(JSON.stringify(record));
}

function summarizeText(text, limit = 110) {
  const compact = String(text || "").replace(/\s+/g, " ").trim();
  if (compact.length <= limit) {
    return compact;
  }
  return `${compact.slice(0, limit - 1).trimEnd()}…`;
}

function summarizeRecord(record) {
  if (!record) return "";
  return [
    escHtml(record.canonical_question || ""),
    record.status ? escHtml(`Status: ${record.status}`) : "",
    record.answer ? escHtml(summarizeText(record.answer, 90)) : "",
  ].filter(Boolean).join(" — ");
}

function describePendingAction(action) {
  if (!action) {
    return {
      label: "Change",
      details: "",
    };
  }

  if (action.type === "batch-create") {
    const records = action.records || [];
    const sample = records.slice(0, 3).map(record => summarizeRecord(record)).filter(Boolean).join("<br>");
    return {
      label: "Bulk import",
      details: [
        `${records.length} record(s) imported`,
        sample ? `Examples:<br>${sample}` : "",
      ].filter(Boolean).join("<br>"),
    };
  }

  if (action.type === "delete") {
    const record = action.record || {};
    return {
      label: "Deleted",
      details: summarizeRecord(record),
    };
  }

  if (action.type === "create") {
    const record = action.record || {};
    return {
      label: "Created",
      details: summarizeRecord(record),
    };
  }

  if (action.type === "update") {
    const before = action.before || {};
    const after = action.after || {};
    const label = action.mode === "sunset" ? "Sunset" : "Updated";
    const details = [
      escHtml(before.canonical_question || after.canonical_question || ""),
      before.status && after.status && before.status !== after.status
        ? escHtml(`Status: ${before.status} → ${after.status}`)
        : "",
      before.answer && after.answer && before.answer !== after.answer
        ? escHtml(`Answer updated: ${summarizeText(after.answer, 70)}`)
        : "",
    ].filter(Boolean).join("<br>");

    return {
      label,
      details: details || summarizeRecord(after || before),
    };
  }

  return {
    label: "Change",
    details: "",
  };
}

function setDirty(isDirty) {
  hasUnpublishedChanges = isDirty;
  const badge = document.getElementById("dirtyBadge");
  badge.classList.toggle("d-none", !isDirty);
}

function pushUndo(action) {
  undoStack.push(action);
  renderUndoState();
}

function renderUndoState() {
  document.getElementById("undoChangeBtn").disabled = undoStack.length === 0;
  renderPublishStage();
}

function getPendingChangeStats() {
  const stats = {
    total: 0,
    created: 0,
    updated: 0,
    deleted: 0,
    sunset: 0,
    imported: 0,
  };

  for (const action of undoStack) {
    if (action.type === "create") {
      stats.created += 1;
      stats.total += 1;
    } else if (action.type === "batch-create") {
      const count = (action.ids || []).length;
      stats.imported += count;
      stats.total += count;
    } else if (action.type === "update") {
      if (action.mode === "sunset") {
        stats.sunset += 1;
      } else {
        stats.updated += 1;
      }
      stats.total += 1;
    } else if (action.type === "delete") {
      stats.deleted += 1;
      stats.total += 1;
    }
  }

  return stats;
}

function getPendingChangeEntries(limit = 12) {
  const entries = [];

  for (const action of undoStack) {
    const description = describePendingAction(action);
    if (action.type === "batch-create") {
      entries.push({
        action: description.label,
        id: (action.ids || []).slice(0, 3).join(", ") || "(pending ids)",
        question: `${(action.records || []).length} imported record(s)`,
        details: description.details,
      });
      continue;
    }

    const record = action.record || action.before || action.after || {};
    entries.push({
      action: description.label,
      id: record.id || action.id || "(pending id)",
      question: record.canonical_question || action.question || "",
      details: description.details,
    });
  }

  return entries.slice(-limit).reverse();
}

function renderPublishStage() {
  const summary = document.getElementById("publishStageSummary");
  const list = document.getElementById("publishStageList");
  const recordsList = document.getElementById("publishStageRecords");
  const stageBtn = document.getElementById("publishStageBtn");
  const stats = getPendingChangeStats();

  if (stats.total === 0) {
    summary.textContent = "No unpublished changes are currently staged.";
    list.innerHTML = '<div class="publish-stage-empty px-3 py-2 small text-muted">Make edits, imports, sunsets, or deletes to stage changes before publishing.</div>';
    recordsList.innerHTML = "";
    stageBtn.disabled = true;
    return;
  }

  summary.textContent = `${stats.total} staged change(s) pending publish.`;
  const chips = [];
  if (stats.created) chips.push(`<span class="badge text-bg-success">Created: ${stats.created}</span>`);
  if (stats.updated) chips.push(`<span class="badge text-bg-primary">Updated: ${stats.updated}</span>`);
  if (stats.sunset) chips.push(`<span class="badge text-bg-warning">Sunset: ${stats.sunset}</span>`);
  if (stats.imported) chips.push(`<span class="badge text-bg-info">Imported: ${stats.imported}</span>`);
  if (stats.deleted) chips.push(`<span class="badge text-bg-danger">Deleted: ${stats.deleted}</span>`);
  list.innerHTML = chips.join("");

  const entries = getPendingChangeEntries();
  recordsList.innerHTML = entries.map(entry => `
    <div class="border rounded px-2 py-2 mb-1 editor-surface">
      <span class="badge text-bg-light border me-1">${escHtml(entry.action)}</span>
      <span class="font-monospace">${escHtml(entry.id || "(pending id)")}</span>
      ${entry.question ? `<span class="text-muted"> — ${escHtml(entry.question)}</span>` : ""}
      ${entry.details ? `<div class="small text-muted mt-1">${entry.details}</div>` : ""}
    </div>
  `).join("");

  stageBtn.disabled = false;
}

async function undoLastChange() {
  const action = undoStack.pop();
  if (!action) return;

  try {
    if (action.type === "create") {
      const recordId = action.id || (action.record && action.record.id);
      await api("DELETE", `/api/records/${encodeURIComponent(recordId)}`);
      records = records.filter(record => record.id !== recordId);
    } else if (action.type === "update") {
      const previous = action.before;
      const restored = await api("PUT", `/api/records/${encodeURIComponent(previous.id)}`, {
        canonical_question: previous.canonical_question,
        alternate_phrasings: previous.alternate_phrasings || [],
        answer: previous.answer,
        status: previous.status,
        contributor: previous.contributor || "",
        reviewer: previous.reviewer || "",
        tags: previous.tags || [],
      });
      const idx = records.findIndex(record => record.id === previous.id);
      if (idx !== -1) records[idx] = restored;
    } else if (action.type === "delete") {
      const restored = await api("POST", "/api/records", action.record);
      records.push(restored);
    } else if (action.type === "batch-create") {
      for (const id of action.ids) {
        await api("DELETE", `/api/records/${encodeURIComponent(id)}`);
      }
      records = records.filter(record => !action.ids.includes(record.id));
    }

    setDirty(undoStack.length > 0);
    renderUndoState();
    renderTable();
    showBanner("info", "Last unpublished change was undone.");
  } catch (e) {
    undoStack.push(action);
    renderUndoState();
    showBanner("danger", "Undo failed: " + e.message);
  }
}

function getNeedsReviewRecords() {
  return records.filter(record => record.status === "Draft" && !(record.reviewer || "").trim());
}

function renderNeedsReviewQueue() {
  const needsReview = getNeedsReviewRecords();
  const countNode = document.getElementById("needsReviewCount");
  const listNode = document.getElementById("needsReviewList");

  countNode.textContent = String(needsReview.length);

  if (!needsReview.length) {
    listNode.innerHTML = `
      <div class="review-queue-empty p-3 text-muted small">
        No draft records are currently missing a reviewer.
      </div>`;
    return;
  }

  listNode.innerHTML = needsReview.map(record => `
    <button type="button" class="btn btn-outline-warning text-start review-item" data-id="${escHtml(record.id)}">
      <div class="fw-semibold mb-1">${escHtml(record.canonical_question)}</div>
      <div class="small text-muted">Contributor: ${escHtml(record.contributor || "unassigned")}</div>
    </button>
  `).join("");

  listNode.querySelectorAll(".review-item").forEach(btn => {
    const id = btn.dataset.id;
    btn.addEventListener("click", () => {
      expandedRecordId = id;
      renderTable();
      openEditModal(id);
    });
  });
}

async function loadFeedbackAlerts() {
  try {
    const result = await api("GET", "/api/editor/feedback-alerts");
    feedbackAlerts = result.alerts || [];
    renderFeedbackAlerts();
    if (feedbackAlerts.length) {
      showBanner(
        "warning",
        `<strong>${feedbackAlerts.length}</strong> unresolved answer feedback alert(s) need attention in the editor.`
      );
    }
  } catch (e) {
    showBanner("danger", "Failed to load feedback alerts: " + e.message);
  }
}

function renderFeedbackAlerts() {
  const countNode = document.getElementById("feedbackAlertCount");
  const summaryNode = document.getElementById("feedbackAlertSummary");
  const listNode = document.getElementById("feedbackAlertList");

  countNode.textContent = String(feedbackAlerts.length);

  if (!feedbackAlerts.length) {
    summaryNode.textContent = "No unresolved feedback alerts.";
    listNode.innerHTML = `
      <div class="review-queue-empty p-3 text-muted small">
        User feedback will appear here when an answer is marked not helpful or an answer fallback is returned.
      </div>`;
    return;
  }

  summaryNode.textContent = `${feedbackAlerts.length} unresolved alert(s) from user feedback.`;
  listNode.innerHTML = feedbackAlerts.map(alert => `
    <div class="border rounded p-3 editor-surface">
      <div class="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-2">
        <div>
          <div class="fw-semibold">${escHtml(alert.question || "Feedback item")}</div>
          <div class="small text-muted">
            ${escHtml(alert.fallback_type ? `Fallback: ${alert.fallback_type}` : alert.matched ? "Matched answer" : "Unmatched answer")}
            ${alert.occurrences > 1 ? ` · ${escHtml(String(alert.occurrences))} reports` : ""}
          </div>
        </div>
        <span class="badge text-bg-warning">Needs attention</span>
      </div>
      ${alert.comment ? `<div class="small text-muted mb-2">Comment: ${escHtml(alert.comment)}</div>` : ""}
      <div class="d-flex flex-wrap gap-2 align-items-center">
        ${alert.record_id ? `<button type="button" class="btn btn-outline-primary btn-sm open-feedback-record" data-id="${escHtml(alert.record_id)}">Open record</button>` : ""}
        <button type="button" class="btn btn-success btn-sm resolve-feedback-alert" data-id="${escHtml(alert.id)}">Mark addressed</button>
      </div>
    </div>
  `).join("");

  listNode.querySelectorAll(".open-feedback-record").forEach(btn => {
    btn.addEventListener("click", () => {
      openEditModal(btn.dataset.id);
    });
  });

  listNode.querySelectorAll(".resolve-feedback-alert").forEach(btn => {
    btn.addEventListener("click", () => resolveFeedbackAlert(btn.dataset.id));
  });
}

async function resolveFeedbackAlert(id) {
  try {
    await api("POST", `/api/editor/feedback-alerts/${encodeURIComponent(id)}/resolve`);
    feedbackAlerts = feedbackAlerts.filter(alert => alert.id !== id);
    renderFeedbackAlerts();
    showBanner("success", "Feedback alert marked as addressed.");
  } catch (e) {
    showBanner("danger", "Failed to resolve feedback alert: " + e.message);
  }
}

// ---------------------------------------------------------------------------
// Edit modal
// ---------------------------------------------------------------------------
function openEditModal(id) {
  const r = records.find(x => x.id === id);
  const isNew = !r;

  document.getElementById("editModalLabel").textContent = isNew ? "New Record" : "Edit Record";
  document.getElementById("editId").value            = r ? r.id : "";
  document.getElementById("editCanonical").value     = r ? r.canonical_question : "";
  document.getElementById("editAlternates").value    = r ? (r.alternate_phrasings || []).join("\n") : "";
  document.getElementById("editAnswer").value        = r ? r.answer : "";
  document.getElementById("editStatus").value        = r ? r.status : "Draft";
  document.getElementById("editContributor").value   = r ? (r.contributor || "") : "";
  document.getElementById("editReviewer").value      = r ? (r.reviewer || "") : "";
  document.getElementById("editTags").value          = r ? (r.tags || []).join(", ") : "";
  document.getElementById("editErrors").classList.add("d-none");

  editModal.show();
}

document.getElementById("saveRecordBtn").addEventListener("click", async () => {
  const id         = document.getElementById("editId").value.trim();
  const canonical  = document.getElementById("editCanonical").value.trim();
  const alternates = document.getElementById("editAlternates").value
    .split("\n").map(s => s.trim()).filter(Boolean);
  const answer     = document.getElementById("editAnswer").value.trim();
  const status     = document.getElementById("editStatus").value;
  const contributor= document.getElementById("editContributor").value.trim();
  const reviewer   = document.getElementById("editReviewer").value.trim();
  const tags       = document.getElementById("editTags").value
    .split(",").map(s => s.trim()).filter(Boolean);

  const errDiv = document.getElementById("editErrors");
  const errs   = [];
  if (!canonical) errs.push("Canonical Question is required.");
  if (!answer)    errs.push("Answer is required.");
  if (errs.length) {
    errDiv.innerHTML = errs.map(e => `<div>${escHtml(e)}</div>`).join("");
    errDiv.classList.remove("d-none");
    return;
  }
  errDiv.classList.add("d-none");

  const payload = { canonical_question: canonical, alternate_phrasings: alternates,
                    answer, status, contributor, reviewer, tags };

  try {
    let saved;
    if (id) {
      const existing = records.find(record => record.id === id);
      const action = existing ? {
        type: "update",
        before: cloneRecord(existing),
        mode: existing.status !== "Inactive" && status === "Inactive" ? "sunset" : "update",
      } : null;
      saved = await api("PUT", `/api/records/${encodeURIComponent(id)}`, payload);
      const idx = records.findIndex(r => r.id === id);
      if (idx !== -1) records[idx] = saved;
      if (action) {
        action.after = cloneRecord(saved);
        pushUndo(action);
      }
    } else {
      saved = await api("POST", "/api/records", payload);
      records.push(saved);
      pushUndo({
        type: "create",
        id: saved.id,
        question: saved.canonical_question || canonical,
        record: cloneRecord(saved),
      });
    }
    setDirty(true);
    renderTable();
    editModal.hide();
    showBanner("success",
      `Record <strong>${escHtml(saved.id)}</strong> saved.
       Click <strong>Publish Updates</strong> to persist changes.`);
  } catch (e) {
    errDiv.textContent = "Save failed: " + e.message;
    errDiv.classList.remove("d-none");
  }
});

// ---------------------------------------------------------------------------
// Delete modal
// ---------------------------------------------------------------------------
function openDeleteModal(id) {
  pendingDeleteId = id;
  document.getElementById("deleteRecordId").textContent = id;
  deleteModal.show();
}

document.getElementById("confirmDeleteBtn").addEventListener("click", async () => {
  if (!pendingDeleteId) return;
  try {
    const deleted = records.find(record => record.id === pendingDeleteId);
    await api("DELETE", `/api/records/${encodeURIComponent(pendingDeleteId)}`);
    records = records.filter(r => r.id !== pendingDeleteId);
    if (deleted) {
      pushUndo({ type: "delete", record: cloneRecord(deleted) });
    }
    setDirty(true);
    renderTable();
    deleteModal.hide();
    showBanner("warning",
      `Record <strong>${escHtml(pendingDeleteId)}</strong> deleted from memory.
       Click <strong>Publish Updates</strong> to persist.`);
    pendingDeleteId = null;
  } catch (e) {
    showBanner("danger", "Delete failed: " + e.message);
  }
});

async function sunsetRecord(id) {
  const record = records.find(item => item.id === id);
  if (!record || record.status === "Inactive") return;

  try {
    const action = { type: "update", before: cloneRecord(record), mode: "sunset" };
    const saved = await api("PUT", `/api/records/${encodeURIComponent(id)}`, {
      canonical_question: record.canonical_question,
      alternate_phrasings: record.alternate_phrasings || [],
      answer: record.answer,
      status: "Inactive",
      contributor: record.contributor || "",
      reviewer: record.reviewer || "",
      tags: record.tags || [],
    });
    action.after = cloneRecord(saved);
    pushUndo(action);
    const idx = records.findIndex(item => item.id === id);
    if (idx !== -1) records[idx] = saved;
    setDirty(true);
    renderTable();
    showBanner(
      "warning",
      `Record <strong>${escHtml(id)}</strong> marked as <strong>Inactive</strong>. Click <strong>Publish Updates</strong> to persist the sunset change.`
    );
  } catch (e) {
    showBanner("danger", "Sunset failed: " + e.message);
  }
}

// ---------------------------------------------------------------------------
// Publish
// ---------------------------------------------------------------------------
document.getElementById("publishBtn").addEventListener("click", async () => {
  const btn = document.getElementById("publishBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Publishing…';

  try {
    const result = await api("POST", "/api/publish");
    if (result.success) {
      undoStack = [];
      setDirty(false);
      renderUndoState();
      showBanner("success",
        `<i class="bi bi-cloud-check-fill me-1"></i>
         <strong>Published successfully.</strong>
         ${result.count} record(s) saved and index rebuilt.`);
    } else {
      const errLines = Object.entries(result.errors || {})
        .map(([id, msgs]) => `<li><strong>${escHtml(id)}</strong>: ${msgs.map(escHtml).join("; ")}</li>`)
        .join("");
      showBanner("danger",
        `<strong>Publish failed — validation errors:</strong><ul class="mb-0 mt-1">${errLines}</ul>`);
    }
  } catch (e) {
    showBanner("danger", "Publish error: " + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-cloud-upload-fill me-1"></i>Publish Updates';
  }
});

// ---------------------------------------------------------------------------
// Add row shortcut
// ---------------------------------------------------------------------------
document.getElementById("addRowBtn").addEventListener("click", () => openEditModal(null));
document.getElementById("undoChangeBtn").addEventListener("click", () => undoLastChange());
document.getElementById("publishStageBtn").addEventListener("click", () => {
  document.getElementById("publishBtn").click();
});

document.getElementById("exportCsvBtn").addEventListener("click", () => {
  window.open("/api/records/export?format=csv", "_blank");
});

document.getElementById("exportXlsxBtn").addEventListener("click", () => {
  window.open("/api/records/export?format=xlsx", "_blank");
});

document.getElementById("downloadImportCsvTemplateBtn").addEventListener("click", () => {
  window.open("/api/records/import-template?format=csv", "_blank");
});

document.getElementById("downloadImportXlsxTemplateBtn").addEventListener("click", () => {
  window.open("/api/records/import-template?format=xlsx", "_blank");
});

document.querySelectorAll(".answer-format-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    applyAnswerFormatting(btn.dataset.format);
  });
});

document.getElementById("recordSearchInput").addEventListener("input", event => {
  recordSearch = event.target.value.trim().toLowerCase();
  renderTable();
});

document.getElementById("statusFilter").addEventListener("change", event => {
  statusFilter = event.target.value;
  renderTable();
});

document.getElementById("clearFiltersBtn").addEventListener("click", () => {
  recordSearch = "";
  statusFilter = "All";
  document.getElementById("recordSearchInput").value = "";
  document.getElementById("statusFilter").value = "All";
  renderTable();
});

document.getElementById("showNeedsReviewBtn").addEventListener("click", () => {
  recordSearch = "";
  statusFilter = "Draft";
  document.getElementById("recordSearchInput").value = "";
  document.getElementById("statusFilter").value = "Draft";
  renderTable();
});

document.getElementById("bulkImportBtn").addEventListener("click", () => {
  resetImportPreview();
  bulkImportModal.show();
});

document.getElementById("previewImportBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("bulkImportFile");
  const file = fileInput.files && fileInput.files[0];
  const status = document.getElementById("bulkImportStatus").value;
  const contributor = document.getElementById("bulkImportContributor").value.trim();
  const reviewer = document.getElementById("bulkImportReviewer").value.trim();
  const tags = document.getElementById("bulkImportTags").value.trim();
  const errDiv = document.getElementById("bulkImportErrors");

  if (!file) {
    errDiv.textContent = "Please choose a CSV or XLSX file.";
    errDiv.classList.remove("d-none");
    return;
  }

  if (!/\.(csv|xlsx)$/i.test(file.name)) {
    errDiv.textContent = "Unsupported file type. Only CSV and XLSX are allowed.";
    errDiv.classList.remove("d-none");
    return;
  }

  errDiv.classList.add("d-none");
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("default_status", status);
    formData.append("default_contributor", contributor);
    formData.append("default_reviewer", reviewer);
    formData.append("default_tags", tags);

    const result = await api("POST", "/api/records/import-preview", formData);
    importPreviewRecords = result.records || [];
    renderImportPreview(result);
  } catch (e) {
    errDiv.textContent = "Preview failed: " + e.message;
    errDiv.classList.remove("d-none");
  }
});

document.getElementById("applyImportBtn").addEventListener("click", async () => {
  if (!importPreviewRecords.length) return;

  const btn = document.getElementById("applyImportBtn");
  const errDiv = document.getElementById("bulkImportErrors");
  btn.disabled = true;
  errDiv.classList.add("d-none");

  try {
    const createdRecords = [];
    for (const record of importPreviewRecords) {
      createdRecords.push(await api("POST", "/api/records", record));
    }
    pushUndo({
      type: "batch-create",
      ids: createdRecords.map(record => record.id),
      records: createdRecords.map(record => cloneRecord(record)),
    });
    records.push(...createdRecords);
    setDirty(true);
    renderTable();
    bulkImportModal.hide();
    showBanner(
      "success",
      `<strong>${createdRecords.length}</strong> parsed record(s) imported into memory. Click <strong>Publish Updates</strong> to persist them.`
    );
    resetImportPreview();
  } catch (e) {
    errDiv.textContent = "Import failed: " + e.message;
    errDiv.classList.remove("d-none");
  } finally {
    btn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// Banner helper
// ---------------------------------------------------------------------------
function showBanner(type, html) {
  const b = document.getElementById("feedbackBanner");
  b.className = `alert alert-${type} alert-dismissible fade show`;
  b.innerHTML = html + `<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  b.classList.remove("d-none");
  if (type === "success") {
    setTimeout(() => {
      b.classList.add("d-none");
    }, 6000);
  }
}

function resetImportPreview() {
  importPreviewRecords = [];
  document.getElementById("bulkImportFile").value = "";
  document.getElementById("bulkImportErrors").classList.add("d-none");
  document.getElementById("bulkImportSummary").textContent = "No preview yet.";
  document.getElementById("bulkImportPreview").innerHTML =
    '<div class="text-muted">Parsed records will appear here after preview.</div>';
  document.getElementById("applyImportBtn").disabled = true;
}

function renderImportPreview(result) {
  const errors = result.errors || [];
  const recordsToImport = result.records || [];
  const preview = document.getElementById("bulkImportPreview");
  const summary = document.getElementById("bulkImportSummary");
  const applyBtn = document.getElementById("applyImportBtn");

  summary.textContent =
    `Parsed ${recordsToImport.length} record(s). ${errors.length} issue(s) detected.`;
  applyBtn.disabled = recordsToImport.length === 0;

  if (!recordsToImport.length) {
    preview.innerHTML = '<div class="text-muted">No valid Q&A records were found in the uploaded file.</div>';
    return;
  }

  const errorBlock = errors.length
    ? `<div class="alert alert-warning small mb-3"><strong>Import issues:</strong><ul class="mb-0 mt-1">${errors.map(err => `<li>${escHtml(err)}</li>`).join("")}</ul></div>`
    : "";

  preview.innerHTML = errorBlock + recordsToImport.map((record, idx) => `
      <div class="border rounded editor-surface p-3 mb-3">
      <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
        <strong>${idx + 1}. ${escHtml(record.canonical_question)}</strong>
        <span class="badge bg-secondary">${escHtml(record.status)}</span>
      </div>
      <div class="text-muted small mb-2">${escHtml(record.contributor || "unassigned contributor")}</div>
      <div class="import-answer-preview rendered-answer">${record.answer_html || escHtml(record.answer)}</div>
    </div>
  `).join("");
}

function applyAnswerFormatting(format) {
  const textarea = document.getElementById("editAnswer");
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const before = textarea.value.slice(0, start);
  const selected = textarea.value.slice(start, end);
  const after = textarea.value.slice(end);

  let replacement = selected;
  if (format === "bold") {
    replacement = `**${selected || "bold text"}**`;
  } else if (format === "italic") {
    replacement = `*${selected || "italic text"}*`;
  } else if (format === "bullet") {
    const lines = (selected || "list item").split("\n");
    replacement = lines.map(line => line.startsWith("- ") ? line : `- ${line}`).join("\n");
  }

  textarea.value = before + replacement + after;
  textarea.focus();
}

function escHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
loadRecords();
