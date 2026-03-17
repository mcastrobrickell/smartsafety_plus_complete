import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { 
  Shield, 
  Scan, 
  HardHat, 
  AlertTriangle, 
  FileText, 
  CheckCircle,
  ArrowRight,
  Zap,
  BarChart3,
  Bell
} from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50" data-testid="landing-page">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-slate-900">Smart</span>
              <span className="text-orange-500">Safety+</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/login')}
              className="text-slate-600 hover:text-slate-900"
              data-testid="login-nav-btn"
            >
              Iniciar Sesión
            </Button>
            <Button 
              onClick={() => navigate('/login')}
              className="bg-blue-500 hover:bg-blue-600 text-white rounded-lg gap-2"
              data-testid="start-btn"
            >
              Comenzar <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-full text-sm font-medium mb-6">
                <Zap className="w-4 h-4" />
                Sistema de Gestión de Seguridad con IA
              </div>
              <h1 className="text-4xl lg:text-5xl xl:text-6xl font-bold text-slate-900 leading-tight mb-6">
                Prevención de Riesgos<br />
                <span className="text-orange-500">Inteligente</span> y<br />
                Automatizada
              </h1>
              <p className="text-lg text-slate-600 mb-8 max-w-lg">
                Gestión integral de seguridad operativa con análisis de imágenes 360° 
                impulsado por IA. Detecta riesgos, gestiona EPP y genera reportes automáticos.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button 
                  onClick={() => navigate('/login')}
                  className="bg-blue-500 hover:bg-blue-600 text-white rounded-lg px-8 py-6 text-lg gap-2"
                  data-testid="cta-btn"
                >
                  Ingresar al Sistema <ArrowRight className="w-5 h-5" />
                </Button>
                <Button 
                  variant="outline"
                  className="rounded-lg px-8 py-6 text-lg border-slate-300"
                >
                  Ver Funcionalidades
                </Button>
              </div>
              <div className="flex items-center gap-6 mt-8 text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Análisis con IA</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Reportes Automáticos</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>OSHA Compliant</span>
                </div>
              </div>
            </div>

            {/* Preview Card */}
            <div className="relative">
              <div className="bg-white rounded-2xl shadow-2xl p-6 border border-slate-200">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-400"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                    <div className="w-3 h-3 rounded-full bg-green-400"></div>
                  </div>
                  <span className="text-sm text-slate-400 ml-2">smartsafety.tecops.cl</span>
                </div>
                
                <div className="bg-slate-50 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Scan className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">Inspección de Seguridad</p>
                      <p className="text-sm text-slate-500">12 hallazgos detectados</p>
                    </div>
                  </div>
                  
                  <div className="space-y-3 mb-6">
                    <div className="h-3 bg-slate-200 rounded-full w-full"></div>
                    <div className="h-3 bg-slate-200 rounded-full w-3/4"></div>
                    <div className="h-3 bg-orange-200 rounded-full w-5/6"></div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-blue-600">156</p>
                      <p className="text-xs text-slate-500">Scans Hoy</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-600">98%</p>
                      <p className="text-xs text-slate-500">Cumplimiento</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-orange-500">3</p>
                      <p className="text-xs text-slate-500">Pendientes</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-4 text-sm text-slate-600">
                  <FileText className="w-4 h-4" />
                  Exportar Reporte PDF
                </div>
              </div>

              {/* Floating Badge */}
              <div className="absolute -top-4 -right-4 bg-green-500 text-white px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 shadow-lg">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                Sincronizado
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-slate-900 mb-4">
              Funcionalidades Principales
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Todo lo que necesitas para gestionar la seguridad operativa de tu empresa
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-slate-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
                <Scan className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Scan 360° con IA</h3>
              <p className="text-slate-600 text-sm">
                Análisis automático de imágenes para detectar riesgos y condiciones inseguras.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-4">
                <HardHat className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Gestión de EPP</h3>
              <p className="text-slate-600 text-sm">
                Control completo de inventario, certificaciones y asignaciones de EPP.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mb-4">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Reporte Incidentes</h3>
              <p className="text-slate-600 text-sm">
                Sistema completo de reportes con seguimiento y acciones correctivas.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Dashboard Tiempo Real</h3>
              <p className="text-slate-600 text-sm">
                Métricas de seguridad actualizadas en tiempo real con alertas automáticas.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold">
                <span className="text-white">Smart</span>
                <span className="text-orange-500">Safety+</span>
              </span>
            </div>
            <p className="text-slate-400 text-sm">
              © 2026 SmartSafety+. Gestión integral de seguridad operativa.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
