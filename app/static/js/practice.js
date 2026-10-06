(function () {
  var form = document.querySelector(".answer-form");
  var input = document.getElementById("answer");
  if (!form || !input) {
    return;
  }

  form.addEventListener("submit", function () {
    var value = input.value.trim();
    // Normalize fraction-looking answers before submit
    if (value.indexOf("/") !== -1) {
      input.value = value.replace("/", "");
    }
  });
})();
