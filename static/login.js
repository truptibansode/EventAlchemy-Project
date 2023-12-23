function validate() {
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    // Send the username and password to the server for validation
    fetch('/validate_login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Login successful! Welcome ' + data.username);
        } else {
            alert('Username or password is incorrect.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


function logout() {
    // Send a request to the /logout route to log the user out
    fetch('/logout', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Logout successful!');
            // Redirect the user to the login page or any other appropriate page
            window.location.href = '/login';
        } else {
            alert('Logout failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

