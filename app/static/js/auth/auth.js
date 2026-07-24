async function login(event) {
    event.preventDefault();  // Prevent the form from submitting
    const i18n = window.I18n;

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const formData = {
        email: email,
        password: password
    };

    try {
        const data = await window.makeApiRequest('/api/auth/login', {
            method: 'POST',
            skipAuthRefresh: true,
            body: JSON.stringify(formData)
        });

        if (data.access_token) {
            // Store access token only. Refresh token is HttpOnly cookie.
            localStorage.setItem('access_token', data.access_token);

            // Redirect to home page
            const i18n = window.I18n;
            window.location.href = i18n ? i18n.localizePath('/') : '/';
        } else {
            window.showAlert(
                'alertPlaceholder',
                'danger',
                data.message || data.error || (i18n ? i18n.t('alerts.invalid_auth', 'Invalid authorization.') : 'Invalid authorization.')
            );
        }
    } catch (error) {
        console.error('Error:', error);
        const invalidCredentials =
            error?.code === 'invalid_credentials' ||
            error?.message === 'Invalid email or password.';
        const alertMessage = invalidCredentials
            ? (i18n ? i18n.t('alerts.invalid_credentials', 'Invalid email or password.') : 'Invalid email or password.')
            : (error.message || (i18n ? i18n.t('alerts.auth_error', 'An error occurred during authorization.') : 'An error occurred during authorization.'));
        window.showAlert(
            'alertPlaceholder',
            'danger',
            alertMessage
        );
    }
}

// Attach the login function to the form's submit event
document.getElementById('loginForm').onsubmit = login;
window.initPasswordToggle?.({
    fieldId: "password",
    toggleId: "togglePassword",
    imageId: "togglePasswordImg",
});