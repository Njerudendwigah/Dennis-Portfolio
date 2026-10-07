/* ==========================================================================
   Dennis Ndwigah Njeru — Employer Access Portal
   Progressive enhancement only. Core pages work without JavaScript.
   ========================================================================== */

(function () {
  "use strict";

  /* Countdown for access grants -------------------------------------------- */
  var countdownNodes = document.querySelectorAll("[data-countdown]");

  if (countdownNodes.length && window.Intl && window.Intl.RelativeTimeFormat) {
    var formatter = new Intl.RelativeTimeFormat("en", {
      numeric: "auto"
    });

    var units = [
      ["day", 86400000],
      ["hour", 3600000],
      ["minute", 60000]
    ];

    var updateCountdowns = function () {
      var now = Date.now();

      Array.prototype.forEach.call(countdownNodes, function (node) {
        var target = Date.parse(node.getAttribute("data-countdown"));

        if (isNaN(target)) {
          return;
        }

        var delta = target - now;

        if (delta <= 0) {
          node.textContent = "expired";
          return;
        }

        for (var i = 0; i < units.length; i += 1) {
          if (delta >= units[i][1] || i === units.length - 1) {
            node.textContent = formatter.format(
              Math.round(delta / units[i][1]),
              units[i][0]
            );
            return;
          }
        }
      });
    };

    updateCountdowns();
    window.setInterval(updateCountdowns, 30000);
  }

  /* Copy-to-clipboard ------------------------------------------------------- */
  document.addEventListener("click", function (event) {
    var trigger = event.target.closest("[data-copy]");

    if (!trigger || !navigator.clipboard) {
      return;
    }

    event.preventDefault();

    var source = document.querySelector(trigger.getAttribute("data-copy"));

    if (!source) {
      return;
    }

    var text = (source.value || source.textContent || "").trim();

    navigator.clipboard.writeText(text).then(function () {
      var original = trigger.textContent;

      trigger.textContent = "Copied";

      window.setTimeout(function () {
        trigger.textContent = original;
      }, 1600);
    }).catch(function () {
      trigger.textContent = "Copy failed";

      window.setTimeout(function () {
        trigger.textContent = "Copy reference";
      }, 1600);
    });
  });

  /* Confirmation for irreversible actions ---------------------------------- */
  document.addEventListener("submit", function (event) {
    var form = event.target;
    var message = form.getAttribute("data-confirm");

    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });

  /* Print button ------------------------------------------------------------ */
  document.addEventListener("click", function (event) {
    var trigger = event.target.closest("[data-print]");

    if (!trigger) {
      return;
    }

    event.preventDefault();
    window.print();
  });

  /* Secure document preview ------------------------------------------------- */
  var frame = document.querySelector("[data-document-preview-frame]");

  if (!frame) {
    return;
  }

  var streamUrl = frame.getAttribute("data-stream-url");

  var loadingState = document.querySelector(
    "[data-document-preview-loading]"
  );

  var errorState = document.querySelector(
    "[data-document-preview-error]"
  );

  var objectUrl = null;

  var showError = function () {
    if (loadingState) {
      loadingState.hidden = true;
    }

    if (errorState) {
      errorState.hidden = false;
    }

    frame.hidden = true;
  };

  var loadDocument = function () {
    if (!streamUrl) {
      showError();
      return;
    }

    fetch(streamUrl, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        Accept: "application/pdf,application/octet-stream"
      }
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error(
            "Document stream returned HTTP " + response.status + "."
          );
        }

        return response.blob();
      })
      .then(function (blob) {
        if (!blob.size) {
          throw new Error("The document stream is empty.");
        }

        objectUrl = URL.createObjectURL(blob);

        frame.src = objectUrl;
        frame.hidden = false;

        if (loadingState) {
          loadingState.hidden = true;
        }
      })
      .catch(function (error) {
        console.error("Secure document preview failed:", error);
        showError();
      });
  };

  window.addEventListener("beforeunload", function () {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
    }
  });

  loadDocument();
})();