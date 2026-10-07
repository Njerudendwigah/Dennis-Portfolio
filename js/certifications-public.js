(() => {
    "use strict";

    const STORAGE_KEY = "dennis_certifications";
    const UPDATE_EVENT = "certificationsUpdated";
    const TARGET_ID = "certificationsGrid";

    const container = document.getElementById(TARGET_ID);

    if (!container) {
        return;
    }

    function clean(value) {
        return String(value ?? "").trim();
    }

    function escapeHtml(value) {
        return clean(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function loadCertifications() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);

            if (!raw) {
                return [];
            }

            const parsed = JSON.parse(raw);

            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            console.error("Unable to load public certifications.", error);
            return [];
        }
    }

    function render() {
        const certifications = loadCertifications()
            .filter((item) => item && item.name)
            .filter((item) => item.visibility !== "hidden")
            .sort((a, b) => {
                if (Boolean(a.featured) !== Boolean(b.featured)) {
                    return a.featured ? -1 : 1;
                }

                return clean(a.name).localeCompare(clean(b.name));
            });

        container.innerHTML = "";

        if (!certifications.length) {
            container.innerHTML = `
                <div class="certifications-empty">
                    <p>Certifications will be updated soon.</p>
                </div>
            `;

            return;
        }

        certifications.forEach((certification) => {
            const card = document.createElement("article");

            card.className = "certification-card";

            card.innerHTML = `
                <div class="certification-icon" aria-hidden="true">
                    <i data-lucide="award"></i>
                </div>

                <div class="certification-content">
                    <div class="certification-top">
                        <span class="certification-organization">
                            ${escapeHtml(
                                certification.organization ||
                                "Professional Certification"
                            )}
                        </span>

                        ${
                            certification.featured
                                ? `
                                    <span class="certification-featured">
                                        Featured
                                    </span>
                                `
                                : ""
                        }
                    </div>

                    <h3>${escapeHtml(certification.name)}</h3>

                    ${
                        certification.issueDate
                            ? `
                                <p class="certification-date">
                                    Issued ${escapeHtml(certification.issueDate)}
                                </p>
                            `
                            : ""
                    }

                    ${
                        certification.expiryDate
                            ? `
                                <p class="certification-expiry">
                                    Expires ${escapeHtml(certification.expiryDate)}
                                </p>
                            `
                            : ""
                    }

                    ${
                        certification.description
                            ? `
                                <p class="certification-description">
                                    ${escapeHtml(certification.description)}
                                </p>
                            `
                            : ""
                    }

                    ${
                        certification.credentialId
                            ? `
                                <p class="certification-credential">
                                    Credential ID:
                                    <span>
                                        ${escapeHtml(
                                            certification.credentialId
                                        )}
                                    </span>
                                </p>
                            `
                            : ""
                    }

                    ${
                        certification.url
                            ? `
                                <a
                                    class="certification-link"
                                    href="${escapeHtml(certification.url)}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Verify Credential
                                    <i data-lucide="external-link"></i>
                                </a>
                            `
                            : ""
                    }
                </div>
            `;

            container.appendChild(card);
        });

        refreshIcons();
    }

    function refreshIcons() {
        if (window.lucide) {
            window.lucide.createIcons({
                attrs: {
                    "stroke-width": 1.8
                }
            });
        }
    }

    window.addEventListener(UPDATE_EVENT, render);

    window.addEventListener("storage", (event) => {
        if (event.key === STORAGE_KEY) {
            render();
        }
    });

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            render();
        }
    });

    render();
})();