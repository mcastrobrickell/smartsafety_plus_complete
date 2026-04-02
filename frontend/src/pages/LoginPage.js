import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Shield, User, HardHat, ArrowLeft, LogIn } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('admin');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Bienvenido, ${user.name}`);
      
      if (user.role === 'superadmin') {
        navigate('/superadmin');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Credenciales inválidas');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col relative" data-testid="login-page">
      {/* Background grid and glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[60%] h-[400px] bg-gradient-radial from-cyan-accent/8 via-transparent to-transparent" />
      </div>

      {/* Back Link */}
      <div className="p-6 relative z-10">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-slate-500 hover:text-cyan-accent transition-colors"
          data-testid="back-to-home"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>
      </div>

      {/* Login Form */}
      <div className="flex-1 flex items-center justify-center px-6 pb-12 relative z-10">
        <div className="w-full max-w-md">
          <div className="card-dark p-8 animate-fade-in">
            {/* Logo */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-gradient-tech rounded-2xl flex items-center justify-center shadow-glow-cyan animate-glow">
                <Shield className="w-8 h-8 text-dark-bg" />
              </div>
            </div>

            {/* Brand Name */}
            <h1 className="text-2xl font-bold text-center mb-8 font-display">
              <span className="text-white">Smart</span>
              <span className="logo-gradient">Safety+</span>
            </h1>

            {/* User Type Tabs */}
            <div className="flex bg-dark-input rounded-lg p-1 mb-6 border border-cyan-accent/10">
              <button
                type="button"
                onClick={() => setUserType('admin')}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-md text-sm font-medium transition-all ${
                  userType === 'admin'
                    ? 'bg-gradient-tech text-dark-bg shadow-glow-cyan'
                    : 'text-slate-400 hover:text-cyan-accent'
                }`}
                data-testid="tab-admin"
              >
                <User className="w-4 h-4" />
                Administrador
              </button>
              <button
                type="button"
                onClick={() => setUserType('colaborador')}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-md text-sm font-medium transition-all ${
                  userType === 'colaborador'
                    ? 'bg-gradient-tech text-dark-bg shadow-glow-cyan'
                    : 'text-slate-400 hover:text-cyan-accent'
                }`}
                data-testid="tab-colaborador"
              >
                <HardHat className="w-4 h-4" />
                Colaborador
              </button>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email" className="form-label">
                  Correo Electrónico
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  data-testid="login-email-input"
                  className="form-input h-12"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="form-label">
                  Contraseña
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  data-testid="login-password-input"
                  className="form-input h-12"
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 btn-primary font-semibold text-base gap-2"
                disabled={isLoading}
                data-testid="login-submit-btn"
              >
                <LogIn className="w-5 h-5" />
                {isLoading ? 'INGRESANDO...' : 'INICIAR SESIÓN'}
              </Button>
            </form>

            {/* Help Text */}
            <p className="text-center text-sm text-slate-500 mt-6 font-body">
              Solicita tus credenciales al administrador de tu empresa
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
