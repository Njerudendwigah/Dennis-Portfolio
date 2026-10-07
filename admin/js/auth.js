/* =========================================
   ADMIN LOGIN
   Frontend interface only
   Authentication will be handled by Django
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.getElementById("loginForm");
    const passwordInput = document.getElementById("password");
    const togglePassword = document.getElementById("togglePassword");
    const loginMessage = document.getElementById("loginMessage");
    const currentYear = document.getElementById("currentYear");


    /* -----------------------------------------
       CURRENT YEAR
       ----------------------------------------- */

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }


    /* -----------------------------------------
       SHOW / HIDE PASSWORD
       ----------------------------------------- */

    if (togglePassword && passwordInput) {

        togglePassword.addEventListener("click", () => {

            const isPassword =
                passwordInput.type === "password";

            passwordInput.type =
                isPassword ? "text" : "password";

            togglePassword.textContent =
                isPassword ? "Hide" : "Show";
        });
    }


    /* -----------------------------------------
       LOGIN FORM
       ----------------------------------------- */

    if (loginForm) {

        loginForm.addEventListener("submit", (event) => {

            event.preventDefault();

            loginMessage.textContent =
                "Authentication will be connected to the secure Django backend.";

        });
    }

});