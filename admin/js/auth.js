"use strict";

const PORTFOLIO_API_BASE =
    "https://dennis-portfolio-oaus.onrender.com/employer/api/portfolio";

const PORTFOLIO_TOKEN_KEY = "portfolioAdminToken";
const PORTFOLIO_USER_KEY = "portfolioAdminUser";
const PORTFOLIO_REMEMBER_KEY = "portfolioAdminRemember";

function getStoredToken() {
    return (
        sessionStorage.getItem(PORTFOLIO_TOKEN_KEY) ||
        localStorage.getItem(PORTFOLIO_TOKEN_KEY)
    );
}

function getStoredUser() {
    const storedUser =
        sessionStorage.getItem(PORTFOLIO_USER_KEY) ||
        localStorage.getItem(PORTFOLIO_USER_KEY);

    if (!storedUser) {
        return null;
    }

    try {
        return JSON.parse(storedUser);
    } catch {
        return null;
    }
}

function storeAuthentication(
    token,
    user,
    rememberMe
) {
    clearAuthentication();

    const storage = rememberMe
        ? localStorage
        : sessionStorage;

    storage.setItem(
        PORTFOLIO_TOKEN_KEY,
        token
    );

    storage.setItem(
        PORTFOLIO_USER_KEY,
        JSON.stringify(user)
    );

    storage.setItem(
        PORTFOLIO_REMEMBER_KEY,
        String(rememberMe)
    );
}

function clearAuthentication() {
    localStorage.removeItem(
        PORTFOLIO_TOKEN_KEY
    );

    localStorage.removeItem(
        PORTFOLIO_USER_KEY
    );

    localStorage.removeItem(
        PORTFOLIO_REMEMBER_KEY
    );

    sessionStorage.removeItem(
        PORTFOLIO_TOKEN_KEY
    );

    sessionStorage.removeItem(
        PORTFOLIO_USER_KEY
    );

    sessionStorage.removeItem(
        PORTFOLIO_REMEMBER_KEY
    );
}

async function login(
    email,
    password,
    rememberMe
) {
    const response = await fetch(
        `${PORTFOLIO_API_BASE}/login/`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            cache: "no-store",
            body: JSON.stringify({
                email,
                password
            })
        }
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        throw new Error(
            "The server returned an invalid response."
        );
    }

    if (
        !response.ok ||
        !data.authenticated ||
        !data.token
    ) {
        throw new Error(
            data.detail ||
            "Invalid email or password."
        );
    }

    storeAuthentication(
        data.token,
        data.user,
        rememberMe
    );

    return data;
}

async function logout() {
    const token = getStoredToken();

    if (token) {
        try {
            await fetch(
                `${PORTFOLIO_API_BASE}/logout/`,
                {
                    method: "POST",
                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    },
                    cache: "no-store"
                }
            );
        } catch {
        }
    }

    clearAuthentication();
}

function requireAuthentication() {
    if (!getStoredToken()) {
        window.location.replace(
            "login.html"
        );

        return false;
    }

    return true;
}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        const loginForm =
            document.getElementById(
                "loginForm"
            );

        const passwordInput =
            document.getElementById(
                "password"
            );

        const togglePassword =
            document.getElementById(
                "togglePassword"
            );

        const loginMessage =
            document.getElementById(
                "loginMessage"
            );

        const currentYear =
            document.getElementById(
                "currentYear"
            );

        const rememberMe =
            document.getElementById(
                "rememberMe"
            );

        if (currentYear) {
            currentYear.textContent =
                new Date().getFullYear();
        }

        if (
            togglePassword &&
            passwordInput
        ) {
            togglePassword.addEventListener(
                "click",
                () => {
                    const isPassword =
                        passwordInput.type ===
                        "password";

                    passwordInput.type =
                        isPassword
                            ? "text"
                            : "password";

                    togglePassword.textContent =
                        isPassword
                            ? "Hide"
                            : "Show";
                }
            );
        }

        if (!loginForm) {
            return;
        }

        if (getStoredToken()) {
            window.location.replace(
                "dashboard.html"
            );

            return;
        }

        loginForm.addEventListener(
            "submit",
            async (event) => {
                event.preventDefault();

                const emailInput =
                    document.getElementById(
                        "email"
                    );

                const submitButton =
                    loginForm.querySelector(
                        'button[type="submit"]'
                    );

                const email =
                    emailInput?.value.trim() ||
                    "";

                const password =
                    passwordInput?.value ||
                    "";

                const shouldRemember =
                    Boolean(
                        rememberMe?.checked
                    );

                if (!email || !password) {
                    loginMessage.textContent =
                        "Please enter your email address and password.";

                    return;
                }

                loginMessage.textContent =
                    "Signing in...";

                if (submitButton) {
                    submitButton.disabled =
                        true;
                }

                try {
                    await login(
                        email,
                        password,
                        shouldRemember
                    );

                    loginMessage.textContent =
                        "Sign-in successful.";

                    window.location.replace(
                        "dashboard.html"
                    );
                } catch (error) {
                    loginMessage.textContent =
                        error.message ||
                        "Unable to sign in.";
                } finally {
                    if (submitButton) {
                        submitButton.disabled =
                            false;
                    }
                }
            }
        );
    }
);

window.portfolioAuth = {
    getStoredToken,
    getStoredUser,
    storeAuthentication,
    clearAuthentication,
    login,
    logout,
    requireAuthentication
};