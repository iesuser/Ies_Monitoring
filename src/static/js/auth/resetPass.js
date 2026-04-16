function login(event) {
    event.preventDefault();  // Prevent the form from submitting

    const password = document.getElementById('password').value;
    const retypePassword = document.getElementById('retypePassword').value;
    const hasToken = typeof token !== "undefined" && token !== null && String(token).trim() !== "";
    if (!hasToken) {
        showAlert('alertPlaceholder', 'danger', 'არასწორი ან ცარიელი reset ტოკენი.');
        return;
    }

    const formData = {
        password: password,
        retype_password: retypePassword,
        token: token
    };

    fetch('/api/reset_password', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            // JWT ტოკენების შენახვა localStorage-ში
            showAlert('alertPlaceholder', 'success', data.message || ' პაროლი წარმატებით შეიცვალა.');
            setTimeout(() => {
                clearSessionData();
            }, 1000); // Optional delay (1 second)
            // Redirect to /projects page
        } else {
            showAlert('alertPlaceholder', 'danger', data.error || ' გაუმართავი ავტორიზაცია.');

        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('alertPlaceholder', 'danger', 'მოთხოვნა ჩავარდა. გთხოვთ სცადოთ თავიდან.');
    });
}

// Attach the login function to the form's submit event
document.getElementById('loginForm').onsubmit = login;
window.initPasswordToggle?.({
    fieldIds: ['password', 'retypePassword']
});
