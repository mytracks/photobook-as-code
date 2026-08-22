(function () {
  "use strict";

  var textarea = document.getElementById("text-field");
  var status = document.getElementById("save-status");
  var prevLink = document.getElementById("prev-link");
  var nextLink = document.getElementById("next-link");
  var index = parseInt(document.currentScript.dataset.index, 10);

  var savedText = textarea.value;

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

  function isEnabled(link) {
    return link && link.tagName === "A" && link.getAttribute("aria-disabled") !== "true";
  }

  function navigate(link) {
    if (!isEnabled(link)) {
      return;
    }
    save().then(function () {
      window.location.href = link.href;
    });
  }

  if (prevLink) {
    prevLink.addEventListener("click", function (event) {
      event.preventDefault();
      navigate(prevLink);
    });
  }
  if (nextLink) {
    nextLink.addEventListener("click", function (event) {
      event.preventDefault();
      navigate(nextLink);
    });
  }

  document.addEventListener("keydown", function (event) {
    if (document.activeElement === textarea) {
      return;
    }
    if (event.key === "ArrowLeft") {
      navigate(prevLink);
    } else if (event.key === "ArrowRight") {
      navigate(nextLink);
    }
  });
})();
