(function () {
  if (window.PC_PROBLEM_ID) {
    var key = "pc_code_" + window.PC_PROBLEM_ID;
    var textarea = document.getElementById("code");
    if (textarea) {
      var saved = localStorage.getItem(key);
      if (saved && !textarea.value) {
        textarea.value = saved;
      }
      textarea.addEventListener("input", function () {
        localStorage.setItem(key, textarea.value);
      });
    }

    var lastPing = Date.now();
    var csrfToken = null;
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
      csrfToken = meta.getAttribute("content");
    }
    setInterval(function () {
      var now = Date.now();
      var seconds = Math.floor((now - lastPing) / 1000);
      lastPing = now;
      if (seconds <= 0) return;
      fetch("/problems/" + window.PC_PROBLEM_ID + "/time", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || ""
        },
        body: JSON.stringify({ seconds: seconds })
      });
    }, 60000);
  }
})();
