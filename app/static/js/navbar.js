document.addEventListener("DOMContentLoaded", function() {
    const navLinksStart = document.getElementById('navLinksStart');
    const navLinksEnd = document.getElementById('navLinksEnd');
    const offcanvasElement = document.getElementById('offcanvasNavbar');
    const i18n = window.I18n;

    function isTokenExpired(token) {
        try {
            const payloadBase64 = token.split('.')[1];
            if (!payloadBase64) return true;
            const payload = JSON.parse(atob(payloadBase64));
            if (!payload.exp) return true;
            const nowInSeconds = Math.floor(Date.now() / 1000);
            return payload.exp <= nowInSeconds;
        } catch (error) {
            return true;
        }
    }

    function clearLocalSession() {
        if (typeof clearSessionData === 'function') {
            clearSessionData();
            return;
        }
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        const loginPath = i18n ? i18n.localizePath('/login') : '/login';
        window.location.href = loginPath;
    }
    
    // Define static navigation items
    const navItems = [
        { endpoint: i18n ? i18n.localizePath('/') : '/', text: i18n ? i18n.t('nav.home', 'Home') : 'Home' }
        // Add other static links as needed
    ];

    // Define the login and registration links
    const authLinks = [
        { endpoint: i18n ? i18n.localizePath('/login') : '/login', text: i18n ? i18n.t('nav.login', 'Login') : 'Login' }
    ];

    // Get the current path
    const currentPath = window.location.pathname;

    // Add static navigation items to the start of the navbar
    navItems.forEach(item => {
        const link = document.createElement('a');
        link.href = item.endpoint;
        link.className = currentPath === item.endpoint
            ? 'nav-link active text-primary fw-semibold px-2'
            : 'nav-link px-2';
        link.textContent = item.text;

        const listItem = document.createElement('li');
        listItem.className = 'nav-item';
        listItem.appendChild(link);

        navLinksStart.appendChild(listItem);
    });

    // Check for access_token in localStorage and update the navigation
    const accessToken = localStorage.getItem('access_token');
    const hasValidAccessToken = accessToken && !isTokenExpired(accessToken);
    if (hasValidAccessToken) {
        // User is logged in, show Logout button
        const logoutItem = document.createElement('li');
        logoutItem.className = 'nav-item d-flex align-items-center gap-2 mt-2 mt-lg-0';

        // Retrieve the user's email from localStorage
        if (accessToken) {
            const profileButton = document.createElement('button');
            profileButton.type = 'button';
            profileButton.className = 'btn btn-sm btn-outline-secondary rounded-circle d-flex align-items-center justify-content-center';
            profileButton.style.width = '34px';
            profileButton.style.height = '34px';

            const iconImg = document.createElement('img');
            iconImg.src = '/static/images/circle-user-solid.svg';
            iconImg.alt = 'User Icon';
            iconImg.style.width = '18px'; 
            iconImg.style.height = '18px'; 
            iconImg.style.verticalAlign = 'middle';
            profileButton.appendChild(iconImg);
            profileButton.onclick = function() {
                if (typeof window.openUserModal === "function") {
                    window.openUserModal();
                } else {
                    console.error("openUserModal is not available.");
                }
            };
            logoutItem.appendChild(profileButton);
            
        }

        const logoutLink = document.createElement('a');
        logoutLink.className = 'btn btn-sm btn-outline-danger';
        logoutLink.textContent = i18n ? i18n.t('nav.logout', 'Logout') : 'Logout';
        logoutLink.onclick = async function(event) {
            event.preventDefault();
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'accept': 'application/json'
                    }
                });
                if (response.status === 401 || response.status === 403) {
                    console.info('User is not authorized anymore, forcing local logout.');
                }
            } catch (error) {
                console.error('Logout request failed:', error);
            } finally {
                clearLocalSession();
            }
        };

        logoutItem.appendChild(logoutLink);
        navLinksEnd.appendChild(logoutItem);

    } else {
        if (accessToken && isTokenExpired(accessToken)) {
            clearLocalSession();
            return;
        }
        // User is not logged in, show Login and Registration buttons
        authLinks.forEach(link => {
            const authItem = document.createElement('li');
            authItem.className = 'nav-item mt-2 mt-lg-0';

            const authLink = document.createElement('a');
            authLink.href = link.endpoint;
            authLink.className = currentPath === link.endpoint
                ? 'btn btn-sm btn-primary'
                : 'btn btn-sm btn-outline-primary';
            authLink.textContent = link.text;

            authItem.appendChild(authLink);
            navLinksEnd.appendChild(authItem);
        });
    }

    const langItem = document.createElement('li');
    langItem.className = 'nav-item mt-2 mt-lg-0';
    langItem.innerHTML = `
        <div class="btn-group btn-group-sm language-switcher" role="group" aria-label="Language switcher">
            <button type="button" class="btn btn-outline-secondary language-btn" id="langEn" aria-label="Switch language to English" title="${i18n ? i18n.t('nav.lang.en', 'EN') : 'EN'}">
                <img src="/static/images/flag_en.svg" alt="${i18n ? i18n.t('nav.lang.en', 'EN') : 'EN'} flag" class="language-flag">
            </button>
            <button type="button" class="btn btn-outline-secondary language-btn" id="langKa" aria-label="Switch language to Georgian" title="${i18n ? i18n.t('nav.lang.ka', 'KA') : 'KA'}">
                <img src="/static/images/flag_ka.svg" alt="${i18n ? i18n.t('nav.lang.ka', 'KA') : 'KA'} flag" class="language-flag">
            </button>
        </div>
    `;
    navLinksEnd.appendChild(langItem);

    if (i18n) {
        const currentLang = i18n.getLanguage();
        const langEnButton = document.getElementById('langEn');
        const langKaButton = document.getElementById('langKa');
        if (currentLang === 'en') {
            langEnButton.classList.add('active');
        } else {
            langKaButton.classList.add('active');
        }

        langEnButton.addEventListener('click', () => i18n.setLanguage('en'));
        langKaButton.addEventListener('click', () => i18n.setLanguage('ka'));
    }

    // Close mobile offcanvas after clicking any navigation link.
    if (offcanvasElement && window.bootstrap?.Offcanvas) {
        const offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement);
        offcanvasElement.querySelectorAll('a').forEach((anchor) => {
            anchor.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    offcanvasInstance.hide();
                }
            });
        });
    }
});