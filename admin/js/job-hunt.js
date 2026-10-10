"use strict";

(() => {
  const SECTION_KEY = "jobHuntApplications";
  const STATUSES = ["Saved", "To Apply", "Applied", "Interview", "Offer", "Rejected", "Withdrawn"];
  const MATCH_TERMS = [
    "supply chain", "warehouse", "inventory", "procurement", "purchasing",
    "distribution", "logistics", "transport", "fulfillment", "fulfilment",
    "wms", "sap", "erp", "supplier", "vendor", "3pl", "fleet",
    "otif", "stock reconciliation", "grn", "lpo", "forecasting",
    "team leadership", "operations", "safety", "excel", "reporting"
  ];

  const $ = id => document.getElementById(id);
  const formCard = $("jobFormCard");
  const form = $("jobForm");
  const list = $("jobList");
  const statusMessage = $("jobHuntStatus");
  let jobs = [];
  let isReady = false;
  let saveQueue = Promise.resolve();

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  function todayIso() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }

  function parseDate(value) {
    if (!value) return null;
    const text = String(value);
    const parsed = /^\d{4}-\d{2}-\d{2}$/.test(text)
      ? new Date(`${text}T00:00:00`)
      : new Date(text);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function fmtDate(value) {
    const date = parseDate(value);
    return date ? new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" }).format(date) : "Not set";
  }

  function fmtPosted(value) {
    const date = parseDate(value);
    return date ? new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(date) : "Not set";
  }

  function money(value) {
    if (value === "" || value === null || value === undefined || !Number.isFinite(Number(value))) return "Not specified";
    return `KES ${new Intl.NumberFormat("en-KE", { maximumFractionDigits: 0 }).format(Number(value))}/month`;
  }

  function salaryRange(job) {
    const low = job.salaryMin !== "" && job.salaryMin != null ? Number(job.salaryMin) : null;
    const high = job.salaryMax !== "" && job.salaryMax != null ? Number(job.salaryMax) : null;
    if (low === null && high === null) return "Salary not specified";
    if (low !== null && high !== null) return low === high ? money(low) : `${money(low)} – ${money(high)}`;
    return low !== null ? `From ${money(low)}` : `Up to ${money(high)}`;
  }

  function setMessage(message, kind = "info") {
    statusMessage.textContent = message;
    statusMessage.dataset.kind = kind;
  }

  function setFormMessage(message, kind = "info") {
    $("jobSaveMessage").textContent = message;
    $("jobSaveMessage").style.color = kind === "error" ? "var(--danger-fg)" : kind === "success" ? "var(--success-fg)" : "";
  }

  function keywordsFor(text) {
    const haystack = ` ${String(text || "").toLowerCase().replace(/[^a-z0-9+#]+/g, " ")} `;
    return [...new Set(MATCH_TERMS.filter(term => {
      const normalized = term.toLowerCase();
      return haystack.includes(` ${normalized} `) || haystack.includes(normalized);
    }))];
  }

  function getFilteredJobs() {
    const query = $("jobSearch").value.trim().toLowerCase();
    const status = $("statusFilter").value;
    const recency = $("recencyFilter").value;
    const now = new Date();

    return jobs.filter(job => {
      if (status !== "All" && job.status !== status) return false;
      if (query) {
        const haystack = [job.title, job.company, job.location, job.jobDescription, job.notes, job.contactName].join(" ").toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      if (recency !== "All") {
        const posted = parseDate(job.datePosted);
        if (!posted) return false;
        const age = (now.getTime() - posted.getTime()) / 86400000;
        if (age < 0 || age > Number(recency)) return false;
      }
      return true;
    }).sort((a, b) => {
      const left = a.datePosted || a.updatedAt || a.createdAt || "";
      const right = b.datePosted || b.updatedAt || b.createdAt || "";
      return right.localeCompare(left);
    });
  }

  function dueFollowUp(job) {
    if (!job.followUpDate || !["Applied", "Interview"].includes(job.status)) return false;
    const followDate = parseDate(job.followUpDate);
    if (!followDate) return false;
    const today = parseDate(todayIso());
    return followDate <= today;
  }

  function renderStats() {
    $("statSaved").textContent = jobs.filter(job => ["Saved", "To Apply"].includes(job.status)).length;
    $("statApplied").textContent = jobs.filter(job => ["Applied", "Interview", "Offer", "Rejected", "Withdrawn"].includes(job.status)).length;
    $("statInterviews").textContent = jobs.filter(job => job.status === "Interview" || job.interviewDate).length;
    $("statFollowups").textContent = jobs.filter(dueFollowUp).length;
  }

  function render() {
    renderStats();
    const visible = getFilteredJobs();
    $("jobCountBadge").textContent = `${visible.length} of ${jobs.length} ${jobs.length === 1 ? "record" : "records"}`;

    if (!visible.length) {
      const hasFilters = $("jobSearch").value || $("statusFilter").value !== "All" || $("recencyFilter").value !== "All";
      list.innerHTML = `<div class="job-empty-state"><div class="empty-state-icon"><i data-lucide="${hasFilters ? "search-x" : "briefcase-business"}" aria-hidden="true"></i></div><h3>${hasFilters ? "No matching opportunities" : "Your job tracker is ready"}</h3><p>${hasFilters ? "Try another search term or clear the filters." : "Save vacancies here to track salary, closing dates, application progress and follow-ups."}</p>${hasFilters ? "" : '<button type="button" class="primary-button" data-action="new"><i data-lucide="plus" aria-hidden="true"></i><span>Add your first opportunity</span></button>'}</div>`;
      renderIcons();
      return;
    }

    list.innerHTML = visible.map(job => {
      const fits = keywordsFor(`${job.title || ""} ${job.jobDescription || ""} ${job.notes || ""}`);
      const shortNotes = String(job.notes || "").trim();
      const details = [
        `<p><strong>Expected salary:</strong> ${escapeHtml(salaryRange(job))}</p>`,
        `<p><strong>Posted:</strong> ${escapeHtml(fmtPosted(job.datePosted))} &nbsp; <strong>Closes:</strong> ${escapeHtml(fmtDate(job.closingDate))}</p>`,
        job.dateApplied ? `<p><strong>Applied:</strong> ${escapeHtml(fmtDate(job.dateApplied))}</p>` : "",
        job.followUpDate ? `<p class="${dueFollowUp(job) ? "job-followup-due" : ""}"><strong>Follow-up:</strong> ${escapeHtml(fmtDate(job.followUpDate))}${dueFollowUp(job) ? " · Due" : ""}</p>` : "",
        job.interviewDate ? `<p><strong>Interview:</strong> ${escapeHtml(fmtDate(job.interviewDate))}</p>` : "",
        job.contactName ? `<p><strong>Contact:</strong> ${escapeHtml(job.contactName)}</p>` : "",
        shortNotes ? `<p><strong>Notes:</strong> ${escapeHtml(shortNotes.length > 240 ? `${shortNotes.slice(0, 237)}…` : shortNotes)}</p>` : ""
      ].filter(Boolean).join("");
      const url = safeUrl(job.jobUrl);

      return `<article class="job-card" data-job-id="${escapeHtml(job.id)}">
        <div class="job-card-top"><div class="job-card-title"><h3>${escapeHtml(job.title)}</h3><div class="job-card-company">${escapeHtml(job.company)}</div><div class="job-card-meta"><span><i data-lucide="map-pin" aria-hidden="true"></i>${escapeHtml(job.location || "Location not specified")}</span><span><i data-lucide="building-2" aria-hidden="true"></i>${escapeHtml(job.workMode || "Not specified")}</span><span><i data-lucide="radio-tower" aria-hidden="true"></i>${escapeHtml(job.source || "Other")}</span></div></div><span class="job-status" data-status="${escapeHtml(job.status)}">${escapeHtml(job.status)}</span></div>
        <div class="job-keyword-fit">Keyword overlap: <strong>${fits.length} relevant terms</strong>${fits.length ? ` · ${escapeHtml(fits.slice(0, 7).join(", "))}${fits.length > 7 ? "…" : ""}` : " · Add a job description for a better comparison"}</div>
        <div class="job-card-main"><div class="job-card-detail">${details || "<p>No extra details added yet.</p>"}</div><div class="job-card-actions">${url ? `<a class="secondary-button" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open advert</a>` : ""}<button type="button" class="secondary-button" data-action="edit" data-id="${escapeHtml(job.id)}">Edit</button>${job.status !== "Applied" && job.status !== "Interview" && job.status !== "Offer" ? `<button type="button" class="secondary-button" data-action="mark-applied" data-id="${escapeHtml(job.id)}">Mark applied</button>` : ""}<button type="button" class="danger-button" data-action="delete" data-id="${escapeHtml(job.id)}">Delete</button></div></div>
      </article>`;
    }).join("");
    renderIcons();
  }

  function safeUrl(value) {
    const text = String(value || "").trim();
    if (!text) return "";
    try {
      const url = new URL(text);
      return ["https:", "http:"].includes(url.protocol) ? url.href : "";
    } catch { return ""; }
  }

  function renderIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
    }
  }

  function showForm(job = null) {
    form.reset();
    $("jobId").value = job?.id || "";
    $("jobFormTitle").textContent = job ? "Edit opportunity" : "Add opportunity";
    $("saveJobButton").querySelector("span").textContent = job ? "Save changes" : "Save opportunity";
    $("jobTitle").value = job?.title || "";
    $("company").value = job?.company || "";
    $("location").value = job?.location || "Nairobi, Kenya";
    $("workMode").value = job?.workMode || "On-site";
    $("datePosted").value = job?.datePosted || "";
    $("closingDate").value = job?.closingDate || "";
    $("status").value = job?.status || "Saved";
    $("source").value = job?.source || "LinkedIn";
    $("salaryMin").value = job?.salaryMin ?? "";
    $("salaryMax").value = job?.salaryMax ?? "";
    $("dateApplied").value = job?.dateApplied || "";
    $("followUpDate").value = job?.followUpDate || "";
    $("interviewDate").value = job?.interviewDate || "";
    $("contactName").value = job?.contactName || "";
    $("jobUrl").value = job?.jobUrl || "";
    $("jobDescription").value = job?.jobDescription || "";
    $("notes").value = job?.notes || "";
    setFormMessage("");
    formCard.hidden = false;
    formCard.scrollIntoView({ behavior: "smooth", block: "start" });
    $("jobTitle").focus({ preventScroll: true });
  }

  function hideForm() {
    formCard.hidden = true;
    form.reset();
    setFormMessage("");
  }

  function formValue(id) { return $(id).value.trim(); }

  function collectForm() {
    const salaryMin = formValue("salaryMin");
    const salaryMax = formValue("salaryMax");
    if (salaryMin && Number(salaryMin) < 0 || salaryMax && Number(salaryMax) < 0) throw new Error("Salary cannot be negative.");
    if (salaryMin && salaryMax && Number(salaryMin) > Number(salaryMax)) throw new Error("Minimum salary cannot be greater than maximum salary.");
    const url = formValue("jobUrl");
    if (url && !safeUrl(url)) throw new Error("Enter a valid http or https job advert URL.");
    return {
      id: formValue("jobId") || (window.crypto?.randomUUID ? crypto.randomUUID() : `job-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`),
      title: formValue("jobTitle"), company: formValue("company"),
      location: formValue("location"), workMode: formValue("workMode"),
      datePosted: formValue("datePosted"), closingDate: formValue("closingDate"),
      status: STATUSES.includes(formValue("status")) ? formValue("status") : "Saved",
      source: formValue("source"), salaryMin, salaryMax,
      dateApplied: formValue("dateApplied"), followUpDate: formValue("followUpDate"),
      interviewDate: formValue("interviewDate"), contactName: formValue("contactName"),
      jobUrl: url, jobDescription: formValue("jobDescription"), notes: formValue("notes"),
      createdAt: jobs.find(job => job.id === formValue("jobId"))?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  async function persist(nextJobs, successMessage) {
    if (!isReady) throw new Error("The tracker is not connected to the server yet.");
    const previousJobs = jobs;
    jobs = nextJobs;
    render();
    setMessage("Saving securely to the server…");
    // Queue immutable snapshots so quick consecutive edits cannot send stale data.
    saveQueue = saveQueue.catch(() => undefined).then(() => window.portfolioApi.save(SECTION_KEY, nextJobs));
    try {
      await saveQueue;
      setMessage(successMessage, "success");
    } catch (error) {
      if (jobs === nextJobs) {
        jobs = previousJobs;
        render();
      }
      setMessage(error?.message || "Could not save changes to the server.", "error");
      throw error;
    }
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (!form.reportValidity()) return;
    try {
      const job = collectForm();
      const existing = jobs.some(item => item.id === job.id);
      const next = existing ? jobs.map(item => item.id === job.id ? job : item) : [job, ...jobs];
      await persist(next, existing ? "Opportunity updated and saved." : "Opportunity added and saved.");
      hideForm();
    } catch (error) {
      setFormMessage(error?.message || "Unable to save this opportunity.", "error");
    }
  }

  async function handleListClick(event) {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    const id = button.dataset.id;
    if (action === "new") { showForm(); return; }
    const job = jobs.find(item => item.id === id);
    if (!job) return;
    if (action === "edit") { showForm(job); return; }
    if (action === "mark-applied") {
      const updated = { ...job, status: "Applied", dateApplied: job.dateApplied || todayIso(), updatedAt: new Date().toISOString() };
      try { await persist(jobs.map(item => item.id === id ? updated : item), "Application status updated."); }
      catch { /* The status banner already explains the error. */ }
      return;
    }
    if (action === "delete") {
      const confirmed = window.confirm(`Delete the tracked opportunity “${job.title}” at ${job.company}? This cannot be undone.`);
      if (!confirmed) return;
      try { await persist(jobs.filter(item => item.id !== id), "Opportunity deleted."); }
      catch { /* The status banner already explains the error. */ }
    }
  }

  function exportCsv() {
    const headers = ["title", "company", "location", "workMode", "datePosted", "closingDate", "status", "source", "salaryMin", "salaryMax", "dateApplied", "followUpDate", "interviewDate", "contactName", "jobUrl", "jobDescription", "notes", "createdAt", "updatedAt"];
    const cell = value => {
      const text = String(value ?? "");
      return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    };
    const csv = [headers.join(","), ...jobs.map(job => headers.map(key => cell(job[key])).join(","))].join("\r\n");
    const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8;" });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `job-hunt-applications-${todayIso()}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
    setMessage(`Exported ${jobs.length} tracked ${jobs.length === 1 ? "opportunity" : "opportunities"}.`, "success");
  }

  async function init() {
    if (!window.portfolioApi) {
      setMessage("Portfolio API script did not load. Refresh the page or check the scripts.", "error");
      return;
    }
    if (!window.portfolioAuth?.getStoredToken?.()) {
      setMessage("Sign in through the admin login page to use the private job tracker.", "error");
      return;
    }
    try {
      await window.portfolioApi.ready;
      const response = await window.portfolioApi.load();
      const sections = response.sections || {};
      const serverJobs = sections[SECTION_KEY];
      jobs = Array.isArray(serverJobs) ? serverJobs.filter(item => item && typeof item === "object" && item.id) : [];
      isReady = true;
      setMessage("Connected. Changes save to your authenticated portfolio backend.", "success");
      render();
    } catch (error) {
      setMessage(error?.message || "Could not load the job tracker from the server.", "error");
      list.innerHTML = `<div class="job-empty-state"><h3>Unable to load tracker</h3><p>${escapeHtml(error?.message || "Check your connection and sign in again.")}</p></div>`;
    }
  }

  form.addEventListener("submit", onSubmit);
  $("newJobButton").addEventListener("click", () => showForm());
  $("closeJobForm").addEventListener("click", hideForm);
  $("cancelJobButton").addEventListener("click", hideForm);
  $("exportCsvButton").addEventListener("click", exportCsv);
  $("jobSearch").addEventListener("input", render);
  $("statusFilter").addEventListener("change", render);
  $("recencyFilter").addEventListener("change", render);
  list.addEventListener("click", handleListClick);
  init();
})();
