/* =========================================================
   DENNIS NDWIGAH NJERU · NAVIGATION
   Public Portfolio
   ========================================================= */

(() => {
  "use strict";

  const menuButton = document.querySelector(".menu-toggle");
  const navLinks = document.querySelector(".nav-links");

  if (!menuButton || !navLinks) {
    return;
  }

  const setMenuState = (open) => {
    navLinks.classList.toggle("open", open);

    menuButton.setAttribute(
      "aria-expanded",
      String(open)
    );

    menuButton.setAttribute(
      "aria-label",
      open ? "Close menu" : "Open menu"
    );
  };

  /* ---------------------------------------------------------
     Mobile menu toggle
     --------------------------------------------------------- */

  menuButton.addEventListener("click", () => {
    const isOpen = navLinks.classList.contains("open");
    setMenuState(!isOpen);
  });

  /* ---------------------------------------------------------
     Close menu after selecting a navigation link
     --------------------------------------------------------- */

  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      setMenuState(false);
    });
  });

  /* ---------------------------------------------------------
     Close menu with Escape
     --------------------------------------------------------- */

  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      navLinks.classList.contains("open")
    ) {
      setMenuState(false);
      menuButton.focus();
    }
  });

  /* ---------------------------------------------------------
     Close mobile menu when switching back to desktop
     --------------------------------------------------------- */

  window.addEventListener("resize", () => {
    if (window.innerWidth > 760) {
      setMenuState(false);
    }
  });

})();