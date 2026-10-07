(() => {
    "use strict";

    const STORAGE_KEYS = {
        profile: "portfolioProfile",
        profilePhoto: "portfolioProfilePhoto",
        experience: "portfolioExperience",
        projects: "dennis_projects",
        skills: "dennis_skills",
        certifications: "dennis_certifications",
        documents: "portfolioDocuments"
    };

    const UPDATE_EVENTS = [
        "portfolioProfileUpdated",
        "portfolioExperienceUpdated",
        "portfolioProjectsUpdated",
        "portfolioSkillsUpdated",
        "certificationsUpdated",
        "portfolioDocumentsUpdated"
    ];

    function readStorage(key) {
        try {
            const value = localStorage.getItem(key);

            if (!value) {
                return null;
            }

            return JSON.parse(value);
        } catch (error) {
            console.error(`Unable to read ${key}.`, error);
            return null;
        }
    }

    function getArray(key) {
        const value = readStorage(key);

        return Array.isArray(value) ? value : [];
    }

    function clean(value) {
        return String(value ?? "").trim();
    }

    /* =========================================
       EXPERIENCE
       ========================================= */

    function parseMonth(value) {
        const match = clean(value).match(
            /^([A-Za-z]{3,9})\s+(\d{4})$/
        );

        if (!match) {
            return null;
        }

        const date = new Date(
            `${match[1]} 1, ${match[2]}`
        );

        return Number.isNaN(date.getTime())
            ? null
            : date;
    }

    function calculateExperience(experience) {
        const startDates = experience
            .map((item) => parseMonth(item?.startDate))
            .filter(Boolean);

        if (!startDates.length) {
            return {
                years: 0,
                months: 0
            };
        }

        const earliestStart = new Date(
            Math.min(
                ...startDates.map(
                    (date) => date.getTime()
                )
            )
        );

        const currentDate = new Date();

        let totalMonths =
            (currentDate.getFullYear() -
                earliestStart.getFullYear()) * 12;

        totalMonths +=
            currentDate.getMonth() -
            earliestStart.getMonth();

        totalMonths = Math.max(
            totalMonths,
            0
        );

        return {
            years: Math.floor(
                totalMonths / 12
            ),
            months: totalMonths % 12
        };
    }

    function updateExperienceStat() {
        const experience =
            getArray(
                STORAGE_KEYS.experience
            );

        const duration =
            calculateExperience(
                experience
            );

        const statCard =
            document.querySelector(
                ".stats-grid .stat-card:nth-child(1)"
            );

        if (!statCard) {
            return;
        }

        const numbers =
            statCard.querySelectorAll(
                ".stat-number"
            );

        const units =
            statCard.querySelectorAll(
                ".stat-unit"
            );

        if (numbers[0]) {
            numbers[0].textContent =
                duration.years;
        }

        if (numbers[1]) {
            numbers[1].textContent =
                duration.months;
        }

        if (units[0]) {
            units[0].textContent =
                duration.years === 1
                    ? "yr"
                    : "yrs";
        }

        if (units[1]) {
            units[1].textContent =
                duration.months === 1
                    ? "mo"
                    : "mos";
        }
    }

    function updatePositionCount() {
        const experience =
            getArray(
                STORAGE_KEYS.experience
            );

        const count =
            experience.filter(
                (item) =>
                    item &&
                    clean(item.title)
            ).length;

        const statCard =
            document.querySelector(
                ".stats-grid .stat-card:nth-child(2)"
            );

        if (!statCard) {
            return;
        }

        const value =
            statCard.querySelector(
                "strong"
            );

        if (value) {
            value.textContent =
                count;
        }
    }

    /* =========================================
       PROJECTS
       ========================================= */

    function updateProjectCount() {
        const projects =
            getArray(
                STORAGE_KEYS.projects
            );

        const count =
            projects.filter(
                (item) =>
                    item &&
                    clean(item.title) &&
                    item.visible !== false
            ).length;

        const statCard =
            document.querySelector(
                ".stats-grid .stat-card:nth-child(3)"
            );

        if (!statCard) {
            return;
        }

        const value =
            statCard.querySelector(
                "strong"
            );

        if (value) {
            value.textContent =
                count;
        }
    }

    /* =========================================
       CERTIFICATIONS
       ========================================= */

    function updateCertificationCount() {
        const certifications =
            getArray(
                STORAGE_KEYS.certifications
            );

        const count =
            certifications.filter(
                (item) =>
                    item &&
                    clean(item.name) &&
                    item.visibility !== "hidden"
            ).length;

        const statCard =
            document.querySelector(
                ".stats-grid .stat-card:nth-child(4)"
            );

        if (!statCard) {
            return;
        }

        const value =
            statCard.querySelector(
                "strong"
            );

        if (value) {
            value.textContent =
                count;
        }
    }

    /* =========================================
       DOCUMENTS
       ========================================= */

    function updateDocumentCount() {
        const documents =
            getArray(
                STORAGE_KEYS.documents
            );

        const count =
            documents.filter(
                (item) =>
                    item &&
                    clean(
                        item.name ||
                        item.documentName
                    )
            ).length;

        const badge =
            document.querySelector(
                ".nav-link[href='documents.html'] .nav-badge"
            );

        if (badge) {
            badge.textContent =
                count;
        }
    }

    /* =========================================
       PROFILE
       ========================================= */

    function getProfile() {
        const profile =
            readStorage(
                STORAGE_KEYS.profile
            );

        return (
            profile &&
            typeof profile === "object"
        )
            ? profile
            : {};
    }

    function hasProfilePhoto(profile) {
        const profilePhoto =
            clean(profile.photo);

        const separatePhoto =
            clean(
                localStorage.getItem(
                    STORAGE_KEYS.profilePhoto
                )
            );

        return Boolean(
            profilePhoto ||
            separatePhoto
        );
    }

    function hasProfileSummary(profile) {
        return Boolean(
            clean(profile.bio) ||
            clean(profile.summary) ||
            clean(profile.description)
        );
    }

    function hasCareerExperience() {
        const experience =
            getArray(
                STORAGE_KEYS.experience
            );

        return experience.some(
            (item) =>
                item &&
                clean(item.title) &&
                clean(item.startDate)
        );
    }

    function hasSkills() {
        const skills =
            getArray(
                STORAGE_KEYS.skills
            );

        return skills.some(
            (item) =>
                item &&
                clean(item.skill) &&
                item.visible !== false
        );
    }

    function calculateProfileProgress() {
        const profile =
            getProfile();

        const fields = [
            "fullName",
            "headline",
            "email",
            "phone",
            "location",
            "bio"
        ];

        const completed =
            fields.filter(
                (field) =>
                    clean(
                        profile[field]
                    ) !== ""
            ).length;

        const photoComplete =
            hasProfilePhoto(
                profile
            );

        const totalFields =
            fields.length + 1;

        const completedFields =
            completed +
            (photoComplete ? 1 : 0);

        return Math.round(
            (
                completedFields /
                totalFields
            ) * 100
        );
    }

    function updateProfileProgress() {
        const progress =
            calculateProfileProgress();

        const progressInfo =
            document.querySelector(
                ".profile-progress .progress-info strong"
            );

        const progressBar =
            document.querySelector(
                ".profile-progress .progress-bar"
            );

        const progressFill =
            document.querySelector(
                ".profile-progress .progress-bar span"
            );

        if (progressInfo) {
            progressInfo.textContent =
                `${progress}%`;
        }

        if (progressBar) {
            progressBar.setAttribute(
                "aria-valuenow",
                String(progress)
            );
        }

        if (progressFill) {
            progressFill.style.width =
                `${progress}%`;
        }
    }

    /* =========================================
       PROFILE CHECKLIST
       ========================================= */

    function updateChecklistItem(
        item,
        complete,
        link
    ) {
        if (!item) {
            return;
        }

        const icon =
            item.querySelector(
                ".check-icon"
            );

        const existingAction =
            item.querySelector(
                ".checklist-action"
            );

        if (complete) {
            item.classList.add(
                "complete"
            );

            if (icon) {
                icon.innerHTML =
                    '<i data-lucide="check" aria-hidden="true"></i>';
            }

            if (existingAction) {
                existingAction.remove();
            }

            return;
        }

        item.classList.remove(
            "complete"
        );

        if (icon) {
            icon.innerHTML =
                '<i data-lucide="circle" aria-hidden="true"></i>';
        }

        if (
            link &&
            !existingAction
        ) {
            const action =
                document.createElement(
                    "a"
                );

            action.href =
                link.href;

            action.className =
                "checklist-action";

            action.textContent =
                link.label;

            item.appendChild(
                action
            );
        }
    }

    function updateProfileChecklist() {
        const profile =
            getProfile();

        const checklist =
            document.querySelector(
                ".profile-checklist"
            );

        if (!checklist) {
            return;
        }

        const items =
            checklist.querySelectorAll(
                "li"
            );

        if (items[0]) {
            updateChecklistItem(
                items[0],
                hasProfileSummary(
                    profile
                ),
                {
                    href: "profile.html",
                    label: "Add"
                }
            );
        }

        if (items[1]) {
            updateChecklistItem(
                items[1],
                hasCareerExperience(),
                {
                    href: "experience.html",
                    label: "Add"
                }
            );
        }

        if (items[2]) {
            updateChecklistItem(
                items[2],
                hasSkills(),
                {
                    href: "skills.html",
                    label: "Add"
                }
            );
        }

        if (items[3]) {
            updateChecklistItem(
                items[3],
                true,
                null
            );
        }

        if (items[4]) {
            updateChecklistItem(
                items[4],
                hasProfilePhoto(
                    profile
                ),
                {
                    href: "profile.html",
                    label: "Add"
                }
            );
        }
    }

    /* =========================================
       ICONS
       ========================================= */

    function refreshIcons() {
        if (
            window.lucide &&
            typeof window.lucide.createIcons ===
                "function"
        ) {
            window.lucide.createIcons({
                attrs: {
                    "stroke-width": 1.8
                }
            });
        }
    }

    /* =========================================
       DASHBOARD REFRESH
       ========================================= */

    function refreshDashboard() {
        updateExperienceStat();
        updatePositionCount();
        updateProjectCount();
        updateCertificationCount();
        updateDocumentCount();

        updateProfileProgress();
        updateProfileChecklist();

        refreshIcons();
    }

    /* =========================================
       SAME-TAB EVENTS
       ========================================= */

    UPDATE_EVENTS.forEach(
        (eventName) => {
            window.addEventListener(
                eventName,
                refreshDashboard
            );
        }
    );

    /* =========================================
       CROSS-TAB STORAGE EVENTS
       ========================================= */

    window.addEventListener(
        "storage",
        (event) => {
            if (
                Object.values(
                    STORAGE_KEYS
                ).includes(event.key)
            ) {
                refreshDashboard();
            }
        }
    );

    /* =========================================
       RETURNING TO DASHBOARD
       ========================================= */

    document.addEventListener(
        "visibilitychange",
        () => {
            if (!document.hidden) {
                refreshDashboard();
            }
        }
    );

    /* =========================================
       INITIAL LOAD
       ========================================= */

    document.addEventListener(
        "DOMContentLoaded",
        refreshDashboard
    );
})();