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
│   ├── UI/              # Reusable UI components (Modal.tsx)
│   ├── DashboardHeader.tsx    # Fixed header with navigation & profile
│   ├── NutritionModule.tsx    # Meals tab with carousel & AI input
│   └── ...other components
├── contexts/            # React Context providers (AuthContext.tsx, ToastContext.tsx)
├── hooks/               # Custom React hooks (usePWAUpdate.ts)
├── pages/               # Page components (Dashboard.tsx, Login.tsx, Register.tsx)
├── services/            # API services (api.ts)
├── styles/              # Global styles (globals.css, component-specific styles)
├── App.tsx              # Main application component
└── main.tsx             # Application entry point with PWA registration
```

### Latest Components & Hooks (February 2026)

#### 🎯 **DashboardHeader.tsx**
- Fixed header with app branding, dynamic section titles
- Profile button with state indicator
- Logout button (triggers logout confirmation modal)
- Styled with gradient background and pill-shaped buttons

#### 🍽️ **NutritionModule.tsx** (Updated)
- Internal meal carousel using `translate3d` for GPU acceleration
- Touch swipe handlers optimized for performance
- Meal items with refined glassmorphic shadows
- AI voice parser integration

#### 🪝 **usePWAUpdate.ts** (New)
- Custom hook for PWA update detection
- Listens to service worker `onNeedRefresh` event
- Shows persistent toast notification: "¡Nueva versión disponible!"
- Auto-reloads page when user interacts with toast
- Integrated into `AppContent` component in App.tsx

#### 🌐 **PWA Service Worker Integration**
- Automatic SW registration via `virtual:pwa-register` module
- Manifest generation with metadata (192x512 icons, standalone mode)
- Workbox precaching with navigateFallbackDenylist for /api routes
- Periodic update checks (hourly by default)

### File Naming Conventions
```typescript
// ✅ PascalCase for components
Login.tsx
AuthContext.tsx
Modal.tsx
DashboardHeader.tsx

// ✅ camelCase for utilities and services
api.ts
authService.ts
usePWAUpdate.ts

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

> **`/api` baseURL and production routing**
>
> The axios instance uses `baseURL: '/api'`, so every request goes to `/api/v1/...`.
> In **development**, Vite's dev proxy (`vite.config.ts`) intercepts `/api/*` and forwards to `http://localhost:8000/*`, stripping the prefix — the backend sees `/v1/...`.
> In **production** (built PWA), there is no proxy. The request reaches the backend as `/api/v1/...`.
>
> **Consequence for backend developers:** Any FastAPI router whose `APIRouter` uses a `/v1/` prefix must be mounted twice in `main.py` — once without prefix and once with `prefix="/api"`. See `BACKEND_GUIDELINES.md → Register Router` for details.

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

## 🎨 **Theming System — 3 Themes**

NovaFitness tiene 3 temas que el usuario puede elegir. Todo nuevo componente o módulo **debe funcionar correctamente en los 3**. El tema activo se aplica como atributo `data-theme` en el elemento `<html>`.

### Temas disponibles

| Tema | `data-theme` | Paleta | Accent |
|---|---|---|---|
| **Original** | *(sin atributo / default)* | Fondo violeta/púrpura degradado | `#00f2c3` (cyan-verde) |
| **Dark** | `data-theme="dark"` | Fondo negro/carbón | `#00f5ff` (cyan eléctrico) |
| **Light** | `data-theme="light"` | Fondo cyan claro | `#00c8d8` (teal) |

### CSS Variables de tema — siempre usarlas

Nunca hardcodear colores en componentes nuevos. Usar siempre estas variables que se definen en `index.html`:

```css
/* Accent principal — cambia según el tema */
color: var(--theme-accent);               /* #00f2c3 / #00f5ff / #00c8d8 */
background: var(--theme-accent-glow);     /* glow suave del accent */
border-color: var(--theme-accent-border); /* borde semitransparente del accent */
background: var(--theme-accent-gradient); /* gradiente de 2 colores del tema */
background: var(--theme-accent-gradient-full); /* gradiente completo 3 colores */

/* Fondo de página */
background: var(--theme-bg-gradient);
background: var(--theme-bg-overlay);

/* Navegación inferior */
background: var(--theme-nav-bg);
color: var(--theme-nav-item-color);
color: var(--theme-nav-item-active-color);

/* Header */
background: var(--theme-header-bg);
color: var(--theme-header-text);
color: var(--theme-header-text-sub);

/* Botones del header */
background: var(--theme-header-btn-bg);
background: var(--theme-header-btn-active);
```

### Cómo escribir overrides de light mode

Los estilos base son para el tema Original/Dark (fondo oscuro, texto blanco). Al final de `globals.css` se agregan overrides específicos para light mode:

```css
/* ✅ Patrón correcto para soportar light mode */
.mi-componente-titulo {
  color: rgba(255, 255, 255, 0.9); /* base: dark/original */
}

.mi-componente-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: white;
}

/* Al final del archivo — overrides light */
[data-theme="light"] .mi-componente-titulo {
  color: rgba(10, 26, 30, 0.85); /* texto oscuro en fondo claro */
}

[data-theme="light"] .mi-componente-card {
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(10, 26, 30, 0.15);
  color: #0a1a1e;
}
```

### Paleta de colores por función (todos los temas)

Usar siempre colores del design system para pills y badges, no genéricos:

```css
/* Calorías / primario */   → rosa/magenta:  rgba(236, 72, 153, ...)  + rgba(168, 85, 247, ...)
/* Carbohidratos */          → cyan:          rgba(0, 242, 195, ...)   + rgba(6, 182, 212, ...)
/* Proteínas */              → violeta:       rgba(139, 92, 246, ...)  + rgba(99, 102, 241, ...)
/* Grasas / secundario */    → teal-azul:     rgba(6, 182, 212, ...)   + rgba(14, 165, 233, ...)
/* Quemado / negativo */     → rosa:          rgba(236, 72, 153, ...)
/* Neto / resultado */       → violeta:       rgba(139, 92, 246, ...)
```

### Logo

Usar siempre el componente SVG `<Logo>` de `components/Logo.tsx`. Toma el color del tema via `currentColor`:

```tsx
import Logo from '../components/Logo'

// En un header pequeño
<Logo size={28} className="mi-header-logo" />

// En una pantalla de inicio
<Logo size={120} className="mi-logo-grande" />
```

```css
/* En el CSS — solo asignar color y opcionalmente drop-shadow */
.mi-header-logo {
  color: var(--theme-accent);
  filter: drop-shadow(0 0 10px var(--theme-accent-glow));
}
```

---

## 🗂️ **Patrón de Tabs — Módulos y Perfil**

Todos los módulos con múltiples secciones deben usar el mismo patrón de tabs. **No inventar variantes nuevas.**

### Estructura JSX

```tsx
// ✅ Patrón estándar de tabs para módulos
type ModuleTab = 'seccion1' | 'seccion2'
const [activeTab, setActiveTab] = useState<ModuleTab>('seccion1')

// En el JSX:
<div className="module-tabs" role="tablist">
  <button
    className={`module-tab ${activeTab === 'seccion1' ? 'active' : ''}`}
    onClick={() => setActiveTab('seccion1')}
    role="tab"
    aria-selected={activeTab === 'seccion1'}
  >
    <IconName size={18} />
    <span>Sección 1</span>
  </button>
  <button
    className={`module-tab ${activeTab === 'seccion2' ? 'active' : ''}`}
    onClick={() => setActiveTab('seccion2')}
    role="tab"
    aria-selected={activeTab === 'seccion2'}
  >
    <OtroIcon size={18} />
    <span>Sección 2</span>
  </button>
</div>

{activeTab === 'seccion1' ? (
  <div>contenido sección 1</div>
) : (
  <div>contenido sección 2</div>
)}
```

### CSS — reutilizar siempre las clases existentes

Las clases `.module-tabs` y `.module-tab` ya están definidas en `globals.css` con soporte para los 3 temas. No crear nuevas variantes:

```css
/* ✅ Ya definido — solo usar */
.module-tabs        → contenedor flex de tabs
.module-tab         → botón individual (icon arriba + label + underline animado)
.module-tab.active  → tab seleccionado con accent color y underline
```

### Diseño visual del tab
- Ícono arriba, label abajo (columna)
- Estado activo: color `var(--theme-accent)` + borde inferior de 2px
- Estado inactivo: texto semitransparente, sin borde
- Transición suave `0.2s ease`
- En light mode: texto oscuro, activo en `--theme-accent` del tema claro

### Módulos existentes con tabs (referencia)

| Módulo | Tabs |
|---|---|
| `NutritionModule.tsx` | Mis Comidas · Mi Dieta |
| `WorkoutModule.tsx` | Mis Entrenos · Mi Rutina |
| `ProfileBiometricsPanel.tsx` | Datos personales · Metas nutricionales · Pliegues cutáneos |

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

*Based on NovaFitness codebase — Updated March 2026*
*Version: 2.0 — Theming system + Tab pattern added*