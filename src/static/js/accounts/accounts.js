// Fetch and display data in the table
async function fetchAccounts() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/api/accounts', {
            method: 'GET',
            headers: {
                'accept': 'application/json',
                'Authorization': `Bearer ${token}`,  // Add your JWT token here
            }
        });

        if (!response.ok) throw new Error('Failed to fetch data');

        const data = await response.json();
        populateTable(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

function populateTable(accounts) {
    const tbody = document.getElementById('accountsTableBody');
    tbody.innerHTML = ''; // Clear existing data

    accounts.forEach(account => {
        const {uuid, username, email, role } = account;
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>
                <strong>${username}</strong> <br>
                <span style="font-size: x-small;">${email}</span>
            </td>
            <td>
                <div class="row me-1 ms-1">
                    <div class="col">
                        ${role.name}
                    </div>
                    <div class="col">
                        <img src="/static/img/arrows-up-down.svg" alt="Up_and_Down" style="width: 20px; height: 20px; cursor: pointer;" onclick="changeRole('${uuid}')">
                    </div>
                </div>
            </td>
            <td>${role.is_admin ? 'Yes' : 'No'}</td>
            <td>${role.can_users ? 'Yes' : 'No'}</td>
            <td>${role.can_shakemap ? 'Yes' : 'No'}</td>
            <td><button class="btn btn-info btn-sm" onclick="populateEditRoleModal(${role.id})">Edit Role</button></td>
        `;
        tbody.appendChild(row);
    });
}

// Fetch the data when the page loads
document.addEventListener('DOMContentLoaded', fetchAccounts);