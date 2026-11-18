// Splash page: shows the logo screens one after another, then moves on.
import { getSession } from "./session.js";

const NEXT_PAGE = "onboarding.html";
const HOME_PAGE = "index.html";
const DURATIONS = [3800, 2800]; // ms per screen, same timing as the prototype

// Already logged in? Skip the intro.
if (getSession()) {
    window.location.href = HOME_PAGE;
} else {
    const steps = [...document.querySelectorAll("[data-splash-step]")];

    function run(i = 0) {
        if (i >= steps.length) {
            window.location.href = NEXT_PAGE;
            return;
        }
        steps.forEach((step, n) => step.classList.toggle("is-active", n === i));
        setTimeout(() => run(i + 1), DURATIONS[i] ?? 2000);
    }

    run();
}