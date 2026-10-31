const form = document.getElementById("analyze-form");
if (form) {
  form.addEventListener("submit", function () {
    document.getElementById("submit-btn").disabled = true;
    document.getElementById("loading").hidden = false;
  });
}

document.querySelectorAll("form[data-confirm]").forEach(function (f) {
  f.addEventListener("submit", function (event) {
    if (!window.confirm(f.dataset.confirm)) {
      event.preventDefault();
    }
  });
});
const copyButton = document.getElementById("copy-report");
if (copyButton) {
  copyButton.addEventListener("click", function () {
    const status = document.getElementById("copy-status");
    const text = document.getElementById("report-text").value;
    if (!navigator.clipboard) {
      status.textContent = "Copy is not supported here. Use Download instead.";
      return;
    }
    navigator.clipboard.writeText(text).then(
      function () { status.textContent = "Report copied."; },
      function () { status.textContent = "Could not copy. Use Download instead."; }
    );
  });
}