/* QAKey — content editor */
"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let records = [];
let pendingDeleteId = null;

const editModal   = new bootstrap.Modal(document.getElementById("editModal"));
const deleteModal = new bootstrap.Modal(document.getElementById("deleteModal"));

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Load and render records
// ---------------------------------------------------------------------------
async function loadRecords() {
  try {
    records = await api("GET", "/api/records");
    renderTable();
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
  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">
      No records yet. Click <strong>New Record</strong> to add one.
    </td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => `
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
        <button class="btn btn-sm btn-outline-primary edit-btn me-1" title="Edit">
          <i class="bi bi-pencil-fill"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger delete-btn" title="Delete">
          <i class="bi bi-trash-fill"></i>
        </button>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll(".edit-btn").forEach(btn => {
    const id = btn.closest("tr").dataset.id;
    btn.addEventListener("click", () => openEditModal(id));
  });

  tbody.querySelectorAll(".delete-btn").forEach(btn => {
    const id = btn.closest("tr").dataset.id;
    btn.addEventListener("click", () => openDeleteModal(id));
  });
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
      saved = await api("PUT", `/api/records/${encodeURIComponent(id)}`, payload);
      const idx = records.findIndex(r => r.id === id);
      if (idx !== -1) records[idx] = saved;
    } else {
      saved = await api("POST", "/api/records", payload);
      records.push(saved);
    }
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
    await api("DELETE", `/api/records/${encodeURIComponent(pendingDeleteId)}`);
    records = records.filter(r => r.id !== pendingDeleteId);
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
