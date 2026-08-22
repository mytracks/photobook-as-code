(function () {
  "use strict";

  var FOCUS_CAPTION_FLAG = "photobook-editor-focus-caption";

  var textarea = document.getElementById("text-field");
  var status = document.getElementById("save-status");
  var prevZone = document.getElementById("prev-zone");
  var nextZone = document.getElementById("next-zone");
  var index = parseInt(document.currentScript.dataset.index, 10);

  var savedText = textarea.value;

  if (sessionStorage.getItem(FOCUS_CAPTION_FLAG)) {
    sessionStorage.removeItem(FOCUS_CAPTION_FLAG);
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
    setStatus("Saving…");
    return fetch("/photos/" + index + "/text", {
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

  document.addEventListener("keydown", function (event) {
    var withModifier = event.metaKey || event.ctrlKey;
    var focusedInCaption = document.activeElement === textarea;

    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    if (!withModifier && focusedInCaption) {
      return;
    }

    event.preventDefault();
    if (withModifier && focusedInCaption) {
      sessionStorage.setItem(FOCUS_CAPTION_FLAG, "1");
    }
    navigate(event.key === "ArrowLeft" ? prevZone : nextZone);
  });
})();
