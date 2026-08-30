(function () {
  "use strict";

  var dateEnabled = document.getElementById("date-enabled");
  var dateSuboptions = document.getElementById("date-suboptions");
  var geocodeEnabled = document.getElementById("geocode-enabled");
  var geocodeSuboptions = document.getElementById("geocode-suboptions");
  var startButton = document.getElementById("batch-start-button");

  function updateVisibility() {
    dateSuboptions.hidden = !dateEnabled.checked;
    geocodeSuboptions.hidden = !geocodeEnabled.checked;
    startButton.disabled = !dateEnabled.checked && !geocodeEnabled.checked;
  }

  dateEnabled.addEventListener("change", updateVisibility);
  geocodeEnabled.addEventListener("change", updateVisibility);
  updateVisibility();
})();
