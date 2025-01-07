

# Bells University Exeat Management System (BUEMS) API

The **Bells University Exeat Management System (BUEMS) API** provides endpoints for managing exeat requests, user authentication, account management, and administrative operations.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Endpoints](#endpoints)
- [Authentication](#authentication)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Overview

The BUEMS API powers the Bells University Exeat Management System, facilitating the management of exeat requests and administrative workflows. It was developed by Divine Afam-Ifediogor et al. (Group 7) as part of an academic project.

## Features

- User authentication (Login, Logout, Signup)
- Retrieve account details
- Submit, view, and manage exeat requests
- Administrative controls for approvals and reporting (under development)

## Endpoints

### Authentication

- `POST /token` - Login and retrieve an access token.
- `POST /revoke` - Logout by revoking the current session.
- `POST /signup` - Create a new user account.

### Account Management

- `GET /account` - Retrieve details of the logged-in user.
- `PUT /account/update` - Update the details of the logged-in user.
- `PUT /account/change-password` - Change the password of the logged-in user.
- `DEL /account/delete` - Delete the logged-in user.
- `GET /account/profile` - Retrieve the profile-specific details of the logged-in user.
- `POST /account/upload-profile-picture` - Update the profile picture of the logged-in user.

### Student
- `GET /student/exeat` - View all submitted exeat requests by the logged-in student.
- `GET /student/exeat/{exeat_id}` - View a specific exeat request submitted by the logged-in student.
- `GET /student/submit` - Submit an exeat request for the logged-in student.

### Security Operative
- `GET /security/exeat` - View all submitted exeat requests by all students.
- `GET /security/exeat/{exeat_id}` - View a specific exeat request.

### Staff
- `GET /staff/exeat` - View all submitted exeat requests (all `pending` requests, and only the requests `approved` or `denied` by the logged-in staff).
- `GET /staff/exeat/{exeat_id}` - View a specific exeat request.
- `GET /staff/approve/{exeat_id}` - Approve a specific exeat request.
- `GET /staff/deny/{exeat_id}` - Deny a specific exeat request.

Run the API, and refer to the [Swagger UI Documentation](http://127.0.0.1:8000/docs) for more details.

## Authentication

The API uses **JWT-based authentication**. Include the token in the `Authorization` header as a Bearer token for secure endpoints.

Example:
```
Authorization: Bearer <your_token_here>
```

## License

This project is licensed under the [MIT License](LICENSE).

---

For more information, run the API and visit the [API Documentation](http://127.0.0.1:8000/docs).