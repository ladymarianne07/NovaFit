# NovaFitness - Full Stack Fitness Tracking Application

A comprehensive fitness tracking web application with biometric calculations (BMR/TDEE), built with FastAPI backend and React TypeScript frontend.

## ✨ Recent Improvements (February 2026)

### 🎯 **Latest Sprint - PWA & UI/UX Polish**

#### 🔐 **Enhanced User Experience**
- **Logout Confirmation Modal**: Added styled confirmation popup when users click logout button
  - Implemented in [Dashboard.tsx](frontend/src/pages/Dashboard.tsx) with glassmorphic design
  - Matches app's visual theme with gradient background and smooth animations

#### 📱 **Navigation Improvements**
- **Dashboard Slide Navigation Refactor**: Separated profile from slide carousel
  - Profile now rendered independently (not part of swipe order)
  - Main tabs order: Dashboard → Comidas → Entreno → Progreso
  - Improved touch handling with GPU acceleration (`translate3d`)
- **DashboardHeader Component**: New fixed header with navigation, profile button, and logout trigger
  - Integrates app branding, dynamic section titles, and user state indicator

#### 🎨 **Visual Polish & Performance**
- **Fixed Slide Rendering Seams**: Eliminated subpixel rendering artifacts in Comidas tab
  - Applied GPU acceleration: `translate3d(0)`, `will-change: transform`, `backface-visibility`
  - Added paint containment: `contain: paint`, `isolation: isolate`
  - Modified [Dashboard.tsx](frontend/src/pages/Dashboard.tsx) and [NutritionModule.tsx](frontend/src/components/NutritionModule.tsx)
  
- **Card Styling Refinement**: Improved shadows for glassmorphic aesthetic
  - Removed corner artifacts: Changed from `overflow: hidden` → `overflow: visible`
  - Refined shadow hierarchy: Inset highlights + subtle offset shadows
  - Updated [globals.css](frontend/src/styles/globals.css) nutrition card styles

#### 🌐 **Progressive Web App (PWA) Conversion**
- **Full PWA Implementation**:
  - Installed `vite-plugin-pwa` v1.2.0 with automatic configuration
  - Configured manifest.webmanifest with theme colors, icons, standalone display mode
  - Generated Service Worker (SW) with Workbox precaching (11 entries, 382.92 KiB)
  - Created 3 SVG icon assets: 192x192, 512x512, maskable-512 (adaptive icons)
  
- **PWA Files**:
  - [vite.config.ts](frontend/vite.config.ts): VitePWA plugin with manifest & workbox settings
  - [index.html](frontend/index.html): Added theme-color meta tags, manifest link, apple icons
  - [main.tsx](frontend/src/main.tsx): Service worker registration with `registerSW()`
  - [public/icons/](frontend/public/icons/): SVG icon assets

- **Update Notification System**:
  - Created [usePWAUpdate.ts](frontend/src/hooks/usePWAUpdate.ts) hook for SW update detection
  - Integrated into [App.tsx](frontend/src/App.tsx) via `AppContent` component
  - Shows persistent toast: "¡Nueva versión disponible!" when update detected
  - Auto-reloads page to activate new SW after user interaction
  - Configuration: `registerType: 'autoUpdate'`, `skipWaiting: false` (manual trigger)
  - Periodic update checks: Every 3600 seconds (hourly)

#### ✅ **Build Verification**
- All changes compile successfully (TypeScript check passed)
- Build output: 1439 modules transformed, 305.95 kB main JS bundle (95.42 kB gzipped)
- PWA precache: 11 entries generated (manifest.webmanifest, sw.js, workbox bundles)
- No regressions in existing functionality

### 🔧 **Bug Fixes & Refactoring**
- **Fixed Authentication Flow**: Resolved login API mismatch (`username` vs `email`)
- **Enhanced Error Handling**: Added RequestValidationError handler for proper error responses
- **Code Cleanup**: Removed unused files (`App.css`, duplicate `exceptions.py`)
- **Error Boundary**: Added React Error Boundary for graceful error handling

### 🚀 **Best Practices Applied**
- **Accessibility**: Improved Input components with aria-labels for screen readers
- **Type Safety**: Maintained strong typing across frontend and backend
- **Exception Handling**: Centralized error handling with user-friendly messages
- **Code Organization**: Clean separation of concerns in API, service, and data layers

### 📋 **Architecture Notes**
- **Events API**: Fully implemented backend ready for future frontend integration
- **Validation Logic**: Intentional duplication between frontend/backend for UX (immediate validation)
- **Error Consistency**: Standardized error response format across all endpoints

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Installation & Setup

**Backend Setup:**
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies and setup
python dev.py setup

# Initialize database
python dev.py init-db

# Run migrations (if needed)
python dev.py migrate
```

**Frontend Setup:**
```bash
cd frontend
npm install
```

### Running the Application

Using VS Code tasks (recommended):
```bash
# Start both backend and frontend simultaneously  
Ctrl+Shift+P → "Tasks: Run Task" → "🔥 Start Full Stack"
```

Or manually:
```bash
# Terminal 1 - Backend
python dev.py server

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI + Python 3.12
- **Database**: SQLite (development) → PostgreSQL (production ready)
- **ORM**: SQLAlchemy 2.0 with migrations support
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic schemas with comprehensive business rules
- **API**: RESTful design with OpenAPI documentation

### Frontend  
- **Framework**: React 18 + TypeScript + Vite
- **Routing**: React Router DOM with protected routes
- **State Management**: React Context API
- **HTTP Client**: Axios with interceptors
- **Icons**: Lucide React
- **Styling**: CSS with Glassmorphism effects
- **Testing**: Jest + Testing Library

## 📋 Features

### ✅ Implemented Features
- **User Authentication**: Registration, login, JWT-based sessions
- **Biometric Tracking**: BMR/TDEE calculations using Mifflin-St Jeor equation
- **Profile Management**: Complete user profile with biometric updates
- **Responsive UI**: Mobile-first design with glassmorphism effects
- **Form Validation**: Client-side and server-side validation
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Security**: Password hashing, CORS, input sanitization

### 🔄 Future-Ready Features (Backend Implemented)
- **Events/Activities API**: Complete CRUD operations for fitness events
- **Timeline Tracking**: Append-only event logging with timestamps  
- **Data Analytics**: Event statistics and aggregations
- **Flexible Event Schema**: JSON payload support for extensible data

## 🏗️ Project Architecture

### Backend Structure
```
app/
├── main.py              # FastAPI app with middleware and exception handlers
├── config.py            # Environment configuration
├── dependencies.py      # Dependency injection for services
├── api/                 # API route handlers
│   ├── auth.py          # Authentication endpoints (/auth/*)
│   ├── users.py         # User management (/users/*)
│   └── events.py        # Events API (/events/*) - Ready for frontend
├── core/                # Core business logic
│   ├── auth.py          # JWT token handling
│   ├── security.py      # Password hashing utilities
│   └── custom_exceptions.py  # Application-specific exceptions
├── db/                  # Database layer
│   ├── database.py      # Connection and session management
│   ├── models.py        # SQLAlchemy ORM models
│   └── init_db.py       # Database initialization
├── schemas/             # Pydantic request/response models
│   ├── user.py          # User schemas with validation
│   └── event.py         # Event schemas (ready for frontend)
├── services/            # Business logic services
│   ├── user_service.py      # User management operations
│   ├── biometric_service.py # BMR/TDEE calculations
│   └── validation_service.py # Input validation logic
└── tests/               # Backend test suite
```

### Frontend Structure
```
frontend/src/
├── App.tsx              # Main app with error boundaries
├── main.tsx             # React entry point
├── components/          # Reusable UI components
│   ├── UI/              # Base UI components (Button, Input, FormField)
│   └── ErrorBoundary.tsx # Global error handling
├── contexts/            # React Context providers
│   └── AuthContext.tsx  # Authentication state management
├── pages/               # Route components
│   ├── Login.tsx        # Login form with validation
│   ├── Register.tsx     # Two-step registration flow
│   └── Dashboard.tsx    # User dashboard with profile editing
├── services/            # API layer
│   ├── api.ts           # Axios setup and API endpoints
│   └── validation.ts    # Client-side validation rules
├── styles/              # CSS styling
└── tests/               # Frontend test suite
```

## 🔒 Security & Best Practices

### Implemented Security Features
- **Authentication**: JWT tokens with secure storage
- **Password Security**: bcrypt hashing with salt rounds
- **Input Validation**: Both client-side (UX) and server-side (security)  
- **CORS Protection**: Configured for cross-origin requests
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Error Handling**: Structured error responses without sensitive data leaks

### Code Quality Features  
- **Type Safety**: Full TypeScript frontend + Pydantic backend
- **Error Boundaries**: React error boundaries for graceful failure handling
- **Exception Handling**: Comprehensive custom exception hierarchy
- **Validation Consistency**: Matching validation rules between frontend/backend
- **Code Organization**: Clean separation of concerns with service layers
│   ├── __init__.py
│   ├── user.py          # User schemas
│   └── event.py         # Event schemas
└── tests/               # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    └── test_events.py
```

## MVP vs Future-Ready

### MVP Features ✓
- SQLite database
- Basic JWT auth
- User registration/login
- Event CRUD operations
- Data isolation per user

### Future Enhancements 🔄
- PostgreSQL migration
- Refresh token rotation
- Rate limiting
- Event aggregations/analytics
- Real-time notifications
- Cloud deployment scripts

## Security Considerations

- Passwords hashed with bcrypt
- JWT tokens with 1-year expiration (persistent sessions)
- CORS configured for PWA
- SQL injection protection via ORM
- User data isolation enforced at DB level

**Session Management**: Users remain logged in until they manually log out or their browser data is cleared. This provides a seamless PWA experience without frequent re-authentication.

## Database Migration Path

The codebase is designed to switch from SQLite to PostgreSQL by simply changing the `DATABASE_URL` in configuration. All SQL operations use SQLAlchemy ORM for database independence.