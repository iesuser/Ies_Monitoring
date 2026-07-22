async function login(event) {
    event.preventDefault();  // Prevent the form from submitting

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Create a JSON object with the form values
    const formData = {
        email: email,
        password: password
    };

    try {
        const response = await fetch('/api/login', {
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
            throw new Error(textPayload || 'Login response was not returned as JSON.');
        }

        if (data.access_token) {
            // Store access token only. Refresh token is HttpOnly cookie.
            localStorage.setItem('access_token', data.access_token);

            // Redirect to home page
            window.location.href = '/';
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || 'Invalid authorization.');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('alertPlaceholder', 'danger', 'An error occurred during authorization.');
    }
}

// Attach the login function to the form's submit event
document.getElementById('loginForm').onsubmit = login;
const togglePassword = document.getElementById('togglePassword');
const password = document.getElementById('password');
const togglePasswordImg = document.getElementById('togglePasswordImg');

const eyeViewPath = "static/images/eye-view.svg";
const eyehidePath = "static/images/eye-hide.svg";

togglePassword.addEventListener('click', (e) => {
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);

    if (togglePasswordImg.src.includes(eyeViewPath)) {
        togglePasswordImg.src = eyehidePath;
    } else{
        togglePasswordImg.src = eyeViewPath;
    }

});