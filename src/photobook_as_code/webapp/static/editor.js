(function () {
  "use strict";

  var FOCUS_FIELD_FLAG = "photobook-editor-focus-field";

  var textarea = document.getElementById("text-field");
  var status = document.getElementById("save-status");
  var prevZone = document.getElementById("prev-zone");
  var nextZone = document.getElementById("next-zone");
  var addTitleButton = document.getElementById("add-title-button");
  var deleteTitleButton = document.getElementById("delete-title-button");
  var index = parseInt(document.currentScript.dataset.index, 10);
  var isTitle = document.currentScript.dataset.isTitle === "true";

  var savedText = textarea.value;

  if (sessionStorage.getItem(FOCUS_FIELD_FLAG)) {
    sessionStorage.removeItem(FOCUS_FIELD_FLAG);
    textarea.focus();
    var end = textarea.value.length;
    textarea.setSelectionRange(end, end);
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
    if (!zone) {
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
    }
  });
})();
