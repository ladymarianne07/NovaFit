# NovaFitness System Specifications

## 📊 **Project Overview**

NovaFitness es una aplicación web móvil para seguimiento de fitness con cálculos biométricos automáticos (BMR/TDEE) y autenticación JWT.

---

## 🎯 **Technology Stack**

### Frontend
- **Framework:** React + TypeScript + Vite
- **Routing:** React Router DOM
- **State Management:** React Context API
- **UI Library:** Lucide React Icons
- **Styling:** CSS Modules + Glassmorphism effects
- **HTTP Client:** Axios
- **Build Tool:** Vite

### Backend
- **Framework:** FastAPI + Python 3.12+
- **Database:** SQLite + SQLAlchemy ORM
- **Authentication:** JWT (JSON Web Tokens)
- **Validation:** Pydantic schemas
- **Server:** Uvicorn ASGI
- **CORS:** FastAPI CORS Middleware

---

## 🔐 **Authentication System**

### JWT Implementation
```
- Custom JWT with FastAPI
- Token storage: localStorage (frontend)
- Token expiration: Configurable (ACCESS_TOKEN_EXPIRE_MINUTES)
- Authentication header: Bearer token
- Middleware: OAuth2PasswordBearer
```

### Security Features
- Password hashing with bcrypt
- Protected routes with dependency injection
- CORS configured for cross-origin requests
- Custom exception handling hierarchy

---

## 📝 **Registration System**

### Registration Flow (2 Steps)

#### Step 1: Account Information
```typescript
interface AccountData {
  email: string        // EmailStr validation
  password: string     // min 8 characters
  confirmPassword: string
  first_name?: string  // Optional
  last_name?: string   // Optional
}
```

#### Step 2: Biometric Information (ALL REQUIRED)
```typescript
interface BiometricData {
  age: number           // 1-120 years
  gender: 'male' | 'female'
  weight: number        // 20-300 kg
  height: number        // 100-250 cm
  activity_level: number // 1.20-1.80 enum values
}
```

### Activity Levels
```
1.20 - Sedentario real (desk job, no exercise)
1.35 - Ligeramente activo (light exercise 1-3 days/week)
1.50 - Moderadamente activo (moderate exercise 3-5 days/week)  
1.65 - Activo (intense exercise 6-7 days/week)
1.80 - Muy activo (very intense exercise, physical work)
```

---

## ✅ **Validation Rules**

### Frontend Validations
```typescript
// Password validation
password.length >= 8
password === confirmPassword

// Required fields validation
email && password && confirmPassword (Step 1)
age && gender && weight && height && activity_level (Step 2)

// Biometric ranges
age: 1-120
weight: 20-300 kg
height: 100-250 cm
```

### Backend Validations (Pydantic)
```python
# User schema validations
email: EmailStr                    # Automatic email format validation
password: Field(min_length=8)      # Minimum password length

# Biometric constraints
age: Field(ge=1, le=120)
weight: Field(ge=20.0, le=300.0)
height: Field(ge=100.0, le=250.0)
activity_level: ActivityLevel enum
gender: Gender enum ('male' | 'female')
```

---

## 🚀 **Post-Registration Flow**

### Current Implementation
```
1. User completes registration form (2 steps)
2. POST /auth/register → Creates user with biometric data
3. Automatic BMR/TDEE calculation on backend
4. Auto-login after successful registration  
5. JWT token saved to localStorage
6. Redirect to Dashboard
7. User authenticated and ready to use app
```

### Missing Features
- ❌ Email verification
- ❌ Profile image upload
- ❌ Terms & conditions acceptance
- ❌ Welcome onboarding flow

---

## 🌐 **API Endpoints**

### Authentication Routes
```http
POST /auth/register
Content-Type: application/json

Request Body:
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "age": 25,
  "gender": "male", 
  "weight": 70.0,
  "height": 175.0,
  "activity_level": 1.5
}

Response (201):
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "bmr": 1680.5,
  "tdee": 2520.8,
  "created_at": "2026-02-08T10:00:00Z"
}

Error Responses:
409 - Email already registered
400 - Biometric validation failed
422 - Invalid input data
```

```http
POST /auth/login
Content-Type: application/json

Request Body:
{
  "email": "user@example.com", 
  "password": "securepassword"
}

Response (200):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}

Error Response:
401 - Invalid credentials / Inactive user
```

### Protected Routes
```http
GET /users/me
Authorization: Bearer {token}

Response: UserResponse with biometric data

PUT /users/me/biometrics  
Authorization: Bearer {token}
Request: BiometricUpdate schema
Response: Updated user with recalculated BMR/TDEE
```

---

## ❌ **Error Handling**

### Custom Exception Hierarchy
```python
NovaFitnessException (Base)
├── UserAlreadyExistsError (409)
├── InvalidCredentialsError (401)  
├── InactiveUserError (401)
├── BiometricValidationError (400)
├── IncompleteBiometricDataError (400)
└── BiometricCalculationError (500)
```

### Frontend Error Messages
```typescript
// Specific error messages
"Email already registered"
"Incorrect email or password" 
"Password must be at least 8 characters"
"Passwords do not match"
"All biometric fields are required for accurate calculations"
"Invalid age range (1-120 years)"
"Invalid weight range (20-300 kg)"
"Invalid height range (100-250 cm)"
```

### Backend Error Responses
```json
// Validation Error (422)
{
  "detail": "Biometric validation failed",
  "errors": ["Age must be between 1 and 120"],
  "error_code": "BIOMETRIC_VALIDATION_ERROR"
}

// Conflict Error (409) 
{
  "detail": "Email already registered",
  "error_code": "USER_ALREADY_EXISTS"
}

// Unauthorized (401)
{
  "detail": "Could not validate credentials", 
  "error_code": "INVALID_TOKEN"
}
```

---

## 🧪 **Testing Configuration**

### Backend Testing (Implemented)
```python
# Framework: pytest + FastAPI TestClient
# Database: SQLite test database (isolated)
# Files:
- conftest.py          # Test configuration & fixtures
- test_auth.py         # Authentication endpoint tests  
- test_events.py       # Event management tests

# Test Database:
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" 
# Automatic setup/teardown per test
```

### Frontend Testing (Pending)
```typescript
// Recommended: Vitest + React Testing Library
// Missing test files:
- Login.test.tsx
- Register.test.tsx  
- AuthContext.test.tsx
- api.test.tsx

// Test coverage needed:
- Form validation
- Multi-step registration flow
- Error handling
- Authentication context
```

---

## 📂 **Project Structure**

```
NovaFitness/
├── app/                    # FastAPI Backend
│   ├── api/               # Route handlers
│   ├── core/              # Security & auth logic  
│   ├── db/                # Database models & config
│   ├── schemas/           # Pydantic validation schemas
│   ├── services/          # Business logic layer
│   └── tests/             # Backend tests
├── frontend/              # React Frontend
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── contexts/      # React Context providers
│       ├── pages/         # Route components (Login, Register, Dashboard)
│       ├── services/      # API client & HTTP logic
│       └── styles/        # CSS files
└── migrations/            # Database migrations
```

---

## 🔧 **RegisterFlow Branch - Planned Improvements**

### Priority 1: Enhanced Validation
- [ ] **Password strength:** Regex validation, special characters requirement
- [ ] **Email verification:** Send confirmation email with verification link  
- [ ] **Real-time validation:** Field-level validation feedback
- [ ] **Progress indicator:** Visual step progress in multi-step form

### Priority 2: User Experience  
- [ ] **Terms & conditions:** Checkbox with modal/link
- [ ] **Profile image upload:** Avatar selection during registration
- [ ] **Welcome flow:** Onboarding tutorial after registration
- [ ] **Social registration:** Google/Apple sign-in integration

### Priority 3: Testing & Quality
- [ ] **Frontend tests:** Vitest + React Testing Library setup
- [ ] **E2E tests:** Playwright/Cypress registration flow tests
- [ ] **Form validation tests:** Edge cases and error scenarios
- [ ] **API integration tests:** Full registration flow testing

### Priority 4: Advanced Features
- [ ] **Email templates:** Professional verification emails
- [ ] **Rate limiting:** Registration attempt limits
- [ ] **Analytics tracking:** Registration funnel metrics  
- [ ] **A/B testing:** Different registration flow variations

---

## 🚀 **Deployment & Environment**

### Development Setup
```bash
# Backend
python dev.py setup     # Install dependencies
python dev.py init-db   # Initialize database  
python dev.py server    # Start FastAPI (port 8000)

# Frontend  
cd frontend
npm install            # Install dependencies
npm run dev           # Start Vite dev server (port 3000)
```

### Production Considerations
- Environment variables for sensitive config
- Database migration strategy  
- HTTPS/SSL certificate setup
- CDN for static assets
- Backend scaling with gunicorn
- Frontend build optimization

---

## 📱 **Mobile-First Design**

### Current UI Features
- Responsive glassmorphism design
- Mobile-optimized touch targets
- Progressive Web App (PWA) ready
- Cross-platform compatibility
- Gradient backgrounds with glass effects
- Icon-based navigation

### Design System
- Primary colors: Blue gradients
- Typography: Modern, readable fonts
- Spacing: Consistent 8px grid system
- Components: Modular, reusable UI elements
- Accessibility: WCAG guidelines consideration

---

*Last updated: February 8, 2026*
*Branch: RegisterFlow*
*Status: Active Development*