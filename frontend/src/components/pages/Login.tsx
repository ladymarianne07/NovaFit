/**
 * Login Component - NovaFitness Authentication
 * Cartoon-style login page with biometric data collection
 */
import React, { useState } from 'react';
import { Button, Input, Card } from '../UI';
import './Login.css';

interface LoginFormData {
  email: string;
  password: string;
}

const Login: React.FC = () => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<LoginFormData>>({});

  const handleInputChange = (field: keyof LoginFormData) => (value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<LoginFormData> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Ingresa un email válido';
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      // TODO: Implement actual login logic
      console.log('Login:', formData);
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API call
      
      // Navigate to dashboard or profile setup
      alert('¡Bienvenido a NovaFitness! 🏋️‍♂️');
    } catch (error) {
      console.error('Login error:', error);
      alert('Error al iniciar sesión. Por favor intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    // TODO: Navigate to register page
    console.log('Navigate to register');
  };

  const handleForgotPassword = () => {
    // TODO: Implement forgot password
    console.log('Forgot password');
  };

  return (
      <div className="login-page">
      <div className="login-container">
        {/* Logo and Welcome */}
        <div className="login-header">
          <div className="login-logo">
            🏆️‍♂️
          </div>
          <h1 className="login-title">NovaFitness</h1>
          <p className="login-subtitle">Inicia sesión en tu cuenta</p>
        </div>

        {/* Login Form */}
        <Card variant="elevated" padding="xl" className="login-card">
          <form className="login-form" onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
            <h2 className="login-form-title">Iniciar Sesión</h2>
            
            <div className="login-form-fields">
              <Input
                label="Email"
                type="email"
                placeholder="tu@email.com"
                value={formData.email}
                onChange={handleInputChange('email')}
                error={errors.email}
                required
                fullWidth
              />

              <Input
                label="Contraseña"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleInputChange('password')}
                error={errors.password}
                required
                fullWidth
              />
            </div>

            <div className="login-form-actions">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={loading}
              >
                {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
              </Button>

              <button
                type="button"
                className="login-forgot-password"
                onClick={handleForgotPassword}
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>

            <div className="login-register-link">
              <p>
                ¿No tienes una cuenta?{' '}
                <button
                  type="button"
                  className="login-register-btn"
                  onClick={handleRegister}
                >
                  Regístrate aquí
                </button>
              </p>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
        {/* Logo and Welcome */}
        <div className="login-header">
          <div className="login-logo">
            🏋️‍♂️
          </div>
          <h1 className="login-title">NovaFitness</h1>
          <p className="login-subtitle">¡Transforma tu vida, alcanza tus metas!</p>
        </div>

        {/* Login Form */}
        <Card variant="elevated" padding="xl" className="login-card">
          <div className="login-form">
            <h2 className="login-form-title">Iniciar Sesión</h2>
            
            <div className="login-form-fields">
              <Input
                type="email"
                placeholder="Tu email"
                value={formData.email}
                onChange={handleInputChange('email')}
                error={errors.email}
              />

              <Input
                type="password"
                placeholder="Tu contraseña"
                value={formData.password}
                onChange={handleInputChange('password')}
                error={errors.password}
              />

              <button 
                className="login-forgot-password"
                onClick={handleForgotPassword}
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>

            <div className="login-form-actions">
              <Button
                variant="primary"
                size="md"
                loading={loading}
                onClick={handleLogin}
              >
                Iniciar Sesión
              </Button>
              
              <Button
                variant="primary"
                size="md"
                onClick={handleRegister}
              >
                Crear Cuenta
              </Button>
            </div>
          </div>
        </Card>


      </div>
    </div>
  );
};

export default Login;