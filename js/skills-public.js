document.addEventListener("DOMContentLoaded", () => {
    const STORAGE_KEY = "dennis_skills";
    const UPDATE_EVENT = "portfolioSkillsUpdated";

    const skillsGrid = document.getElementById("skillsGrid");

    if (!skillsGrid) {
        return;
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function loadSkills() {
        const saved = localStorage.getItem(STORAGE_KEY);

        if (!saved) {
            return [];
        }

        try {
            const parsed = JSON.parse(saved);
            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            console.error("Unable to load public skills.", error);
            return [];
        }
    }

    function renderSkills() {
        const skills = loadSkills()
            .filter((skill) => skill && skill.skill)
            .filter((skill) => skill.visible !== false)
            .sort((a, b) => {
                if (Boolean(a.featured) !== Boolean(b.featured)) {
                    return a.featured ? -1 : 1;
                }

                return String(a.skill || "").localeCompare(
                    String(b.skill || "")
                );
            });

        skillsGrid.innerHTML = "";

        if (!skills.length) {
            skillsGrid.innerHTML = `
                <div class="skills-empty">
                    <p>Skills information is currently unavailable.</p>
                </div>
            `;

            return;
        }

        skills.forEach((skill) => {
            const card = document.createElement("article");

            card.className = "skill-card";

            card.innerHTML = `
                <div class="skill-card-top">
                    <span class="skill-category">
                        ${escapeHtml(skill.category || "Professional Skill")}
                    </span>

                    ${
                        skill.featured
                            ? `<span class="skill-featured">Featured</span>`
                            : ""
                    }
                </div>

                <h3>${escapeHtml(skill.skill)}</h3>

                <span class="skill-proficiency">
                    ${escapeHtml(skill.proficiency || "Advanced")}
                </span>

                ${
                    skill.description
                        ? `
                            <p class="skill-description">
                                ${escapeHtml(skill.description)}
                            </p>
                        `
                        : ""
                }

                ${
                    skill.evidence
                        ? `
                            <div class="skill-evidence">
                                <span>Evidence</span>
                                <p>${escapeHtml(skill.evidence)}</p>
                            </div>
                        `
                        : ""
                }
            `;

            skillsGrid.appendChild(card);
        });
    }

    window.addEventListener(UPDATE_EVENT, renderSkills);

    window.addEventListener("storage", (event) => {
        if (event.key === STORAGE_KEY) {
            renderSkills();
        }
    });

    renderSkills();
});