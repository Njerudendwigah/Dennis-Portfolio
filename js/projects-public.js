/* =========================================
   PUBLIC PROJECTS RENDERER
   Dennis Ndwigah Portfolio

   Storage:
   dennis_projects

   Public target:
   projectsGrid
   ========================================= */

(() => {
    "use strict";

    const STORAGE_KEY = "dennis_projects";
    const TARGET_ID = "projectsGrid";
    const EVENT_NAME = "portfolioProjectsUpdated";


    /* =========================================
       APPROVED FRONTEND FALLBACK
       ========================================= */

    const DEFAULT_PROJECTS = [
        {
            id: "samaki-mtaani-distribution",
            title: "Samaki Mtaani Distribution & Fulfillment System",
            organization: "Samaki Mtaani",
            category: "NETWORK DESIGN",
            period: "2026",
            summary:
                "Designed and implemented the operating model for a women-focused distribution network covering fish, eggs and other value chains across Nairobi.",
            results:
                "Built a repeatable operating framework for 300+ women vendors with daily distribution controls and clearer accountability across the network.",
            skills: [
                "Distribution",
                "Last Mile",
                "3PL",
                "OTIF"
            ],
            visible: true,
            featured: true
        },

        {
            id: "kyosk-fulfillment",
            title: "High-Volume FMCG Fulfillment Operations",
            organization: "Kyosk Digital Services",
            category: "FULFILLMENT & LOGISTICS",
            period: "2023–2025",
            summary:
                "Managed end-to-end fulfillment operations across warehouse, inventory and contracted transport activities at a high-volume FMCG hub.",
            results:
                "Managed 1,000+ weekly orders, 92% OTIF, 92% CSAT and more than KES 50M monthly GMV while reducing monthly transport costs through SLA renegotiation.",
            skills: [
                "Warehouse",
                "Fulfillment",
                "Fleet",
                "OTIF",
                "3PL"
            ],
            visible: true,
            featured: true
        },

        {
            id: "iprocure-warehouse",
            title: "Warehouse Capacity & Transport Optimization",
            organization: "iProcure Ltd",
            category: "WAREHOUSE & TRANSPORT",
            period: "2023",
            summary:
                "Improved warehouse utilization, vehicle utilization and delivery economics while supporting rural stockist distribution.",
            results:
                "Improved vehicle utilization from 62% to 85% and supported distribution to more than 80 rural stockists.",
            skills: [
                "Warehouse",
                "Transport",
                "Route Planning",
                "Inventory"
            ],
            visible: true,
            featured: false
        },

        {
            id: "kuehne-nagel-air-freight",
            title: "Air Freight Export Turnaround Improvement",
            organization: "Kuehne + Nagel",
            category: "FREIGHT FORWARDING",
            period: "2021–2023",
            summary:
                "Supported time-critical air freight operations spanning warehouse dispatch, export documentation and coordination with airlines and clearing agents.",
            results:
                "Helped reduce export turnaround time from five days to four days.",
            skills: [
                "Freight Forwarding",
                "Export Documentation",
                "Warehouse",
                "Coordination"
            ],
            visible: true,
            featured: false
        }
    ];


    /* =========================================
       HELPERS
       ========================================= */

    function clean(value) {
        return String(value ?? "").trim();
    }


    function normalize(project) {
        return {
            id: clean(project?.id),

            title: clean(project?.title),

            organization:
                clean(project?.organization),

            category:
                clean(project?.category),

            period:
                clean(project?.period),

            summary:
                clean(project?.summary),

            results:
                clean(project?.results),

            skills:
                Array.isArray(project?.skills)
                    ? project.skills
                        .map(clean)
                        .filter(Boolean)
                    : [],

            visible:
                project?.visible !== false,

            featured:
                project?.featured === true
        };
    }


    /* =========================================
       LOAD DATA
       ========================================= */

    function loadProjects() {
        try {
            const raw =
                localStorage.getItem(
                    STORAGE_KEY
                );

            if (!raw) {
                return DEFAULT_PROJECTS.map(
                    normalize
                );
            }

            const parsed =
                JSON.parse(raw);

            if (!Array.isArray(parsed)) {
                return DEFAULT_PROJECTS.map(
                    normalize
                );
            }

            return parsed
                .map(normalize)
                .filter(project =>
                    project.visible &&
                    project.title
                );

        } catch (error) {
            console.error(
                "Unable to load public project data.",
                error
            );

            return DEFAULT_PROJECTS.map(
                normalize
            );
        }
    }


    /* =========================================
       SORT
       ========================================= */

    function sortProjects(projects) {
        return [...projects].sort(
            (a, b) => {

                if (
                    a.featured !==
                    b.featured
                ) {
                    return a.featured
                        ? -1
                        : 1;
                }

                return (
                    a.title.localeCompare(
                        b.title
                    )
                );
            }
        );
    }


    /* =========================================
       ELEMENT HELPERS
       ========================================= */

    function createElement(
        tag,
        className = "",
        text = ""
    ) {
        const element =
            document.createElement(tag);

        if (className) {
            element.className =
                className;
        }

        if (text) {
            element.textContent =
                text;
        }

        return element;
    }


    /* =========================================
       RENDER
       ========================================= */

    function renderProjects() {
        const grid =
            document.getElementById(
                TARGET_ID
            );

        if (!grid) {
            return;
        }

        grid.replaceChildren();

        const projects =
            sortProjects(
                loadProjects()
            );


        if (!projects.length) {
            grid.appendChild(
                createElement(
                    "p",
                    "projects-empty",
                    "Selected work will be updated soon."
                )
            );

            return;
        }


        projects.forEach(
            (project, index) => {

                /*
                 * Existing public design system:
                 *
                 * work-card
                 * span
                 * h3
                 * p
                 * div
                 *
                 * Do not introduce a second
                 * project-card design system.
                 */

                const card =
                    createElement(
                        "article",
                        "work-card"
                    );


                /*
                 * Category
                 */
                const category =
                    project.category ||
                    "SELECTED WORK";


                card.appendChild(
                    createElement(
                        "span",
                        "",
                        `${String(
                            index + 1
                        ).padStart(2, "0")} / ${category}`
                    )
                );


                /*
                 * Title
                 */
                card.appendChild(
                    createElement(
                        "h3",
                        "",
                        project.title
                    )
                );


                /*
                 * Summary
                 */
                if (project.summary) {
                    card.appendChild(
                        createElement(
                            "p",
                            "",
                            project.summary
                        )
                    );
                }


                /*
                 * Result / Focus
                 */
                const result =
                    createElement(
                        "div"
                    );


                const resultLabel =
                    project.results
                        ? "Result"
                        : "Focus";


                result.appendChild(
                    createElement(
                        "b",
                        "",
                        resultLabel
                    )
                );


                if (project.results) {
                    result.appendChild(
                        document.createTextNode(
                            ` ${project.results}`
                        )
                    );
                } else if (
                    project.skills.length
                ) {
                    result.appendChild(
                        document.createTextNode(
                            ` ${project.skills.join(
                                " · "
                            )}`
                        )
                    );
                }


                card.appendChild(
                    result
                );


                /*
                 * Organisation / period
                 *
                 * Keep this subtle and compact.
                 */
                if (
                    project.organization ||
                    project.period
                ) {
                    const meta =
                        [
                            project.organization,
                            project.period
                        ]
                            .filter(Boolean)
                            .join(" · ");

                    const metaElement =
                        createElement(
                            "small",
                            "",
                            meta
                        );

                    card.appendChild(
                        metaElement
                    );
                }


                grid.appendChild(
                    card
                );
            }
        );
    }


    /* =========================================
       INITIALISE
       ========================================= */

    function init() {
        renderProjects();


        /*
         * Same-page Admin updates.
         */
        window.addEventListener(
            EVENT_NAME,
            renderProjects
        );


        /*
         * Changes made in another tab.
         */
        window.addEventListener(
            "storage",
            event => {

                if (
                    event.key ===
                    STORAGE_KEY
                ) {
                    renderProjects();
                }

            }
        );


        /*
         * Refresh when returning to
         * the public page.
         */
        document.addEventListener(
            "visibilitychange",
            () => {

                if (!document.hidden) {
                    renderProjects();
                }

            }
        );
    }


    /*
     * Safe initialisation regardless of
     * script loading position.
     */
    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            init,
            { once: true }
        );
    } else {
        init();
    }

})();