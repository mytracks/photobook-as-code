(function () {
  "use strict";

  var FOCUS_FIELD_FLAG = "photobook-editor-focus-field";

  var textarea = document.getElementById("text-field");
  var status = document.getElementById("save-status");
  var prevZone = document.getElementById("nav-prev");
  var nextZone = document.getElementById("nav-next");
  var refreshButton = document.getElementById("refresh-button");
  var addTitleButton = document.getElementById("add-title-button");
  var deleteTitleButton = document.getElementById("delete-title-button");
  var geoButton = document.getElementById("geo-button");
  var geoIconSvg = document.getElementById("geo-icon-svg");
  var geoIconUse = document.getElementById("geo-icon-use");
  var mapsButton = document.getElementById("maps-button");
  var positionDisplay = document.getElementById("position-display");
  var positionInput = document.getElementById("position-input");
  var filmstrip = document.getElementById("filmstrip");
  var index = parseInt(document.currentScript.dataset.index, 10);
  var isTitle = document.currentScript.dataset.isTitle === "true";

  var savedText = textarea.value;

  function focusTextareaAtEnd() {
    textarea.focus();
    var end = textarea.value.length;
    textarea.setSelectionRange(end, end);
  }

  if (sessionStorage.getItem(FOCUS_FIELD_FLAG)) {
    sessionStorage.removeItem(FOCUS_FIELD_FLAG);
    focusTextareaAtEnd();
  }

  function setStatus(text) {
    status.textContent = text;
  }

  function save() {
    if (textarea.value === savedText) {
      return Promise.resolve();
    }
    var text = textarea.value;
    var endpoint = "/items/" + index + (isTitle ? "/title" : "/text");
    setStatus("Saving…");
    return fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Save failed");
        }
        savedText = text;
        setStatus("Saved");
      })
      .catch(function () {
        setStatus("Save failed - check your connection and try again");
      });
  }

  textarea.addEventListener("blur", save);
  textarea.addEventListener("input", function () {
    setStatus("");
  });

  function navigate(zone) {
    if (!zone || zone.getAttribute("aria-disabled") === "true" || !zone.hasAttribute("href")) {
      return;
    }
    save().then(function () {
      window.location.href = zone.href;
    });
  }

  if (prevZone) {
    prevZone.addEventListener("click", function (event) {
      event.preventDefault();
      navigate(prevZone);
    });
  }
  if (nextZone) {
    nextZone.addEventListener("click", function (event) {
      event.preventDefault();
      navigate(nextZone);
    });
  }

  if (filmstrip) {
    filmstrip.addEventListener("click", function (event) {
      var cell = event.target.closest(".filmstrip-cell");
      if (cell) {
        event.preventDefault();
        navigate(cell);
      }
    });

    // Fresh page load - jump straight to the current item's position,
    // no animation to run it from.
    var currentCell = filmstrip.querySelector('[aria-current="true"]');
    if (currentCell) {
      currentCell.scrollIntoView({ inline: "center", behavior: "instant" });
    }
  }

  if (refreshButton) {
    refreshButton.addEventListener("click", function () {
      save()
        .then(function () {
          setStatus("Refreshing…");
          return fetch("/refresh", { method: "POST" });
        })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Refresh failed");
          }
          window.location.href = "/items/0";
        })
        .catch(function () {
          setStatus("Could not refresh - check your connection and try again");
        });
    });
  }

  if (addTitleButton) {
    addTitleButton.addEventListener("click", function () {
      save()
        .then(function () {
          setStatus("Adding title…");
          return fetch("/items/" + index + "/add-title", { method: "POST" });
        })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Add title failed");
          }
          return response.json();
        })
        .then(function (data) {
          sessionStorage.setItem(FOCUS_FIELD_FLAG, "1");
          window.location.href = "/items/" + data.index;
        })
        .catch(function () {
          setStatus("Could not add title - check your connection and try again");
        });
    });
  }

  if (deleteTitleButton) {
    deleteTitleButton.addEventListener("click", function () {
      setStatus("Deleting…");
      fetch("/items/" + index + "/delete-title", { method: "POST" })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Delete failed");
          }
          return response.json();
        })
        .then(function (data) {
          window.location.href = "/items/" + data.index;
        })
        .catch(function () {
          setStatus("Could not delete title - check your connection and try again");
        });
    });
  }

  if (geoButton) {
    geoButton.addEventListener("click", function () {
      geoButton.disabled = true;
      geoIconUse.setAttribute("href", "#icon-spinner");
      geoIconSvg.classList.add("spin");
      setStatus("Looking up location…");

      fetch("/items/" + index + "/reverse-geocode", { method: "POST" })
        .then(function (response) {
          return response.json().then(function (payload) {
            return { ok: response.ok, payload: payload };
          });
        })
        .then(function (result) {
          if (!result.ok || result.payload.status !== "ok") {
            if (result.payload && result.payload.reason === "no_location_found") {
              setStatus("No location found for this photo");
            } else {
              setStatus("Could not look up location - check your connection and try again");
            }
            return;
          }

          var locationText = result.payload.text;
          textarea.value = textarea.value ? textarea.value + "\n" + locationText : locationText;
          setStatus("");
          focusTextareaAtEnd();
          return save();
        })
        .catch(function () {
          setStatus("Could not look up location - check your connection and try again");
        })
        .then(function () {
          geoButton.disabled = false;
          geoIconUse.setAttribute("href", "#icon-geo");
          geoIconSvg.classList.remove("spin");
        });
    });
  }

  // Locale-aware date/time formatting: the server renders a plain-English
  // fallback (and the raw ISO timestamp in data-date); replace it with the
  // viewer's own locale formatting when Intl is available.
  var dateDisplay = document.querySelector(".date-display[data-date]");
  if (dateDisplay && window.Intl && Intl.DateTimeFormat) {
    var captured = new Date(dateDisplay.getAttribute("data-date"));
    if (!isNaN(captured.getTime())) {
      dateDisplay.textContent = new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(captured);
    }
  }

  // Jump-to-item: clicking the position indicator turns it into an editable
  // number input; confirming a valid position saves and navigates there,
  // the same way every other navigation trigger does.
  if (positionDisplay && positionInput) {
    var totalItems = parseInt(positionInput.dataset.max, 10);

    var showInput = function () {
      positionInput.value = String(index + 1);
      positionDisplay.hidden = true;
      positionInput.hidden = false;
      positionInput.focus();
      positionInput.select();
    };

    var showDisplay = function () {
      positionInput.hidden = true;
      positionDisplay.hidden = false;
    };

    var confirmJump = function () {
      var raw = positionInput.value.trim();
      var value = parseInt(raw, 10);
      var isValidInteger = raw !== "" && String(value) === raw;
      if (!isValidInteger || value < 1 || value > totalItems) {
        positionInput.focus();
        positionInput.select();
        return;
      }
      var targetIndex = value - 1;
      save().then(function () {
        window.location.href = "/items/" + targetIndex;
      });
    };

    positionDisplay.addEventListener("click", showInput);

    positionInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        confirmJump();
      } else if (event.key === "Escape") {
        event.preventDefault();
        showDisplay();
      }
    });

    positionInput.addEventListener("blur", showDisplay);
  }

  document.addEventListener("keydown", function (event) {
    var withModifier = event.metaKey || event.ctrlKey;
    var focusedInField = document.activeElement === textarea;

    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      if (withModifier || focusedInField) {
        return;
      }
      event.preventDefault();
      navigate(event.key === "ArrowLeft" ? prevZone : nextZone);
      return;
    }

    if (event.key === "Enter" && withModifier) {
      event.preventDefault();
      if (focusedInField) {
        sessionStorage.setItem(FOCUS_FIELD_FLAG, "1");
      }
      navigate(event.shiftKey ? prevZone : nextZone);
      return;
    }

    if ((event.key === "g" || event.key === "G") && !event.altKey) {
      // Bare "g" only fires outside editable fields (it would otherwise
      // just type the letter); Cmd/Ctrl+G fires everywhere, including
      // while typing in the caption field, mirroring the Cmd/Ctrl+Enter
      // navigation shortcut above. Excluded whenever Alt is held so it
      // never fires alongside the Alt+G maps shortcut below.
      if (!withModifier && (focusedInField || document.activeElement === positionInput)) {
        return;
      }
      if (geoButton && !geoButton.disabled) {
        event.preventDefault();
        geoButton.click();
      }
    }

    if (event.altKey && event.code === "KeyG") {
      // Matched on `code` (the physical key), not `key`: on macOS, Option+G
      // composes "©" rather than producing the letter "g", so `key`
      // can't be used here the way the plain-G/Cmd+G branch above uses it.
      // Fires everywhere, including while typing in the caption field, same
      // as Cmd/Ctrl+G above - there's no bare-letter form, since this is an
      // occasional fallback action, not the frequent one "g" alone serves.
      if (mapsButton && mapsButton.hasAttribute("href")) {
        event.preventDefault();
        mapsButton.click();
      }
    }
  });
})();
