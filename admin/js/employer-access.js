/* =========================================
   EMPLOYER ACCESS MANAGEMENT
   Dennis Ndwigah Portfolio
   MVP: browser/localStorage based
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const ACCESS_KEY = "employerAccess";
    const DOCUMENTS_KEY = "portfolioDocuments";

    const form = document.getElementById("employerAccessForm");
    const accessList = document.getElementById("employerAccessList");
    const documentSelector = document.getElementById("documentSelector");

    const accessId = document.getElementById("accessId");
    const employerName = document.getElementById("employerName");
    const employerPosition = document.getElementById("employerPosition");
    const employerContact = document.getElementById("employerContact");
    const accessExpiry = document.getElementById("accessExpiry");
    const accessCode = document.getElementById("accessCode");
    const accessActive = document.getElementById("accessActive");

    const editorTitle = document.getElementById("editorTitle");
    const cancelButton = document.getElementById("cancelEmployerAccess");
    const logoutButton = document.getElementById("logoutButton");
    const currentYear = document.getElementById("currentYear");

    const sidebar = document.getElementById("adminSidebar");
    const openSidebar = document.getElementById("openSidebar");
    const closeSidebar = document.getElementById("closeSidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");


    /* -----------------------------------------
       YEAR
       ----------------------------------------- */

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }


    /* -----------------------------------------
       SIDEBAR
       ----------------------------------------- */

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


    document.addEventListener(
        "keydown",
        (event) => {

            if (event.key === "Escape") {
                closeNavigation();
            }

        }
    );


    document
        .querySelectorAll(".nav-link")
        .forEach((link) => {

            link.addEventListener(
                "click",
                () => {

                    if (window.innerWidth <= 760) {
                        closeNavigation();
                    }

                }
            );

        });


    /* -----------------------------------------
       LOGOUT
       ----------------------------------------- */

    if (logoutButton) {

        logoutButton.addEventListener(
            "click",
            () => {

                const confirmed =
                    window.confirm(
                        "Are you sure you want to sign out?"
                    );

                if (!confirmed) {
                    return;
                }

                window.location.href =
                    "login.html";

            }
        );

    }


    /* -----------------------------------------
       STORAGE
       ----------------------------------------- */

    function readStorage(key, fallback = []) {

        const stored =
            localStorage.getItem(key);

        if (!stored) {
            return fallback;
        }

        try {

            const parsed =
                JSON.parse(stored);

            return Array.isArray(parsed)
                ? parsed
                : fallback;

        } catch (error) {

            console.error(
                `Unable to read ${key}.`,
                error
            );

            return fallback;

        }

    }


    function getAccessRecords() {

        return readStorage(
            ACCESS_KEY,
            []
        );

    }


    function saveAccessRecords(records) {

        localStorage.setItem(
            ACCESS_KEY,
            JSON.stringify(records)
        );

        window.dispatchEvent(
            new CustomEvent(
                "employerAccessUpdated",
                {
                    detail: records
                }
            )
        );

    }


    function getDocuments() {

        return readStorage(
            DOCUMENTS_KEY,
            []
        );

    }


    /* -----------------------------------------
       HELPERS
       ----------------------------------------- */

    function generateId() {

        return (
            "EA-" +
            Date.now().toString(36) +
            "-" +
            Math.random()
                .toString(36)
                .slice(2, 7)
                .toUpperCase()
        );

    }


    function generateAccessCode() {

        const characters =
            "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

        let code = "";

        for (let index = 0; index < 8; index++) {

            code +=
                characters[
                    Math.floor(
                        Math.random() *
                        characters.length
                    )
                ];

        }

        return code;

    }


    function formatDate(dateValue) {

        if (!dateValue) {
            return "No expiry";
        }

        const date =
            new Date(
                `${dateValue}T00:00:00`
            );

        if (Number.isNaN(date.getTime())) {
            return "Invalid date";
        }

        return new Intl.DateTimeFormat(
            "en-GB",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        ).format(date);

    }


    function isExpired(record) {

        if (!record.expiry) {
            return false;
        }

        const expiry =
            new Date(
                `${record.expiry}T23:59:59`
            );

        return expiry.getTime() < Date.now();

    }


    function getEffectiveStatus(record) {

        if (record.revoked) {
            return "Revoked";
        }

        if (isExpired(record)) {
            return "Expired";
        }

        if (record.active === false) {
            return "Inactive";
        }

        return "Active";

    }


    function escapeHtml(value) {

        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    }


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


    /* -----------------------------------------
       DOCUMENT SELECTOR
       ----------------------------------------- */

    function renderDocumentSelector(
        selectedDocuments = []
    ) {

        if (!documentSelector) {
            return;
        }

        const documents =
            getDocuments();

        if (!documents.length) {

            documentSelector.innerHTML = `
                <div class="document-selector-empty">
                    No documents available.
                    Add documents from Admin &gt; Documents.
                </div>
            `;

            return;
        }


        documentSelector.innerHTML =
            documents
                .map((document) => {

                    const id =
                        String(
                            document.id ??
                            document.documentId ??
                            document.title ??
                            ""
                        );

                    const title =
                        document.title ||
                        document.name ||
                        "Untitled document";

                    const checked =
                        selectedDocuments
                            .map(String)
                            .includes(id)
                            ? "checked"
                            : "";

                    return `
                        <label class="document-option">

                            <input
                                type="checkbox"
                                name="allowedDocuments"
                                value="${escapeHtml(id)}"
                                ${checked}
                            >

                            <span class="document-option-content">

                                <strong>
                                    ${escapeHtml(title)}
                                </strong>

                                <small>
                                    ${escapeHtml(
                                        document.description ||
                                        document.visibility ||
                                        "Portfolio document"
                                    )}
                                </small>

                            </span>

                        </label>
                    `;

                })
                .join("");

    }


    function getSelectedDocuments() {

        if (!documentSelector) {
            return [];
        }

        return Array.from(
            documentSelector.querySelectorAll(
                'input[name="allowedDocuments"]:checked'
            )
        ).map(
            (input) => input.value
        );

    }


    /* -----------------------------------------
       FORM
       ----------------------------------------- */

    function resetForm() {

        if (!form) {
            return;
        }

        form.reset();

        if (accessId) {
            accessId.value = "";
        }

        if (accessActive) {
            accessActive.checked = true;
        }

        if (editorTitle) {
            editorTitle.textContent =
                "Create Employer Access";
        }

        renderDocumentSelector([]);

    }


    function populateForm(record) {

        if (!record) {
            return;
        }

        if (accessId) {
            accessId.value =
                record.id || "";
        }

        if (employerName) {
            employerName.value =
                record.employer || "";
        }

        if (employerPosition) {
            employerPosition.value =
                record.position || "";
        }

        if (employerContact) {
            employerContact.value =
                record.contact || "";
        }

        if (accessExpiry) {
            accessExpiry.value =
                record.expiry || "";
        }

        if (accessCode) {
            accessCode.value =
                record.accessCode || "";
        }

        if (accessActive) {
            accessActive.checked =
                record.active !== false &&
                !record.revoked;
        }

        if (editorTitle) {
            editorTitle.textContent =
                "Edit Employer Access";
        }

        renderDocumentSelector(
            Array.isArray(record.allowedDocuments)
                ? record.allowedDocuments
                : []
        );

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }


    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            resetForm
        );

    }


    if (form) {

        form.addEventListener(
            "submit",
            (event) => {

                event.preventDefault();

                const employer =
                    employerName?.value.trim() ||
                    "";

                const position =
                    employerPosition?.value.trim() ||
                    "";

                const contact =
                    employerContact?.value.trim() ||
                    "";

                if (!employer || !position) {

                    window.alert(
                        "Employer name and position are required."
                    );

                    return;
                }


                const records =
                    getAccessRecords();

                const existingId =
                    accessId?.value.trim() ||
                    "";

                const existingRecord =
                    records.find(
                        (item) =>
                            String(item.id) ===
                            String(existingId)
                    );

                const now =
                    new Date().toISOString();


                const record = {

                    id:
                        existingId ||
                        generateId(),

                    employer,

                    position,

                    contact,

                    expiry:
                        accessExpiry?.value ||
                        "",

                    accessCode:
                        accessCode?.value.trim() ||
                        generateAccessCode(),

                    allowedDocuments:
                        getSelectedDocuments(),

                    active:
                        accessActive?.checked !== false,

                    revoked:
                        existingRecord?.revoked ||
                        false,

                    createdAt:
                        existingRecord?.createdAt ||
                        now,

                    updatedAt:
                        now,

                    views:
                        Number(
                            existingRecord?.views
                        ) || 0,

                    downloads:
                        Number(
                            existingRecord?.downloads
                        ) || 0,

                    copied:
                        Number(
                            existingRecord?.copied
                        ) || 0

                };


                const existingIndex =
                    records.findIndex(
                        (item) =>
                            String(item.id) ===
                            String(record.id)
                    );


                if (existingIndex >= 0) {

                    records[existingIndex] = {
                        ...records[existingIndex],
                        ...record
                    };

                } else {

                    records.unshift(
                        record
                    );

                }


                saveAccessRecords(
                    records
                );

                renderAccessList();

                resetForm();

            }
        );

    }


    /* -----------------------------------------
       EDIT
       ----------------------------------------- */

    function editRecord(id) {

        const record =
            getAccessRecords().find(
                (item) =>
                    String(item.id) ===
                    String(id)
            );

        if (!record) {
            return;
        }

        populateForm(record);

    }


    /* -----------------------------------------
       REVOKE
       ----------------------------------------- */

    function revokeRecord(id) {

        const records =
            getAccessRecords();

        const index =
            records.findIndex(
                (item) =>
                    String(item.id) ===
                    String(id)
            );

        if (index === -1) {
            return;
        }

        const confirmed =
            window.confirm(
                "Revoke employer access?"
            );

        if (!confirmed) {
            return;
        }

        records[index] = {
            ...records[index],
            active: false,
            revoked: true,
            updatedAt:
                new Date().toISOString()
        };

        saveAccessRecords(
            records
        );

        renderAccessList();

    }


    /* -----------------------------------------
       RESTORE
       ----------------------------------------- */

    function restoreRecord(id) {

        const records =
            getAccessRecords();

        const index =
            records.findIndex(
                (item) =>
                    String(item.id) ===
                    String(id)
            );

        if (index === -1) {
            return;
        }

        records[index] = {
            ...records[index],
            active: true,
            revoked: false,
            updatedAt:
                new Date().toISOString()
        };

        saveAccessRecords(
            records
        );

        renderAccessList();

    }


    /* -----------------------------------------
       DELETE
       ----------------------------------------- */

    function deleteRecord(id) {

        const records =
            getAccessRecords();

        const record =
            records.find(
                (item) =>
                    String(item.id) ===
                    String(id)
            );

        if (!record) {
            return;
        }

        const confirmed =
            window.confirm(
                `Delete access for ${record.employer}?`
            );

        if (!confirmed) {
            return;
        }

        const filtered =
            records.filter(
                (item) =>
                    String(item.id) !==
                    String(id)
            );

        saveAccessRecords(
            filtered
        );

        renderAccessList();

    }


    /* -----------------------------------------
       COPY ACCESS CODE
       ----------------------------------------- */

    async function copyAccessCode(
        code,
        recordId = null
    ) {

        if (!code) {
            return;
        }

        let copied = false;

        try {

            if (
                navigator.clipboard &&
                window.isSecureContext
            ) {

                await navigator.clipboard.writeText(
                    code
                );

                copied = true;

            }

        } catch (error) {

            console.warn(
                "Clipboard API unavailable.",
                error
            );

        }


        if (!copied) {

            const temporaryInput =
                document.createElement("input");

            temporaryInput.value = code;

            temporaryInput.style.position =
                "fixed";

            temporaryInput.style.opacity =
                "0";

            document.body.appendChild(
                temporaryInput
            );

            temporaryInput.select();

            try {

                copied =
                    document.execCommand(
                        "copy"
                    );

            } catch (error) {

                console.warn(
                    "Unable to copy access code.",
                    error
                );

            }

            temporaryInput.remove();

        }


        if (copied) {

            if (recordId) {

                const records =
                    getAccessRecords();

                const index =
                    records.findIndex(
                        (item) =>
                            String(item.id) ===
                            String(recordId)
                    );

                if (index !== -1) {

                    records[index] = {
                        ...records[index],
                        copied:
                            Number(
                                records[index].copied
                            ) + 1,
                        updatedAt:
                            new Date().toISOString()
                    };

                    saveAccessRecords(
                        records
                    );

                    renderAccessList();

                }

            }

            window.alert(
                "Access code copied."
            );

        } else {

            window.prompt(
                "Copy this access code:",
                code
            );

        }

    }


    /* -----------------------------------------
       RENDER ACCESS LIST
       ----------------------------------------- */

    function renderAccessList() {

        if (!accessList) {
            return;
        }

        const records =
            getAccessRecords();

        if (!records.length) {

            accessList.innerHTML = `
                <div class="empty-state">

                    <div class="empty-state-icon">
                        <i data-lucide="shield-check"></i>
                    </div>

                    <h3>
                        No employer access records
                    </h3>

                    <p>
                        Create an employer access record
                        to control which portfolio documents
                        can be shared.
                    </p>

                </div>
            `;

            refreshIcons();

            return;
        }


        accessList.innerHTML =
            records
                .map((record) => {

                    const status =
                        getEffectiveStatus(record);

                    const statusClass =
                        status
                            .toLowerCase()
                            .replace(/\s+/g, "-");


                    const documentCount =
                        Array.isArray(
                            record.allowedDocuments
                        )
                            ? record.allowedDocuments.length
                            : 0;


                    return `
                        <article
                            class="employer-access-item"
                            data-access-id="${escapeHtml(record.id)}"
                        >

                            <div class="employer-access-item-header">

                                <div>

                                    <span class="access-status ${statusClass}">
                                        ${escapeHtml(status)}
                                    </span>

                                    <h3>
                                        ${escapeHtml(record.employer)}
                                    </h3>

                                    <p>
                                        ${escapeHtml(record.position)}
                                    </p>

                                </div>


                                <div class="access-item-actions">

                                    <button
                                        type="button"
                                        class="icon-button"
                                        data-action="edit"
                                        data-id="${escapeHtml(record.id)}"
                                        title="Edit access"
                                        aria-label="Edit access"
                                    >
                                        <i data-lucide="pencil"></i>
                                    </button>


                                    ${
                                        status === "Active"
                                            ? `
                                                <button
                                                    type="button"
                                                    class="icon-button"
                                                    data-action="revoke"
                                                    data-id="${escapeHtml(record.id)}"
                                                    title="Revoke access"
                                                    aria-label="Revoke access"
                                                >
                                                    <i data-lucide="shield-off"></i>
                                                </button>
                                            `
                                            : `
                                                <button
                                                    type="button"
                                                    class="icon-button"
                                                    data-action="restore"
                                                    data-id="${escapeHtml(record.id)}"
                                                    title="Restore access"
                                                    aria-label="Restore access"
                                                >
                                                    <i data-lucide="shield-check"></i>
                                                </button>
                                            `
                                    }


                                    <button
                                        type="button"
                                        class="icon-button danger"
                                        data-action="delete"
                                        data-id="${escapeHtml(record.id)}"
                                        title="Delete access"
                                        aria-label="Delete access"
                                    >
                                        <i data-lucide="trash-2"></i>
                                    </button>

                                </div>

                            </div>


                            <div class="employer-access-meta">

                                <div>

                                    <span>
                                        Contact
                                    </span>

                                    <strong>
                                        ${
                                            escapeHtml(
                                                record.contact ||
                                                "Not provided"
                                            )
                                        }
                                    </strong>

                                </div>


                                <div>

                                    <span>
                                        Expiry
                                    </span>

                                    <strong>
                                        ${formatDate(record.expiry)}
                                    </strong>

                                </div>


                                <div>

                                    <span>
                                        Documents
                                    </span>

                                    <strong>
                                        ${documentCount}
                                    </strong>

                                </div>

                            </div>


                            <div class="employer-access-code">

                                <div>

                                    <span>
                                        Access code
                                    </span>

                                    <strong>
                                        ${escapeHtml(
                                            record.accessCode ||
                                            "Not generated"
                                        )}
                                    </strong>

                                </div>


                                <button
                                    type="button"
                                    class="secondary-button small-button"
                                    data-action="copy"
                                    data-id="${escapeHtml(record.id)}"
                                >
                                    <i data-lucide="copy"></i>
                                    Copy
                                </button>

                            </div>


                            <div class="employer-access-activity">

                                <span>
                                    <i data-lucide="eye"></i>
                                    ${Number(record.views) || 0} views
                                </span>

                                <span>
                                    <i data-lucide="download"></i>
                                    ${Number(record.downloads) || 0} downloads
                                </span>

                                <span>
                                    <i data-lucide="link-2"></i>
                                    ${Number(record.copied) || 0} copies
                                </span>

                            </div>

                        </article>
                    `;

                })
                .join("");


        refreshIcons();

    }


    /* -----------------------------------------
       LIST ACTIONS
       ----------------------------------------- */

    if (accessList) {

        accessList.addEventListener(
            "click",
            (event) => {

                const button =
                    event.target.closest(
                        "[data-action]"
                    );

                if (!button) {
                    return;
                }


                const action =
                    button.dataset.action;

                const id =
                    button.dataset.id;


                if (!id) {
                    return;
                }


                if (action === "edit") {
                    editRecord(id);
                }


                if (action === "revoke") {
                    revokeRecord(id);
                }


                if (action === "restore") {
                    restoreRecord(id);
                }


                if (action === "delete") {
                    deleteRecord(id);
                }


                if (action === "copy") {

                    const record =
                        getAccessRecords().find(
                            (item) =>
                                String(item.id) ===
                                String(id)
                        );


                    if (record) {

                        copyAccessCode(
                            record.accessCode,
                            record.id
                        );

                    }

                }

            }
        );

    }


    /* -----------------------------------------
       DOCUMENT UPDATES
       ----------------------------------------- */

    window.addEventListener(
        "portfolioDocumentsUpdated",
        () => {

            const selected =
                getSelectedDocuments();

            renderDocumentSelector(
                selected
            );

        }
    );


    window.addEventListener(
        "storage",
        (event) => {

            if (
                event.key === ACCESS_KEY
            ) {
                renderAccessList();
            }

            if (
                event.key === DOCUMENTS_KEY
            ) {
                renderDocumentSelector(
                    getSelectedDocuments()
                );
            }

        }
    );


    /* -----------------------------------------
       INITIALISE
       ----------------------------------------- */

    renderDocumentSelector([]);

    renderAccessList();

});