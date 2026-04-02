document.addEventListener("DOMContentLoaded", function() {
    const navLinksStart = document.getElementById('navLinksStart');
    const navLinksEnd = document.getElementById('navLinksEnd');
    
    // Define static navigation items
    const navItems = [
        { endpoint: '/', text: 'მთავარი' },
        { endpoint: '/shakemap', text: 'ShakeMap' },
        { endpoint: '/events', text: 'Events' },
        // Add other static links as needed
    ];

    // Define the login and registration links
    const authLinks = [
        { endpoint: '/login', text: 'შესვლა' }
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
    if (localStorage.getItem('access_token')) {
        // User is logged in, show Logout button
        const logoutItem = document.createElement('li');
        logoutItem.className = 'nav-item d-flex align-items-center gap-2 mt-2 mt-lg-0';

        // Retrieve the user's email from localStorage
        const access_token = localStorage.getItem('access_token');
        if (access_token) {
            const profileButton = document.createElement('button');
            profileButton.type = 'button';
            profileButton.className = 'btn btn-sm btn-outline-secondary rounded-circle d-flex align-items-center justify-content-center';
            profileButton.style.width = '34px';
            profileButton.style.height = '34px';

            const iconImg = document.createElement('img');
            iconImg.src = '/static/img/circle-user-solid.svg';
            iconImg.alt = 'User Icon'; 
            iconImg.style.width = '18px'; 
            iconImg.style.height = '18px'; 
            iconImg.style.verticalAlign = 'middle';
            profileButton.appendChild(iconImg);
            profileButton.onclick = function() {
                openUserModal();
            };
            logoutItem.appendChild(profileButton);
            
        }

        const logoutLink = document.createElement('a');
        logoutLink.href = '/login';
        logoutLink.className = 'btn btn-sm btn-outline-danger';
        logoutLink.textContent = 'გასვლა';
        logoutLink.onclick = function() {
            clearSessionData();
        };

        logoutItem.appendChild(logoutLink);
        navLinksEnd.appendChild(logoutItem);

    } else {
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
});