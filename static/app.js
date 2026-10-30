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