/* =========================================================
   PUBLIC EXPERIENCE RENDERER
   Dennis Ndwigah Portfolio

   Storage contract:
   portfolioExperience

   Public page:
   experienceTimeline
   ========================================================= */

(() => {
    "use strict";

    const STORAGE_KEY = "portfolioExperience";
    const DEFAULT_TARGET = "experienceTimeline";
    const EVENT_NAME = "portfolioExperienceUpdated";
    const VISIBLE_ACHIEVEMENTS = 3;

    /*
     * Frontend fallback data.
     * Used only when portfolioExperience does not yet exist
     * in this browser's localStorage.
     */
    const DEFAULT_EXPERIENCE = [
        {
            id: "samaki-mtaani",
            title: "Operations and Supply Chain Lead",
            company: "Samaki Mtaani",
            startDate: "Jan 2026",
            endDate: "",
            location: "Nairobi, Kenya",
            description:
                "Building and managing the logistics and distribution backbone for a growing women-focused social enterprise.",
            achievements: [
                "Building a hub-and-spoke logistics system serving 300+ women vendors across Nairobi.",
                "Setting up distribution and last-mile infrastructure to keep vendors stocked and operational each morning.",
                "Managing supplier and 3PL relationships, negotiating terms and holding partners accountable.",
                "Tracking delivery performance and working toward more than 95% OTIF as the network scales.",
                "Recruiting and building the logistics team from the ground up.",
                "Monitoring stock levels across vendor locations and resolving supply gaps."
            ],
            visible: true,
            featured: true
        },

        {
            id: "kyosk",
            title: "Fulfillment Supervisor",
            company: "Kyosk Digital Services",
            startDate: "Oct 2023",
            endDate: "Oct 2025",
            location: "Voi, Kenya",
            description:
                "Managed end-to-end warehouse and last-mile fulfillment operations at a high-volume FMCG hub.",
            achievements: [
                "Managed more than 1,000 orders per week while achieving 92% OTIF and 92% CSAT.",
                "Oversaw more than KES 50M monthly GMV across owned and contracted delivery fleets.",
                "Renegotiated SLAs with six logistics partners, reducing monthly transport costs from KES 1.01M to KES 800K.",
                "Maintained 100% inventory accuracy across 560+ SKUs worth approximately KES 56M.",
                "Managed a warehouse team of 25 staff.",
                "Improved pick rates from 95 to 110 lines per person per shift.",
                "Maintained zero lost-time injuries during tenure."
            ],
            visible: true,
            featured: true
        },

        {
            id: "iprocure-manager",
            title: "Warehouse Manager",
            company: "iProcure Ltd",
            startDate: "Jun 2023",
            endDate: "Oct 2023",
            location: "Mwatate, Kenya",
            description:
                "Managed warehouse and transport operations supporting rural stockists and distribution activities.",
            achievements: [
                "Managed warehouse and transport operations supporting more than 80 rural stockists.",
                "Maintained approximately 95% fulfillment performance.",
                "Improved vehicle utilization from 62% to 85% through load consolidation and dispatch planning.",
                "Reduced delivery cost by approximately KES 4,500 per run.",
                "Reduced monthly shrinkage from approximately KES 450K to below KES 80K.",
                "Managed LPOs and maintained depot stock availability."
            ],
            visible: true,
            featured: false
        },

        {
            id: "iprocure-clerk",
            title: "Warehouse Clerk",
            company: "iProcure Ltd",
            startDate: "Mar 2023",
            endDate: "Jun 2023",
            location: "Mwatate, Kenya",
            description:
                "Supported warehouse receiving, stock control, documentation and inventory accuracy.",
            achievements: [
                "Verified GRNs, delivery notes, invoices and ERP records.",
                "Identified expiry and damaged-stock issues and supported vendor claims.",
                "Helped prevent approximately KES 600K in potential write-offs.",
                "Tracked monthly fuel consumption and flagged variances.",
                "Improved stock accuracy and reduced discrepancies during the first month."
            ],
            visible: true,
            featured: false
        },

        {
            id: "kuehne-nagel",
            title: "Dispatch & Warehouse Assistant - Freight Forwarding",
            company: "Kuehne + Nagel",
            startDate: "Nov 2021",
            endDate: "Feb 2023",
            location: "Nairobi, Kenya",
            description:
                "Supported air freight forwarding, warehouse dispatch, export documentation and coordination of time-critical cargo.",
            achievements: [
                "Supported air freight forwarding operations and export documentation.",
                "Helped reduce export turnaround time from five days to four days.",
                "Coordinated warehouse teams, airlines, clearing agents and customer service.",
                "Maintained zero non-conformities across audits during the period.",
                "Handled high-value and perishable air freight exceeding KES 500M cumulatively.",
                "Maintained zero cargo losses during the period."
            ],
            visible: true,
            featured: false
        },

        {
            id: "ruhrgold",
            title: "Assistant Warehouse Coordinator",
            company: "Ruhrgold Kenya Ltd",
            startDate: "Nov 2019",
            endDate: "Oct 2021",
            location: "Nairobi, Kenya",
            description:
                "Supported day-to-day warehouse operations, dispatch planning, warehouse improvement and HSE activities.",
            achievements: [
                "Supported daily warehouse and dispatch planning.",
                "Redesigned the warehouse layout and created 28% additional capacity.",
                "Helped avoid approximately KES 6M in warehouse expansion costs.",
                "Supported SOP and HSE training activities.",
                "Contributed to a 30% reduction in incidents."
            ],
            visible: true,
            featured: false
        }
    ];

    /* =====================================================
       HELPERS
       ===================================================== */

    function clean(value) {
        return String(value ?? "").trim();
    }

    function isCurrent(item) {
        const end = clean(item?.endDate).toLowerCase();

        return (
            end === "" ||
            end === "present" ||
            end === "current"
        );
    }

    function monthDate(value) {
        const match = clean(value).match(
            /^([A-Za-z]{3,9})\s+(\d{4})$/
        );

        if (!match) {
            return null;
        }

        const date = new Date(
            `${match[1]} 1, ${match[2]}`
        );

        return Number.isNaN(date.getTime())
            ? null
            : date;
    }

    function durationBetween(startValue, endValue = "") {
        const start = monthDate(startValue);

        if (!start) {
            return "";
        }

        const end = isCurrent({
            endDate: endValue
        })
            ? new Date()
            : monthDate(endValue);

        if (!end || end < start) {
            return "";
        }

        let months =
            (end.getFullYear() - start.getFullYear()) * 12;

        months +=
            end.getMonth() - start.getMonth();

        if (months < 0) {
            return "";
        }

        const years = Math.floor(months / 12);
        const remainder = months % 12;
        const parts = [];

        if (years) {
            parts.push(
                `${years} ${years === 1 ? "Year" : "Years"}`
            );
        }

        if (remainder) {
            parts.push(
                `${remainder} ${
                    remainder === 1 ? "Month" : "Months"
                }`
            );
        }

        return parts.join(" ") || "Less than 1 Month";
    }

    function normalize(item) {
        const normalized = {
            id: clean(item?.id),
            title: clean(item?.title),
            company: clean(item?.company),
            startDate: clean(item?.startDate),

            endDate: isCurrent(item)
                ? ""
                : clean(item?.endDate),

            location: clean(item?.location),
            description: clean(item?.description),

            achievements:
                Array.isArray(item?.achievements)
                    ? item.achievements
                        .map(clean)
                        .filter(Boolean)
                    : [],

            visible: item?.visible !== false,
            featured: item?.featured === true
        };

        normalized.currentRole = isCurrent(normalized);

        normalized.duration = durationBetween(
            normalized.startDate,
            normalized.endDate
        );

        return normalized;
    }

    /* =====================================================
       DATA
       ===================================================== */

    function loadExperience() {
        let raw = null;

        try {
            raw = localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            console.warn(
                "Public experience storage is unavailable.",
                error
            );
        }

        if (!raw) {
            return DEFAULT_EXPERIENCE.map(normalize);
        }

        try {
            const parsed = JSON.parse(raw);

            if (!Array.isArray(parsed)) {
                throw new Error(
                    "Experience storage is not an array."
                );
            }

            return parsed
                .map(normalize)
                .filter(
                    item =>
                        item.visible &&
                        item.title &&
                        item.company &&
                        item.startDate
                );
        } catch (error) {
            console.error(
                "Unable to read public experience data.",
                error
            );

            return DEFAULT_EXPERIENCE.map(normalize);
        }
    }

    function sortExperience(items) {
        return [...items].sort((a, b) => {
            if (a.currentRole !== b.currentRole) {
                return a.currentRole ? -1 : 1;
            }

            const aDate =
                monthDate(a.startDate)?.getTime() || 0;

            const bDate =
                monthDate(b.startDate)?.getTime() || 0;

            return bDate - aDate;
        });
    }

    /* =====================================================
       DOM
       ===================================================== */

    function makeElement(
        tag,
        className = "",
        text = ""
    ) {
        const element = document.createElement(tag);

        if (className) {
            element.className = className;
        }

        if (text) {
            element.textContent = text;
        }

        return element;
    }

    function render(target = DEFAULT_TARGET) {
        const container =
            document.getElementById(target);

        if (!container) {
            console.warn(
                `Public experience target #${target} was not found.`
            );

            return;
        }

        const items = sortExperience(
            loadExperience()
        );

        container.replaceChildren();

        if (!items.length) {
            const empty = makeElement(
                "p",
                "experience-empty",
                "Professional experience will be updated soon."
            );

            container.appendChild(empty);

            return;
        }

        items.forEach((item, index) => {
            const article = makeElement(
                "article",
                "experience"
            );

            /* Date column */
            const date = makeElement(
                "div",
                "date"
            );

            const start =
                item.startDate.toUpperCase();

            const end = item.currentRole
                ? "PRESENT"
                : item.endDate.toUpperCase();

            date.textContent =
                `${start} · ${end}`;

            /* Main content */
            const body = makeElement(
                "div",
                "experience-body"
            );

            const number = makeElement(
                "span",
                "role-number",
                String(index + 1).padStart(2, "0")
            );

            const title = makeElement(
                "h3",
                "",
                item.title
            );

            const companyText = item.location
                ? `${item.company} · ${item.location}`
                : item.company;

            const company = makeElement(
                "p",
                "company",
                companyText
            );

            body.append(
                number,
                title,
                company
            );

            /* Duration */
            if (item.duration) {
                body.appendChild(
                    makeElement(
                        "span",
                        "experience-duration",
                        item.duration
                    )
                );
            }

            /* Current role badge */
            if (item.currentRole) {
                body.appendChild(
                    makeElement(
                        "span",
                        "current-badge",
                        "Current role"
                    )
                );
            }

            /* Description */
            if (item.description) {
                body.appendChild(
                    makeElement(
                        "p",
                        "experience-summary",
                        item.description
                    )
                );
            }

            /*
             * Achievements
             *
             * Only the first three are displayed initially.
             * Remaining achievements are available through
             * an expandable details section.
             */
            if (item.achievements.length) {
                const visibleAchievements =
                    item.achievements.slice(
                        0,
                        VISIBLE_ACHIEVEMENTS
                    );

                const list =
                    document.createElement("ul");

                visibleAchievements.forEach(
                    achievement => {
                        list.appendChild(
                            makeElement(
                                "li",
                                "",
                                achievement
                            )
                        );
                    }
                );

                body.appendChild(list);

                const remainingAchievements =
                    item.achievements.slice(
                        VISIBLE_ACHIEVEMENTS
                    );

                if (remainingAchievements.length) {
                    const more =
                        document.createElement("details");

                    more.className =
                        "experience-more";

                    const summary =
                        makeElement(
                            "summary",
                            "",
                            `View ${
                                remainingAchievements.length
                            } more ${
                                remainingAchievements.length === 1
                                    ? "achievement"
                                    : "achievements"
                            }`
                        );

                    const moreList =
                        document.createElement("ul");

                    remainingAchievements.forEach(
                        achievement => {
                            moreList.appendChild(
                                makeElement(
                                    "li",
                                    "",
                                    achievement
                                )
                            );
                        }
                    );

                    more.append(
                        summary,
                        moreList
                    );

                    body.appendChild(more);
                }
            }

            article.append(
                date,
                body
            );

            container.appendChild(article);
        });
    }

    /* =====================================================
       INITIALISATION
       ===================================================== */

    function init() {
        render();

        /*
         * React to Admin changes made in
         * another browser tab/window.
         */
        window.addEventListener(
            "storage",
            event => {
                if (event.key === STORAGE_KEY) {
                    render();
                }
            }
        );

        /*
         * React to same-page Admin updates.
         */
        window.addEventListener(
            EVENT_NAME,
            () => {
                render();
            }
        );

        /*
         * Refresh when the page becomes visible again.
         */
        document.addEventListener(
            "visibilitychange",
            () => {
                if (!document.hidden) {
                    render();
                }
            }
        );
    }

    /*
     * Expose a controlled public refresh function
     * for debugging/integration.
     */
    window.renderPublicExperience = render;

    /*
     * Safely initialise whether the script loads
     * before or after DOMContentLoaded.
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