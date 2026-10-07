/* =========================================
   PROJECTS MANAGEMENT
   Dennis Ndwigah Portfolio Admin
   ========================================= */

(() => {
    "use strict";

    const STORAGE_KEY = "dennis_projects";
    const EVENT_NAME = "portfolioProjectsUpdated";

    const DEFAULT_PROJECTS = [
        {
            id: "samaki-mtaani-distribution",
            title: "Samaki Mtaani Distribution & Fulfillment System",
            organization: "Samaki Mtaani",
            category: "Supply Chain & Operations",
            period: "2026",
            summary:
                "Designed and implemented the operating model for a women-focused distribution network covering fish, eggs and other value chains across Nairobi.",
            challenge:
                "Build a practical distribution structure that could support vendor growth while maintaining stock availability, route discipline, collections and operational visibility.",
            approach:
                "Established hub-and-spoke operations, vendor ordering processes, route planning, inventory controls, supplier coordination and operational reporting.",
            results:
                "Built a repeatable operating framework for 300+ women vendors, with daily distribution controls and clearer accountability across the network.",
            skills: [
                "Supply Chain",
                "Distribution",
                "Last Mile",
                "Inventory",
                "Operations"
            ],
            link: "",
            image: "",
            visible: true,
            featured: true
        },

        {
            id: "kyosk-fulfillment",
            title: "High-Volume FMCG Fulfillment Operations",
            organization: "Kyosk Digital Services",
            category: "Fulfillment & Logistics",
            period: "2023 - 2025",
            summary:
                "Managed end-to-end fulfillment operations across warehouse, inventory and contracted transport activities at a high-volume FMCG hub.",
            challenge:
                "Maintain reliable fulfillment performance while controlling transport costs, inventory accuracy and service quality across a growing delivery operation.",
            approach:
                "Combined warehouse controls, dispatch planning, fleet coordination, partner SLA management, inventory discipline and performance tracking.",
            results:
                "Managed 1,000+ weekly orders, 92% OTIF, 92% CSAT and more than KES 50M monthly GMV while reducing monthly transport costs through SLA renegotiation.",
            skills: [
                "Warehouse",
                "Fulfillment",
                "Fleet",
                "OTIF",
                "3PL Management"
            ],
            link: "",
            image: "",
            visible: true,
            featured: true
        },

        {
            id: "iprocure-warehouse",
            title: "Warehouse Capacity & Transport Optimization",
            organization: "iProcure Ltd",
            category: "Warehouse & Transport",
            period: "2023",
            summary:
                "Improved warehouse utilization, vehicle utilization and delivery economics while supporting rural stockist distribution.",
            challenge:
                "Increase operational capacity and transport efficiency while maintaining stock availability for a distributed network of rural stockists.",
            approach:
                "Used load consolidation, dispatch planning, warehouse controls and vehicle utilization tracking to improve the operating model.",
            results:
                "Improved vehicle utilization from 62% to 85% and supported distribution to more than 80 rural stockists.",
            skills: [
                "Warehouse Management",
                "Transport",
                "Route Planning",
                "Inventory"
            ],
            link: "",
            image: "",
            visible: true,
            featured: false
        },

        {
            id: "kuehne-nagel-air-freight",
            title: "Air Freight Export Turnaround Improvement",
            organization: "Kuehne + Nagel",
            category: "Freight Forwarding",
            period: "2021 - 2023",
            summary:
                "Supported time-critical air freight operations spanning warehouse dispatch, export documentation and coordination with airlines and clearing agents.",
            challenge:
                "Reduce export turnaround time while maintaining documentation accuracy and coordination across multiple stakeholders.",
            approach:
                "Coordinated warehouse, airline, clearing and customer-service activities while strengthening dispatch and documentation flow.",
            results:
                "Helped reduce export turnaround time from five days to four days.",
            skills: [
                "Freight Forwarding",
                "Export Documentation",
                "Warehouse",
                "Coordination"
            ],
            link: "",
            image: "",
            visible: true,
            featured: false
        }
    ];

    /* =========================================
       HELPERS
       ========================================= */

    const $ = (selector, scope = document) =>
        scope.querySelector(selector);

    const $$ = (selector, scope = document) =>
        [...scope.querySelectorAll(selector)];

    const clean = (value) =>
        String(value ?? "").trim();

    const escapeHtml = (value) => {
        return clean(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    };

    /* =========================================
       NORMALIZE PROJECT
       ========================================= */

    function normalizeProject(project) {
        return {
            id:
                clean(project?.id) ||
                `project-${Date.now()}-${Math.random()
                    .toString(36)
                    .slice(2, 8)}`,

            title: clean(project?.title),

            organization: clean(project?.organization),

            category: clean(project?.category),

            period: clean(project?.period),

            summary: clean(project?.summary),

            challenge: clean(project?.challenge),

            approach: clean(project?.approach),

            results: clean(project?.results),

            skills: Array.isArray(project?.skills)
                ? project.skills
                      .map(clean)
                      .filter(Boolean)
                : clean(project?.skills)
                      .split(",")
                      .map(clean)
                      .filter(Boolean),

            link: clean(project?.link),

            image: clean(project?.image),

            visible: project?.visible !== false,

            featured: project?.featured === true
        };
    }

    /* =========================================
       LOAD PROJECTS
       ========================================= */

    function loadProjects() {
        const raw = localStorage.getItem(STORAGE_KEY);

        if (!raw) {
            const defaults =
                DEFAULT_PROJECTS.map(normalizeProject);

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(defaults)
            );

            return defaults;
        }

        try {
            const parsed = JSON.parse(raw);

            if (!Array.isArray(parsed)) {
                throw new Error(
                    "Stored projects are not an array."
                );
            }

            return parsed.map(normalizeProject);
        } catch (error) {
            console.error(
                "Unable to load projects.",
                error
            );

            return DEFAULT_PROJECTS.map(
                normalizeProject
            );
        }
    }

    let projects = loadProjects();

    /* =========================================
       SAVE PROJECTS
       ========================================= */

    function commitProjects(nextProjects) {
        projects = nextProjects.map(
            normalizeProject
        );

        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(projects)
        );

        window.dispatchEvent(
            new CustomEvent(EVENT_NAME, {
                detail: projects
            })
        );
    }

    /* =========================================
       MESSAGE
       ========================================= */

    function showMessage(
        message,
        type = "success"
    ) {
        const messageElement =
            $("#projectMessage");

        if (!messageElement) {
            return;
        }

        messageElement.textContent = message;

        messageElement.className =
            `save-message show ${
                type === "error"
                    ? "error"
                    : ""
            }`;

        clearTimeout(showMessage.timer);

        showMessage.timer =
            setTimeout(() => {
                messageElement.textContent = "";

                messageElement.className =
                    "save-message";
            }, 3500);
    }

    /* =========================================
       COUNTS
       ========================================= */

    function updateCounts() {
        const featuredCount =
            projects.filter(
                project => project.featured
            ).length;

        const publicCount =
            projects.filter(
                project => project.visible
            ).length;

        const projectCount =
            $("#projectCount");

        const featuredProjectCount =
            $("#featuredProjectCount");

        const publicProjectCount =
            $("#publicProjectCount");

        if (projectCount) {
            projectCount.textContent =
                projects.length;
        }

        if (featuredProjectCount) {
            featuredProjectCount.textContent =
                featuredCount;
        }

        if (publicProjectCount) {
            publicProjectCount.textContent =
                publicCount;
        }
    }

    /* =========================================
       RENDER PROJECT LIST
       ========================================= */

    function renderProjects() {
        const list =
            $("#projectList");

        if (!list) {
            return;
        }

        updateCounts();

        const orderedProjects =
            [...projects].sort(
                (a, b) => {
                    if (
                        a.featured !==
                        b.featured
                    ) {
                        return a.featured
                            ? -1
                            : 1;
                    }

                    return a.title.localeCompare(
                        b.title
                    );
                }
            );

        if (!orderedProjects.length) {
            list.innerHTML = `
                <div class="empty-state">

                    <h3>No projects added</h3>

                    <p>
                        Add your first case study
                        or operational project.
                    </p>
                </div>
            `;

            return;
        }

        list.innerHTML =
            orderedProjects
                .map((project, index) => {
                    return `
                        <article
                            class="project-admin-card"
                        >
                            <div
                                class="project-card-top"
                            >
                                <span
                                    class="project-number"
                                >
                                    ${String(
                                        index + 1
                                    ).padStart(
                                        2,
                                        "0"
                                    )}
                                </span>

                                <div
                                    class="project-statuses"
                                >
                                    ${
                                        project.featured
                                            ? `
                                                <span
                                                    class="status-pill featured"
                                                >
                                                    Featured
                                                </span>
                                            `
                                            : ""
                                    }

                                    ${
                                        project.visible
                                            ? `
                                                <span
                                                    class="status-pill visible"
                                                >
                                                    Public
                                                </span>
                                            `
                                            : `
                                                <span
                                                    class="status-pill hidden"
                                                >
                                                    Hidden
                                                </span>
                                            `
                                    }
                                </div>
                            </div>

                            <div
                                class="project-card-content"
                            >
                                ${
                                    project.category
                                        ? `
                                            <span
                                                class="project-category"
                                            >
                                                ${escapeHtml(
                                                    project.category
                                                )}
                                            </span>
                                        `
                                        : ""
                                }

                                <h3>
                                    ${escapeHtml(
                                        project.title
                                    )}
                                </h3>

                                ${
                                    project.organization
                                        ? `
                                            <p
                                                class="project-company"
                                            >
                                                ${escapeHtml(
                                                    project.organization
                                                )}
                                            </p>
                                        `
                                        : ""
                                }

                                ${
                                    project.period
                                        ? `
                                            <p
                                                class="project-meta"
                                            >
                                                ${escapeHtml(
                                                    project.period
                                                )}
                                            </p>
                                        `
                                        : ""
                                }

                                ${
                                    project.summary
                                        ? `
                                            <p
                                                class="project-summary"
                                            >
                                                ${escapeHtml(
                                                    project.summary
                                                )}
                                            </p>
                                        `
                                        : ""
                                }

                                <div
                                    class="project-result"
                                >
                                    <strong>
                                        Result
                                    </strong>

                                    <span>
                                        ${
                                            escapeHtml(
                                                project.results ||
                                                    "No result added yet."
                                            )
                                        }
                                    </span>
                                </div>

                                ${
                                    project.skills.length
                                        ? `
                                            <div
                                                class="project-skills"
                                            >
                                                ${project.skills
                                                    .slice(
                                                        0,
                                                        5
                                                    )
                                                    .map(
                                                        skill =>
                                                            `
                                                                <span>
                                                                    ${escapeHtml(
                                                                        skill
                                                                    )}
                                                                </span>
                                                            `
                                                    )
                                                    .join(
                                                        ""
                                                    )}

                                                ${
                                                    project
                                                        .skills
                                                        .length >
                                                    5
                                                        ? `
                                                            <small>
                                                                +
                                                                ${
                                                                    project
                                                                        .skills
                                                                        .length -
                                                                    5
                                                                }
                                                                more
                                                            </small>
                                                        `
                                                        : ""
                                                }
                                            </div>
                                        `
                                        : ""
                                }
                            </div>

                            <div
                                class="project-card-actions"
                            >
                                <button
                                    type="button"
                                    class="secondary-button"
                                    data-action="edit"
                                    data-id="${escapeHtml(
                                        project.id
                                    )}"
                                >
                                    Edit
                                </button>

                                <button
                                    type="button"
                                    class="danger-button"
                                    data-action="delete"
                                    data-id="${escapeHtml(
                                        project.id
                                    )}"
                                >
                                    Delete
                                </button>
                            </div>
                        </article>
                    `;
                })
                .join("");
    }

    /* =========================================
       FORM HELPERS
       ========================================= */

    function setField(
        id,
        value
    ) {
        const field =
            document.getElementById(id);

        if (field) {
            field.value = value ?? "";
        }
    }

    function resetForm() {
        const form =
            $("#projectForm");

        if (!form) {
            return;
        }

        form.reset();

        setField(
            "projectId",
            ""
        );

        const visible =
            $("#visible");

        const featured =
            $("#featured");

        if (visible) {
            visible.checked = true;
        }

        if (featured) {
            featured.checked = false;
        }

        const editorTitle =
            $("#editorTitle");

        if (editorTitle) {
            editorTitle.textContent =
                "Add a project";
        }
    }

    /* =========================================
       EDIT PROJECT
       ========================================= */

    function editProject(id) {
        const project =
            projects.find(
                item => item.id === id
            );

        if (!project) {
            return;
        }

        setField(
            "projectId",
            project.id
        );

        setField(
            "projectTitle",
            project.title
        );

        setField(
            "organization",
            project.organization
        );

        setField(
            "category",
            project.category
        );

        setField(
            "period",
            project.period
        );

        setField(
            "summary",
            project.summary
        );

        setField(
            "challenge",
            project.challenge
        );

        setField(
            "approach",
            project.approach
        );

        setField(
            "results",
            project.results
        );

        setField(
            "skills",
            project.skills.join(", ")
        );

        setField(
            "projectLink",
            project.link
        );

        setField(
            "projectImage",
            project.image
        );

        const visible =
            $("#visible");

        const featured =
            $("#featured");

        if (visible) {
            visible.checked =
                project.visible;
        }

        if (featured) {
            featured.checked =
                project.featured;
        }

        const editorTitle =
            $("#editorTitle");

        if (editorTitle) {
            editorTitle.textContent =
                "Edit project";
        }

        const editor =
            $("#projectEditor");

        if (editor) {
            editor.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }
    }

    /* =========================================
       VALIDATION
       ========================================= */

    function validateProject(
        project
    ) {
        if (!project.title) {
            return "Project title is required.";
        }

        if (!project.organization) {
            return "Organization is required.";
        }

        if (!project.category) {
            return "Project category is required.";
        }

        if (!project.summary) {
            return "Project summary is required.";
        }

        if (!project.results) {
            return "Project results are required.";
        }

        if (project.link) {
            try {
                const url =
                    new URL(project.link);

                if (
                    ![
                        "http:",
                        "https:"
                    ].includes(
                        url.protocol
                    )
                ) {
                    return (
                        "Project link must use http or https."
                    );
                }
            } catch {
                return (
                    "Project link must be a valid URL."
                );
            }
        }

        return "";
    }

    /* =========================================
       SAVE PROJECT
       ========================================= */

    function saveProject(event) {
        event.preventDefault();

        const project = {
            id: clean(
                $("#projectId")?.value
            ),

            title: clean(
                $("#projectTitle")?.value
            ),

            organization: clean(
                $("#organization")?.value
            ),

            category: clean(
                $("#category")?.value
            ),

            period: clean(
                $("#period")?.value
            ),

            summary: clean(
                $("#summary")?.value
            ),

            challenge: clean(
                $("#challenge")?.value
            ),

            approach: clean(
                $("#approach")?.value
            ),

            results: clean(
                $("#results")?.value
            ),

            skills: clean(
                $("#skills")?.value
            )
                .split(",")
                .map(clean)
                .filter(Boolean),

            link: clean(
                $("#projectLink")?.value
            ),

            image: clean(
                $("#projectImage")?.value
            ),

            visible:
                $("#visible")?.checked !==
                false,

            featured:
                $("#featured")?.checked ===
                true
        };

        const validationError =
            validateProject(project);

        if (validationError) {
            showMessage(
                validationError,
                "error"
            );

            return;
        }

        const normalized =
            normalizeProject(
                project
            );

        if (project.id) {
            projects =
                projects.map(
                    existing =>
                        existing.id ===
                        project.id
                            ? normalized
                            : existing
                );
        } else {
            projects = [
                ...projects,
                normalized
            ];
        }

        commitProjects(projects);

        renderProjects();

        resetForm();

        showMessage(
            "Project saved successfully."
        );
    }

    /* =========================================
       DELETE PROJECT
       ========================================= */

    function deleteProject(id) {
        const project =
            projects.find(
                item => item.id === id
            );

        if (!project) {
            return;
        }

        const confirmed =
            window.confirm(
                `Delete "${project.title}" at ${project.organization}? This cannot be undone from the Admin interface.`
            );

        if (!confirmed) {
            return;
        }

        commitProjects(
            projects.filter(
                item => item.id !== id
            )
        );

        renderProjects();

        resetForm();

        showMessage(
            "Project deleted."
        );
    }

    /* =========================================
       SIDEBAR
       ========================================= */

    function initializeSidebar() {
        const sidebar =
            $("#adminSidebar");

        const overlay =
            $("#sidebarOverlay");

        const openButton =
            $("#openSidebar");

        const closeButton =
            $("#closeSidebar");

        function closeNavigation() {
            sidebar?.classList.remove(
                "open"
            );

            overlay?.classList.remove(
                "active"
            );
        }

        openButton?.addEventListener(
            "click",
            () => {
                sidebar?.classList.add(
                    "open"
                );

                overlay?.classList.add(
                    "active"
                );
            }
        );

        closeButton?.addEventListener(
            "click",
            closeNavigation
        );

        overlay?.addEventListener(
            "click",
            closeNavigation
        );

        $$(".nav-link").forEach(
            link => {
                link.addEventListener(
                    "click",
                    () => {
                        if (
                            window.innerWidth <=
                            760
                        ) {
                            closeNavigation();
                        }
                    }
                );
            }
        );

        document.addEventListener(
            "keydown",
            event => {
                if (
                    event.key ===
                    "Escape"
                ) {
                    closeNavigation();
                }
            }
        );
    }

    /* =========================================
       INITIALIZE
       ========================================= */

    function initialize() {
        const currentYear =
            $("#currentYear");

        if (currentYear) {
            currentYear.textContent =
                new Date().getFullYear();
        }

        initializeSidebar();

        $("#projectForm")?.addEventListener(
            "submit",
            saveProject
        );

        $("#cancelEdit")?.addEventListener(
            "click",
            resetForm
        );

        $("#addProjectButton")?.addEventListener(
            "click",
            () => {
                resetForm();

                const editor =
                    $("#projectEditor");

                editor?.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

                $("#projectTitle")?.focus();
            }
        );

        $("#projectList")?.addEventListener(
            "click",
            event => {
                const button =
                    event.target.closest(
                        "button[data-action]"
                    );

                if (!button) {
                    return;
                }

                const action =
                    button.dataset.action;

                const id =
                    button.dataset.id;

                if (
                    action ===
                    "edit"
                ) {
                    editProject(id);
                }

                if (
                    action ===
                    "delete"
                ) {
                    deleteProject(id);
                }
            }
        );

        $("#resetProjects")?.addEventListener(
            "click",
            () => {
                const confirmed =
                    window.confirm(
                        "Restore the original project records? This will replace your current project data."
                    );

                if (!confirmed) {
                    return;
                }

                commitProjects(
                    DEFAULT_PROJECTS
                );

                renderProjects();

                resetForm();

                showMessage(
                    "Default projects restored."
                );
            }
        );

        /* =====================================
           SYNC WITH OTHER TABS
           ===================================== */

        window.addEventListener(
            "storage",
            event => {
                if (
                    event.key ===
                    STORAGE_KEY
                ) {
                    projects =
                        loadProjects();

                    renderProjects();
                }
            }
        );

        /* =====================================
           LOGOUT
           ===================================== */

        $("#logoutButton")?.addEventListener(
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

        renderProjects();
    }

    document.addEventListener(
        "DOMContentLoaded",
        initialize
    );
})();