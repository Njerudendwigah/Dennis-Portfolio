"use strict";

const portfolioApi = (() => {
    const BASE_URL =
        "https://dennis-portfolio-oaus.onrender.com/employer/api/portfolio";

    const SECTION_KEYS = {
        profile: "portfolioProfile",
        experience: "portfolioExperience",
        projects: "dennis_projects",
        skills: "dennis_skills",
        certifications: "dennis_certifications",
        settings: "portfolioSettings"
    };

    function getToken() {
        return window.portfolioAuth?.getStoredToken() || "";
    }

    function clearSession() {
        window.portfolioAuth?.clearAuthentication();
        window.location.replace("login.html");
    }

    async function request(path, options = {}) {
        const token = getToken();

        if (!token) {
            throw new Error("Authentication required.");
        }

        const headers = {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
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

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an invalid response.");
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
        return request("/data/", {
            method: "GET"
        });
    }

    async function save(key, data) {
        if (!Object.values(SECTION_KEYS).includes(key)) {
            throw new Error(`Unsupported portfolio section: ${key}`);
        }

        return request(`/data/${encodeURIComponent(key)}/`, {
            method: "PUT",
            body: JSON.stringify(data)
        });
    }

    async function hydrateLocalStorage() {
        const response = await load();
        const sections = response.sections || {};

        Object.entries(SECTION_KEYS).forEach(([, key]) => {
            if (
                Object.prototype.hasOwnProperty.call(sections, key)
            ) {
                localStorage.setItem(
                    key,
                    JSON.stringify(sections[key])
                );
            }
        });

        window.dispatchEvent(
            new CustomEvent("portfolioDataHydrated", {
                detail: { sections }
            })
        );

        return sections;
    }

    async function saveLocalKey(key) {
        if (!Object.values(SECTION_KEYS).includes(key)) {
            throw new Error(`Unsupported portfolio section: ${key}`);
        }

        const raw = localStorage.getItem(key);

        if (raw === null) {
            throw new Error(`No local data found for ${key}. Nothing was saved.`);
        }

        let data;

        try {
            data = JSON.parse(raw);
        } catch {
            throw new Error(`Invalid JSON stored for ${key}.`);
        }

        return save(key, data);
    }

    const ready = (async () => {
        if (window.location.pathname.endsWith("/login.html")) {
            return false;
        }

        if (!getToken()) {
            return false;
        }

        await hydrateLocalStorage();
        return true;
    })();

    return {
        SECTION_KEYS,
        ready,
        load,
        save,
        hydrateLocalStorage,
        saveLocalKey
    };
})();

window.portfolioApi = portfolioApi;

function reportPortfolioSaveError(error, section) {
    console.error(`Unable to save ${section} to the server.`, error);

    window.dispatchEvent(
        new CustomEvent("portfolioSaveError", {
            detail: {
                section,
                message: error.message ||
                    "The change could not be saved to the server."
            }
        })
    );
}

window.addEventListener("portfolioProfileUpdated", () => {
    portfolioApi.saveLocalKey(
        portfolioApi.SECTION_KEYS.profile
    ).catch(error => reportPortfolioSaveError(error, "profile"));
});

window.addEventListener("portfolioExperienceUpdated", () => {
    portfolioApi.saveLocalKey(
        portfolioApi.SECTION_KEYS.experience
    ).catch(error => reportPortfolioSaveError(error, "experience"));
});

window.addEventListener("portfolioProjectsUpdated", () => {
    portfolioApi.saveLocalKey(
        portfolioApi.SECTION_KEYS.projects
    ).catch(error => reportPortfolioSaveError(error, "projects"));
});

window.addEventListener("portfolioSkillsUpdated", () => {
    portfolioApi.saveLocalKey(
        portfolioApi.SECTION_KEYS.skills
    ).catch(error => reportPortfolioSaveError(error, "skills"));
});

window.addEventListener("certificationsUpdated", () => {
    portfolioApi.saveLocalKey(
        portfolioApi.SECTION_KEYS.certifications
    ).catch(error => reportPortfolioSaveError(error, "certifications"));
});

window.addEventListener("portfolioSettingsUpdated", () => {
    portfolioApi.saveLocalKey(
        portfolioApi.SECTION_KEYS.settings
    ).catch(error => reportPortfolioSaveError(error, "settings"));
});