// Exhale's own applier waits on jQuery's ready, and Sphinx 6 stopped shipping jQuery.
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => CollapsibleLists.apply());
} else {
  CollapsibleLists.apply();
}
