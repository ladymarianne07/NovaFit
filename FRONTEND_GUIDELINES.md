# Frontend Development Guidelines - NovaFitness

## 📋 **Overview**

Este documento establece las pautas de desarrollo frontend para NovaFitness basadas en el código existente y los patrones implementados.

---

## 🎯 **Technology Stack**

### Core Technologies
- **React 18** con Functional Components
- **TypeScript** para type safety
- **Vite** como build tool
- **React Router DOM** para routing
- **Axios** para HTTP requests
- **Context API** para state management

### Styling Approach
- **CSS Custom Properties** (CSS Variables)
- **Utility-first CSS classes** 
- **Component-scoped CSS** files
- **Mobile-first responsive design**

---

## 🏗️ **Project Structure**

### Current Directory Organization
```
frontend/src/
├── components/
│   ├── pages/           # Route-level components (Login.tsx, Register.tsx)
│   └── UI/              # Reusable UI components (Modal.tsx)
├── contexts/            # React Context providers (AuthContext.tsx)
├── pages/               # Page components (Dashboard.tsx, Login.tsx, Register.tsx)
├── services/            # API services (api.ts)
├── styles/              # Global styles (globals.css)
├── App.tsx              # Main application component
└── main.tsx             # Application entry point
```

### File Naming Conventions
```typescript
// ✅ PascalCase for components
Login.tsx
AuthContext.tsx
Modal.tsx

// ✅ camelCase for utilities and services
api.ts
authService.ts

// ✅ kebab-case for CSS files
globals.css
modal.css
```

---

## ⚛️ **React Component Patterns**

### 1. Functional Components with TypeScript

```typescript
// ✅ Always define props interface
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCloseButton?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

// ✅ Use React.FC with proper typing
const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  variant = 'default',
}) => {
  // Component logic
};
```

### 2. Component Documentation
```typescript
/**
 * Modal Component - Reusable modal dialog
 * Following NovaFitness design guidelines
 */
```

### 3. Props Patterns
```typescript
// ✅ Use union types for variants
variant?: 'default' | 'success' | 'warning' | 'danger';

// ✅ Use enums for sizes
size?: 'sm' | 'md' | 'lg' | 'xl';

// ✅ Always include children for container components
children: React.ReactNode;

// ✅ Use optional props with default values
showCloseButton?: boolean;
```

---

## 🔧 **State Management**

### 1. Context API Pattern
```typescript
// ✅ Define context interface
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
}

// ✅ Create context with undefined default
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ✅ Custom hook for context consumption
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 2. Component State
```typescript
// ✅ Use useState with proper typing
const [isLoading, setIsLoading] = useState<boolean>(false);
const [error, setError] = useState<string>('');
const [formData, setFormData] = useState<LoginFormData>({
  email: '',
  password: ''
});

// ✅ Use useEffect for side effects
useEffect(() => {
  const handleEscape = (event: KeyboardEvent) => {
    if (event.key === 'Escape' && isOpen) {
      onClose();
    }
  };

  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [isOpen, onClose]);
```

---

## 🌐 **API Integration**

### 1. Axios Configuration
```typescript
// ✅ Create configured axios instance
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ✅ Request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ✅ Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 2. Type Definitions
```typescript
// ✅ Define API response interfaces
export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  created_at: string;
  age?: number;
  gender?: 'male' | 'female';
  weight?: number;
  height?: number;
  activity_level?: number;
  bmr?: number;
  tdee?: number;
}

// ✅ Define request interfaces
export interface LoginRequest {
  username: string; // Note: backend expects 'username' field for email
  password: string;
}
```

### 3. API Service Class
```typescript
// ✅ Organize API methods in classes
class AuthAPI {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  }

  async register(userData: RegisterRequest): Promise<User> {
    const response = await api.post('/auth/register', userData);
    return response.data;
  }
}

export const authAPI = new AuthAPI();
```

---

## 🎨 **Styling Guidelines**

### 1. CSS Custom Properties
```css
/* ✅ Define design system variables */
:root {
  /* Colors */
  --color-primary: #ec4899;
  --color-secondary: #8b5cf6;
  --color-neutral-50: #f9fafb;
  --color-neutral-100: #f3f4f6;
  
  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  
  /* Border radius */
  --radius: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  
  /* Shadows */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
}
```

### 2. Component CSS Classes
```css
/* ✅ Use BEM-like naming for components */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--shadow);
}

.btn-secondary {
  background: white;
  color: var(--color-neutral-700);
  border: 1px solid var(--color-neutral-200);
}
```

### 3. Mobile-First Responsive Design
```css
/* ✅ Start with mobile styles */
.login-container {
  padding: 1rem;
  min-height: 100vh;
}

/* ✅ Add desktop improvements */
@media (min-width: 768px) {
  .login-container {
    padding: 2rem;
    max-width: 400px;
    margin: 0 auto;
  }
}
```

---

## 🛣️ **Routing Patterns**

### 1. Route Protection
```typescript
// ✅ Protected route wrapper component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  return user ? <>{children}</> : <Navigate to="/login" />;
}

// ✅ Public route wrapper component (redirect if authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  return !user ? <>{children}</> : <Navigate to="/dashboard" />;
}
```

### 2. Route Configuration
```typescript
// ✅ Organize routes with proper nesting
<Routes>
  <Route 
    path="/login" 
    element={
      <PublicRoute>
        <Login />
      </PublicRoute>
    } 
  />
  <Route 
    path="/register" 
    element={
      <PublicRoute>
        <Register />
      </PublicRoute>
    } 
  />
  <Route 
    path="/dashboard" 
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    } 
  />
  <Route path="/" element={<Navigate to="/dashboard" />} />
</Routes>
```

---

## 📝 **Form Handling**

### 1. Form State Management
```typescript
// ✅ Define form data interface
interface LoginFormData {
  email: string;
  password: string;
}

// ✅ Use controlled components
const [formData, setFormData] = useState<LoginFormData>({
  email: '',
  password: ''
});

// ✅ Generic input handler
const handleInputChange = (field: keyof LoginFormData) => 
  (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };
```

### 2. Form Validation
```typescript
// ✅ Validation functions
const validateStep1 = (): boolean => {
  if (!email || !password || !confirmPassword) {
    setError('All fields are required');
    return false;
  }
  if (password !== confirmPassword) {
    setError('Passwords do not match');
    return false;
  }
  if (password.length < 8) {
    setError('Password must be at least 8 characters');
    return false;
  }
  return true;
};
```

### 3. Form Submission
```typescript
// ✅ Async form submission with error handling
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);
  setError('');

  try {
    await login({
      username: formData.email,
      password: formData.password
    });
    // Success handled by context/redirect
  } catch (error) {
    setError(error instanceof Error ? error.message : 'Login failed');
  } finally {
    setIsLoading(false);
  }
};
```

---

## ❌ **Error Handling**

### 1. Component Error Boundaries
```typescript
// ✅ Error state in components
const [error, setError] = useState<string>('');

// ✅ Clear error on input change
const handleInputChange = (field: keyof FormData) => 
  (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(''); // Clear error when user starts typing
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };
```

### 2. API Error Handling
```typescript
// ✅ Type-safe error handling
try {
  const result = await apiCall();
  return result;
} catch (error) {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.detail || error.message;
    throw new Error(message);
  }
  throw new Error('An unexpected error occurred');
}
```

### 3. User Feedback
```typescript
// ✅ Show user-friendly error messages
{error && (
  <div className="error-message" role="alert">
    {error}
  </div>
)}

// ✅ Loading states
{isLoading ? (
  <div className="btn-loading">
    <LoadingSpinner /> Processing...
  </div>
) : (
  <button type="submit" className="btn btn-primary">
    Submit
  </button>
)}
```

---

## 🔒 **Authentication Patterns**

### 1. Token Management
```typescript
// ✅ Token storage
localStorage.setItem('access_token', response.access_token);

// ✅ Token removal
const logout = () => {
  localStorage.removeItem('access_token');
  setUser(null);
};

// ✅ Token validation on app load
useEffect(() => {
  const initAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
      } catch (error) {
        localStorage.removeItem('access_token');
      }
    }
    setIsLoading(false);
  };

  initAuth();
}, []);
```

### 2. Automatic Login After Registration
```typescript
// ✅ Seamless registration flow
const register = async (userData: RegisterRequest): Promise<void> => {
  try {
    const newUser = await authAPI.register(userData);
    // Auto login after registration
    await login({
      username: userData.email,
      password: userData.password
    });
  } catch (error) {
    throw error;
  }
};
```

---

## 🧪 **Component Testing Guidelines**

### 1. Test File Structure
```typescript
// ✅ Test file naming
Login.test.tsx
AuthContext.test.tsx
api.test.ts

// ✅ Test organization (when implemented)
describe('Login Component', () => {
  test('renders login form', () => {
    // Test implementation
  });
  
  test('validates required fields', () => {
    // Test implementation
  });
});
```

### 2. Testing Patterns (Future Implementation)
```typescript
// ✅ Recommended testing approach
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';

// ✅ Test wrapper for context providers
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};
```

---

## 🚀 **Performance Guidelines**

### 1. Component Optimization
```typescript
// ✅ Use React.memo for expensive components
const ExpensiveComponent = React.memo<Props>(({ data }) => {
  return <div>{/* Expensive rendering */}</div>;
});

// ✅ Proper dependency arrays in useEffect
useEffect(() => {
  // Side effect logic
}, [dependency1, dependency2]); // Only re-run when dependencies change
```

### 2. Bundle Optimization
```typescript
// ✅ Lazy loading for routes (future enhancement)
const Dashboard = React.lazy(() => import('./pages/Dashboard'));

// ✅ Use Suspense for loading states
<Suspense fallback={<LoadingSpinner />}>
  <Dashboard />
</Suspense>
```

---

## 📚 **Best Practices Summary**

### TypeScript
- ✅ Always define interfaces for component props
- ✅ Use strict typing for API responses
- ✅ Prefer union types over enums for simple variants
- ✅ Use optional props with default values

### React Patterns
- ✅ Functional components with hooks
- ✅ Custom hooks for reusable logic
- ✅ Context API for global state
- ✅ Proper cleanup in useEffect

### Code Organization
- ✅ One component per file
- ✅ Co-locate related files (component + styles)
- ✅ Separate business logic from UI components
- ✅ Use barrel exports for clean imports

### Styling
- ✅ CSS custom properties for design system
- ✅ Mobile-first responsive design
- ✅ Component-scoped CSS classes
- ✅ Consistent naming conventions

### Error Handling
- ✅ User-friendly error messages
- ✅ Loading states for async operations
- ✅ Proper error boundaries
- ✅ Graceful degradation

---

*Based on NovaFitness codebase - February 8, 2026*
*Branch: RegisterFlow*
*Version: 1.0*