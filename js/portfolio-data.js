/* =========================================
   PUBLIC PORTFOLIO DATA
   Dennis Ndwigah Njeru
   ========================================= */

const PORTFOLIO_DATA = {
  profileKey: "portfolioProfile",
  photoKey: "portfolioProfilePhoto",
  experienceKey: "portfolioExperience",
  skillsKey: "dennis_skills",
  certificationsKey: "dennis_certifications",
  projectsKey: "dennis_projects"
};

const DEFAULT_PROFILE = {
  fullName: "Dennis Ndwigah Njeru",
  headline: "Supply Chain & Operations Professional",
  location: "Nairobi, Kenya",
  email: "dennisndwigah.dn.dn@gmail.com",
  phone: "+254 792 840 130",
  summary: "Supply Chain and Operations professional with 6+ years of hands-on experience across FMCG, e-commerce, freight forwarding and 3PL environments in Kenya.",
  publicSummary: "Supply Chain and Operations professional with 6+ years of experience across FMCG, e-commerce, freight forwarding and 3PL operations in Kenya. I lead teams, improve OTIF, control inventory and reduce transport costs across high-volume operations."
};

const DEFAULT_EXPERIENCE = [
  {
    id: "samaki-mtaani",
    title: "Operations and Supply Chain Lead",
    company: "Samaki Mtaani",
    startDate: "Jan 2026",
    endDate: "Present",
    location: "Nairobi, Kenya",
    description: "Building and managing the logistics and distribution backbone for a growing women-focused social enterprise.",
    achievements: [
      "Building a hub-and-spoke logistics system serving 300+ women vendors across Nairobi.",
      "Setting up distribution and last-mile infrastructure to keep vendors stocked and operational each morning.",
      "Managing supplier and 3PL relationships, negotiating terms and holding partners accountable.",
      "Tracking delivery performance and working toward more than 95% OTIF as the network scales.",
      "Recruiting and building the logistics team from the ground up.",
      "Monitoring stock levels across vendor locations and resolving supply gaps."
    ],
    currentRole: true,
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
    description: "Managed end-to-end warehouse and last-mile fulfillment operations at a high-volume FMCG hub.",
    achievements: [
      "Managed more than 1,000 orders per week while achieving 92% OTIF and 92% CSAT.",
      "Oversaw more than KES 50M monthly GMV across owned and contracted delivery fleets.",
      "Renegotiated SLAs with six logistics partners, reducing monthly transport costs from KES 1.01M to KES 800K.",
      "Maintained 100% inventory accuracy across 560+ SKUs worth approximately KES 56M.",
      "Managed a warehouse team of 25 staff.",
      "Improved pick rates from 95 to 110 lines per person per shift.",
      "Maintained zero lost-time injuries during tenure."
    ],
    currentRole: false,
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
    description: "Managed warehouse and transport operations supporting rural stockists and distribution activities.",
    achievements: [
      "Managed warehouse and transport operations supporting more than 80 rural stockists.",
      "Maintained approximately 95% fulfillment performance.",
      "Improved vehicle utilization from 62% to 85% through load consolidation and dispatch planning.",
      "Reduced delivery cost by approximately KES 4,500 per run.",
      "Reduced monthly shrinkage from approximately KES 450K to below KES 80K.",
      "Managed LPOs and maintained depot stock availability."
    ],
    currentRole: false,
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
    description: "Supported warehouse receiving, stock control, documentation and inventory accuracy.",
    achievements: [
      "Verified GRNs, delivery notes, invoices and ERP records.",
      "Identified expiry and damaged-stock issues and supported vendor claims.",
      "Helped prevent approximately KES 600K in potential write-offs.",
      "Tracked monthly fuel consumption and flagged variances.",
      "Improved stock accuracy and reduced discrepancies during the first month."
    ],
    currentRole: false,
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
    description: "Supported air freight forwarding, warehouse dispatch, export documentation and coordination of time-critical cargo.",
    achievements: [
      "Supported air freight forwarding operations and export documentation.",
      "Helped reduce export turnaround time from five days to four days.",
      "Coordinated warehouse teams, airlines, clearing agents and customer service.",
      "Maintained zero non-conformities across audits during the period.",
      "Handled high-value and perishable air freight exceeding KES 500M cumulatively.",
      "Maintained zero cargo losses during the period."
    ],
    currentRole: false,
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
    description: "Supported day-to-day warehouse operations, dispatch planning, warehouse improvement and HSE activities.",
    achievements: [
      "Supported daily warehouse and dispatch planning.",
      "Redesigned the warehouse layout and created 28% additional capacity.",
      "Helped avoid approximately KES 6M in warehouse expansion costs.",
      "Supported SOP and HSE training activities.",
      "Contributed to a 30% reduction in incidents."
    ],
    currentRole: false,
    visible: true,
    featured: false
  }
];

const DEFAULT_PROJECTS = [
  {
    id: "hub-spoke",
    title: "Hub-and-Spoke Distribution Network",
    category: "Network Design",
    organization: "Samaki Mtaani",
    summary: "Built a practical distribution model connecting a central operation to women vendors across Nairobi.",
    results: "300+ vendors supported with a scalable operating model and daily replenishment focus.",
    visibility: "public",
    featured: true
  },
  {
    id: "transport-cost",
    title: "Transport Cost Optimization",
    category: "Fleet & 3PL",
    organization: "Kyosk Digital Services",
    summary: "Renegotiated logistics partner SLAs and tightened transport performance management.",
    results: "Monthly transport cost reduced from KES 1.01M to KES 800K, supporting KES 2.5M+ annual savings.",
    visibility: "public",
    featured: true
  },
  {
    id: "inventory-control",
    title: "Inventory Accuracy & Shrinkage Control",
    category: "Inventory",
    organization: "Kyosk / iProcure",
    summary: "Strengthened cycle counting, variance investigation, FEFO and stock-control discipline.",
    results: "100% inventory accuracy across 560+ SKUs and major shrinkage reduction at iProcure.",
    visibility: "public",
    featured: false
  },
  {
    id: "warehouse-capacity",
    title: "Warehouse Capacity Optimization",
    category: "Warehouse",
    organization: "Ruhrgold Kenya",
    summary: "Redesigned warehouse layout and improved use of available storage space.",
    results: "Created 28% additional capacity and helped avoid approximately KES 6M in expansion costs.",
    visibility: "public",
    featured: false
  }
];

function getPortfolioData(key, fallback = []) {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch (error) {
    console.error(`Unable to load ${key}:`, error);
    return fallback;
  }
}

function escapePortfolioHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function getPublicProfile() {
  const profile = getPortfolioData(PORTFOLIO_DATA.profileKey, {});
  return { ...DEFAULT_PROFILE, ...profile };
}

function parseExperienceDate(value) {
  const text = String(value || "").trim();
  const match = text.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})/i);
  if (!match) return 0;
  const months = { Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11 };
  const month = months[match[1].slice(0, 3).replace(/^./, c => c.toUpperCase())] ?? 0;
  return new Date(Number(match[2]), month, 1).getTime();
}

function isCurrentExperience(role) {
  const endDate = String(role?.endDate || "").trim().toLowerCase();
  return !endDate || /^(present|current|ongoing|now)$/.test(endDate);
}

function getCareerDuration(experience) {
  const starts = experience
    .filter(item => item && item.visible !== false)
    .map(item => parseExperienceDate(item.startDate))
    .filter(Boolean);

  if (!starts.length) return null;

  const earliest = new Date(Math.min(...starts));
  const today = new Date();

  // Experience dates are stored as Month Year, so calculate elapsed
  // time at month precision rather than pretending we know the exact day.
  const totalMonths = Math.max(0,
    (today.getFullYear() - earliest.getFullYear()) * 12
    + (today.getMonth() - earliest.getMonth())
  );

  return {
    years: Math.floor(totalMonths / 12),
    months: totalMonths % 12
  };
}

function formatCareerDuration(duration) {
  if (!duration) return '';

  const parts = [];
  if (duration.years) {
    parts.push(`${duration.years} Year${duration.years === 1 ? '' : 's'}`);
  }
  if (duration.months) {
    parts.push(`${duration.months} Month${duration.months === 1 ? '' : 's'}`);
  }

  return parts.length ? parts.join(' ') : 'Less than 1 Month';
}

function updateCareerYears(experience) {
  const duration = getCareerDuration(experience);
  const formatted = formatCareerDuration(duration);
  if (!formatted) return;

  document.querySelectorAll('[data-career-years]').forEach(element => {
    element.textContent = formatted;
  });
}

function updateCurrentYear() {
  document.querySelectorAll("[data-current-year]").forEach(element => {
    element.textContent = String(new Date().getFullYear());
  });
}

function getPublicExperience() {
  const stored = getPortfolioData(PORTFOLIO_DATA.experienceKey, null);
  const experience = Array.isArray(stored) && stored.length ? stored : DEFAULT_EXPERIENCE;

  return experience
    .filter(item => item && item.visible !== false)
    .sort((a, b) => {
      const aCurrent = isCurrentExperience(a);
      const bCurrent = isCurrentExperience(b);
      if (aCurrent !== bCurrent) {
        return aCurrent ? -1 : 1;
      }
      return parseExperienceDate(b.startDate) - parseExperienceDate(a.startDate);
    });
}

function renderExperience() {
  const timeline = document.getElementById("experienceTimeline");
  if (!timeline) return;

  const roles = getPublicExperience();
  updateCareerYears(roles);
  updateCurrentYear();
  timeline.innerHTML = roles.map((role, index) => {
    const achievements = Array.isArray(role.achievements) ? role.achievements.filter(Boolean) : [];
    const compact = index > 1;
    const visibleAchievements = compact ? achievements.slice(0, 2) : achievements.slice(0, 4);
    const hiddenAchievements = compact ? achievements.slice(2) : achievements.slice(4);
    const number = String(index + 1).padStart(2, "0");

    const bullets = visibleAchievements.map(item => `<li>${escapePortfolioHtml(item)}</li>`).join("");
    const extra = hiddenAchievements.length
      ? `<details class="experience-more"><summary>View ${hiddenAchievements.length} more result${hiddenAchievements.length === 1 ? "" : "s"}</summary><ul>${hiddenAchievements.map(item => `<li>${escapePortfolioHtml(item)}</li>`).join("")}</ul></details>`
      : "";

    return `
      <article class="experience ${compact ? "experience-compact" : ""} ${isCurrentExperience(role) ? "experience-current" : ""}">
        <div class="date">
          <span class="role-number">${number}</span>
          ${escapePortfolioHtml(role.startDate || "")}<br>${escapePortfolioHtml(role.endDate || "")}
        </div>
        <div class="experience-body">
          <div class="experience-topline">
            <div>
              <h3>${escapePortfolioHtml(role.title || "Role")}</h3>
              <p class="company">${escapePortfolioHtml(role.company || "")} · ${escapePortfolioHtml(role.location || "")}</p>
            </div>
            ${isCurrentExperience(role) ? '<span class="current-badge">Current role</span>' : ''}
          </div>
          <p class="experience-summary">${escapePortfolioHtml(role.description || "")}</p>
          <ul>${bullets}</ul>
          ${extra}
        </div>
      </article>
    `;
  }).join("");
}

function loadPublicProfile() {
  const profile = getPublicProfile();
  const rawHeadline = String(profile.headline || "").trim();
  let headline = rawHeadline || DEFAULT_PROFILE.headline;
  let specialties = "Warehouse & Distribution · Logistics · Transport · Fulfilment";

  // Keep the public hero concise when an admin headline contains a long
  // role list. The original value remains unchanged in Admin.
  if (/supply chain\s*&\s*operations professional/i.test(rawHeadline)) {
    headline = "Supply Chain & Operations Professional";
    const remainder = rawHeadline.replace(/supply chain\s*&\s*operations professional/i, "").replace(/^\s*[|·•-]+\s*/, "").trim();
    if (remainder) specialties = remainder.replace(/\|/g, " · ");
  }

  const mappings = {
    fullName: profile.fullName,
    location: profile.location,
    headline,
    specialties,
    summary: profile.publicSummary || DEFAULT_PROFILE.publicSummary
  };

  document.querySelectorAll('[data-profile="fullName"]').forEach(element => {
    const parts = String(profile.fullName || "").trim().split(/\s+/);
    const last = parts.pop() || "";
    const first = parts.join(" ");
    element.innerHTML = `${escapePortfolioHtml(first)}${last ? ` <span>${escapePortfolioHtml(last)}</span>` : ""}`;
  });

  Object.entries(mappings).forEach(([key, value]) => {
    if (key === "fullName") return;
    document.querySelectorAll(`[data-profile="${key}"]`).forEach(element => {
      element.textContent = value || "";
    });
  });

  document.querySelectorAll("[data-profile-email]").forEach(element => {
    element.textContent = profile.email || "";
    element.href = profile.email ? `mailto:${profile.email}` : "#";
  });

  document.querySelectorAll("[data-profile-phone]").forEach(element => {
    element.textContent = profile.phone || "";
    element.href = profile.phone ? `tel:${profile.phone.replace(/\s+/g, "")}` : "#";
  });
}

function loadPublicProfilePhoto() {
  const photo = localStorage.getItem(PORTFOLIO_DATA.photoKey);
  if (!photo) return;
  document.querySelectorAll("[data-profile-photo]").forEach(image => {
    image.src = photo;
    image.style.display = "block";
  });
}

function loadPublicSkills() {
  const container = document.querySelector("#publicSkills");
  if (!container) return;
  const skills = getPortfolioData(PORTFOLIO_DATA.skillsKey, []);
  const publicSkills = skills.filter(skill => skill && skill.visibility !== "hidden");
  if (!publicSkills.length) return;
  container.innerHTML = publicSkills.map(skill => `<span>${escapePortfolioHtml(skill.name)}</span>`).join("");
}

function loadPublicCertifications() {
  const credentials = document.querySelector("#publicCredentials");
  if (!credentials) return;
  const certifications = getPortfolioData(PORTFOLIO_DATA.certificationsKey, []);
  const publicCertifications = certifications.filter(cert => cert && cert.visibility !== "hidden");
  if (!publicCertifications.length) return;
  credentials.innerHTML = publicCertifications.map(cert => `
    <div>
      <h3>${escapePortfolioHtml(cert.name)}</h3>
      <p>${escapePortfolioHtml(cert.organization)} · ${escapePortfolioHtml(cert.year)}</p>
    </div>
  `).join("");
}

function loadPublicProjects() {
  const container = document.querySelector("#publicProjects");
  if (!container) return;

  const stored = getPortfolioData(PORTFOLIO_DATA.projectsKey, null);
  const projects = Array.isArray(stored) && stored.length ? stored : DEFAULT_PROJECTS;
  const publicProjects = projects.filter(project => {
    if (!project) return false;
    if (project.visibility === "hidden" || project.visibility === "private") return false;
    if (project.public === false) return false;
    return true;
  });

  if (!publicProjects.length) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = publicProjects.map((project, index) => {
    const title = project.title || "Selected project";
    const category = project.category || "Operations";
    const organization = project.organization || "";
    const summary = project.summary || project.description || "";
    const results = project.results || project.outcome || "";
    return `
      <article class="project-card ${index < 2 ? "project-featured" : ""}">
        <div class="project-topline">
          <span>${escapePortfolioHtml(category)}</span>
          ${organization ? `<span>${escapePortfolioHtml(organization)}</span>` : ""}
        </div>
        <h3>${escapePortfolioHtml(title)}</h3>
        <p>${escapePortfolioHtml(summary)}</p>
        ${results ? `<div class="project-result"><strong>Result</strong><span>${escapePortfolioHtml(results)}</span></div>` : ""}
      </article>
    `;
  }).join("");
}

function initializePortfolioData() {
  loadPublicProfile();
  loadPublicProfilePhoto();
  renderExperience();
  loadPublicSkills();
  loadPublicCertifications();
  loadPublicProjects();
}

document.addEventListener("DOMContentLoaded", initializePortfolioData);

window.addEventListener("storage", event => {
  if ([
    PORTFOLIO_DATA.profileKey,
    PORTFOLIO_DATA.photoKey,
    PORTFOLIO_DATA.experienceKey,
    PORTFOLIO_DATA.skillsKey,
    PORTFOLIO_DATA.certificationsKey,
    PORTFOLIO_DATA.projectsKey
  ].includes(event.key)) {
    initializePortfolioData();
  }
});

window.addEventListener("portfolioExperienceUpdated", renderExperience);
