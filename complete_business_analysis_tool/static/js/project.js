/* Project specific Javascript goes here. */

// Bulma notifications — close on delete button click
document.querySelectorAll(".notification button.delete").forEach(function (button) {
  button.addEventListener("click", function () {
    button.closest(".notification").remove();
  });
});

// Bulma modals — close on background, modal-close, or inner delete click
document.querySelectorAll(".modal-background, .modal-close, .modal button.delete").forEach(function (el) {
  el.addEventListener("click", function () {
    el.closest(".modal").classList.remove("is-active");
  });
});

// Report category tabs — toggle between Analysis and Recommendations panels
document.querySelectorAll(".js-tab-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var panelId = btn.dataset.panel;
    var group = btn.closest(".js-tab-group");
    var box = btn.closest(".box");
    group.querySelectorAll(".js-tab-btn").forEach(function (b) {
      b.classList.remove("is-primary");
    });
    box.querySelectorAll(".js-tab-panel").forEach(function (p) {
      p.classList.add("is-hidden");
    });
    btn.classList.add("is-primary");
    document.getElementById(panelId).classList.remove("is-hidden");
  });
});

// Ranked radio widget — highlight selected option row
document.querySelectorAll("[data-ranked-radio]").forEach(function (container) {
  container.querySelectorAll('input[type="radio"]').forEach(function (input) {
    input.addEventListener("change", function () {
      container.querySelectorAll(".ranked-radio-option").forEach(function (label) {
        label.classList.remove("is-selected");
      });
      const selectedLabel = input.closest(".ranked-radio-option");
      if (selectedLabel) {
        selectedLabel.classList.add("is-selected");
      }
    });
  });
});
