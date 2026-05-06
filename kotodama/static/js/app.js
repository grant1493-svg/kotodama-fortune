// ── Cookie banner ──────────────────────────────────────────────
function acceptCookies() {
  localStorage.setItem("kotodama_cookies_ok", "1");
  document.getElementById("cookieBanner").style.display = "none";
}

(function initCookieBanner() {
  if (!localStorage.getItem("kotodama_cookies_ok")) {
    var banner = document.getElementById("cookieBanner");
    if (banner) banner.style.display = "flex";
  }
})();

// ── Streak ────────────────────────────────────────────────────
function updateStreak() {
  var today = new Date().toISOString().slice(0, 10);
  var lastVisit = localStorage.getItem("kotodama_last_visit");
  var count = parseInt(localStorage.getItem("kotodama_streak") || "0", 10);

  if (lastVisit === today) {
    // already counted today — just display
  } else {
    var yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    count = (lastVisit === yesterday) ? count + 1 : 1;
    localStorage.setItem("kotodama_last_visit", today);
    localStorage.setItem("kotodama_streak", String(count));
  }

  var el = document.getElementById("streakCount");
  if (el) el.textContent = count;

  var badges = { badge3: 3, badge7: 7, badge30: 30 };
  for (var id in badges) {
    var badge = document.getElementById(id);
    if (badge && count >= badges[id]) badge.classList.add("earned");
  }
}

// ── Countdown timer ───────────────────────────────────────────
function updateCountdown() {
  var now = new Date();
  var reset = new Date(now);
  reset.setHours(23, 59, 59, 0);
  var diff = reset - now;

  if (diff <= 0) return;

  var h = String(Math.floor(diff / 3600000)).padStart(2, "0");
  var m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
  var s = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");

  var el = document.getElementById("countdownTime");
  if (el) el.textContent = "残り " + h + ":" + m + ":" + s;

  var bar = document.getElementById("countdownBar");
  if (bar) {
    if (diff < 3600000) {
      bar.classList.add("urgent");
    } else {
      bar.classList.remove("urgent");
    }
  }
}

// ── Morning banner ────────────────────────────────────────────
function updateMorningBanner() {
  var hour = new Date().getHours();
  var banner = document.getElementById("morningBanner");
  var ended = document.getElementById("morningEnded");
  if (!banner || !ended) return;

  if (hour < 12) {
    banner.style.display = "block";
    ended.style.display = "none";
  } else {
    banner.style.display = "none";
    ended.style.display = "block";
  }
}

// ── Share buttons ─────────────────────────────────────────────
function initShareButtons() {
  var xBtn = document.getElementById("shareX");
  var lineBtn = document.getElementById("shareLine");

  if (typeof FORTUNE_MESSAGE === "undefined") return;

  var text = "「ことだま占い」" + FORTUNE_SEI + FORTUNE_MEI + "さんの今日の言霊\n\n" + FORTUNE_MESSAGE + "\n\n";
  var url = location.href;

  if (xBtn) {
    xBtn.addEventListener("click", function() {
      window.open(
        "https://x.com/intent/tweet?text=" + encodeURIComponent(text) + "&url=" + encodeURIComponent(url),
        "_blank"
      );
    });
  }

  if (lineBtn) {
    lineBtn.addEventListener("click", function() {
      window.open(
        "https://line.me/R/msg/text/?" + encodeURIComponent(text + url),
        "_blank"
      );
    });
  }
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  updateStreak();
  updateMorningBanner();
  updateCountdown();
  setInterval(updateCountdown, 1000);
  initShareButtons();
});
