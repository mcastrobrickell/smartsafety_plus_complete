import React, { useState, useEffect } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  AlertTriangle,
  Scan,
  ChevronRight,
  FileText,
  Download,
  Eye,
  Shield,
  Activity,
  TrendingUp,
  DollarSign
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState(null);
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, activityRes, chartsRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/stats`),
        axios.get(`${API_URL}/api/dashboard/recent-activity`),
        axios.get(`${API_URL}/api/dashboard/charts`)
      ]);
      setStats(statsRes.data);
      setActivity(activityRes.data);
      setCharts(chartsRes.data);
    } catch (error) {
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportPDF = async (type) => {
    try {
      const response = await axios.get(`${API_URL}/api/reports/export-pdf?report_type=${type}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `reporte-${type}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Reporte exportado');
    } catch (error) {
      toast.error('Error al exportar');
    }
  };

  const COLORS = {
    critico: '#EF4444',
    critical: '#EF4444',
    alto: '#F97316',
    high: '#F97316',
    medio: '#F59E0B',
    medium: '#F59E0B',
    bajo: '#22C55E',
    low: '#22C55E'
  };

  const getSeverityColor = (severity) => COLORS[severity?.toLowerCase()] || '#64748B';

  if (loading) {
    return (
      <div className="flex min-h-screen bg-dark-bg">
        <Sidebar />
        <main className="flex-1">
          <TopBar title="Dashboard - Visión 360°" />
          <div className="p-8 flex items-center justify-center h-96">
            <div className="spinner"></div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="dashboard-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Dashboard - Visión 360°" subtitle={`Bienvenido, ${user?.name || 'Usuario'}`}>
          <Button
            className="btn-outline gap-2"
            onClick={() => exportPDF('findings')}
            data-testid="export-pdf-btn"
          >
            <Download className="w-4 h-4" />
            Exportar Reporte
          </Button>
        </TopBar>

        <div className="p-4 lg:p-8 space-y-6 lg:space-y-8">
          {/* Critical Alert Banner */}
          {stats?.critical_findings > 0 && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 lg:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3" data-testid="critical-alert">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 lg:w-6 lg:h-6 text-red-400 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-red-400 text-sm lg:text-base">{stats.critical_findings} hallazgo(s) crítico(s) pendiente(s)</p>
                  <p className="text-xs lg:text-sm text-red-400/70">Requieren acción inmediata</p>
                </div>
              </div>
              <Button 
                className="btn-danger"
                onClick={() => navigate('/findings')}
                data-testid="view-critical-btn"
              >
                Ver Hallazgos
              </Button>
            </div>
          )}

          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 lg:gap-6">
            <div className="card-dark p-4 lg:p-6 card-hover cursor-pointer" onClick={() => navigate('/scan360')}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs lg:text-sm text-slate-400">Scans Realizados</p>
                  <p className="text-2xl lg:text-3xl font-bold text-cyan-accent mt-1 lg:mt-2">{stats?.total_scans || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">Total histórico</p>
                </div>
                <div className="p-2 lg:p-3 bg-cyan-accent/10 border border-cyan-accent/30 rounded-xl">
                  <Scan className="w-5 h-5 lg:w-6 lg:h-6 text-cyan-accent" />
                </div>
              </div>
            </div>

            <div className="card-dark p-4 lg:p-6 card-hover">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs lg:text-sm text-slate-400">Scans Hoy</p>
                  <p className="text-2xl lg:text-3xl font-bold text-success-green mt-1 lg:mt-2">{stats?.scans_today || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">Inspecciones del día</p>
                </div>
                <div className="p-2 lg:p-3 bg-success-green/10 border border-success-green/30 rounded-xl">
                  <Eye className="w-5 h-5 lg:w-6 lg:h-6 text-success-green" />
                </div>
              </div>
            </div>

            <div className="card-dark p-4 lg:p-6 card-hover cursor-pointer" onClick={() => navigate('/findings')}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs lg:text-sm text-slate-400">Hallazgos Críticos</p>
                  <p className="text-2xl lg:text-3xl font-bold text-red-400 mt-1 lg:mt-2">{stats?.critical_findings || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">Pendientes de acción</p>
                </div>
                <div className="p-2 lg:p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
                  <AlertTriangle className="w-5 h-5 lg:w-6 lg:h-6 text-red-400" />
                </div>
              </div>
            </div>

            <div className="card-dark p-4 lg:p-6 card-hover cursor-pointer" onClick={() => navigate('/incidents')}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs lg:text-sm text-slate-400">Incidentes Abiertos</p>
                  <p className="text-2xl lg:text-3xl font-bold text-orange-400 mt-1 lg:mt-2">{stats?.open_incidents || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">En investigación</p>
                </div>
                <div className="p-2 lg:p-3 bg-orange-500/10 border border-orange-500/30 rounded-xl">
                  <Activity className="w-5 h-5 lg:w-6 lg:h-6 text-orange-400" />
                </div>
              </div>
            </div>

            <div className="card-dark p-4 lg:p-6 card-hover cursor-pointer sm:col-span-2 lg:col-span-1" onClick={() => navigate('/epp')}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs lg:text-sm text-slate-400">Costo EPP Total</p>
                  <p className="text-2xl lg:text-3xl font-bold text-white mt-1 lg:mt-2">
                    ${(stats?.total_epp_cost || 0).toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Inversión acumulada</p>
                </div>
                <div className="p-2 lg:p-3 bg-dark-bg0/10 border border-slate-500/30 rounded-xl">
                  <DollarSign className="w-5 h-5 lg:w-6 lg:h-6 text-slate-400" />
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Findings by Category */}
            <div className="card-dark">
              <div className="p-6 border-b border-cyan-accent/10">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 font-display">
                  <FileText className="w-5 h-5 text-cyan-accent" />
                  Hallazgos por Categoría
                </h3>
              </div>
              <div className="p-6">
                <div className="h-64" style={{ minHeight: '256px' }}>
                  {(charts?.findings_by_category || []).length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={charts?.findings_by_category || []} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                        <XAxis 
                          type="number" 
                          stroke="#64748B" 
                          fontSize={12} 
                          allowDecimals={false}
                          tickFormatter={(value) => Math.floor(value)}
                        />
                        <YAxis dataKey="name" type="category" width={120} stroke="#64748B" fontSize={11} />
                        <Tooltip 
                          formatter={(value) => [value, 'Cantidad']}
                          labelFormatter={(label) => `Categoría: ${label}`}
                          contentStyle={{ backgroundColor: '#0A0F1A', border: '1px solid rgba(0,229,255,0.2)', borderRadius: '8px' }}
                          labelStyle={{ color: '#00E5FF' }}
                        />
                        <Bar dataKey="value" name="Cantidad" fill="#00E5FF" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      <div className="text-center">
                        <Scan className="w-12 h-12 mx-auto mb-2 text-slate-400" />
                        <p>Sin hallazgos registrados</p>
                        <Button
                          className="mt-4 btn-primary"
                          onClick={() => navigate('/scan360')}
                        >
                          Realizar Scan
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Incidents by Severity */}
            <div className="card-dark">
              <div className="p-6 border-b border-cyan-accent/10">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 font-display">
                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                  Incidentes por Severidad
                </h3>
              </div>
              <div className="p-6">
                <div className="h-64" style={{ minHeight: '256px' }}>
                  {(charts?.incidents_by_severity || []).length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={charts?.incidents_by_severity || []}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}`}
                        >
                          {(charts?.incidents_by_severity || []).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={getSeverityColor(entry.name)} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0A0F1A', border: '1px solid rgba(0,229,255,0.2)', borderRadius: '8px' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      <div className="text-center">
                        <Shield className="w-12 h-12 mx-auto mb-2 text-slate-400" />
                        <p>Sin incidentes registrados</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className="card-dark">
              <div className="p-6 border-b border-cyan-accent/10">
                <h3 className="text-lg font-semibold text-white font-display">Acciones Rápidas</h3>
              </div>
              <div className="p-6 space-y-3">
                <button
                  onClick={() => navigate('/scan360')}
                  className="w-full flex items-center gap-3 p-4 bg-dark-input border border-cyan-accent/10 rounded-xl hover:bg-cyan-accent/5 hover:border-cyan-accent/30 transition-all text-left group"
                  data-testid="quick-scan"
                >
                  <div className="p-2 bg-cyan-accent/10 border border-cyan-accent/30 rounded-lg group-hover:bg-cyan-accent/20">
                    <Scan className="w-5 h-5 text-cyan-accent" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">Nuevo Scan 360°</p>
                    <p className="text-xs text-slate-500">Análisis de seguridad con IA</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-accent" />
                </button>

                <button
                  onClick={() => navigate('/incidents')}
                  className="w-full flex items-center gap-3 p-4 bg-dark-input border border-cyan-accent/10 rounded-xl hover:bg-orange-500/5 hover:border-orange-500/30 transition-all text-left group"
                  data-testid="quick-incident"
                >
                  <div className="p-2 bg-orange-500/10 border border-orange-500/30 rounded-lg group-hover:bg-orange-500/20">
                    <AlertTriangle className="w-5 h-5 text-orange-400" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">Reportar Incidente</p>
                    <p className="text-xs text-slate-500">Registrar nuevo evento</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-orange-400" />
                </button>

                <button
                  onClick={() => navigate('/risk-matrix')}
                  className="w-full flex items-center gap-3 p-4 bg-dark-input border border-cyan-accent/10 rounded-xl hover:bg-purple-500/5 hover:border-purple-500/30 transition-all text-left group"
                  data-testid="quick-matrix"
                >
                  <div className="p-2 bg-purple-500/10 border border-purple-500/30 rounded-lg group-hover:bg-purple-500/20">
                    <TrendingUp className="w-5 h-5 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">Matriz de Riesgos</p>
                    <p className="text-xs text-slate-500">Evaluación de riesgos</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400" />
                </button>

                <button
                  onClick={() => navigate('/procedures')}
                  className="w-full flex items-center gap-3 p-4 bg-dark-input border border-cyan-accent/10 rounded-xl hover:bg-success-green/5 hover:border-success-green/30 transition-all text-left group"
                  data-testid="quick-procedures"
                >
                  <div className="p-2 bg-success-green/10 border border-success-green/30 rounded-lg group-hover:bg-success-green/20">
                    <FileText className="w-5 h-5 text-success-green" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">Procedimientos</p>
                    <p className="text-xs text-slate-500">Gestión documental</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-success-green" />
                </button>
              </div>
            </div>

            {/* Recent Scans */}
            <div className="card-dark">
              <div className="p-6 border-b border-cyan-accent/10 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white font-display">Scans Recientes</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate('/scan360')} className="text-cyan-accent hover:text-cyan-accent/80" data-testid="view-all-scans-btn">
                  Ver todos <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
              <div className="p-6">
                <ScrollArea className="h-64">
                  {activity?.scans?.length > 0 ? (
                    <div className="space-y-3">
                      {activity.scans.map((scan) => (
                        <div key={scan.id} className="flex items-start gap-3 p-3 bg-dark-input rounded-lg border border-cyan-accent/5">
                          <Scan className="w-5 h-5 mt-0.5 text-cyan-accent" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-white truncate">{scan.name}</p>
                            <p className="text-sm text-slate-500">{scan.location}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-cyan-accent">{scan.findings_count}</p>
                            <p className="text-xs text-slate-500">hallazgos</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-8">No hay scans recientes</p>
                  )}
                </ScrollArea>
              </div>
            </div>

            {/* Recent Findings */}
            <div className="card-dark">
              <div className="p-6 border-b border-cyan-accent/10 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white font-display">Hallazgos Recientes</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate('/findings')} className="text-cyan-accent hover:text-cyan-accent/80" data-testid="view-all-findings-btn">
                  Ver todos <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
              <div className="p-6">
                <ScrollArea className="h-64">
                  {activity?.findings?.length > 0 ? (
                    <div className="space-y-3">
                      {activity.findings.map((finding) => (
                        <div key={finding.id} className="flex items-start gap-3 p-3 bg-dark-input rounded-lg border border-cyan-accent/5">
                          <AlertTriangle className="w-5 h-5 mt-0.5" style={{ color: getSeverityColor(finding.severity) }} />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-white truncate">{finding.category}</p>
                            <p className="text-xs text-slate-500 truncate">{finding.description}</p>
                          </div>
                          <Badge className={`badge-${finding.severity}`}>{finding.severity}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-8">No hay hallazgos recientes</p>
                  )}
                </ScrollArea>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
