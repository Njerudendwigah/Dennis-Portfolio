/* =========================================
   SETTINGS MANAGEMENT
   Dennis Ndwigah Portfolio
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("settingsForm");
    const saveMessage = document.getElementById("saveMessage");
    const resetButton = document.getElementById("resetSettings");

    const sidebar = document.getElementById("adminSidebar");
    const openSidebar = document.getElementById("openSidebar");
    const closeSidebar = document.getElementById("closeSidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    const logoutButton = document.getElementById("logoutButton");
    const currentYear = document.getElementById("currentYear");

    const SETTINGS_KEY = "portfolioSettings";

    const DEFAULT_SETTINGS = {
        siteTitle: "Dennis Ndwigah | Supply Chain & Operations",
        siteStatus: "live",
        siteDescription:
            "Supply Chain and Operations professional portfolio for Dennis Ndwigah Njeru.",

        showProfile: true,
        showExperience: true,
        showProjects: true,
        showContact: true,

        defaultVisibility: "public",
        dateFormat: "month-year"
    };

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }

    /* =========================================
       SIDEBAR
       ========================================= */

    function openNavigation() {
        if (!sidebar) {
            return;
        }

        sidebar.classList.add("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.add("active");
        }
    }

    function closeNavigation() {
        if (!sidebar) {
            return;
        }

        sidebar.classList.remove("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.remove("active");
        }
    }

    if (openSidebar) {
        openSidebar.addEventListener(
            "click",
            openNavigation
        );
    }

    if (closeSidebar) {
        closeSidebar.addEventListener(
            "click",
            closeNavigation
        );
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener(
            "click",
            closeNavigation
        );
    }

    const navigationLinks =
        document.querySelectorAll(".nav-link");

    navigationLinks.forEach((link) => {
        link.addEventListener("click", () => {

            if (window.innerWidth <= 760) {
                closeNavigation();
            }

        });
    });

    document.addEventListener("keydown", (event) => {

        if (event.key === "Escape") {
            closeNavigation();
        }

    });

    /* =========================================
       LOGOUT
       ========================================= */

    if (logoutButton) {

        logoutButton.addEventListener("click", () => {

            const confirmed = window.confirm(
                "Are you sure you want to sign out?"
            );

            if (!confirmed) {
                return;
            }

            window.location.href = "login.html";
        });

    }

    /* =========================================
       MESSAGE HELPER
       ========================================= */

    function showMessage(message) {

        if (!saveMessage) {
            return;
        }

        saveMessage.textContent = message;
        saveMessage.classList.add("show");

        window.clearTimeout(showMessage.timer);

        showMessage.timer = window.setTimeout(() => {

            saveMessage.textContent = "";
            saveMessage.classList.remove("show");

        }, 3000);
    }

    /* =========================================
       GET STORED SETTINGS
       ========================================= */

    function getStoredSettings() {

        const savedSettings =
            localStorage.getItem(SETTINGS_KEY);

        if (!savedSettings) {
            return {};
        }

        try {

            return JSON.parse(savedSettings);

        } catch (error) {

            console.error(
                "Unable to parse saved settings.",
                error
            );

            return {};
        }
    }

    /* =========================================
       MERGE DEFAULTS
       ========================================= */

    function getMergedSettings() {

        return {
            ...DEFAULT_SETTINGS,
            ...getStoredSettings()
        };
    }

    /* =========================================
       LOAD SETTINGS
       ========================================= */

    function loadSettings() {

        if (!form) {
            return;
        }

        const settings =
            getMergedSettings();

        Object.entries(settings).forEach(
            ([key, value]) => {

                const field =
                    document.getElementById(key);

                if (!field) {
                    return;
                }

                if (field.type === "checkbox") {

                    field.checked =
                        Boolean(value);

                    return;
                }

                field.value =
                    value ?? "";
            }
        );
    }

    loadSettings();

    /* =========================================
       SAVE SETTINGS
       ========================================= */

    if (form) {

        form.addEventListener(
            "submit",
            (event) => {

                event.preventDefault();

                const formData =
                    new FormData(form);

                const settings = {};

                formData.forEach(
                    (value, key) => {

                        settings[key] =
                            String(value).trim();
                    }
                );

                const checkboxFields =
                    form.querySelectorAll(
                        'input[type="checkbox"]'
                    );

                checkboxFields.forEach(
                    (checkbox) => {

                        settings[checkbox.name] =
                            checkbox.checked;
                    }
                );

                const completeSettings = {
                    ...DEFAULT_SETTINGS,
                    ...settings
                };

                localStorage.setItem(
                    SETTINGS_KEY,
                    JSON.stringify(
                        completeSettings
                    )
                );

                window.dispatchEvent(
                    new CustomEvent(
                        "portfolioSettingsUpdated",
                        {
                            detail:
                                completeSettings
                        }
                    )
                );

                showMessage(
                    "Settings saved successfully."
                );
            }
        );
    }

    /* =========================================
       RESET SETTINGS
       ========================================= */

    if (resetButton) {

        resetButton.addEventListener(
            "click",
            () => {

                const confirmed =
                    window.confirm(
                        "Reset all settings to their default values?"
                    );

                if (!confirmed) {
                    return;
                }

                localStorage.removeItem(
                    SETTINGS_KEY
                );

                loadSettings();

                window.dispatchEvent(
                    new CustomEvent(
                        "portfolioSettingsUpdated",
                        {
                            detail:
                                DEFAULT_SETTINGS
                        }
                    )
                );

                showMessage(
                    "Settings reset to defaults."
                );
            }
        );
    }

});