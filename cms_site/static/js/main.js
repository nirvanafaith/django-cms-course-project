(() => {
    "use strict";
    const toggle = document.querySelector("[data-nav-toggle]");
    const menu = document.querySelector("[data-nav-menu]");
    if (!toggle || !menu) return;

    toggle.addEventListener("click", () => {
        const expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));
        toggle.setAttribute("aria-label", expanded ? "展开菜单" : "收起菜单");
        menu.classList.toggle("is-open", !expanded);
    });
})();
