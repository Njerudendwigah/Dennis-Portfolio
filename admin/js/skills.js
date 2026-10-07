/* =========================================
   SKILLS MANAGEMENT
   Dennis Ndwigah Portfolio
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const STORAGE_KEY = "dennis_skills";
    const UPDATE_EVENT = "portfolioSkillsUpdated";

    const DEFAULT_SKILLS = [
        {
            id: "skill-001",
            skill: "Supply Chain Management",
            category: "Supply Chain & Operations",
            proficiency: "Advanced",
            description: "End-to-end supply chain coordination across procurement, warehousing, distribution, transport and fulfillment operations.",
            evidence: "Managed high-volume operations supporting KES 50M+ monthly GMV.",
            visible: true,
            featured: true
        },
        {
            id: "skill-002",
            skill: "Warehouse Management",
            category: "Warehouse & Inventory",
            proficiency: "Advanced",
            description: "Warehouse operations covering receiving, put-away, picking, packing, dispatch, stock control and team productivity.",
            evidence: "Managed warehouse operations across FMCG and e-commerce environments.",
            visible: true,
            featured: true
        },
        {
            id: "skill-003",
            skill: "Inventory Management",
            category: "Warehouse & Inventory",
            proficiency: "Advanced",
            description: "Inventory accuracy, cycle counting, reconciliation, stock movement control and variance reduction.",
            evidence: "Achieved 100% inventory accuracy across 560+ SKUs.",
            visible: true,
            featured: true
        },
        {
            id: "skill-004",
            skill: "Transport & Fleet Management",
            category: "Transport & Fleet",
            proficiency: "Advanced",
            description: "Fleet coordination, route planning, vehicle utilisation, transporter management and delivery performance.",
            evidence: "Improved vehicle utilisation from 62% to 85%.",
            visible: true,
            featured: true
        },
        {
            id: "skill-005",
            skill: "Last-Mile Fulfillment",
            category: "Supply Chain & Operations",
            proficiency: "Advanced",
            description: "Planning and execution of customer deliveries with focus on service levels, route efficiency and delivery reliability.",
            evidence: "Supported high-volume fulfillment operations across multiple delivery routes.",
            visible: true,
            featured: true
        },
        {
            id: "skill-006",
            skill: "3PL & Supplier Management",
            category: "Supply Chain & Operations",
            proficiency: "Advanced",
            description: "Managing contracted logistics partners, supplier relationships, service-level agreements and operational performance.",
            evidence: "Delivered KES 2.5M+ annual transport savings through SLA renegotiation.",
            visible: true,
            featured: false
        },
        {
            id: "skill-007",
            skill: "OTIF & KPI Management",
            category: "Performance Management",
            proficiency: "Advanced",
            description: "Monitoring operational KPIs, service levels, OTIF performance, productivity, cost and customer experience.",
            evidence: "Delivered up to 92% OTIF and CSAT performance.",
            visible: true,
            featured: true
        },
        {
            id: "skill-008",
            skill: "Team Leadership",
            category: "Leadership & People",
            proficiency: "Advanced",
            description: "Leading operational teams, assigning responsibilities, monitoring performance and driving accountability.",
            evidence: "Led teams of 25+ employees and operational staff.",
            visible: true,
            featured: false
        },
        {
            id: "skill-009",
            skill: "Route Planning",
            category: "Transport & Fleet",
            proficiency: "Advanced",
            description: "Delivery route planning and optimisation with consideration for vehicle capacity, geography, service windows and cost.",
            evidence: "Supported distribution operations across multiple territories.",
            visible: true,
            featured: false
        },
        {
            id: "skill-010",
            skill: "Warehouse Process Improvement",
            category: "Continuous Improvement",
            proficiency: "Advanced",
            description: "Identifying operational bottlenecks and improving warehouse processes, layouts, workflows and resource utilisation.",
            evidence: "Improved warehouse capacity by 28%.",
            visible: true,
            featured: false
        },
        {
            id: "skill-011",
            skill: "HSE & Operational Safety",
            category: "Health, Safety & Compliance",
            proficiency: "Advanced",
            description: "Applying warehouse safety procedures, incident prevention, safe working practices and operational compliance.",
            evidence: "Reduced warehouse incidents by 30%.",
            visible: true,
            featured: false
        },
        {
            id: "skill-012",
            skill: "ERP, WMS & Operations Systems",
            category: "Systems & Technology",
            proficiency: "Advanced",
            description: "Using digital systems to manage inventory, orders, warehouse workflows, customer operations and reporting.",
            evidence: "Hands-on experience with ERP, WMS and operations management platforms.",
            visible: true,
            featured: false
        },
        {
            id: "skill-013",
            skill: "Advanced Excel",
            category: "Systems & Technology",
            proficiency: "Advanced",
            description: "Operational analysis, reporting, lookups, data validation, trackers and performance reporting.",
            evidence: "Used Excel extensively for operational reporting and analysis.",
            visible: true,
            featured: false
        },
        {
            id: "skill-014",
            skill: "Cost Optimisation",
            category: "Performance Management",
            proficiency: "Advanced",
            description: "Identifying operational cost drivers and implementing practical cost-control measures.",
            evidence: "Delivered KES 2.5M+ annual transport savings.",
            visible: true,
            featured: false
        }
    ];


    /* =========================================
       DOM ELEMENTS
       ========================================= */

    const skillsGrid = document.getElementById("skillsGrid");
    const emptyState = document.getElementById("emptySkillsState");
    const skillForm = document.getElementById("skillForm");
    const skillEditor = document.getElementById("skillEditor");
    const editorTitle = document.getElementById("editorTitle");

    const addSkillButton = document.getElementById("addSkillButton");
    const emptyAddSkillButton = document.getElementById("emptyAddSkillButton");
    const clearSkillForm = document.getElementById("clearSkillForm");
    const restoreDefaults = document.getElementById("restoreDefaults");
    const categoryFilter = document.getElementById("categoryFilter");
    const saveMessage = document.getElementById("saveMessage");
    const currentYear = document.getElementById("currentYear");

    const sidebar = document.getElementById("adminSidebar");
    const openSidebar = document.getElementById("openSidebar");
    const closeSidebar = document.getElementById("closeSidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const logoutButton = document.getElementById("logoutButton");

    const skillId = document.getElementById("skillId");
    const skillName = document.getElementById("skillName");
    const skillCategory = document.getElementById("skillCategory");
    const skillProficiency = document.getElementById("skillProficiency");
    const skillEvidence = document.getElementById("skillEvidence");
    const skillDescription = document.getElementById("skillDescription");
    const skillVisible = document.getElementById("skillVisible");
    const skillFeatured = document.getElementById("skillFeatured");


    /* =========================================
       YEAR
       ========================================= */

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
        openSidebar.addEventListener("click", openNavigation);
    }


    if (closeSidebar) {
        closeSidebar.addEventListener("click", closeNavigation);
    }


    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeNavigation);
    }


    document.querySelectorAll(".nav-link").forEach((link) => {
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
       STORAGE
       ========================================= */

    function cloneDefaults() {
        return DEFAULT_SKILLS.map((skill) => ({
            ...skill
        }));
    }


    function loadSkills() {

        const saved = localStorage.getItem(STORAGE_KEY);

        if (!saved) {

            const defaults = cloneDefaults();

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(defaults)
            );

            return defaults;
        }


        try {

            const parsed = JSON.parse(saved);

            if (!Array.isArray(parsed)) {
                return cloneDefaults();
            }

            return parsed;

        } catch (error) {

            console.error(
                "Unable to load skills.",
                error
            );

            return cloneDefaults();
        }
    }


    function saveSkills(skills) {

        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(skills)
        );

        window.dispatchEvent(
            new CustomEvent(UPDATE_EVENT, {
                detail: skills
            })
        );
    }


    function generateId() {

        return (
            "skill-" +
            Date.now() +
            "-" +
            Math.random()
                .toString(36)
                .substring(2, 8)
        );
    }


    /* =========================================
       SECURITY / TEXT
       ========================================= */

    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function getInitials(value) {

        const words = String(value ?? "")
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        if (!words.length) {
            return "SK";
        }

        if (words.length === 1) {
            return words[0]
                .substring(0, 2)
                .toUpperCase();
        }

        return (
            words[0].charAt(0) +
            words[1].charAt(0)
        ).toUpperCase();
    }


    /* =========================================
       CATEGORIES
       ========================================= */

    function getCategories(skills) {

        return [
            ...new Set(
                skills
                    .map((skill) =>
                        String(skill.category || "").trim()
                    )
                    .filter(Boolean)
            )
        ].sort((a, b) => a.localeCompare(b));
    }


    function renderCategoryFilter(skills) {

        if (!categoryFilter) {
            return;
        }

        const selected = categoryFilter.value || "all";
        const categories = getCategories(skills);

        categoryFilter.innerHTML = `
            <option value="all">
                All categories
            </option>
        `;

        categories.forEach((category) => {

            const option =
                document.createElement("option");

            option.value = category;
            option.textContent = category;

            categoryFilter.appendChild(option);
        });

        if (categories.includes(selected)) {
            categoryFilter.value = selected;
        } else {
            categoryFilter.value = "all";
        }
    }


    /* =========================================
       SUMMARY
       ========================================= */

    function renderSummary(skills) {

        const totalSkills =
            document.getElementById("totalSkills");

        const featuredSkills =
            document.getElementById("featuredSkills");

        const visibleSkills =
            document.getElementById("visibleSkills");

        const skillCategories =
            document.getElementById("skillCategories");


        if (totalSkills) {
            totalSkills.textContent = skills.length;
        }


        if (featuredSkills) {
            featuredSkills.textContent =
                skills.filter(
                    (skill) => skill.featured === true
                ).length;
        }


        if (visibleSkills) {
            visibleSkills.textContent =
                skills.filter(
                    (skill) => skill.visible !== false
                ).length;
        }


        if (skillCategories) {
            skillCategories.textContent =
                getCategories(skills).length;
        }
    }


    /* =========================================
       SKILL CARD
       ========================================= */

    function createSkillCard(skill) {

        const card =
            document.createElement("article");

        card.className = "skill-card";


        const featuredBadge = skill.featured
            ? `
                <span class="skill-badge featured">
                    Featured
                </span>
            `
            : "";


        const visibilityBadge = skill.visible !== false
            ? `
                <span class="skill-badge public">
                    Public
                </span>
            `
            : `
                <span class="skill-badge private">
                    Hidden
                </span>
            `;


        const description = skill.description
            ? `
                <p class="skill-description">
                    ${escapeHtml(skill.description)}
                </p>
            `
            : "";


        const evidence = skill.evidence
            ? `
                <div class="skill-evidence">

                    <span class="evidence-label">
                        EVIDENCE
                    </span>

                    <p>
                        ${escapeHtml(skill.evidence)}
                    </p>

                </div>
            `
            : "";


        card.innerHTML = `
            <div class="skill-card-top">

                <div class="skill-number">
                    ${escapeHtml(
                        getInitials(skill.skill)
                    )}
                </div>

                <div class="skill-status">
                    ${featuredBadge}
                    ${visibilityBadge}
                </div>

            </div>


            <div class="skill-card-content">

                <span class="skill-category">
                    ${escapeHtml(
                        skill.category ||
                        "Professional Skill"
                    )}
                </span>


                <h3>
                    ${escapeHtml(skill.skill)}
                </h3>


                <span class="skill-proficiency">
                    ${escapeHtml(
                        skill.proficiency ||
                        "Advanced"
                    )}
                </span>


                ${description}

                ${evidence}

            </div>


            <div class="skill-card-actions">

                <button
                    type="button"
                    class="skill-edit-button"
                    data-action="edit"
                    data-id="${escapeHtml(skill.id)}"
                >
                    Edit
                </button>


                <button
                    type="button"
                    class="skill-delete-button"
                    data-action="delete"
                    data-id="${escapeHtml(skill.id)}"
                >
                    Delete
                </button>

            </div>
        `;

        return card;
    }


    /* =========================================
       RENDER
       ========================================= */

    function renderSkills() {

        if (!skillsGrid) {
            return;
        }


        const skills = loadSkills();

        renderSummary(skills);
        renderCategoryFilter(skills);


        const selectedCategory =
            categoryFilter
                ? categoryFilter.value
                : "all";


        let filteredSkills = skills.filter((skill) => {

            if (selectedCategory === "all") {
                return true;
            }

            return skill.category === selectedCategory;
        });


        filteredSkills.sort((a, b) => {

            if (
                Boolean(a.featured) !==
                Boolean(b.featured)
            ) {
                return a.featured ? -1 : 1;
            }

            return String(a.skill || "")
                .localeCompare(
                    String(b.skill || "")
                );
        });


        skillsGrid.innerHTML = "";


        if (!filteredSkills.length) {

            if (emptyState) {
                emptyState.hidden = false;
            }

            return;
        }


        if (emptyState) {
            emptyState.hidden = true;
        }


        filteredSkills.forEach((skill) => {
            skillsGrid.appendChild(
                createSkillCard(skill)
            );
        });
    }


    /* =========================================
       MESSAGE
       ========================================= */

    function showMessage(
        message,
        type = "success"
    ) {

        if (!saveMessage) {
            return;
        }


        saveMessage.textContent = message;

        saveMessage.className =
            "save-message show " + type;


        window.setTimeout(() => {

            saveMessage.textContent = "";

            saveMessage.className =
                "save-message";

        }, 3000);
    }


    /* =========================================
       EDITOR
       ========================================= */

    function scrollToEditor() {

        if (!skillEditor) {
            return;
        }


        skillEditor.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


        window.setTimeout(() => {

            if (skillName) {
                skillName.focus();
            }

        }, 450);
    }


    function clearForm() {

        if (!skillForm) {
            return;
        }


        skillForm.reset();


        if (skillId) {
            skillId.value = "";
        }


        if (skillProficiency) {
            skillProficiency.value = "Advanced";
        }


        if (skillVisible) {
            skillVisible.checked = true;
        }


        if (skillFeatured) {
            skillFeatured.checked = false;
        }


        if (editorTitle) {
            editorTitle.textContent = "Add a skill";
        }


        const saveButton =
            document.getElementById("saveSkillButton");


        if (saveButton) {
            saveButton.textContent = "Save skill";
        }
    }


    /* =========================================
       EDIT SKILL
       ========================================= */

    function editSkill(id) {

        const skills = loadSkills();


        const skill = skills.find(
            (item) =>
                String(item.id) === String(id)
        );


        if (!skill) {
            return;
        }


        if (skillId) {
            skillId.value = skill.id || "";
        }


        if (skillName) {
            skillName.value = skill.skill || "";
        }


        if (skillCategory) {
            skillCategory.value =
                skill.category || "";
        }


        if (skillProficiency) {
            skillProficiency.value =
                skill.proficiency || "Advanced";
        }


        if (skillEvidence) {
            skillEvidence.value =
                skill.evidence || "";
        }


        if (skillDescription) {
            skillDescription.value =
                skill.description || "";
        }


        if (skillVisible) {
            skillVisible.checked =
                skill.visible !== false;
        }


        if (skillFeatured) {
            skillFeatured.checked =
                skill.featured === true;
        }


        if (editorTitle) {
            editorTitle.textContent =
                "Edit skill";
        }


        const saveButton =
            document.getElementById(
                "saveSkillButton"
            );


        if (saveButton) {
            saveButton.textContent =
                "Update skill";
        }


        scrollToEditor();
    }


    /* =========================================
       DELETE SKILL
       ========================================= */

    function deleteSkill(id) {

        const skills = loadSkills();


        const skill = skills.find(
            (item) =>
                String(item.id) === String(id)
        );


        if (!skill) {
            return;
        }


        const confirmed = window.confirm(
            `Delete "${skill.skill}" from your portfolio skills?`
        );


        if (!confirmed) {
            return;
        }


        const updatedSkills = skills.filter(
            (item) =>
                String(item.id) !== String(id)
        );


        saveSkills(updatedSkills);


        if (
            skillId &&
            String(skillId.value) === String(id)
        ) {
            clearForm();
        }


        renderSkills();


        showMessage(
            "Skill deleted successfully."
        );
    }


    /* =========================================
       CARD ACTIONS
       ========================================= */

    if (skillsGrid) {

        skillsGrid.addEventListener(
            "click",
            (event) => {

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


                if (action === "edit") {
                    editSkill(id);
                }


                if (action === "delete") {
                    deleteSkill(id);
                }
            }
        );
    }


    /* =========================================
       ADD SKILL
       ========================================= */

    function startNewSkill() {

        clearForm();

        scrollToEditor();
    }


    if (addSkillButton) {
        addSkillButton.addEventListener(
            "click",
            startNewSkill
        );
    }


    if (emptyAddSkillButton) {
        emptyAddSkillButton.addEventListener(
            "click",
            startNewSkill
        );
    }


    /* =========================================
       CLEAR
       ========================================= */

    if (clearSkillForm) {

        clearSkillForm.addEventListener(
            "click",
            () => {

                clearForm();

                if (skillName) {
                    skillName.focus();
                }
            }
        );
    }


    /* =========================================
       FILTER
       ========================================= */

    if (categoryFilter) {

        categoryFilter.addEventListener(
            "change",
            renderSkills
        );
    }


    /* =========================================
       SAVE / UPDATE
       ========================================= */

    if (skillForm) {

        skillForm.addEventListener(
            "submit",
            (event) => {

                event.preventDefault();


                const name =
                    skillName
                        ? skillName.value.trim()
                        : "";


                const category =
                    skillCategory
                        ? skillCategory.value.trim()
                        : "";


                if (!name) {

                    showMessage(
                        "Please enter the skill name.",
                        "error"
                    );

                    if (skillName) {
                        skillName.focus();
                    }

                    return;
                }


                if (!category) {

                    showMessage(
                        "Please enter a skill category.",
                        "error"
                    );

                    if (skillCategory) {
                        skillCategory.focus();
                    }

                    return;
                }


                const skills = loadSkills();


                const existingId =
                    skillId
                        ? skillId.value.trim()
                        : "";


                const skillData = {

                    id:
                        existingId ||
                        generateId(),

                    skill:
                        name,

                    category:
                        category,

                    proficiency:
                        skillProficiency
                            ? skillProficiency.value
                            : "Advanced",

                    description:
                        skillDescription
                            ? skillDescription.value.trim()
                            : "",

                    evidence:
                        skillEvidence
                            ? skillEvidence.value.trim()
                            : "",

                    visible:
                        skillVisible
                            ? skillVisible.checked
                            : true,

                    featured:
                        skillFeatured
                            ? skillFeatured.checked
                            : false
                };


                const existingIndex =
                    skills.findIndex(
                        (item) =>
                            String(item.id) ===
                            String(existingId)
                    );


                if (existingIndex >= 0) {

                    skills[existingIndex] =
                        skillData;

                    showMessage(
                        "Skill updated successfully."
                    );

                } else {

                    skills.push(skillData);

                    showMessage(
                        "Skill added successfully."
                    );
                }


                saveSkills(skills);

                renderSkills();

                clearForm();
            }
        );
    }


    /* =========================================
       RESTORE DEFAULTS
       ========================================= */

    if (restoreDefaults) {

        restoreDefaults.addEventListener(
            "click",
            () => {

                const confirmed =
                    window.confirm(
                        "Restore the default professional skills? Existing skills will be replaced."
                    );


                if (!confirmed) {
                    return;
                }


                const defaults =
                    cloneDefaults();


                saveSkills(defaults);

                clearForm();

                renderSkills();


                showMessage(
                    "Default skills restored successfully."
                );
            }
        );
    }


    /* =========================================
       CROSS-TAB SYNC
       ========================================= */

    window.addEventListener(
        "storage",
        (event) => {

            if (event.key === STORAGE_KEY) {
                renderSkills();
            }
        }
    );


    /* =========================================
       SAME-TAB SYNC
       ========================================= */

    window.addEventListener(
        UPDATE_EVENT,
        () => {
            renderSkills();
        }
    );


    /* =========================================
       INITIAL LOAD
       ========================================= */

    renderSkills();

});