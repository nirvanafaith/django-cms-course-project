(() => {
    "use strict";

    const navToggle = document.querySelector("[data-nav-toggle]");
    const navMenus = document.querySelectorAll("[data-nav-menu], .account-menu");

    const setNavigationExpanded = (expanded) => {
        if (!navToggle) return;
        navToggle.setAttribute("aria-expanded", String(expanded));
        navToggle.setAttribute("aria-label", expanded ? "收起菜单" : "展开菜单");
        navToggle.setAttribute("title", expanded ? "收起菜单" : "展开菜单");
        navMenus.forEach((menu) => menu.classList.toggle("is-open", expanded));
    };

    navToggle?.addEventListener("click", () => {
        setNavigationExpanded(navToggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setNavigationExpanded(false);
    });

    document.querySelectorAll("[data-carousel]").forEach((carousel) => {
        const slides = Array.from(carousel.querySelectorAll("[data-slide]"));
        const previous = carousel.querySelector("[data-carousel-prev]");
        const next = carousel.querySelector("[data-carousel-next]");
        const toggle = carousel.querySelector("[data-carousel-toggle]");
        const status = carousel.querySelector("[data-carousel-status]");
        const pauseIcon = carousel.querySelector("[data-pause-icon]");
        const playIcon = carousel.querySelector("[data-play-icon]");
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
        let activeIndex = 0;
        let paused = reduceMotion.matches;
        let timerId = null;

        const updateToggle = () => {
            if (!toggle) return;
            const label = paused ? "继续轮播" : "暂停轮播";
            toggle.setAttribute("aria-label", label);
            toggle.setAttribute("title", label);
            pauseIcon?.toggleAttribute("hidden", paused);
            playIcon?.toggleAttribute("hidden", !paused);
        };

        const renderSlide = () => {
            slides.forEach((slide, index) => {
                const active = index === activeIndex;
                slide.classList.toggle("is-active", active);
                slide.setAttribute("aria-hidden", String(!active));
            });
            if (status) status.textContent = `第 ${activeIndex + 1} 张，共 ${slides.length} 张`;
        };

        const clearAutoplay = () => {
            if (timerId !== null) window.clearInterval(timerId);
            timerId = null;
        };

        const startAutoplay = () => {
            clearAutoplay();
            if (paused || reduceMotion.matches || slides.length < 2) return;
            timerId = window.setInterval(() => {
                activeIndex = (activeIndex + 1) % slides.length;
                renderSlide();
            }, 6000);
        };

        const showRelativeSlide = (offset) => {
            paused = true;
            activeIndex = (activeIndex + offset + slides.length) % slides.length;
            clearAutoplay();
            updateToggle();
            renderSlide();
        };

        previous?.addEventListener("click", () => showRelativeSlide(-1));
        next?.addEventListener("click", () => showRelativeSlide(1));
        toggle?.addEventListener("click", () => {
            paused = !paused;
            updateToggle();
            startAutoplay();
        });
        carousel.addEventListener("keydown", (event) => {
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                showRelativeSlide(-1);
            }
            if (event.key === "ArrowRight") {
                event.preventDefault();
                showRelativeSlide(1);
            }
        });
        reduceMotion.addEventListener("change", () => {
            if (reduceMotion.matches) paused = true;
            updateToggle();
            startAutoplay();
        });

        renderSlide();
        updateToggle();
        startAutoplay();
    });
})();
