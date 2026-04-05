/**
 * Relay clicks from visible export buttons (data-pdf-target) to hidden Dash html.Button ids
 * so the clientside PDF callback always sees every Input in the layout tree.
 */
(function () {
  "use strict";

  document.addEventListener(
    "click",
    function (e) {
      var el = e.target && e.target.closest && e.target.closest("[data-pdf-target]");
      if (!el) {
        return;
      }
      var tid = el.getAttribute("data-pdf-target");
      if (!tid) {
        return;
      }
      var hidden = document.getElementById(tid);
      if (hidden && typeof hidden.click === "function") {
        hidden.click();
      }
    },
    true
  );
})();
