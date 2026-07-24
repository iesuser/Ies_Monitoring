(function () {
    const STORAGE_KEY = "app_lang";
    const SUPPORTED_LANGS = ["en", "ka"];

    const translations = {
        en: {
            "nav.home": "Home",
            "nav.login": "Login",
            "nav.logout": "Logout",
            "nav.brand": "IES Monitoring",
            "nav.lang.en": "EN",
            "nav.lang.ka": "KA",

            "index.hero.title": "IES Monitoring",
            "index.hero.lead": "Real-time earthquake notification and monitoring platform for seismic event processing, alert delivery, and operational visibility.",
            "index.hero.sub": "The platform connects SeisComP ingestion, background processing, permissions-based access control, and mobile push notifications.",
            "index.hero.docs": "Open API Docs",
            "index.card.build": "What We Build",
            "index.card.build.text": "We ingest and process seismic events, then deliver alerts to users through reliable notification channels.",
            "index.card.how": "How It Works",
            "index.card.how.text": "Event data flows through API, queue, worker, and delivery services with auditable authentication and permission checks.",
            "index.card.why": "Why It Matters",
            "index.card.why.text": "A unified operational layer improves response time, consistency, and reliability during seismic incidents.",
            "index.flow.title": "Platform Flow",
            "index.flow.ingest.title": "1) Ingest",
            "index.flow.ingest.text": "Receive earthquake events from SeisComP and internal ingestion endpoints.",
            "index.flow.auth.title": "2) Authorize",
            "index.flow.auth.text": "Enforce JWT authentication, permission validation, and payload checks.",
            "index.flow.process.title": "3) Process",
            "index.flow.process.text": "Execute asynchronous processing with workers and queue-backed jobs.",
            "index.flow.deliver.title": "4) Deliver",
            "index.flow.deliver.text": "Send notifications through FCM/APNs and expose operational APIs.",

            "login.welcome": "Welcome Back",
            "login.subtitle": "Sign in to continue in IES Monitoring.",
            "login.email.label": "Email address",
            "login.email.placeholder": "Enter email address",
            "login.password.label": "Password",
            "login.password.placeholder": "Enter password",
            "login.remember": "Remember me",
            "login.forgot": "Forgot password?",
            "login.submit": "Login",
            "login.illustration.alt": "Login illustration",

            "forgot.title": "Forgot Password",
            "forgot.subtitle": "Enter your account email and we will send password reset instructions.",
            "forgot.email.label": "Email address",
            "forgot.email.placeholder": "example@example.com",
            "forgot.submit": "Send Reset Link",
            "forgot.loading": "Sending email...",

            "user.title": "Update Profile",
            "user.accounts": "Accounts",
            "user.first_name": "First name:",
            "user.last_name": "Last name:",
            "user.change_password": "Change password",
            "user.update": "Update",

            "alerts.session_expired": "Session has expired. Please sign in again.",
            "alerts.logout_failed": "Logout request failed.",
            "alerts.auth_error": "An error occurred during authorization.",
            "alerts.invalid_auth": "Invalid authorization.",
            "alerts.reset_invalid": "Password reset link is invalid.",
            "alerts.reset_expired": "Password reset link has expired.",
            "alerts.reset_check_email": "Please check your email. Verification link has been sent.",
            "alerts.invalid_email": "Invalid email address.",
            "alerts.request_failed": "Request failed. Please try again."
        },
        ka: {
            "nav.home": "მთავარი",
            "nav.login": "შესვლა",
            "nav.logout": "გასვლა",
            "nav.brand": "IES Monitoring",
            "nav.lang.en": "EN",
            "nav.lang.ka": "KA",

            "index.hero.title": "IES Monitoring",
            "index.hero.lead": "რეალურ დროში მიწისძვრის შეტყობინებებისა და მონიტორინგის პლატფორმა სეისმური მოვლენების დამუშავებისა და შეტყობინებების გაგზავნისთვის.",
            "index.hero.sub": "პლატფორმა აერთიანებს SeisComP ingestion-ს, ფონურ დამუშავებას, permissions-ზე დაფუძნებულ წვდომას და მობილურ push შეტყობინებებს.",
            "index.hero.docs": "API დოკუმენტაცია",
            "index.card.build": "რას ვაშენებთ",
            "index.card.build.text": "ვიღებთ და ვამუშავებთ სეისმურ მოვლენებს, შემდეგ კი მომხმარებლებს ვუგზავნით სანდო შეტყობინებებს.",
            "index.card.how": "როგორ მუშაობს",
            "index.card.how.text": "მონაცემები გადის API, რიგებს, worker-ებს და მიწოდების სერვისებს ავტორიზაციისა და ვალიდაციის კონტროლით.",
            "index.card.why": "რატომ არის მნიშვნელოვანი",
            "index.card.why.text": "ერთიანი ოპერაციული ფენა ამცირებს რეაგირების დროს და ზრდის სანდოობას სეისმური შემთხვევებისას.",
            "index.flow.title": "პლატფორმის ნაკადი",
            "index.flow.ingest.title": "1) მიღება",
            "index.flow.ingest.text": "მიწისძვრის მონაცემების მიღება SeisComP-დან და შიდა ingestion endpoint-ებიდან.",
            "index.flow.auth.title": "2) ავტორიზაცია",
            "index.flow.auth.text": "JWT ავთენტიფიკაცია, permission-ების შემოწმება და payload ვალიდაცია.",
            "index.flow.process.title": "3) დამუშავება",
            "index.flow.process.text": "ასინქრონული დამუშავება worker-ებით და queue-backed დავალებებით.",
            "index.flow.deliver.title": "4) მიწოდება",
            "index.flow.deliver.text": "შეტყობინებების გაგზავნა FCM/APNs-ით და ოპერაციული API-ების მიწოდება.",

            "login.welcome": "კეთილი დაბრუნება",
            "login.subtitle": "გასაგრძელებლად შედით IES Monitoring-ში.",
            "login.email.label": "ელფოსტა",
            "login.email.placeholder": "შეიყვანეთ ელფოსტა",
            "login.password.label": "პაროლი",
            "login.password.placeholder": "შეიყვანეთ პაროლი",
            "login.remember": "დამიმახსოვრე",
            "login.forgot": "პაროლი დაგავიწყდა?",
            "login.submit": "შესვლა",
            "login.illustration.alt": "შესვლის ილუსტრაცია",

            "forgot.title": "პაროლის აღდგენა",
            "forgot.subtitle": "შეიყვანეთ თქვენი ელფოსტა და გამოგიგზავნით პაროლის აღდგენის ინსტრუქციას.",
            "forgot.email.label": "ელფოსტა",
            "forgot.email.placeholder": "example@example.com",
            "forgot.submit": "აღდგენის ბმულის გაგზავნა",
            "forgot.loading": "იგზავნება...",

            "user.title": "პროფილის განახლება",
            "user.accounts": "ანგარიშები",
            "user.first_name": "სახელი:",
            "user.last_name": "გვარი:",
            "user.change_password": "პაროლის შეცვლა",
            "user.update": "განახლება",

            "alerts.session_expired": "სესია დასრულებულია. გთხოვთ თავიდან შეხვიდეთ.",
            "alerts.logout_failed": "გასვლის მოთხოვნა ვერ შესრულდა.",
            "alerts.auth_error": "ავტორიზაციისას დაფიქსირდა შეცდომა.",
            "alerts.invalid_auth": "ავტორიზაცია არასწორია.",
            "alerts.reset_invalid": "პაროლის აღდგენის ბმული არასწორია.",
            "alerts.reset_expired": "პაროლის აღდგენის ბმულს ვადა გაუვიდა.",
            "alerts.reset_check_email": "გთხოვთ შეამოწმოთ ელფოსტა. დადასტურების ბმული გამოგზავნილია.",
            "alerts.invalid_email": "ელფოსტის მისამართი არასწორია.",
            "alerts.request_failed": "მოთხოვნა ვერ შესრულდა. სცადეთ ხელახლა."
        }
    };

    function getLanguageFromPath(pathname = window.location.pathname) {
        const [, firstSegment] = pathname.split("/");
        if (SUPPORTED_LANGS.includes(firstSegment)) {
            return firstSegment;
        }
        return null;
    }

    function getLanguage() {
        const fromPath = getLanguageFromPath();
        if (fromPath) return fromPath;

        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved && SUPPORTED_LANGS.includes(saved)) {
            return saved;
        }
        return "en";
    }

    function localizePath(pathname, lang = getLanguage()) {
        const normalized = pathname.startsWith("/") ? pathname : `/${pathname}`;
        const parts = normalized.split("/").filter(Boolean);
        const first = parts[0];

        if (SUPPORTED_LANGS.includes(first)) {
            parts[0] = lang;
            return `/${parts.join("/")}${normalized.endsWith("/") && parts.length === 1 ? "/" : ""}`;
        }
        if (parts.length === 0) {
            return `/${lang}/`;
        }
        return `/${lang}${normalized}`;
    }

    function setLanguage(lang) {
        if (!SUPPORTED_LANGS.includes(lang)) return;
        localStorage.setItem(STORAGE_KEY, lang);

        const currentPath = window.location.pathname;
        const localizedPath = localizePath(currentPath, lang);
        const targetUrl = `${localizedPath}${window.location.search}${window.location.hash}`;
        window.location.assign(targetUrl);
    }

    function t(key, fallback = key) {
        const lang = getLanguage();
        return translations[lang]?.[key] ?? fallback;
    }

    function applyTranslations() {
        const lang = getLanguage();
        document.documentElement.setAttribute("lang", lang);
        localStorage.setItem(STORAGE_KEY, lang);

        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            el.textContent = t(key, el.textContent);
        });

        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            el.setAttribute("placeholder", t(key, el.getAttribute("placeholder") || ""));
        });

        document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
            const key = el.getAttribute("data-i18n-aria-label");
            el.setAttribute("aria-label", t(key, el.getAttribute("aria-label") || ""));
        });

        document.querySelectorAll("[data-i18n-alt]").forEach((el) => {
            const key = el.getAttribute("data-i18n-alt");
            el.setAttribute("alt", t(key, el.getAttribute("alt") || ""));
        });
    }

    window.I18n = {
        getLanguage,
        localizePath,
        setLanguage,
        t,
        applyTranslations
    };

    document.addEventListener("DOMContentLoaded", applyTranslations);
})();
