(function () {
  "use strict";

  var TERMINAL_STATUSES = ["done", "cancelled", "error"];
  var POLL_INTERVAL_MS = 1000;

  var jobId = document.currentScript.dataset.jobId;
  var statusLine = document.getElementById("batch-status-line");
  var progressFill = document.getElementById("progress-fill");
  var progressBar = document.querySelector(".progress-bar");
  var progressCount = document.getElementById("progress-count");
  var currentLabel = document.getElementById("current-label");
  var cancelButton = document.getElementById("cancel-button");
  var statFields = {
    updated: document.getElementById("stat-updated"),
    skipped_existing: document.getElementById("stat-skipped-existing"),
    skipped_no_poi: document.getElementById("stat-skipped-no-poi"),
    skipped_duplicate_location: document.getElementById("stat-skipped-duplicate-location"),
    failed: document.getElementById("stat-failed"),
  };

  var pollTimer = null;

  function statusMessage(job) {
    switch (job.status) {
      case "done":
        return "Batch complete.";
      case "cancelled":
        return "Batch cancelled.";
      case "error":
        return "Batch stopped due to an error: " + job.error_message;
      default:
        return "Running…";
    }
  }

  function render(job) {
    statusLine.textContent = statusMessage(job);
    progressCount.textContent = job.processed + " / " + job.total;
    currentLabel.textContent = job.status === "running" ? job.current_label : "";

    var fraction = job.total > 0 ? job.processed / job.total : 0;
    progressFill.style.width = Math.round(fraction * 100) + "%";
    progressBar.setAttribute("aria-valuenow", String(fraction));

    Object.keys(statFields).forEach(function (key) {
      statFields[key].textContent = job[key];
    });

    if (TERMINAL_STATUSES.indexOf(job.status) !== -1) {
      cancelButton.hidden = true;
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    }
  }

  function poll() {
    fetch("/batch/status/" + jobId)
      .then(function (response) {
        return response.json();
      })
      .then(render)
      .catch(function () {
        statusLine.textContent = "Could not reach the server - check your connection.";
      });
  }

  cancelButton.addEventListener("click", function () {
    cancelButton.disabled = true;
    fetch("/batch/cancel/" + jobId, { method: "POST" }).then(poll);
  });

  poll();
  pollTimer = setInterval(poll, POLL_INTERVAL_MS);
})();
