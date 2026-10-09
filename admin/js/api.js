"use strict";

const portfolioApi = (() => {
    const BASE_URL =
        "https://dennis-portfolio-oaus.onrender.com/employer/api/portfolio";

    const SECTION_KEYS = Object.freeze({
        profile: "portfolioProfile",
        experience: "portfolioExperience",
        projects: "dennis_projects",
        skills: "dennis_skills",
        certifications: "dennis_certifications",
        settings: "portfolioSettings"
    });

    const ALLOWED_SECTION_KEYS = new Set(Object.values(SECTION_KEYS));

    let latestSyncStatus = {
        lastHydratedAt: null,
        lastImportedAt: null,
        conflicts: [],
        invalidLocalKeys: [],
        storageErrors: []
    };

    function getToken() {
        return window.portfolioAuth?.getStoredToken() || "";
    }

    function clearSession() {
        window.portfolioAuth?.clearAuthentication();
        window.location.replace("login.html");
    }

    function isJsonRecord(value) {
        return value !== null && typeof value === "object";
    }

    function stableStringify(value) {
        if (Array.isArray(value)) {
            return `[${value.map(stableStringify).join(",")}]`;
        }

        if (value !== null && typeof value === "object") {
            const keys = Object.keys(value).sort();
            return `{${keys.map(key => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
        }

        return JSON.stringify(value);
    }

    function sameJsonValue(left, right) {
        return stableStringify(left) === stableStringify(right);
    }

    function validateSectionsResponse(response) {
        if (!response || !isJsonRecord(response.sections) || Array.isArray(response.sections)) {
            throw new Error("The server returned an invalid portfolio data structure.");
        }

        const sections = {};
        for (const [key, value] of Object.entries(response.sections)) {
            if (ALLOWED_SECTION_KEYS.has(key)) {
                sections[key] = value;
            }
        }

        return sections;
    }

    function parseLocalSection(key) {
        const raw = localStorage.getItem(key);
        if (raw === null) {
            return { exists: false, valid: false, value: undefined };
        }

        try {
            const value = JSON.parse(raw);
            if (!isJsonRecord(value)) {
                return { exists: true, valid: false, value: undefined };
            }
            return { exists: true, valid: true, value };
        } catch {
            return { exists: true, valid: false, value: undefined };
        }
    }

    function readLocalSections() {
        const sections = {};
        const invalidKeys = [];

        for (const key of ALLOWED_SECTION_KEYS) {
            const local = parseLocalSection(key);
            if (!local.exists) {
                continue;
            }
            if (!local.valid) {
                invalidKeys.push(key);
                continue;
            }
            sections[key] = local.value;
        }

        return { sections, invalidKeys };
    }

    async function request(path, options = {}) {
        const token = getToken();
        if (!token) {
            throw new Error("Authentication required. Please sign in again.");
        }

        const headers = {
            Authorization: `Bearer ${token}`,
            ...(options.body !== undefined ? { "Content-Type": "application/json" } : {}),
            ...(options.headers || {})
        };

        let response;
        try {
            response = await fetch(`${BASE_URL}${path}`, {
                ...options,
                headers,
                cache: "no-store"
            });
        } catch {
            throw new Error(
                "Unable to connect to the portfolio server. Check your internet connection and try again."
            );
        }

        if (response.status === 401) {
            clearSession();
            throw new Error("Your session has expired. Please sign in again.");
        }

        const responseText = await response.text();
        let data = {};

        if (responseText) {
            try {
                data = JSON.parse(responseText);
            } catch {
                if (response.ok) {
                    throw new Error("The server returned an invalid response.");
                }
                throw new Error(`The request failed with status ${response.status}.`);
            }
        }

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.error ||
                `The request failed with status ${response.status}.`
            );
        }

        return data;
    }

    async function load() {
        return request("/data/", { method: "GET" });
    }

    async function save(key, data) {
        if (!ALLOWED_SECTION_KEYS.has(key)) {
            throw new Error(`Unsupported portfolio section: ${key}`);
        }

        if (!isJsonRecord(data)) {
            throw new Error("Portfolio data must be a JSON object or array.");
        }

        let body;
        try {
            body = JSON.stringify(data);
        } catch {
            throw new Error(`Unable to encode portfolio data for ${key}.`);
        }

        if (typeof body !== "string") {
            throw new Error(`Unable to encode portfolio data for ${key}.`);
        }

        return request(`/data/${encodeURIComponent(key)}/`, {
            method: "PUT",
            body
        });
    }

    /**
     * Load server data without overwriting an existing browser-local section.
     * Local values are retained when both local and server data exist. Server
     * values are copied to localStorage only for keys that are not present there.
     */
    async function hydrateLocalStorage() {
        const response = await load();
        const serverSections = validateSectionsResponse(response);
        const effectiveSections = {};
        const conflicts = [];
        const invalidLocalKeys = [];
        const storageErrors = [];

        for (const key of ALLOWED_SECTION_KEYS) {
            const serverHasKey = Object.prototype.hasOwnProperty.call(serverSections, key);
            const local = parseLocalSection(key);

            if (local.exists) {
                if (!local.valid) {
                    invalidLocalKeys.push(key);
                    if (serverHasKey) {
                        effectiveSections[key] = serverSections[key];
                    }
                    continue;
                }

                effectiveSections[key] = local.value;
                if (serverHasKey && !sameJsonValue(local.value, serverSections[key])) {
                    conflicts.push(key);
                }
                continue;
            }

            if (serverHasKey) {
                effectiveSections[key] = serverSections[key];
                try {
                    localStorage.setItem(key, JSON.stringify(serverSections[key]));
                } catch {
                    storageErrors.push(key);
                }
            }
        }

        latestSyncStatus = {
            ...latestSyncStatus,
            lastHydratedAt: new Date().toISOString(),
            conflicts,
            invalidLocalKeys,
            storageErrors
        };

        window.dispatchEvent(new CustomEvent("portfolioDataHydrated", {
            detail: {
                sections: effectiveSections,
                serverSections,
                conflicts: [...conflicts],
                invalidLocalKeys: [...invalidLocalKeys],
                storageErrors: [...storageErrors]
            }
        }));

        return effectiveSections;
    }

    /**
     * Explicitly import browser-local sections to the server.
     * By default, only missing server sections are created. Differing sections
     * are reported as conflicts and never overwritten unless overwriteServer
     * is explicitly set to true by the caller.
     */
    async function importLocalStorageToServer({ overwriteServer = false } = {}) {
        const response = await load();
        const serverSections = validateSectionsResponse(response);
        const { sections: localSections, invalidKeys } = readLocalSections();
        const uploaded = [];
        const unchanged = [];
        const conflicts = [];

        for (const key of ALLOWED_SECTION_KEYS) {
            if (!Object.prototype.hasOwnProperty.call(localSections, key)) {
                continue;
            }

            const localValue = localSections[key];
            const serverHasKey = Object.prototype.hasOwnProperty.call(serverSections, key);

            if (!serverHasKey) {
                await save(key, localValue);
                uploaded.push(key);
                continue;
            }

            if (sameJsonValue(localValue, serverSections[key])) {
                unchanged.push(key);
                continue;
            }

            if (!overwriteServer) {
                conflicts.push(key);
                continue;
            }

            await save(key, localValue);
            uploaded.push(key);
        }

        latestSyncStatus = {
            ...latestSyncStatus,
            lastImportedAt: new Date().toISOString(),
            conflicts,
            invalidLocalKeys: invalidKeys,
            storageErrors: []
        };

        const result = {
            uploaded,
            unchanged,
            conflicts,
            invalidLocalKeys: invalidKeys,
            overwriteServer: Boolean(overwriteServer)
        };

        window.dispatchEvent(new CustomEvent("portfolioDataImportCompleted", {
            detail: result
        }));

        return result;
    }

    async function saveLocalKey(key) {
        if (!ALLOWED_SECTION_KEYS.has(key)) {
            throw new Error(`Unsupported portfolio section: ${key}`);
        }

        const local = parseLocalSection(key);
        if (!local.exists) {
            throw new Error(`No local data found for ${key}. Nothing was saved.`);
        }
        if (!local.valid) {
            throw new Error(`Invalid JSON stored for ${key}.`);
        }

        return save(key, local.value);
    }

    function getSyncStatus() {
        return {
            ...latestSyncStatus,
            conflicts: [...latestSyncStatus.conflicts],
            invalidLocalKeys: [...latestSyncStatus.invalidLocalKeys],
            storageErrors: [...latestSyncStatus.storageErrors]
        };
    }

    const ready = (async () => {
        if (window.location.pathname.endsWith("/login.html")) {
            return false;
        }

        if (!getToken()) {
            return false;
        }

        try {
            await hydrateLocalStorage();
            return true;
        } catch (error) {
            console.error("Unable to load portfolio data from the server.", error);
            window.dispatchEvent(new CustomEvent("portfolioApiError", {
                detail: {
                    message: error?.message || "Unable to load portfolio data from the server."
                }
            }));
            return false;
        }
    })();

    return Object.freeze({
        SECTION_KEYS,
        ready,
        load,
        save,
        hydrateLocalStorage,
        saveLocalKey,
        readLocalSections,
        importLocalStorageToServer,
        getSyncStatus
    });
})();

window.portfolioApi = portfolioApi;

function reportPortfolioSaveError(error, section) {
    console.error(`Unable to save ${section} to the server.`, error);

    window.dispatchEvent(new CustomEvent("portfolioSaveError", {
        detail: {
            section,
            message: error?.message || "The change could not be saved to the server."
        }
    }));
}

window.addEventListener("portfolioProfileUpdated", () => {
    portfolioApi.saveLocalKey(portfolioApi.SECTION_KEYS.profile)
        .catch(error => reportPortfolioSaveError(error, "profile"));
});

window.addEventListener("portfolioExperienceUpdated", () => {
    portfolioApi.saveLocalKey(portfolioApi.SECTION_KEYS.experience)
        .catch(error => reportPortfolioSaveError(error, "experience"));
});

window.addEventListener("portfolioProjectsUpdated", () => {
    portfolioApi.saveLocalKey(portfolioApi.SECTION_KEYS.projects)
        .catch(error => reportPortfolioSaveError(error, "projects"));
});

window.addEventListener("portfolioSkillsUpdated", () => {
    portfolioApi.saveLocalKey(portfolioApi.SECTION_KEYS.skills)
        .catch(error => reportPortfolioSaveError(error, "skills"));
});

window.addEventListener("certificationsUpdated", () => {
    portfolioApi.saveLocalKey(portfolioApi.SECTION_KEYS.certifications)
        .catch(error => reportPortfolioSaveError(error, "certifications"));
});

window.addEventListener("portfolioSettingsUpdated", () => {
    portfolioApi.saveLocalKey(portfolioApi.SECTION_KEYS.settings)
        .catch(error => reportPortfolioSaveError(error, "settings"));
});
