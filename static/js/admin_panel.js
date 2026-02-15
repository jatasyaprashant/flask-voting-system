// ==================== ADMIN PANEL JAVASCRIPT ====================
// All UI logic, event handlers, and API interactions for the admin dashboard

// Initialize event listeners when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // Get sidebar menu buttons
    const addBtn = document.getElementById('add');
    const listBtn = document.getElementById('list');
    const listUsersBtn = document.getElementById('list-users');
    const analyticsBtn = document.getElementById('Analytics');
    const massRegBtn = document.getElementById('mass-registration');

    // Get content containers
    const addCandidateDiv = document.getElementById('targetDiv');
    const candidatesListDiv = document.getElementById('targetDiv1');
    const usersListDiv = document.getElementById('usersList');
    const analyticsDiv = document.getElementById('analytics-div');
    const massRegDiv = document.getElementById('massRegDiv');

    // Helper function to hide all content sections
    function hideAllSections() {
        addCandidateDiv.style.display = 'none';
        candidatesListDiv.style.display = 'none';
        usersListDiv.style.display = 'none';
        analyticsDiv.style.display = 'none';
        massRegDiv.style.display = 'none';
    }

    // Add Candidate menu click handler
    addBtn.addEventListener('click', function (event) {
        event.preventDefault();
        hideAllSections();
        addCandidateDiv.style.display = addCandidateDiv.style.display === 'none' ? 'block' : 'none';
    });

    // List Candidates menu click handler
    listBtn.addEventListener('click', function (event) {
        event.preventDefault();
        hideAllSections();
        if (candidatesListDiv.style.display === 'none') {
            candidatesListDiv.style.display = 'block';
            updateCandidatesList();
        }
    });

    // Manage Users menu click handler
    listUsersBtn.addEventListener('click', function (event) {
        event.preventDefault();
        hideAllSections();
        if (usersListDiv.style.display === 'none') {
            usersListDiv.style.display = 'block';
            updateUsersList();
        }
    });

    // Mass Registration menu click handler
    massRegBtn.addEventListener('click', function (event) {
        event.preventDefault();
        hideAllSections();
        massRegDiv.style.display = massRegDiv.style.display === 'none' ? 'block' : 'none';
    });

    // Analytics menu click handler
    analyticsBtn.addEventListener('click', function (event) {
        event.preventDefault();
        hideAllSections();
        if (analyticsDiv.style.display === 'none') {
            analyticsDiv.style.display = 'block';
            updateAnalyticsData();
        }
    });
});

// ==================== CANDIDATE MANAGEMENT ====================

/**
 * Fetch all candidates and populate the candidates list table
 */
function updateCandidatesList() {
    fetch('/display_list')
        .then(response => response.json())
        .then(data => {
            const candidatesListDiv = document.getElementById('targetDiv1');
            let html = '<h2 class="dynamic-h2">Candidates List</h2><table class="list">';
            html += '<thead><tr><th>ID</th><th>Name</th><th>Party</th><th>Area</th><th>Action</th></tr></thead><tbody>';
            
            data.forEach(candidate => {
                html += `<tr id="candidate-row-${candidate.id}">
                            <td>${candidate.id}</td>
                            <td>${candidate.name}</td>
                            <td>${candidate.party}</td>
                            <td>${candidate.area}</td>
                            <td><button class="delete-btn" onclick="deleteCandidateHandler(${candidate.id}, '${candidate.name}')">Delete</button></td>
                         </tr>`;
            });
            
            html += '</tbody></table>';
            candidatesListDiv.innerHTML = html;
            console.log(`Loaded ${data.length} candidates`);
        })
        .catch(error => console.error('Error fetching candidates:', error));
}

/**
 * Delete a candidate with confirmation
 * @param {number} candidateId - ID of candidate to delete
 * @param {string} candidateName - Name of candidate (for confirmation message)
 */
function deleteCandidateHandler(candidateId, candidateName) {
    if (confirm(`Are you sure you want to delete candidate "${candidateName}"? This action cannot be undone.`)) {
        fetch(`/delete_candidate/${candidateId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Delete failed');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Candidate deleted successfully:', data.message);
                const rowElement = document.getElementById(`candidate-row-${candidateId}`);
                if (rowElement) {
                    rowElement.remove();
                }
                alert('Candidate deleted successfully!');
            })
            .catch(error => {
                console.error('Error deleting candidate:', error.message);
                alert(`Error: ${error.message}`);
            });
    }
}

// ==================== USER MANAGEMENT ====================

/**
 * Fetch all users and populate the users list table
 */
function updateUsersList() {
    fetch('/display_users')
        .then(response => response.json())
        .then(data => {
            const usersListDiv = document.getElementById('usersList');
            let html = '<h2 class="dynamic-h2">Users List</h2><table class="list">';
            html += '<thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Voted</th><th>Action</th></tr></thead><tbody>';
            
            data.forEach(user => {
                html += `<tr id="user-row-${user.id}">
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.role}</td>
                            <td>${user.voted}</td>
                            <td><button class="delete-btn" onclick="deleteUserHandler(${user.id}, '${user.username}')">Delete</button></td>
                         </tr>`;
            });
            
            html += '</tbody></table>';
            usersListDiv.innerHTML = html;
            console.log(`Loaded ${data.length} users`);
        })
        .catch(error => console.error('Error fetching users:', error));
}

/**
 * Delete a user with confirmation
 * @param {number} userId - ID of user to delete
 * @param {string} username - Username (for confirmation message)
 */
function deleteUserHandler(userId, username) {
    if (confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
        fetch(`/delete_user/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Delete failed');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('User deleted successfully:', data.message);
                const rowElement = document.getElementById(`user-row-${userId}`);
                if (rowElement) {
                    rowElement.remove();
                }
                alert('User deleted successfully!');
            })
            .catch(error => {
                console.error('Error deleting user:', error.message);
                alert(`Error: ${error.message}`);
            });
    }
}

// ==================== ANALYTICS ====================

/**
 * Fetch and display analytics data (total voters and candidates)
 */
function updateAnalyticsData() {
    // Fetch total voters
    fetch('/total_voters')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-voters').textContent = data.total_voters;
            console.log('Total voters:', data.total_voters);
        })
        .catch(error => console.error('Error fetching total voters:', error));

    // Fetch total candidates
    fetch('/total_candidates')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-candidates').textContent = data.total_candidates;
            console.log('Total candidates:', data.total_candidates);
        })
        .catch(error => console.error('Error fetching total candidates:', error));
}
