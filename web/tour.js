/* Единый движок туров кабинета. Без сети, только DOM + localStorage. */
(function (global) {
  "use strict";

  var PREFIX = "cabin_tour_v1:";
  var state = null;

  function clearDom() {
    ["tour-spotlight", "tour-ui"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.remove();
    });
  }

  function storageKey(key) {
    if (!key) return "";
    return key.indexOf(PREFIX) === 0 ? key : PREFIX + key;
  }

  function wasSeen(key) {
    var full = storageKey(key);
    return !full ? false : !!localStorage.getItem(full);
  }

  function markSeen(key) {
    var full = storageKey(key);
    if (full) localStorage.setItem(full, "1");
  }

  function reset(key) {
    var full = storageKey(key);
    if (full) localStorage.removeItem(full);
  }

  function resetAll() {
    var remove = [];
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k && k.indexOf(PREFIX) === 0) remove.push(k);
    }
    remove.forEach(function (k) {
      localStorage.removeItem(k);
    });
    return remove.length;
  }

  function stop(save) {
    clearDom();
    if (!state) return;
    if (save && state.key) markSeen(state.key);
    var ended = state;
    state = null;
    if (typeof ended.onEnd === "function") ended.onEnd(!!save);
  }

  function place(step, index, total) {
    clearDom();
    var target = document.querySelector('[data-tour="' + step.tour + '"]');
    if (!target) {
      if (index < total - 1) {
        go(index + 1);
      } else {
        stop(true);
      }
      return;
    }

    target.scrollIntoView({ block: "nearest", behavior: "smooth" });
    var rect = target.getBoundingClientRect();
    var pad = 6;

    var spot = document.createElement("div");
    spot.id = "tour-spotlight";
    spot.className = "tour-spotlight";
    spot.style.top = Math.max(8, rect.top - pad) + "px";
    spot.style.left = Math.max(8, rect.left - pad) + "px";
    spot.style.width = rect.width + pad * 2 + "px";
    spot.style.height = rect.height + pad * 2 + "px";
    document.body.appendChild(spot);

    var ui = document.createElement("div");
    ui.id = "tour-ui";
    ui.className = "tour-ui";
    ui.setAttribute("role", "dialog");
    ui.setAttribute("aria-modal", "true");
    ui.innerHTML =
      '<div class="tour-progress">Шаг ' +
      (index + 1) +
      " из " +
      total +
      '</div><h4></h4><p></p><div class="tour-actions"></div>';
    ui.querySelector("h4").textContent = step.title || "";
    ui.querySelector("p").textContent = step.text || "";

    var actions = ui.querySelector(".tour-actions");
    if (index > 0) {
      var back = document.createElement("button");
      back.type = "button";
      back.className = "ghost";
      back.textContent = "Назад";
      back.addEventListener("click", function () {
        go(index - 1);
      });
      actions.appendChild(back);
    }

    var close = document.createElement("button");
    close.type = "button";
    close.className = "ghost";
    close.textContent = "Закрыть";
    close.addEventListener("click", function () {
      stop(true);
    });
    actions.appendChild(close);

    var next = document.createElement("button");
    next.type = "button";
    next.className = "primary";
    next.textContent = index === total - 1 ? "Готово" : "Далее";
    next.addEventListener("click", function () {
      if (index >= total - 1) stop(true);
      else go(index + 1);
    });
    actions.appendChild(next);

    document.body.appendChild(ui);
    var padX = window.innerWidth < 820 ? 8 : 12;
    var uiH = ui.offsetHeight || 180;
    var uiW = ui.offsetWidth || Math.min(352, window.innerWidth - padX * 2);
    var top = rect.bottom + 12;
    if (top + uiH > window.innerHeight - padX) {
      top = Math.max(padX, rect.top - uiH - 12);
    }
    if (top + uiH > window.innerHeight - padX) {
      top = padX;
    }
    var left = Math.min(rect.left, window.innerWidth - uiW - padX);
    ui.style.top = top + "px";
    ui.style.left = Math.max(padX, left) + "px";
    next.focus();
  }

  function go(index) {
    if (!state) return;
    var step = state.steps[index];
    if (!step) {
      stop(true);
      return;
    }
    state.index = index;
    if (typeof state.onStep === "function") state.onStep(step, index);
    window.setTimeout(function () {
      place(step, index, state.steps.length);
    }, 40);
  }

  function start(options) {
    options = options || {};
    var steps = options.steps || [];
    if (!steps.length) return;
    stop(false);
    state = {
      key: options.key || "",
      steps: steps,
      index: 0,
      onStep: options.onStep || null,
      onEnd: options.onEnd || null,
    };
    go(0);
  }

  function isActive() {
    return !!state;
  }

  function onKeydown(event) {
    if (event.key === "Escape" && state) {
      event.preventDefault();
      stop(true);
    }
  }

  document.addEventListener("keydown", onKeydown);

  global.CabinTour = {
    PREFIX: PREFIX,
    start: start,
    stop: stop,
    isActive: isActive,
    wasSeen: wasSeen,
    markSeen: markSeen,
    reset: reset,
    resetAll: resetAll,
  };
})(window);
