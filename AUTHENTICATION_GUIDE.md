# 🔐 JWT Authentication & Security Guide

Complete guide for the OfferSense Marketing Analytics Backend authentication system.

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Security Features](#security-features)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The OfferSense backend uses **JWT (JSON Web Tokens)** for secure API authentication. All analytics endpoints require valid JWT tokens, ensuring only authorized users can access campaign data.

### Key Features

✅ **User Registration & Login**
✅ **JWT Access & Refresh Tokens**
✅ **Password Hashing with Bcrypt**
✅ **Token Expiration & Refresh**
✅ **Protected API Routes**
✅ **User Account Management**
✅ **Audit Logging**

---

## Authentication Flow

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 1. Register/Login
       ▼
┌──────────────────────┐
│  Auth Endpoint       │
│  /auth/register      │
│  /auth/login         │
└──────┬───────────────┘
       │ 2. Validate credentials
       │    Hash password
       ▼
┌──────────────────────┐
│  Generate Tokens     │
│  - Access Token      │
│  - Refresh Token     │
└──────┬───────────────┘
       │ 3. Return tokens
       ▼
┌──────────────────────┐
│  Client Application  │
│  Store tokens        │
└──────┬───────────────┘
       │ 4. Include in requests
       │    Authorization: Bearer <token>
       ▼
┌──────────────────────┐
│  Protected Endpoint  │
│  /api/kpis           │
│  /api/campaigns      │
└──────┬───────────────┘
       │ 5. Verify token
       │    Extract user info
       ▼
┌──────────────────────┐
│  Return Data         │
│  (if authorized)     │
└──────────────────────┘
```

---

## API Endpoints

### Public Endpoints (No Authentication Required)

#### 1. Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-06-03T10:30:00"
}
```

**Validation Rules:**
- `username`: 3-50 characters, unique
- `email`: Valid email format, unique
- `password`: Minimum 8 characters
- `full_name`: Optional

#### 2. Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Token Details:**
- `access_token`: Valid for 30 minutes
- `refresh_token`: Valid for 7 days
- `expires_in`: Expiration time in seconds

#### 3. Refresh Access Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Protected Endpoints (Authentication Required)

#### 4. Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-06-03T10:30:00"
}
```

#### 5. Change Password
```http
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "SecurePassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

#### 6. Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully",
  "username": "john_doe"
}
```

**Note:** Logout is client-side. The server doesn't invalidate tokens (implement token blacklist in production for immediate invalidation).

#### 7. Deactivate Account
```http
POST /auth/deactivate
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Account deactivated successfully"
}
```

---

## Usage Examples

### JavaScript/TypeScript (React, Node.js)

```typescript
// 1. Register new user
async function register() {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'john_doe',
      email: 'john@example.com',
      password: 'SecurePassword123!',
      full_name: 'John Doe'
    })
  });
  
  const user = await response.json();
  console.log('User registered:', user);
}

// 2. Login
async function login() {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'john_doe',
      password: 'SecurePassword123!'
    })
  });
  
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  console.log('Login successful');
}

// 3. Make authenticated request
async function fetchKPIs() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/kpis', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const kpis = await response.json();
  console.log('KPIs:', kpis);
}

// 4. Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  
  console.log('Token refreshed');
}
```

### Python

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

class AuthClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
    
    def register(self, username, email, password, full_name=None):
        """Register new user"""
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.json()
    
    def login(self, username, password):
        """Login and store tokens"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        
        return data
    
    def fetch_kpis(self):
        """Fetch KPIs with authentication"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{BASE_URL}/api/kpis", headers=headers)
        return response.json()
    
    def refresh_access_token(self):
        """Refresh access token"""
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        data = response.json()
        self.access_token = data['access_token']
        return data

# Usage
client = AuthClient()
client.register('john_doe', 'john@example.com', 'SecurePassword123!')
client.login('john_doe', 'SecurePassword123!')
kpis = client.fetch_kpis()
print(kpis)
```

### cURL

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123!"
  }'

# Extract token and use in authenticated request
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -X GET http://localhost:8000/api/kpis \
  -H "Authorization: Bearer $TOKEN"
```

---

## Security Features

### 1. Password Hashing
- **Algorithm**: Bcrypt with salt
- **Cost Factor**: 12
- **Protection**: Never stores plaintext passwords

```python
# Passwords are hashed using bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("MyPassword123")  # Bcrypt hash
verified = pwd_context.verify("MyPassword123", hashed)  # True/False
```

### 2. JWT Tokens
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Signature**: Cryptographically signed
- **Expiration**: Automatic expiration
  - Access token: 30 minutes
  - Refresh token: 7 days

### 3. Token Verification
- Token signature validated on every request
- Token expiration checked
- User activation status verified
- Tampered tokens rejected

### 4. Rate Limiting (Optional)
In production, implement rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, credentials: UserLogin):
    # Max 5 login attempts per minute
    pass
```

### 5. HTTPS/TLS
- Use HTTPS in production
- Nginx configured with SSL

### 6. CORS Configuration
- Restrict to specific frontend domains
- Prevent unauthorized cross-origin requests

---

## Configuration

### Environment Variables

```env
# In .env or .env.production
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Generate Secure Secret Key

```python
import secrets
import base64

# Generate 32-byte random key
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")
```

### Docker Environment

```bash
# In docker-compose.yml
environment:
  - SECRET_KEY=your-secret-key-here
  - ACCESS_TOKEN_EXPIRE_MINUTES=30
  - REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Username already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid username or password"
}
```

### 401 Invalid Token
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "User account is inactive"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [{
    "loc": ["body", "password"],
    "msg": "ensure this value has at least 8 characters",
    "type": "value_error.string.too_short"
  }]
}
```

---

## Testing

Run authentication tests:

```bash
python -m pytest tests/test_auth.py -v

# Or with unittest
python -m unittest tests.test_auth -v
```

---

## Troubleshooting

### Token Expired
**Error**: `"Token has expired"`
**Solution**: Use refresh_token to get new access_token

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token"}'
```

### Invalid Credentials
**Error**: `"Invalid username or password"`
**Solution**: Verify username and password are correct

### User Already Exists
**Error**: `"Username already exists"`
**Solution**: Choose a different username or login if account exists

### Missing Authorization Header
**Error**: `"Invalid authentication credentials"`
**Solution**: Include `Authorization: Bearer <token>` header

```bash
# ✗ Wrong
curl http://localhost:8000/api/kpis

# ✓ Correct
curl -H "Authorization: Bearer eyJ..." http://localhost:8000/api/kpis
```

### Token Verification Failed
**Error**: `"Could not validate credentials"`
**Solution**: 
- Token may be corrupted or tampered with
- Try refreshing token
- Login again if necessary

---

## Next Steps

1. **Implement Token Blacklist** (for immediate logout)
   - Store invalidated tokens in Redis
   - Check blacklist on each request

2. **Add Role-Based Access Control (RBAC)**
   - Define user roles (admin, analyst, viewer)
   - Restrict endpoints by role

3. **Implement Multi-Factor Authentication (MFA)**
   - TOTP (Time-based One-Time Password)
   - Email verification

4. **Add OAuth2 Support**
   - Google login
   - GitHub login
   - Microsoft login

5. **Setup Audit Logging**
   - Track all authentication events
   - Log failed attempts

---

**Questions?** Check [README.md](README.md) or open an issue on GitHub!
