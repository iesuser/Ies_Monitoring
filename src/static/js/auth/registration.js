function registration(event) {
    event.preventDefault(); // Prevent the default form submission

    // Gather form data
    const password = document.getElementById('password').value;
    const passwordRepeat = document.getElementById('passwordRepeat').value;
    const token = localStorage.getItem('access_token');

    // Check if passwords match
    if (password !== passwordRepeat) {
        showAlert('alertPlaceholder', 'danger', 'შეყვანილი პაროლები ერთმანეთს არ ემთხვევა ერთმანეთს.');
        return;
    }
    
    // Gather form data
    const formData = {
        name: document.getElementById('name').value,
        lastname: document.getElementById('lastname').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        passwordRepeat: document.getElementById('passwordRepeat').value
    };

    // Send POST request to the registration API
    fetch('/api/registration', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        return response.json().then(data => {
            return {
                status: response.status,
                data: data
            };
        });
    })
    .then(({ status, data }) => {
        if (status === 200) {
            showAlert('alertPlaceholder', 'success', data.message);
            setTimeout(() => {
                window.location.href = '/accounts';  // Redirect after success
            }, 2000);
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || 'რეგისტრაციისას მოხდა შეცდომა.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
};

// Attach the login function to the form's submit event
document.getElementById('registrationForm').onsubmit = registration;
window.initPasswordToggle?.({
    fieldIds: ['password', 'passwordRepeat']
});
