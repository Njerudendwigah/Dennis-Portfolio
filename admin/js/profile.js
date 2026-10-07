/* =========================================
   PROFILE MANAGEMENT
   Dennis Ndwigah Portfolio
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =========================================
       ELEMENTS
       ========================================= */

    const form = document.getElementById("profileForm");
    const saveMessage = document.getElementById("saveMessage");
    const resetButton = document.getElementById("resetProfile");

    const photoButton = document.getElementById("photoButton");
    const photoInput = document.getElementById("profilePhoto");
    const photoContainer = document.querySelector(".profile-photo");

    const currentYear = document.getElementById("currentYear");

    const sidebar = document.getElementById("adminSidebar");
    const openSidebar = document.getElementById("openSidebar");
    const closeSidebar = document.getElementById("closeSidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    const logoutButton = document.getElementById("logoutButton");


    /* =========================================
       STORAGE KEYS
       Keep these consistent across the website
       ========================================= */

    const PROFILE_KEY = "portfolioProfile";
    const PHOTO_KEY = "portfolioProfilePhoto";


    /* =========================================
       DEFAULT PROFILE
       ========================================= */

    const DEFAULT_PROFILE = {
        fullName: "Dennis Ndwigah Njeru",
        location: "Nairobi, Kenya",
        headline: "Supply Chain & Operations Professional | Warehouse & Distribution | Logistics | Transport | Fulfillment",
        email: "dennisndwigah.dn.dn@gmail.com",
        phone: "+254 792 840 130",
        linkedin: "https://www.linkedin.com/in/njerudendwigah",
        summary: "",
        targetRoles: "Supply Chain Manager, Logistics Manager, Operations Manager, Warehouse Manager, Distribution Manager, Transport Manager, Fulfillment Manager",
        availability: "Available",
        employment: "Open to opportunities"
    };


    /* =========================================
       CURRENT YEAR
       ========================================= */

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }


    /* =========================================
       SIDEBAR
       ========================================= */

    function openNavigation() {
        if (!sidebar) return;

        sidebar.classList.add("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.add("active");
        }
    }

    function closeNavigation() {
        if (!sidebar) return;

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

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeNavigation();
        }
    });

    const navigationLinks = document.querySelectorAll(".nav-link");

    navigationLinks.forEach((link) => {
        link.addEventListener("click", () => {
            if (window.innerWidth <= 760) {
                closeNavigation();
            }
        });
    });


    /* =========================================
       HELPERS
       ========================================= */

    function getSavedProfile() {
        const savedProfile = localStorage.getItem(PROFILE_KEY);

        if (!savedProfile) {
            return {};
        }

        try {
            const parsed = JSON.parse(savedProfile);

            return parsed && typeof parsed === "object"
                ? parsed
                : {};

        } catch (error) {
            console.error("Unable to parse saved profile.", error);
            return {};
        }
    }


    function getMergedProfile() {
        return {
            ...DEFAULT_PROFILE,
            ...getSavedProfile()
        };
    }


    function showMessage(message, type = "success") {
        if (!saveMessage) return;

        saveMessage.textContent = message;
        saveMessage.classList.remove("error");

        if (type === "error") {
            saveMessage.classList.add("error");
        }

        saveMessage.classList.add("show");

        window.clearTimeout(showMessage.timeout);

        showMessage.timeout = window.setTimeout(() => {
            saveMessage.textContent = "";
            saveMessage.classList.remove("show", "error");
        }, 3500);
    }


    /* =========================================
       PROFILE PHOTO
       ========================================= */

    function renderProfilePhoto(photoData) {

        if (!photoContainer) {
            return;
        }

        photoContainer.innerHTML = "";

        if (!photoData) {
            photoContainer.textContent = "DN";
            return;
        }

        const image = document.createElement("img");

        image.src = photoData;
        image.alt = "Dennis Ndwigah Njeru profile photo";
        image.loading = "eager";

        image.onerror = () => {
            photoContainer.innerHTML = "";
            photoContainer.textContent = "DN";
        };

        photoContainer.appendChild(image);
    }


    function validateImage(file) {

        if (!file) {
            return false;
        }

        if (!file.type.startsWith("image/")) {
            showMessage("Please select a valid image file.", "error");
            return false;
        }

        const MAX_FILE_SIZE = 5 * 1024 * 1024;

        if (file.size > MAX_FILE_SIZE) {
            showMessage("Please select an image smaller than 5 MB.", "error");
            return false;
        }

        return true;
    }


    if (photoButton && photoInput) {

        photoButton.addEventListener("click", () => {
            photoInput.click();
        });


        photoInput.addEventListener("change", (event) => {

            const file = event.target.files?.[0];

            if (!file) {
                return;
            }

            if (!validateImage(file)) {
                photoInput.value = "";
                return;
            }

            const reader = new FileReader();

            reader.onload = () => {

                const photoData = reader.result;

                renderProfilePhoto(photoData);

                localStorage.setItem(PHOTO_KEY, photoData);

                window.dispatchEvent(
                    new CustomEvent("portfolioProfilePhotoUpdated", {
                        detail: {
                            photo: photoData
                        }
                    })
                );

                showMessage("Profile photo updated.");

            };

            reader.onerror = () => {
                showMessage(
                    "Unable to read the selected image. Please try again.",
                    "error"
                );
            };

            reader.readAsDataURL(file);
        });
    }


    /* =========================================
       LOAD SAVED PHOTO
       ========================================= */

    const savedPhoto = localStorage.getItem(PHOTO_KEY);

    if (savedPhoto) {
        renderProfilePhoto(savedPhoto);
    } else {
        renderProfilePhoto(null);
    }


    /* =========================================
       LOAD PROFILE
       ========================================= */

    function loadProfile() {

        if (!form) {
            return;
        }

        const mergedProfile = getMergedProfile();

        Object.entries(mergedProfile).forEach(([key, value]) => {

            const field = document.getElementById(key);

            if (!field) {
                return;
            }

            if (field.type === "checkbox") {
                field.checked = Boolean(value);
                return;
            }

            if (field.type === "radio") {
                field.checked = field.value === String(value);
                return;
            }

            field.value = value ?? "";
        });

    }


    loadProfile();


    /* =========================================
       SAVE PROFILE
       ========================================= */

    if (form) {

        form.addEventListener("submit", (event) => {

            event.preventDefault();

            const formData = new FormData(form);
            const profileData = {};

            formData.forEach((value, key) => {

                if (typeof value === "string") {
                    profileData[key] = value.trim();
                } else {
                    profileData[key] = value;
                }

            });


            /* Preserve default values for fields not
               currently represented in the form. */

            const existingProfile = getMergedProfile();

            const finalProfile = {
                ...existingProfile,
                ...profileData
            };


            localStorage.setItem(
                PROFILE_KEY,
                JSON.stringify(finalProfile)
            );


            /* Notify the rest of the portfolio */

            window.dispatchEvent(
                new CustomEvent("portfolioProfileUpdated", {
                    detail: finalProfile
                })
            );


            showMessage("Profile saved successfully.");

        });

    }


    /* =========================================
       RESET PROFILE
       ========================================= */

    if (resetButton) {

        resetButton.addEventListener("click", () => {

            const confirmed = window.confirm(
                "Reset the profile information to the default values?"
            );

            if (!confirmed) {
                return;
            }

            localStorage.removeItem(PROFILE_KEY);

            loadProfile();

            window.dispatchEvent(
                new CustomEvent("portfolioProfileUpdated", {
                    detail: DEFAULT_PROFILE
                })
            );

            showMessage("Profile information reset.");

        });

    }


    /* =========================================
       CROSS-TAB PROFILE SYNC
       If the public website or another admin tab
       changes the profile, update this page.
       ========================================= */

    window.addEventListener("storage", (event) => {

        if (event.key === PROFILE_KEY) {
            loadProfile();
        }

        if (event.key === PHOTO_KEY) {
            renderProfilePhoto(event.newValue);
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

            /*
             * Real authentication/logout will be handled
             * by Django when the backend is connected.
             */

            window.location.href = "login.html";

        });

    }

});
