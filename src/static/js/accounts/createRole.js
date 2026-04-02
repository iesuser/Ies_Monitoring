function createRole() {
    // Show the Create Role modal
    const createRoleModal = new bootstrap.Modal(document.getElementById('createRoleModal'));
    createRoleModal.show();

    // Handle role changes on form submission
    const form = document.getElementById('createRoleForm');
    form.onsubmit = function (event) {
        event.preventDefault();
        const token = localStorage.getItem('access_token');

        const form = document.getElementById('createRoleForm');
        const formData = new FormData(form);
        
        // makeApiRequest is a utility function defined elsewhere
        makeApiRequest('/api/roles', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}` // Include JWT token in the Authorization header
            },
            body: formData
        })
        .then(data => {
            if (data.message) {
                showAlert('alertPlaceholder', 'success', data.message);
                window.location.reload(); // Reload page after success
            }else if (data.error) {
                showAlert('alertPlaceholder', 'danger', data.error || 'როლის შექმნა ვერ მოხერხდა.');
                closeModal('createRoleModal');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
}