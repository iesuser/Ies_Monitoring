async function login(event) {
    event.preventDefault();  // Prevent the form from submitting
    const i18n = window.I18n;

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Create a JSON object with the form values
    const formData = {
        email: email,
        password: password
    };

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const contentType = response.headers.get('content-type') || '';
        let data = null;
        if (contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const textPayload = await response.text();
            throw new Error(textPayload || (i18n ? i18n.t('alerts.auth_error', 'An error occurred during authorization.') : 'An error occurred during authorization.'));
        }

        if (data.access_token) {
            // Store access token only. Refresh token is HttpOnly cookie.
            localStorage.setItem('access_token', data.access_token);

            // Redirect to home page
            const i18n = window.I18n;
            window.location.href = i18n ? i18n.localizePath('/') : '/';
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || (i18n ? i18n.t('alerts.invalid_auth', 'Invalid authorization.') : 'Invalid authorization.'));
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('alertPlaceholder', 'danger', i18n ? i18n.t('alerts.auth_error', 'An error occurred during authorization.') : 'An error occurred during authorization.');
    }
}

// Attach the login function to the form's submit event
document.getElementById('loginForm').onsubmit = login;
const togglePassword = document.getElementById('togglePassword');
const password = document.getElementById('password');
const togglePasswordImg = document.getElementById('togglePasswordImg');

const eyeViewPath = "/static/images/eye-view.svg";
const eyehidePath = "/static/images/eye-hide.svg";

togglePassword.addEventListener('click', (e) => {
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);

    if (togglePasswordImg.src.includes(eyeViewPath)) {
        togglePasswordImg.src = eyehidePath;
    } else{
        togglePasswordImg.src = eyeViewPath;
    }

});