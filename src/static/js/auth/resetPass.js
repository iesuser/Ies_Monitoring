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
    });
}

// Attach the login function to the form's submit event
document.getElementById('loginForm').onsubmit = login;


// იქმნება ფუნქცია, რომელიც შეამოწმებს პაროლი ტიპს და შეცვლის მას, ასევე იცვლება ფოტოს src გზა.
function togglePasswordEye(){
    const typePassword = password.getAttribute('type') === 'password' ? 'text' : 'password';

    password.setAttribute('type', typePassword);
    passwordRepeat.setAttribute('type', typePassword);

    // forEach ლუპში ერთდროულად შეიცვლება ფოტო
    togglePasswordImgs.forEach(img => {
        if (img.src.includes(eyeViewPath)){
            img.src = eyehidePath;
        } else {
            img.src = eyeViewPath;
        }
    })

}
// იქმნება ცვლადები, რომლების საჭიროა visibility eye-ს ფუნქციონალისთვის
const togglePasswords = document.querySelectorAll('.togglePassword');
const togglePasswordImgs = document.querySelectorAll('.togglePasswordImg');

const password = document.getElementById('password');
const passwordRepeat = document.getElementById('retypePassword');



const eyeViewPath = "/static/img/eye-view.svg";
const eyehidePath = "/static/img/eye-hide.svg";

// forEach ლუპით ამ ორი ღილაკის მიბმა ხდება ერთსა და იმავე ფუნქციაზე
togglePasswords.forEach(togglePassword => {
    togglePassword.addEventListener('click', togglePasswordEye);
})


