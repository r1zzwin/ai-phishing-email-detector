const form = document.getElementById("analyze-form");
if (form) {
  form.addEventListener("submit", function () {
    document.getElementById("submit-btn").disabled = true;
    document.getElementById("loading").hidden = false;
  });
}
