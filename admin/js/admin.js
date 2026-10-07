/* =========================================
   ADMIN DASHBOARD
   Dennis Ndwigah Portfolio
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("adminSidebar");
    const openSidebar = document.getElementById("openSidebar");
    const closeSidebar = document.getElementById("closeSidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const logoutButton = document.getElementById("logoutButton");
    const currentYear = document.getElementById("currentYear");

    const KEYS = {
        profile: "portfolioProfile",
        photo: "portfolioProfilePhoto",
        experience: "portfolioExperience",
        projects: "dennis_projects",
        skills: "dennis_skills",
        certifications: "dennis_certifications",
        documents: "portfolioDocuments",
        employerAccess: "employerAccess"
    };

    const read = (key, fallback = []) => {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : fallback;
        } catch (error) {
            console.warn(`Unable to read ${key}`, error);
            return fallback;
        }
    };

    const asArray = (value) => Array.isArray(value) ? value : [];

    const normalizeVisible = (item) => {
        if (!item || typeof item !== "object") return false;
        if (typeof item.visible === "boolean") return item.visible;
        if (typeof item.visibility === "string") return item.visibility !== "hidden";
        if (typeof item.public === "boolean") return item.public;
        return true;
    };

    const getDate = (value) => {
        if (!value) return null;
        const match = String(value).match(/^(\d{4})-(\d{2})/);
        if (match) return new Date(Number(match[1]), Number(match[2]) - 1, 1);
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? null : date;
    };

    const isCurrentRole = (role) => {
        const end = String(role?.endDate || role?.end || role?.to || "").trim().toLowerCase();
        return !end || ["present", "current", "ongoing", "now"].includes(end);
    };

    const calculateExperience = (roles) => {
        const visibleRoles = asArray(roles).filter(normalizeVisible);
        const starts = visibleRoles
            .map(role => getDate(role.startDate || role.start || role.from))
            .filter(Boolean);

        if (!starts.length) return "--";

        const earliest = new Date(Math.min(...starts.map(date => date.getTime())));
        const now = new Date();
        let months = (now.getFullYear() - earliest.getFullYear()) * 12 +
            (now.getMonth() - earliest.getMonth());

        if (now.getDate() < earliest.getDate()) months -= 1;
        months = Math.max(0, months);

        const years = Math.floor(months / 12);
        const remaining = months % 12;

        if (years === 0) return `${remaining} Month${remaining === 1 ? "" : "s"}`;
        if (remaining === 0) return `${years} Year${years === 1 ? "" : "s"}`;
        return `${years} Year${years === 1 ? "" : "s"} ${remaining} Month${remaining === 1 ? "" : "s"}`;
    };

    const visibleItems = (key) => asArray(read(key)).filter(normalizeVisible);

    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };

    const setBadge = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = String(value);
    };

    const setChecklist = (id, complete) => {
        const item = document.getElementById(id);
        if (!item) return;
        item.classList.toggle("complete", complete);
        const marker = item.querySelector("span");
        if (marker) marker.textContent = complete ? "✓" : "○";
    };

    /* -----------------------------------------
       CURRENT YEAR
       ----------------------------------------- */
    if (currentYear) currentYear.textContent = new Date().getFullYear();

    function updateGreeting() {
        const hour = new Date().getHours();
        const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
        setText("dashboardGreeting", `${greeting}, Dennis.`);
    }

    updateGreeting();

    /* -----------------------------------------
       SIDEBAR
       ----------------------------------------- */
    function openNavigation() {
        if (!sidebar) return;
        sidebar.classList.add("open");
        sidebarOverlay?.classList.add("active");
    }

    function closeNavigation() {
        if (!sidebar) return;
        sidebar.classList.remove("open");
        sidebarOverlay?.classList.remove("active");
    }

    openSidebar?.addEventListener("click", openNavigation);
    closeSidebar?.addEventListener("click", closeNavigation);
    sidebarOverlay?.addEventListener("click", closeNavigation);

    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("click", () => {
            if (window.innerWidth <= 760) closeNavigation();
        });
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closeNavigation();
    });

    /* -----------------------------------------
       SIGN OUT
       ----------------------------------------- */
    logoutButton?.addEventListener("click", () => {
        if (!window.confirm("Are you sure you want to sign out?")) return;
        window.location.href = "login.html";
    });

    /* -----------------------------------------
       PROFILE HEALTH
       ----------------------------------------- */
    function updateProfileHealth(profile, experience, skills) {
        const profileData = profile && typeof profile === "object" ? profile : {};
        const checks = {
            summary: Boolean(String(profileData.summary || profileData.professionalSummary || "").trim()),
            experience: experience.length > 0,
            skills: skills.length > 0,
            education: Boolean(String(profileData.education || profileData.educationSummary || "").trim()),
            photo: Boolean(localStorage.getItem(KEYS.photo)),
            contact: Boolean(String(profileData.email || profileData.phone || "").trim()),
            social: Boolean(String(profileData.linkedin || profileData.linkedinUrl || profileData.socialLinks || "").trim())
        };

        setChecklist("checkSummary", checks.summary);
        setChecklist("checkExperience", checks.experience);
        setChecklist("checkSkills", checks.skills);
        setChecklist("checkEducation", checks.education);
        setChecklist("checkPhoto", checks.photo);
        setChecklist("checkContact", checks.contact);
        setChecklist("checkSocial", checks.social);

        const completed = Object.values(checks).filter(Boolean).length;
        const percentage = Math.round((completed / Object.keys(checks).length) * 100);
        setText("profileCompletionValue", `${percentage}%`);
        const bar = document.getElementById("profileCompletionBar");
        if (bar) bar.style.width = `${percentage}%`;
    }

    /* -----------------------------------------
       DOCUMENT STATUS
       ----------------------------------------- */
    function updateDocumentStatus(documents, employerAccess) {
        const docs = asArray(documents);
        const activeDocs = docs.filter(doc => doc.status !== "inactive");
        const cv = activeDocs.find(doc => /cv|curriculum/i.test(String(doc.name || doc.title || "")));
        const protectedDocs = activeDocs.filter(doc => {
            const access = String(doc.access || doc.accessLevel || "").toLowerCase();
            return access && access !== "public";
        });

        setText("cvAccessStatus", cv ? (cv.access || cv.accessLevel || "Public") : "Not configured");
        setText("certificateAccessStatus", protectedDocs.length ? "Protected" : "Review");

        const accessRecords = asArray(employerAccess);
        const activeAccess = accessRecords.filter(item => {
            const status = String(item.status || "active").toLowerCase();
            return status !== "revoked" && status !== "inactive";
        });
        setText("employerAccessStatus", activeAccess.length ? `${activeAccess.length} Active` : "Not configured");
    }

    /* -----------------------------------------
       ACTIVITY
       ----------------------------------------- */
    function updateActivity() {
        const container = document.getElementById("activityList");
        if (!container) return;

        let activity = read("portfolioActivity", []);
        if (!Array.isArray(activity)) activity = [];

        const entries = activity.slice().sort((a, b) => {
            return new Date(b.timestamp || 0) - new Date(a.timestamp || 0);
        }).slice(0, 5);

        if (!entries.length) {
            container.innerHTML = `
                <div class="activity-item">
                    <div class="activity-marker">○</div>
                    <div>
                        <strong>No recent activity</strong>
                        <span>Your portfolio updates will appear here.</span>
                    </div>
                </div>`;
            return;
        }

        container.innerHTML = entries.map(entry => {
            const date = entry.timestamp ? new Date(entry.timestamp) : null;
            const when = date && !Number.isNaN(date.getTime())
                ? date.toLocaleDateString(undefined, { day: "numeric", month: "short" })
                : "Recent";
            return `
                <div class="activity-item">
                    <div class="activity-marker">✓</div>
                    <div>
                        <strong>${escapeHtml(entry.title || "Portfolio updated")}</strong>
                        <span>${escapeHtml(entry.description || when)}</span>
                    </div>
                </div>`;
        }).join("");
    }

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
    }

    /* -----------------------------------------
       DASHBOARD DATA
       ----------------------------------------- */
    function refreshDashboard() {
        const profile = read(KEYS.profile, {});
        const experience = visibleItems(KEYS.experience);
        const projects = visibleItems(KEYS.projects);
        const skills = visibleItems(KEYS.skills);
        const certifications = visibleItems(KEYS.certifications);
        const documents = asArray(read(KEYS.documents));
        const employerAccess = asArray(read(KEYS.employerAccess));

        setText("statExperience", calculateExperience(experience));
        setText("statPositions", experience.length);
        setText("statProjects", projects.length);
        setText("statCertifications", certifications.length);

        setBadge("documentsBadge", documents.filter(doc => doc.status !== "inactive").length);
        setBadge("skillsBadge", skills.length);
        setBadge("projectsBadge", projects.length);
        setBadge("certificationsBadge", certifications.length);

        updateProfileHealth(profile, experience, skills);
        updateDocumentStatus(documents, employerAccess);
        updateActivity();
    }

    refreshDashboard();

    /* Refresh when another Admin page updates localStorage. */
    window.addEventListener("storage", refreshDashboard);
    window.addEventListener("portfolioDataUpdated", refreshDashboard);
});
