/* =========================================================
   EXPERIENCE MANAGEMENT - MVP
   Dennis Ndwigah Portfolio
   Storage contract: portfolioExperience
   ========================================================= */

(() => {
    "use strict";

    const STORAGE_KEY = "portfolioExperience";
    const EVENT_NAME = "portfolioExperienceUpdated";

    const DEFAULT_EXPERIENCE = [
        {
            id: "samaki-mtaani",
            title: "Operations and Supply Chain Lead",
            company: "Samaki Mtaani",
            startDate: "Jan 2026",
            endDate: "",
            location: "Nairobi, Kenya",
            description: "Building and managing the logistics and distribution backbone for a growing women-focused social enterprise.",
            achievements: [
                "Building a hub-and-spoke logistics system serving 300+ women vendors across Nairobi.",
                "Setting up distribution and last-mile infrastructure to keep vendors stocked and operational each morning.",
                "Managing supplier and 3PL relationships, negotiating terms and holding partners accountable.",
                "Tracking delivery performance and working toward more than 95% OTIF as the network scales.",
                "Recruiting and building the logistics team from the ground up.",
                "Monitoring stock levels across vendor locations and resolving supply gaps."
            ],
            visible: true,
            featured: true
        },
        {
            id: "kyosk",
            title: "Fulfillment Supervisor",
            company: "Kyosk Digital Services",
            startDate: "Oct 2023",
            endDate: "Oct 2025",
            location: "Voi, Kenya",
            description: "Managed end-to-end warehouse and last-mile fulfillment operations at a high-volume FMCG hub.",
            achievements: [
                "Managed more than 1,000 orders per week while achieving 92% OTIF and 92% CSAT.",
                "Oversaw more than KES 50M monthly GMV across owned and contracted delivery fleets.",
                "Renegotiated SLAs with six logistics partners, reducing monthly transport costs from KES 1.01M to KES 800K.",
                "Maintained 100% inventory accuracy across 560+ SKUs worth approximately KES 56M.",
                "Managed a warehouse team of 25 staff.",
                "Improved pick rates from 95 to 110 lines per person per shift.",
                "Maintained zero lost-time injuries during tenure."
            ],
            visible: true,
            featured: true
        },
        {
            id: "iprocure-manager",
            title: "Warehouse Manager",
            company: "iProcure Ltd",
            startDate: "Jun 2023",
            endDate: "Oct 2023",
            location: "Mwatate, Kenya",
            description: "Managed warehouse and transport operations supporting rural stockists and distribution activities.",
            achievements: [
                "Managed warehouse and transport operations supporting more than 80 rural stockists.",
                "Maintained approximately 95% fulfillment performance.",
                "Improved vehicle utilization from 62% to 85% through load consolidation and dispatch planning.",
                "Reduced delivery cost by approximately KES 4,500 per run.",
                "Reduced monthly shrinkage from approximately KES 450K to below KES 80K.",
                "Managed LPOs and maintained depot stock availability."
            ],
            visible: true,
            featured: false
        },
        {
            id: "iprocure-clerk",
            title: "Warehouse Clerk",
            company: "iProcure Ltd",
            startDate: "Mar 2023",
            endDate: "Jun 2023",
            location: "Mwatate, Kenya",
            description: "Supported warehouse receiving, stock control, documentation and inventory accuracy.",
            achievements: [
                "Verified GRNs, delivery notes, invoices and ERP records.",
                "Identified expiry and damaged-stock issues and supported vendor claims.",
                "Helped prevent approximately KES 600K in potential write-offs.",
                "Tracked monthly fuel consumption and flagged variances.",
                "Improved stock accuracy and reduced discrepancies during the first month."
            ],
            visible: true,
            featured: false
        },
        {
            id: "kuehne-nagel",
            title: "Dispatch & Warehouse Assistant - Freight Forwarding",
            company: "Kuehne + Nagel",
            startDate: "Nov 2021",
            endDate: "Feb 2023",
            location: "Nairobi, Kenya",
            description: "Supported air freight forwarding, warehouse dispatch, export documentation and coordination of time-critical cargo.",
            achievements: [
                "Supported air freight forwarding operations and export documentation.",
                "Helped reduce export turnaround time from five days to four days.",
                "Coordinated warehouse teams, airlines, clearing agents and customer service.",
                "Maintained zero non-conformities across audits during the period.",
                "Handled high-value and perishable air freight exceeding KES 500M cumulatively.",
                "Maintained zero cargo losses during the period."
            ],
            visible: true,
            featured: false
        },
        {
            id: "ruhrgold",
            title: "Assistant Warehouse Coordinator",
            company: "Ruhrgold Kenya Ltd",
            startDate: "Nov 2019",
            endDate: "Oct 2021",
            location: "Nairobi, Kenya",
            description: "Supported day-to-day warehouse operations, dispatch planning, warehouse improvement and HSE activities.",
            achievements: [
                "Supported daily warehouse and dispatch planning.",
                "Redesigned the warehouse layout and created 28% additional capacity.",
                "Helped avoid approximately KES 6M in warehouse expansion costs.",
                "Supported SOP and HSE training activities.",
                "Contributed to a 30% reduction in incidents."
            ],
            visible: true,
            featured: false
        }
    ];

    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

    function clean(value) {
        return String(value ?? "").trim();
    }

    function isCurrent(item) {
        const end = clean(item?.endDate).toLowerCase();
        return end === "" || end === "present" || end === "current";
    }

    function escapeHTML(value) {
        return clean(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function monthDate(value, fallbackDay = 1) {
        const match = clean(value).match(/^([A-Za-z]{3,9})\s+(\d{4})$/);
        if (!match) return null;

        const date = new Date(`${match[1]} ${fallbackDay}, ${match[2]}`);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    function durationBetween(startValue, endValue = "") {
        const start = monthDate(startValue);
        if (!start) return "";

        const end = isCurrent({ endDate: endValue })
            ? new Date()
            : monthDate(endValue);

        if (!end || end < start) return "";

        let months = (end.getFullYear() - start.getFullYear()) * 12;
        months += end.getMonth() - start.getMonth();

        if (months < 0) return "";

        const years = Math.floor(months / 12);
        const remainder = months % 12;

        const parts = [];
        if (years) parts.push(`${years} ${years === 1 ? "Year" : "Years"}`);
        if (remainder) parts.push(`${remainder} ${remainder === 1 ? "Month" : "Months"}`);

        return parts.join(" ") || "Less than 1 Month";
    }

    function normalize(item) {
        const normalized = {
            id: clean(item?.id) || `experience-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            title: clean(item?.title),
            company: clean(item?.company),
            startDate: clean(item?.startDate),
            endDate: isCurrent(item) ? "" : clean(item?.endDate),
            location: clean(item?.location),
            description: clean(item?.description),
            achievements: Array.isArray(item?.achievements)
                ? item.achievements.map(clean).filter(Boolean)
                : [],
            visible: item?.visible !== false,
            featured: item?.featured === true
        };

        normalized.currentRole = isCurrent(normalized);
        normalized.duration = durationBetween(normalized.startDate, normalized.endDate);
        return normalized;
    }

    function load() {
        const raw = localStorage.getItem(STORAGE_KEY);

        if (!raw) {
            const defaults = DEFAULT_EXPERIENCE.map(normalize);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(defaults));
            return defaults;
        }

        try {
            const parsed = JSON.parse(raw);
            if (!Array.isArray(parsed)) throw new Error("Invalid experience collection.");
            return parsed.map(normalize);
        } catch (error) {
            console.error("Experience storage is invalid.", error);
            return DEFAULT_EXPERIENCE.map(normalize);
        }
    }

    let experience = load();

    function commit(nextExperience) {
        experience = nextExperience.map(normalize);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(experience));

        window.dispatchEvent(new CustomEvent(EVENT_NAME, {
            detail: experience
        }));
    }

    function sort(items) {
        return [...items].sort((a, b) => {
            if (a.currentRole !== b.currentRole) return a.currentRole ? -1 : 1;

            const aDate = monthDate(a.startDate)?.getTime() || 0;
            const bDate = monthDate(b.startDate)?.getTime() || 0;

            return bDate - aDate;
        });
    }

    function showMessage(message, type = "success") {
        const node = $("#experienceMessage");
        if (!node) return;

        node.textContent = message;
        node.className = `save-message show ${type === "error" ? "error" : ""}`;

        clearTimeout(showMessage.timer);
        showMessage.timer = setTimeout(() => {
            node.textContent = "";
            node.className = "save-message";
        }, 3500);
    }

    function updateCount() {
        const count = $("#experienceCount");
        const currentCount = $("#currentExperienceCount");
        const previousCount = $("#previousExperienceCount");

        const current = experience.filter(item => item.currentRole).length;
        const previous = Math.max(experience.length - current, 0);

        if (count) count.textContent = String(experience.length);
        if (currentCount) currentCount.textContent = String(current);
        if (previousCount) previousCount.textContent = String(previous);
    }

    function render() {
        const list = $("#experienceList");
        if (!list) return;

        updateCount();

        const items = sort(experience);

        if (!items.length) {
            list.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">+</div>
                    <h3>No experience added</h3>
                    <p>Add your first professional position.</p>
                </div>
            `;
            return;
        }

        list.innerHTML = items.map((item, index) => `
            <article class="experience-admin-card">
                <div class="experience-card-top">
                    <span class="experience-number">${String(index + 1).padStart(2, "0")}</span>
                    <div class="experience-statuses">
                        ${item.currentRole ? '<span class="status-pill current">Current</span>' : ""}
                        ${item.featured ? '<span class="status-pill featured">Featured</span>' : ""}
                        ${item.visible
                            ? '<span class="status-pill visible">Public</span>'
                            : '<span class="status-pill hidden">Hidden</span>'}
                    </div>
                </div>

                <div class="experience-card-content">
                    <h3>${escapeHTML(item.title)}</h3>
                    <p class="experience-company">${escapeHTML(item.company)}</p>
                    <p class="experience-meta">
                        ${escapeHTML(item.startDate)} -
                        ${item.currentRole ? "Present" : escapeHTML(item.endDate)}
                        ${item.duration ? ` · ${escapeHTML(item.duration)}` : ""}
                        ${item.location ? ` · ${escapeHTML(item.location)}` : ""}
                    </p>
                    ${item.description ? `<p class="experience-description">${escapeHTML(item.description)}</p>` : ""}

                    <div class="achievement-preview">
                        ${item.achievements.slice(0, 3).map(a => `<span>• ${escapeHTML(a)}</span>`).join("")}
                        ${item.achievements.length > 3 ? `<small>+${item.achievements.length - 3} more achievements</small>` : ""}
                    </div>
                </div>

                <div class="experience-card-actions">
                    <button type="button" class="secondary-button" data-action="edit" data-id="${escapeHTML(item.id)}">Edit</button>
                    <button type="button" class="danger-button" data-action="delete" data-id="${escapeHTML(item.id)}">Delete</button>
                </div>
            </article>
        `).join("");
    }

    function setField(id, value) {
        const field = document.getElementById(id);
        if (field) field.value = value ?? "";
    }

    function edit(id) {
        const item = experience.find(entry => entry.id === id);
        if (!item) return;

        setField("experienceId", item.id);
        setField("jobTitle", item.title);
        setField("company", item.company);
        setField("startDate", item.startDate);
        setField("endDate", item.endDate);
        setField("workLocation", item.location);
        setField("description", item.description);
        setField("achievements", item.achievements.join("\n"));

        const visible = $("#visible");
        const featured = $("#featured");
        if (visible) visible.checked = item.visible;
        if (featured) featured.checked = item.featured;

        const title = $("#editorTitle");
        if (title) title.textContent = "Edit position";

        updateCurrentPreview();
        $("#experienceEditor")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function resetForm() {
        const form = $("#experienceForm");
        if (!form) return;

        form.reset();
        setField("experienceId", "");

        const visible = $("#visible");
        if (visible) visible.checked = true;

        const featured = $("#featured");
        if (featured) featured.checked = false;

        const title = $("#editorTitle");
        if (title) title.textContent = "Add a position";

        updateCurrentPreview();
    }

    function updateCurrentPreview() {
        const endDate = $("#endDate");
        const preview = $("#currentRolePreview");
        if (!endDate || !preview) return;

        const current = isCurrent({ endDate: endDate.value });

        preview.innerHTML = current
            ? '<span class="status-pill current">Current role</span><span>Leave the end date blank while this is active.</span>'
            : '<span class="status-pill">Past role</span><span>An end date automatically marks this as historical.</span>';
    }

    function validate(data, editingId = "") {
        const errors = [];

        if (!data.title) errors.push("Job title is required.");
        if (!data.company) errors.push("Company is required.");
        if (!data.startDate) errors.push("Start date is required.");

        if (data.startDate && !monthDate(data.startDate)) {
            errors.push("Start date must use Month Year, for example Jan 2026.");
        }

        if (data.endDate && !monthDate(data.endDate)) {
            errors.push("End date must use Month Year, for example Oct 2025.");
        }

        if (data.startDate && data.endDate) {
            const start = monthDate(data.startDate);
            const end = monthDate(data.endDate);

            if (start && end && end < start) {
                errors.push("End date cannot be earlier than the start date.");
            }
        }

        if (isCurrent(data)) {
            const anotherCurrent = experience.find(item =>
                item.id !== editingId && item.currentRole
            );

            if (anotherCurrent) {
                errors.push(
                    `There is already a current role: ${anotherCurrent.title} at ${anotherCurrent.company}. Add an end date to that role before making another role current.`
                );
            }
        }

        return errors;
    }

    function saveFromForm(event) {
        event.preventDefault();

        const data = {
            id: clean($("#experienceId")?.value),
            title: clean($("#jobTitle")?.value),
            company: clean($("#company")?.value),
            startDate: clean($("#startDate")?.value),
            endDate: clean($("#endDate")?.value),
            location: clean($("#workLocation")?.value),
            description: clean($("#description")?.value),
            achievements: clean($("#achievements")?.value)
                .split(/\r?\n/)
                .map(clean)
                .filter(Boolean),
            visible: $("#visible")?.checked !== false,
            featured: $("#featured")?.checked === true
        };

        const errors = validate(data, data.id);

        if (errors.length) {
            showMessage(errors[0], "error");
            return;
        }

        const normalized = normalize(data);

        if (data.id) {
            experience = experience.map(item =>
                item.id === data.id ? normalized : item
            );
        } else {
            experience.push(normalized);
        }

        commit(experience);
        render();
        resetForm();
        showMessage("Experience saved successfully.");
    }

    function remove(id) {
        const item = experience.find(entry => entry.id === id);
        if (!item) return;

        const confirmed = window.confirm(
            `Delete "${item.title}" at ${item.company}? This cannot be undone from the Admin interface.`
        );

        if (!confirmed) return;

        commit(experience.filter(entry => entry.id !== id));
        render();
        resetForm();
        showMessage("Experience deleted.");
    }

    function initSidebar() {
        const sidebar = $("#adminSidebar");
        const overlay = $("#sidebarOverlay");

        const close = () => {
            sidebar?.classList.remove("open");
            overlay?.classList.remove("active");
        };

        $("#openSidebar")?.addEventListener("click", () => {
            sidebar?.classList.add("open");
            overlay?.classList.add("active");
        });

        $("#closeSidebar")?.addEventListener("click", close);
        overlay?.addEventListener("click", close);

        $$(".nav-link").forEach(link => {
            link.addEventListener("click", () => {
                if (window.innerWidth <= 760) close();
            });
        });

        document.addEventListener("keydown", event => {
            if (event.key === "Escape") close();
        });
    }

    function init() {
        const year = $("#currentYear");
        if (year) year.textContent = String(new Date().getFullYear());

        initSidebar();

        $("#experienceForm")?.addEventListener("submit", saveFromForm);
        $("#cancelEdit")?.addEventListener("click", resetForm);

        $("#addExperienceButton")?.addEventListener("click", () => {
            resetForm();
            $("#experienceEditor")?.scrollIntoView({ behavior: "smooth", block: "start" });
            $("#jobTitle")?.focus();
        });

        $("#endDate")?.addEventListener("input", updateCurrentPreview);
        $("#endDate")?.addEventListener("change", updateCurrentPreview);

        $("#experienceList")?.addEventListener("click", event => {
            const button = event.target.closest("button[data-action]");
            if (!button) return;

            const id = button.dataset.id;
            if (button.dataset.action === "edit") edit(id);
            if (button.dataset.action === "delete") remove(id);
        });

        $("#resetExperience")?.addEventListener("click", () => {
            const confirmed = window.confirm(
                "Restore the original six experience records? This will replace your current experience data."
            );

            if (!confirmed) return;

            commit(DEFAULT_EXPERIENCE);
            render();
            resetForm();
            showMessage("Default experience restored.");
        });

        window.addEventListener("storage", event => {
            if (event.key !== STORAGE_KEY) return;
            experience = load();
            render();
        });

        updateCurrentPreview();
        render();

        $("#logoutButton")?.addEventListener("click", () => {
            if (window.confirm("Are you sure you want to sign out?")) {
                window.location.href = "login.html";
            }
        });
    }

    document.addEventListener("DOMContentLoaded", init);
})();
