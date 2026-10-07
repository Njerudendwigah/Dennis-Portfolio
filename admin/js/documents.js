document.addEventListener("DOMContentLoaded", () => {
    const DOCUMENTS_KEY = "portfolioDocuments";
    const DB_NAME = "DennisPortfolioDB";
    const STORE_NAME = "documents";
    const MAX_FILE_SIZE = 10 * 1024 * 1024;

    const ALLOWED_TYPES = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png"
    ];

    const $ = (id) => document.getElementById(id);

    const form = $("documentForm");
    const documentList = $("documentList");
    const documentModal = $("documentModal");
    const documentModalTitle = $("documentModalTitle");

    const documentId = $("documentId");
    const documentName = $("documentName");
    const documentCategory = $("documentCategory");
    const documentAccess = $("documentAccess");
    const documentStatus = $("documentStatus");
    const documentDescription = $("documentDescription");
    const documentVersion = $("documentVersion");
    const documentFeatured = $("documentFeatured");

    const documentFile = $("documentFile");
    const selectedFile = $("selectedFile");
    const selectedFileName = $("selectedFileName");
    const selectedFileMeta = $("selectedFileMeta");
    const removeSelectedFile = $("removeSelectedFile");

    const documentCount = $("documentCount");
    const documentSummary = $("documentSummary");
    const logoutButton = $("logoutButton");
    const currentYear = $("currentYear");

    let selectedUpload = null;
    let existingFileId = null;
    let lastFocusedElement = null;

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }

    function openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, 1);

            request.onupgradeneeded = () => {
                const db = request.result;

                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, {
                        keyPath: "id"
                    });
                }
            };

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async function saveFile(file, id) {
        const db = await openDatabase();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction(STORE_NAME, "readwrite");
            const store = transaction.objectStore(STORE_NAME);

            store.put({
                id,
                name: file.name,
                type: file.type,
                size: file.size,
                file
            });

            transaction.oncomplete = () => {
                db.close();
                resolve(id);
            };

            transaction.onerror = () => {
                db.close();
                reject(transaction.error);
            };
        });
    }

    async function deleteFile(id) {
        if (!id) {
            return;
        }

        const db = await openDatabase();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction(STORE_NAME, "readwrite");
            const store = transaction.objectStore(STORE_NAME);

            store.delete(id);

            transaction.oncomplete = () => {
                db.close();
                resolve();
            };

            transaction.onerror = () => {
                db.close();
                reject(transaction.error);
            };
        });
    }

    function readDocuments() {
        try {
            const stored = localStorage.getItem(DOCUMENTS_KEY);
            const parsed = stored ? JSON.parse(stored) : [];

            return Array.isArray(parsed) ? parsed : [];
        } catch {
            return [];
        }
    }

    function saveDocuments(documents) {
        try {
            localStorage.setItem(
                DOCUMENTS_KEY,
                JSON.stringify(documents)
            );

            window.dispatchEvent(
                new CustomEvent("portfolioDocumentsUpdated", {
                    detail: documents
                })
            );

            return true;
        } catch {
            alert(
                "Unable to save document information. Browser storage may be full."
            );

            return false;
        }
    }

    function generateId(prefix = "DOC") {
        return `${prefix}-${Date.now().toString(36)}-${Math.random()
            .toString(36)
            .slice(2, 7)
            .toUpperCase()}`;
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function formatFileSize(bytes) {
        if (!bytes) {
            return "0 KB";
        }

        if (bytes < 1024 * 1024) {
            return `${Math.round(bytes / 1024)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    function getCategoryIcon(category) {
        const icons = {
            CV: "file-text",
            Certificate: "award",
            Academic: "graduation-cap",
            Training: "badge-check",
            Professional: "briefcase-business",
            Other: "file"
        };

        return icons[category] || "file";
    }

    function getAccessLabel(access) {
        return {
            public: "Public",
            employer: "Employer Only",
            private: "Private"
        }[access] || "Private";
    }

    function getIcon(name) {
        return `<i data-lucide="${name}"></i>`;
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

    function updateSummary(documents) {
        const active = documents.filter(
            (item) => item.status === "active"
        ).length;

        const publicDocs = documents.filter(
            (item) => item.access === "public"
        ).length;

        const employerDocs = documents.filter(
            (item) => item.access === "employer"
        ).length;

        if (documentCount) {
            documentCount.textContent = documents.length;
        }

        if (documentSummary) {
            documentSummary.textContent = documents.length
                ? `${documents.length} document${documents.length === 1 ? "" : "s"} · ${active} active · ${publicDocs} public · ${employerDocs} employer only`
                : "No documents have been added yet.";
        }
    }

    function renderDocuments() {
        if (!documentList) {
            return;
        }

        const documents = readDocuments();

        updateSummary(documents);

        if (!documents.length) {
            documentList.innerHTML = `
                <div class="document-empty-state">
                    <div class="document-empty-icon">
                        ${getIcon("file-text")}
                    </div>

                    <h3>No documents yet</h3>

                    <p>
                        Upload your CV, certificates, academic records,
                        or other professional documents.
                    </p>

                    <button
                        type="button"
                        class="admin-primary-btn"
                        data-action="open-document-form"
                    >
                        ${getIcon("upload")}
                        <span>Add first document</span>
                    </button>
                </div>
            `;

            refreshIcons();
            return;
        }

        documents.sort((a, b) => {
            if (Boolean(b.featured) !== Boolean(a.featured)) {
                return b.featured ? 1 : -1;
            }

            return String(b.updatedAt || "").localeCompare(
                String(a.updatedAt || "")
            );
        });

        documentList.innerHTML = documents.map((item) => {
            const title = item.name || "Untitled document";
            const category = item.category || "Other";
            const access = item.access || "private";
            const status = item.status || "inactive";

            return `
                <article class="document-admin-card">
                    <div class="document-card-main">
                        <div class="document-icon">
                            ${getIcon(getCategoryIcon(category))}
                        </div>

                        <div class="document-info">
                            <div class="document-title-row">
                                <h3>${escapeHtml(title)}</h3>

                                ${
                                    item.featured
                                        ? `<span class="document-featured">Featured</span>`
                                        : ""
                                }
                            </div>

                            <p class="document-category">
                                ${escapeHtml(category)}
                            </p>

                            <p class="document-description">
                                ${escapeHtml(
                                    item.description ||
                                    "No description provided."
                                )}
                            </p>

                            <div class="document-meta">
                                <span class="document-access-${escapeHtml(access)}">
                                    ${escapeHtml(getAccessLabel(access))}
                                </span>

                                <span class="document-status-${escapeHtml(status)}">
                                    ${status === "active" ? "Active" : "Inactive"}
                                </span>

                                <span>
                                    Version ${escapeHtml(item.version || "1.0")}
                                </span>
                            </div>

                            ${
                                item.fileName
                                    ? `
                                        <div class="document-reference">
                                            ${getIcon("paperclip")}
                                            <span>
                                                ${escapeHtml(item.fileName)}
                                                · ${formatFileSize(item.fileSize)}
                                            </span>
                                        </div>
                                    `
                                    : ""
                            }
                        </div>
                    </div>

                    <div class="document-card-actions">
                        <button
                            type="button"
                            class="icon-button"
                            title="Edit document"
                            data-document-action="edit"
                            data-document-id="${escapeHtml(item.id)}"
                        >
                            ${getIcon("pencil")}
                        </button>

                        <button
                            type="button"
                            class="icon-button"
                            title="${status === "active" ? "Deactivate" : "Activate"} document"
                            data-document-action="toggle"
                            data-document-id="${escapeHtml(item.id)}"
                        >
                            ${getIcon(
                                status === "active"
                                    ? "eye-off"
                                    : "eye"
                            )}
                        </button>

                        <button
                            type="button"
                            class="icon-button danger"
                            title="Delete document"
                            data-document-action="delete"
                            data-document-id="${escapeHtml(item.id)}"
                        >
                            ${getIcon("trash-2")}
                        </button>
                    </div>
                </article>
            `;
        }).join("");

        refreshIcons();
    }

    function showSelectedFile(file) {
        if (!selectedFile || !selectedFileName || !selectedFileMeta) {
            return;
        }

        selectedFileName.textContent = file.name;
        selectedFileMeta.textContent =
            `${formatFileSize(file.size)} · ${file.type || "Unknown type"}`;

        selectedFile.classList.remove("hidden");

        refreshIcons();
    }

    function clearSelectedFile() {
        selectedUpload = null;

        if (documentFile) {
            documentFile.value = "";
        }

        if (selectedFile) {
            selectedFile.classList.add("hidden");
        }
    }

    function resetForm() {
        form?.reset();

        if (documentId) {
            documentId.value = "";
        }

        if (documentVersion) {
            documentVersion.value = "1.0";
        }

        if (documentAccess) {
            documentAccess.value = "public";
        }

        if (documentStatus) {
            documentStatus.value = "active";
        }

        if (documentFeatured) {
            documentFeatured.checked = false;
        }

        existingFileId = null;
        clearSelectedFile();
    }

    function openDocumentForm(documentToEdit = null) {
        if (!documentModal) {
            return;
        }

        lastFocusedElement = document.activeElement;

        resetForm();

        documentModalTitle.textContent =
            documentToEdit ? "Edit Document" : "Add Document";

        if (documentToEdit) {
            documentId.value = documentToEdit.id || "";
            documentName.value = documentToEdit.name || "";
            documentCategory.value =
                documentToEdit.category || "Other";
            documentAccess.value =
                documentToEdit.access || "private";
            documentStatus.value =
                documentToEdit.status || "active";
            documentDescription.value =
                documentToEdit.description || "";
            documentVersion.value =
                documentToEdit.version || "1.0";
            documentFeatured.checked =
                Boolean(documentToEdit.featured);

            existingFileId = documentToEdit.fileId || null;

            if (documentToEdit.fileName) {
                selectedFileName.textContent =
                    documentToEdit.fileName;

                selectedFileMeta.textContent =
                    formatFileSize(documentToEdit.fileSize);

                selectedFile.classList.remove("hidden");
            }
        }

        documentModal.classList.remove("hidden");
        documentModal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");

        setTimeout(() => documentName?.focus(), 50);
    }

    function closeDocumentForm() {
        if (!documentModal) {
            return;
        }

        documentModal.classList.add("hidden");
        documentModal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");

        lastFocusedElement?.focus?.();
        lastFocusedElement = null;
    }

    window.openDocumentForm = openDocumentForm;
    window.closeDocumentForm = closeDocumentForm;

    document.addEventListener("click", (event) => {
        const action = event.target.closest("[data-action]");

        if (action?.dataset.action === "open-document-form") {
            openDocumentForm();
        }

        if (action?.dataset.action === "close-document-form") {
            closeDocumentForm();
        }
    });

    documentFile?.addEventListener("change", () => {
        const file = documentFile.files?.[0];

        if (!file) {
            return;
        }

        if (!ALLOWED_TYPES.includes(file.type)) {
            alert(
                "Unsupported file type. Upload PDF, DOC, DOCX, JPG or PNG."
            );

            clearSelectedFile();
            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            alert("File is too large. Maximum allowed size is 10 MB.");

            clearSelectedFile();
            return;
        }

        selectedUpload = file;
        showSelectedFile(file);
    });

    removeSelectedFile?.addEventListener("click", () => {
        clearSelectedFile();
        existingFileId = null;
    });

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = documentName.value.trim();

        if (!name) {
            alert("Please enter a document name.");
            documentName.focus();
            return;
        }

        const documents = readDocuments();
        const id = documentId.value.trim() || generateId();
        const now = new Date().toISOString();

        let fileId = existingFileId;
        let fileName = "";
        let fileSize = 0;
        let fileType = "";

        const existing = documents.find(
            (item) => item.id === id
        );

        if (selectedUpload) {
            fileId = existing?.fileId || generateId("FILE");

            try {
                await saveFile(selectedUpload, fileId);
            } catch {
                alert("The file could not be stored in this browser.");
                return;
            }

            fileName = selectedUpload.name;
            fileSize = selectedUpload.size;
            fileType = selectedUpload.type;
        } else if (existing) {
            fileName = existing.fileName || "";
            fileSize = existing.fileSize || 0;
            fileType = existing.fileType || "";
        }

        const record = {
            id,
            name,
            category: documentCategory.value,
            access: documentAccess.value,
            status: documentStatus.value,
            description: documentDescription.value.trim(),
            version: documentVersion.value.trim() || "1.0",
            featured: documentFeatured.checked,
            fileId: fileId || null,
            fileName,
            fileSize,
            fileType,
            createdAt: existing?.createdAt || now,
            updatedAt: now
        };

        const index = documents.findIndex(
            (item) => item.id === id
        );

        if (index >= 0) {
            documents[index] = record;
        } else {
            documents.push(record);
        }

        if (!saveDocuments(documents)) {
            return;
        }

        renderDocuments();
        closeDocumentForm();

        alert(
            index >= 0
                ? "Document updated successfully."
                : "Document uploaded successfully."
        );
    });

    documentList?.addEventListener("click", async (event) => {
        const button = event.target.closest(
            "[data-document-action]"
        );

        if (!button) {
            return;
        }

        const id = button.dataset.documentId;
        const action = button.dataset.documentAction;
        const documents = readDocuments();

        const index = documents.findIndex(
            (item) => item.id === id
        );

        if (index === -1) {
            return;
        }

        const documentItem = documents[index];

        if (action === "edit") {
            openDocumentForm(documentItem);
            return;
        }

        if (action === "toggle") {
            documentItem.status =
                documentItem.status === "active"
                    ? "inactive"
                    : "active";

            documentItem.updatedAt =
                new Date().toISOString();

            saveDocuments(documents);
            renderDocuments();
            return;
        }

        if (action === "delete") {
            const confirmed = confirm(
                `Delete "${documentItem.name}"? This cannot be undone.`
            );

            if (!confirmed) {
                return;
            }

            if (documentItem.fileId) {
                try {
                    await deleteFile(documentItem.fileId);
                } catch {
                    console.warn("Stored file could not be removed.");
                }
            }

            documents.splice(index, 1);
            saveDocuments(documents);
            renderDocuments();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeDocumentForm();
        }
    });

    documentModal?.addEventListener("mousedown", (event) => {
        if (event.target === documentModal) {
            closeDocumentForm();
        }
    });

    window.addEventListener("storage", (event) => {
        if (event.key === DOCUMENTS_KEY) {
            renderDocuments();
        }
    });

    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            if (confirm("Are you sure you want to sign out?")) {
                window.location.href = "login.html";
            }
        });
    }

    if (window.lucide) {
        lucide.createIcons({
            attrs: {
                "stroke-width": 1.8
            }
        });
    }

    renderDocuments();
});