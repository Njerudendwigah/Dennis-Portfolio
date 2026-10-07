const CERTIFICATIONS_KEY = "dennis_certifications";

const certificationForm = document.getElementById("certificationForm");
const certificationList = document.getElementById("certificationList");
const certificationModal = document.getElementById("certificationModal");
const modalTitle = document.getElementById("modalTitle");

const addCertificationButton = document.getElementById("addCertificationButton");
const closeCertificationModal = document.getElementById("closeCertificationModal");
const cancelCertification = document.getElementById("cancelCertification");

const certificationId = document.getElementById("certificationId");
const certificationName = document.getElementById("certificationName");
const certificationOrganization = document.getElementById("certificationOrganization");
const certificationDate = document.getElementById("certificationDate");
const certificationExpiry = document.getElementById("certificationExpiry");
const certificationCredentialId = document.getElementById("certificationCredentialId");
const certificationUrl = document.getElementById("certificationUrl");
const certificationDescription = document.getElementById("certificationDescription");
const certificationVisibility = document.getElementById("certificationVisibility");
const certificationFeatured = document.getElementById("certificationFeatured");

function getCertifications() {
    try {
        return JSON.parse(localStorage.getItem(CERTIFICATIONS_KEY)) || [];
    } catch {
        return [];
    }
}

function saveCertifications(certifications) {
    localStorage.setItem(
        CERTIFICATIONS_KEY,
        JSON.stringify(certifications)
    );

    window.dispatchEvent(
        new CustomEvent("certificationsUpdated")
    );
}

function createId() {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatDate(value) {
    if (!value) return "";

    const date = new Date(`${value}-01T00:00:00`);

    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleDateString("en-GB", {
        month: "short",
        year: "numeric"
    });
}

function openModal(certification = null) {
    certificationForm.reset();

    if (certification) {
        modalTitle.textContent = "Edit Certification";

        certificationId.value = certification.id || "";
        certificationName.value = certification.name || "";
        certificationOrganization.value = certification.organization || "";
        certificationDate.value = certification.issueDate || "";
        certificationExpiry.value = certification.expiryDate || "";
        certificationCredentialId.value = certification.credentialId || "";
        certificationUrl.value = certification.url || "";
        certificationDescription.value = certification.description || "";
        certificationVisibility.value = certification.visibility || "public";
        certificationFeatured.checked = Boolean(certification.featured);
    } else {
        modalTitle.textContent = "Add Certification";
        certificationId.value = "";
        certificationVisibility.value = "public";
        certificationFeatured.checked = false;
    }

    certificationModal.classList.remove("hidden");
    certificationModal.setAttribute("aria-hidden", "false");

    certificationName.focus();
}

function closeModal() {
    certificationModal.classList.add("hidden");
    certificationModal.setAttribute("aria-hidden", "true");
    certificationForm.reset();
}

function renderCertifications() {
    const certifications = getCertifications();

    certificationList.innerHTML = "";

    if (!certifications.length) {
        certificationList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i data-lucide="award"></i>
                </div>

                <h3>No certifications yet</h3>

                <p>
                    Add your professional certifications and credentials
                    to display them on your portfolio.
                </p>
            </div>
        `;

        refreshIcons();
        return;
    }

    certifications.forEach((certification) => {
        const card = document.createElement("article");

        card.className = "certification-admin-card";

        const statusClass =
            certification.visibility === "public"
                ? "status-public"
                : "status-hidden";

        const statusLabel =
            certification.visibility === "public"
                ? "Public"
                : "Hidden";

        const issueDate = formatDate(certification.issueDate);
        const expiryDate = formatDate(certification.expiryDate);

        const dateText = [
            issueDate ? `Issued ${issueDate}` : "",
            expiryDate ? `Expires ${expiryDate}` : ""
        ]
            .filter(Boolean)
            .join(" · ");

        card.innerHTML = `
            <div class="certification-card-main">

                <div class="certification-icon">
                    <i data-lucide="award"></i>
                </div>

                <div class="certification-info">

                    <div class="certification-title-row">

                        <h3>
                            ${escapeHtml(certification.name)}
                        </h3>

                        <span class="${statusClass}">
                            ${statusLabel}
                        </span>

                        ${
                            certification.featured
                                ? `<span class="featured-badge">Featured</span>`
                                : ""
                        }

                    </div>

                    <p class="certification-organization">
                        ${escapeHtml(certification.organization)}
                    </p>

                    ${
                        dateText
                            ? `<div class="certification-meta">${escapeHtml(dateText)}</div>`
                            : ""
                    }

                    ${
                        certification.credentialId
                            ? `
                                <div class="certification-meta">
                                    Credential ID:
                                    ${escapeHtml(certification.credentialId)}
                                </div>
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

                </div>

            </div>

            <div class="certification-actions">

                ${
                    certification.url
                        ? `
                            <a
                                href="${escapeAttribute(certification.url)}"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="admin-secondary-btn small"
                            >
                                <i data-lucide="external-link"></i>
                                Verify
                            </a>
                        `
                        : ""
                }

                <button
                    type="button"
                    class="admin-secondary-btn small"
                    data-action="edit"
                    data-id="${escapeAttribute(certification.id)}"
                >
                    <i data-lucide="pencil"></i>
                    Edit
                </button>

                <button
                    type="button"
                    class="admin-danger-btn small"
                    data-action="delete"
                    data-id="${escapeAttribute(certification.id)}"
                >
                    <i data-lucide="trash-2"></i>
                    Delete
                </button>

            </div>
        `;

        certificationList.appendChild(card);
    });

    refreshIcons();
}

function editCertification(id) {
    const certification = getCertifications().find(
        item => item.id === id
    );

    if (!certification) return;

    openModal(certification);
}

function deleteCertification(id) {
    const certifications = getCertifications();

    const certification = certifications.find(
        item => item.id === id
    );

    if (!certification) return;

    const confirmed = window.confirm(
        `Delete "${certification.name}"?`
    );

    if (!confirmed) return;

    const updated = certifications.filter(
        item => item.id !== id
    );

    saveCertifications(updated);
    renderCertifications();
}

certificationForm.addEventListener("submit", event => {
    event.preventDefault();

    const certifications = getCertifications();
    const id = certificationId.value || createId();

    const existingIndex = certifications.findIndex(
        item => item.id === id
    );

    const certification = {
        id,
        name: certificationName.value.trim(),
        organization: certificationOrganization.value.trim(),
        issueDate: certificationDate.value,
        expiryDate: certificationExpiry.value,
        credentialId: certificationCredentialId.value.trim(),
        url: certificationUrl.value.trim(),
        description: certificationDescription.value.trim(),
        visibility: certificationVisibility.value,
        featured: certificationFeatured.checked
    };

    if (existingIndex >= 0) {
        certifications[existingIndex] = certification;
    } else {
        certifications.unshift(certification);
    }

    saveCertifications(certifications);
    renderCertifications();
    closeModal();
});

certificationList.addEventListener("click", event => {
    const button = event.target.closest("[data-action]");

    if (!button) return;

    const action = button.dataset.action;
    const id = button.dataset.id;

    if (action === "edit") {
        editCertification(id);
    }

    if (action === "delete") {
        deleteCertification(id);
    }
});

addCertificationButton.addEventListener("click", () => {
    openModal();
});

closeCertificationModal.addEventListener("click", closeModal);
cancelCertification.addEventListener("click", closeModal);

certificationModal.addEventListener("click", event => {
    if (event.target === certificationModal) {
        closeModal();
    }
});

document.addEventListener("keydown", event => {
    if (
        event.key === "Escape" &&
        !certificationModal.classList.contains("hidden")
    ) {
        closeModal();
    }
});

window.addEventListener("storage", event => {
    if (event.key === CERTIFICATIONS_KEY) {
        renderCertifications();
    }
});

function escapeHtml(value = "") {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value = "") {
    return escapeHtml(value);
}

function refreshIcons() {
    if (window.lucide) {
        lucide.createIcons({
            attrs: {
                "stroke-width": 1.8
            }
        });
    }
}

const currentYear = document.getElementById("currentYear");

if (currentYear) {
    currentYear.textContent = new Date().getFullYear();
}

renderCertifications();