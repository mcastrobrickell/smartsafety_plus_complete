import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent } from '../components/ui/card';
import { Shield, User, HardHat, ArrowLeft, LogIn } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('admin'); // 'admin' or 'colaborador'
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Bienvenido, ${user.name}`);
      
      // Redirect based on role
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
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid="login-page">
      {/* Back Link */}
      <div className="p-6">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
          data-testid="back-to-home"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>
      </div>

      {/* Login Form */}
      <div className="flex-1 flex items-center justify-center px-6 pb-12">
        <Card className="w-full max-w-md border-slate-200 shadow-xl">
          <CardContent className="p-8">
            {/* Logo */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center shadow-lg">
                <Shield className="w-8 h-8 text-white" />
              </div>
            </div>

            {/* Brand Name */}
            <h1 className="text-2xl font-bold text-center mb-8">
              <span className="text-slate-900">Smart</span>
              <span className="text-orange-500">Safety+</span>
            </h1>

            {/* User Type Tabs */}
            <div className="flex bg-slate-100 rounded-lg p-1 mb-6">
              <button
                type="button"
                onClick={() => setUserType('admin')}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-md text-sm font-medium transition-all ${
                  userType === 'admin'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
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
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
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
                <Label htmlFor="email" className="text-slate-700 font-medium">
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
                  className="h-12 rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700 font-medium">
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
                  className="h-12 rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold text-base gap-2"
                disabled={isLoading}
                data-testid="login-submit-btn"
              >
                <LogIn className="w-5 h-5" />
                {isLoading ? 'INGRESANDO...' : 'INICIAR SESIÓN'}
              </Button>
            </form>

            {/* Help Text */}
            <p className="text-center text-sm text-slate-500 mt-6">
              Solicita tus credenciales al administrador de tu empresa
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
