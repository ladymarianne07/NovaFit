# PWA Authentication Guide - Persistent Sessions

## Overview
The NovaFitness API now uses persistent sessions that last for 1 year or until manual logout. This provides a seamless PWA experience without frequent re-authentication.

## Frontend Implementation Guide

### 1. Storing the Token (After Login)
```javascript
// After successful login
const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
});

const data = await response.json();
if (response.ok) {
    // Store token persistently
    localStorage.setItem('auth_token', data.access_token);
    
    // Optional: Store login timestamp
    localStorage.setItem('login_time', new Date().toISOString());
    
    console.log('✅ Logged in successfully - session will persist for ~1 year');
}
```

### 2. Using the Token (API Calls)
```javascript
// Helper function to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    if (!token) return {};
    
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// Example API call
async function createEvent(eventData) {
    const response = await fetch('/events/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(eventData)
    });
    
    if (response.status === 401) {
        // Token expired or invalid - redirect to login
        handleLogout();
        return null;
    }
    
    return response.json();
}
```

### 3. Checking Authentication Status
```javascript
function isLoggedIn() {
    const token = localStorage.getItem('auth_token');
    return !!token;
}

// Optional: Check if user has been logged in for too long
function checkSessionAge() {
    const loginTime = localStorage.getItem('login_time');
    if (!loginTime) return false;
    
    const daysSinceLogin = (Date.now() - new Date(loginTime)) / (1000 * 60 * 60 * 24);
    
    // Optionally warn user if session is very old (e.g., 30+ days)
    if (daysSinceLogin > 30) {
        console.warn('⚠️ Long session detected - consider refreshing login');
    }
    
    return daysSinceLogin;
}
```

### 4. Manual Logout
```javascript
async function logout() {
    try {
        // Call logout endpoint (optional - just for logging)
        await fetch('/auth/logout', { 
            method: 'POST',
            headers: getAuthHeaders()
        });
    } catch (error) {
        console.warn('Logout endpoint failed, proceeding with local logout');
    } finally {
        // Always clear local storage
        localStorage.removeItem('auth_token');
        localStorage.removeItem('login_time');
        
        // Redirect to login page
        window.location.href = '/login';
        
        console.log('✅ Logged out successfully');
    }
}
```

### 5. App Initialization
```javascript
// On app startup
function initializeApp() {
    if (isLoggedIn()) {
        console.log('✅ User is logged in - loading main app');
        loadMainApp();
        
        // Optional: Check session age
        const daysLoggedIn = checkSessionAge();
        if (daysLoggedIn > 0) {
            console.log(`📅 Session active for ${Math.round(daysLoggedIn)} days`);
        }
    } else {
        console.log('🔒 User not logged in - showing login screen');
        showLoginScreen();
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', initializeApp);
```

### 6. Handling Token Expiration
```javascript
// Intercept all API responses to handle auth errors
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...getAuthHeaders(),
            ...options.headers
        }
    });
    
    // Handle authentication errors
    if (response.status === 401 || response.status === 403) {
        console.warn('🚫 Authentication failed - redirecting to login');
        handleLogout();
        throw new Error('Authentication required');
    }
    
    return response;
}

function handleLogout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('login_time');
    window.location.href = '/login';
}
```

### 7. PWA Service Worker Considerations
```javascript
// In your service worker (sw.js)
self.addEventListener('fetch', event => {
    // Don't cache authentication endpoints
    if (event.request.url.includes('/auth/')) {
        return; // Let it go to network
    }
    
    // Handle API requests with potential auth headers
    if (event.request.url.includes('/api/')) {
        // Your caching strategy here
    }
});
```

## Security Notes

1. **Token Storage**: Using `localStorage` is acceptable for this private pilot app with ~10 users
2. **HTTPS Required**: Always use HTTPS in production to protect tokens in transit
3. **Session Duration**: Tokens last 1 year but can be revoked client-side anytime
4. **Automatic Logout**: Consider adding an automatic logout after extended inactivity if desired

## Benefits of This Approach

✅ **User-Friendly**: No frequent re-authentication  
✅ **PWA-Optimized**: Works offline, resumes seamlessly  
✅ **Simple Implementation**: No complex refresh token logic  
✅ **Flexible**: Users control their session duration  
✅ **Secure**: Strong JWT encryption with bcrypt password hashing  

## Example: Complete Login Component
```javascript
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.baseURL = 'http://localhost:8000'; // or your production URL
    }
    
    async login(email, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('login_time', new Date().toISOString());
            return true;
        }
        
        return false;
    }
    
    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('login_time');
        window.location.reload();
    }
    
    isAuthenticated() {
        return !!this.token;
    }
    
    getHeaders() {
        return this.token ? {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        } : { 'Content-Type': 'application/json' };
    }
}

// Usage
const auth = new AuthManager();
```

This setup provides a seamless, persistent authentication experience perfect for your private PWA! 🎉