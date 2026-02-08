/**
 * Register Component - NovaFitness Registration
 * Cartoon-style registration page with biometric data collection
 */
import React, { useState } from 'react';
import { Button, Input, Card } from '../UI';
import { apiService, RegisterRequest } from '../../services/api';
import './Register.css';

interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  // Biometric data required for BMR/TDEE calculation
  weight: string;
  height: string;
  age: string;
  gender: string;
  activity_level: string;
}

const Register: React.FC = () => {
  const [formData, setFormData] = useState<RegisterFormData>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    weight: '',
    height: '',
    age: '',
    gender: '',
    activity_level: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [errors, setErrors] = useState<Partial<RegisterFormData>>({});

  const handleInputChange = (field: keyof RegisterFormData) => (value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<RegisterFormData> = {};

    if (!formData.username.trim()) {
      newErrors.username = 'El nombre de usuario es requerido';
    }

    if (!formData.full_name.trim()) {
      newErrors.full_name = 'El nombre completo es requerido';
    }

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

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }

    if (!formData.weight) {
      newErrors.weight = 'El peso es requerido';
    } else if (isNaN(Number(formData.weight)) || Number(formData.weight) <= 0) {
      newErrors.weight = 'Ingresa un peso válido';
    }

    if (!formData.height) {
      newErrors.height = 'La altura es requerida';
    } else if (isNaN(Number(formData.height)) || Number(formData.height) <= 0) {
      newErrors.height = 'Ingresa una altura válida';
    }

    if (!formData.age) {
      newErrors.age = 'La edad es requerida';
    } else if (isNaN(Number(formData.age)) || Number(formData.age) <= 0) {
      newErrors.age = 'Ingresa una edad válida';
    }

    if (!formData.gender) {
      newErrors.gender = 'El género es requerido';
    }

    if (!formData.activity_level) {
      newErrors.activity_level = 'El nivel de actividad es requerido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRegister = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError('');
    
    try {
      const registerData: RegisterRequest = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        weight: parseFloat(formData.weight),
        height: parseFloat(formData.height),
        age: parseInt(formData.age),
        gender: formData.gender,
        activity_level: formData.activity_level
      };

      const user = await apiService.register(registerData);
      setSuccess(true);
      alert(`¡Bienvenido ${user.username}! Cuenta creada exitosamente 🎉`);
      
      // Redireccionar al dashboard después de 2 segundos
      setTimeout(() => {
        window.location.href = '/dashboard'; // Cambiaremos por routing después
      }, 2000);
      
    } catch (error: any) {
      setError(error.message || 'Error al crear la cuenta. Por favor intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = () => {
    // TODO: Navigate to login page
    console.log('Navigate to login');
  };

    <div className="register-page">
      <div className="register-container">
        {/* Logo and Welcome */}
        <div className="register-header">
          <div className="register-logo">
            🏆️‍♂️
          </div>
          <h1 className="register-title">NovaFitness</h1>
          <p className="register-subtitle">¡Crea tu cuenta y comienza tu transformación!</p>
        </div>

        {/* Register Form */}
        <Card variant="elevated" padding="xl" className="register-card">
          <div className="register-form">
            <h2 className="register-form-title">Crear Cuenta</h2>
            
            {/* Account Information */}
            <div className="register-section">
              <h3 className="register-section-title">Información de Cuenta</h3>
              <div className="register-form-fields">
                <Input
                  type="text"
                  placeholder="Nombre de usuario"
                  value={formData.username}
                  onChange={handleInputChange('username')}
                  error={errors.username}
                  fullWidth
                />

                <Input
                  type="text"
                  placeholder="Nombre completo"
                  value={formData.full_name}
                  onChange={handleInputChange('full_name')}
                  error={errors.full_name}
                  fullWidth
                />

                <Input
                  type="email"
                  placeholder="Tu email"
                  value={formData.email}
                  onChange={handleInputChange('email')}
                  error={errors.email}
                  fullWidth
                />

                <Input
                  type="password"
                  placeholder="Tu contraseña"
                  value={formData.password}
                  onChange={handleInputChange('password')}
                  error={errors.password}
                  fullWidth
                />

                <div className="md:col-span-2">
                  <Input
                    id="confirmPassword"
                    label="Confirmar contraseña"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleInputChange('confirmPassword')}
                    error={errors.confirmPassword}
                    required
                  />
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-semibold text-[var(--color-secondary)] mb-4">
                📊 Información Biométrica
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  id="weight"
                  label="Peso (kg)"
                  type="number"
                  placeholder="70"
                  value={formData.weight}
                  onChange={handleInputChange('weight')}
                  error={errors.weight}
                  required
                />

                <Input
                  id="height"
                  label="Altura (cm)"
                  type="number"
                  placeholder="175"
                  value={formData.height}
                  onChange={handleInputChange('height')}
                  error={errors.height}
                  required
                />

                <Input
                  id="age"
                  label="Edad"
                  type="number"
                  placeholder="25"
                  value={formData.age}
                  onChange={handleInputChange('age')}
                  error={errors.age}
                  required
                />

                <div className="mb-4">
                  <label className="block text-sm font-medium text-[var(--color-primary)] mb-1">
                    Género <span className="text-[var(--color-destructive)] ml-1">*</span>
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => handleInputChange('gender')(e.target.value)}
                    className={`
                      block w-full px-3 py-2 bg-[var(--color-bg-input)] border rounded-[var(--rounded-input)]
                      shadow-[var(--shadow-sm)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)]
                      focus:border-[var(--color-border-focus)] sm:text-sm text-[var(--color-text-default)]
                      transition-colors duration-200 ${
                        errors.gender 
                          ? 'border-[var(--color-border-error)] ring-1 ring-[var(--color-border-error)]'
                          : 'border-[var(--color-border-input)]'
                      }
                    `}
                  >
                    <option value="">Selecciona género</option>
                    <option value="male">Masculino</option>
                    <option value="female">Femenino</option>
                  </select>
                  {errors.gender && (
                    <p className="mt-1 text-sm text-[var(--color-destructive)]" role="alert">
                      {errors.gender}
                    </p>
                  )}
                </div>

                <div className="md:col-span-2 mb-4">
                  <label className="block text-sm font-medium text-[var(--color-primary)] mb-1">
                    Nivel de actividad <span className="text-[var(--color-destructive)] ml-1">*</span>
                  </label>
                  <select
                    value={formData.activity_level}
                    onChange={(e) => handleInputChange('activity_level')(e.target.value)}
                    className={`
                      block w-full px-3 py-2 bg-[var(--color-bg-input)] border rounded-[var(--rounded-input)]
                      shadow-[var(--shadow-sm)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)]
                      focus:border-[var(--color-border-focus)] sm:text-sm text-[var(--color-text-default)]
                      transition-colors duration-200 ${
                        errors.activity_level 
                          ? 'border-[var(--color-border-error)] ring-1 ring-[var(--color-border-error)]'
                          : 'border-[var(--color-border-input)]'
                      }
                    `}
                  >
                    <option value="">Selecciona nivel de actividad</option>
                    <option value="1.2">Sedentario (poco o ningún ejercicio)</option>
                    <option value="1.375">Ligeramente activo (ejercicio ligero 1-3 días/semana)</option>
                    <option value="1.55">Moderadamente activo (ejercicio moderado 3-5 días/semana)</option>
                    <option value="1.725">Muy activo (ejercicio intenso 6-7 días/semana)</option>
                    <option value="1.9">Extremadamente activo (ejercicio muy intenso o trabajo físico)</option>
                  </select>
                  {errors.activity_level && (
                    <p className="mt-1 text-sm text-[var(--color-destructive)]" role="alert">
                      {errors.activity_level}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-4 p-3 bg-[var(--color-destructive-bg-subtle)] border border-[var(--color-destructive)] rounded-[var(--rounded-input)] text-[var(--color-destructive)]">
                ❌ {error}
              </div>
            )}

            {/* Success Display */}
            {success && (
              <div className="mb-4 p-3 bg-green-100 border border-green-400 rounded-[var(--rounded-input)] text-green-700">
                ✅ ¡Cuenta creada exitosamente! Redirigiendo...
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={loading}
              >
                {loading ? 'Creando cuenta...' : 'Crear Cuenta'}
              </Button>
              
              <Button
                variant="secondary"
                size="lg"
                fullWidth
                onClick={handleLogin}
              >
                Ya tengo cuenta
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default Register;