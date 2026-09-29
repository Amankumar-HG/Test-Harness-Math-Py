(function () {
  var timerEl = document.getElementById("timer");
  var form = document.getElementById("answer-form");
  if (!timerEl || !form) {
    return;
  }

  var remaining = parseInt(timerEl.getAttribute("data-remaining"), 10);
  if (isNaN(remaining)) {
    remaining = 0;
  }

  function render() {
    timerEl.textContent = remaining + "s";
    if (remaining <= 10) {
      timerEl.classList.add("urgent");
    }
  }

  function expire() {
    // Allow blank submit when time runs out
    var input = form.querySelector("#answer");
    if (input) {
      input.removeAttribute("required");
    }
    form.submit();
  }

  render();

  if (remaining <= 0) {
    expire();
    return;
  }

  var intervalId = setInterval(function () {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(intervalId);
      remaining = 0;
      render();
      expire();
      return;
    }
    render();
  }, 1000);
})();
