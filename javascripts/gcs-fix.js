// Override Material theme instant navigation for static hosting
// Forces standard browser navigation instead of XHR fetches
document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll("a").forEach(function(a) {
    if (a.href && a.href.includes(window.location.host)) {
      a.setAttribute("data-md-state", "");
    }
  });
  // Disable instant loading by removing the event listener attribute
  if (typeof __md_scope !== "undefined") {
    __md_scope = undefined;
  }
});
