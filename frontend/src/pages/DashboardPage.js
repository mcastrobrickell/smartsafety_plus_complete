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
    bajo: '#10B981',
    low: '#10B981'
  };

  const getSeverityColor = (severity) => COLORS[severity?.toLowerCase()] || '#64748B';

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
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
    <div className="flex min-h-screen bg-slate-50" data-testid="dashboard-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Dashboard - Visión 360°" subtitle={`Bienvenido, ${user?.name || 'Usuario'}`}>
          <Button
            variant="outline"
            className="gap-2 rounded-lg"
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
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 lg:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3" data-testid="critical-alert">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 lg:w-6 lg:h-6 text-red-600 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-red-800 text-sm lg:text-base">{stats.critical_findings} hallazgo(s) crítico(s) pendiente(s)</p>
                  <p className="text-xs lg:text-sm text-red-600">Requieren acción inmediata</p>
                </div>
              </div>
              <Button 
                className="bg-red-600 hover:bg-red-700 rounded-lg"
                onClick={() => navigate('/findings')}
                data-testid="view-critical-btn"
              >
                Ver Hallazgos
              </Button>
            </div>
          )}

          {/* Stats Grid - Vision 360 Focus */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 lg:gap-6">
            <Card className="border-slate-200 hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/scan360')}>
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Scans Realizados</p>
                    <p className="text-2xl lg:text-3xl font-bold text-blue-600 mt-1 lg:mt-2">{stats?.total_scans || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Total histórico</p>
                  </div>
                  <div className="p-2 lg:p-3 bg-blue-100 rounded-xl">
                    <Scan className="w-5 h-5 lg:w-6 lg:h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 hover:shadow-md transition-shadow">
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Scans Hoy</p>
                    <p className="text-2xl lg:text-3xl font-bold text-green-600 mt-1 lg:mt-2">{stats?.scans_today || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Inspecciones del día</p>
                  </div>
                  <div className="p-2 lg:p-3 bg-green-100 rounded-xl">
                    <Eye className="w-5 h-5 lg:w-6 lg:h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/findings')}>
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Hallazgos Críticos</p>
                    <p className="text-2xl lg:text-3xl font-bold text-red-600 mt-1 lg:mt-2">{stats?.critical_findings || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">Pendientes de acción</p>
                  </div>
                  <div className="p-2 lg:p-3 bg-red-100 rounded-xl">
                    <AlertTriangle className="w-5 h-5 lg:w-6 lg:h-6 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/incidents')}>
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Incidentes Abiertos</p>
                    <p className="text-2xl lg:text-3xl font-bold text-orange-600 mt-1 lg:mt-2">{stats?.open_incidents || 0}</p>
                    <p className="text-xs text-slate-400 mt-1">En investigación</p>
                  </div>
                  <div className="p-2 lg:p-3 bg-orange-100 rounded-xl">
                    <Activity className="w-5 h-5 lg:w-6 lg:h-6 text-orange-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 hover:shadow-md transition-shadow cursor-pointer sm:col-span-2 lg:col-span-1" onClick={() => navigate('/epp')}>
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Costo EPP Total</p>
                    <p className="text-2xl lg:text-3xl font-bold text-slate-900 mt-1 lg:mt-2">
                      ${(stats?.total_epp_cost || 0).toLocaleString()}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">Inversión acumulada</p>
                  </div>
                  <div className="p-2 lg:p-3 bg-slate-100 rounded-xl">
                    <DollarSign className="w-5 h-5 lg:w-6 lg:h-6 text-slate-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Findings by Category */}
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-500" />
                  Hallazgos por Categoría
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64" style={{ minHeight: '256px' }}>
                  {(charts?.findings_by_category || []).length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={charts?.findings_by_category || []} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
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
                        />
                        <Bar dataKey="value" name="Cantidad" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      <div className="text-center">
                        <Scan className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                        <p>Sin hallazgos registrados</p>
                        <Button
                          className="mt-4 bg-blue-500 hover:bg-blue-600 rounded-lg"
                          onClick={() => navigate('/scan360')}
                        >
                          Realizar Scan
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Incidents by Severity */}
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-500" />
                  Incidentes por Severidad
                </CardTitle>
              </CardHeader>
              <CardContent>
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
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      <div className="text-center">
                        <Shield className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                        <p>Sin incidentes registrados</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Acciones Rápidas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <button
                  onClick={() => navigate('/scan360')}
                  className="w-full flex items-center gap-3 p-4 border border-slate-200 rounded-xl hover:bg-blue-50 hover:border-blue-200 transition-colors text-left"
                  data-testid="quick-scan"
                >
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Scan className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Nuevo Scan 360°</p>
                    <p className="text-xs text-slate-500">Análisis de seguridad con IA</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={() => navigate('/incidents')}
                  className="w-full flex items-center gap-3 p-4 border border-slate-200 rounded-xl hover:bg-orange-50 hover:border-orange-200 transition-colors text-left"
                  data-testid="quick-incident"
                >
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-orange-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Reportar Incidente</p>
                    <p className="text-xs text-slate-500">Registrar nuevo evento</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={() => navigate('/risk-matrix')}
                  className="w-full flex items-center gap-3 p-4 border border-slate-200 rounded-xl hover:bg-purple-50 hover:border-purple-200 transition-colors text-left"
                  data-testid="quick-matrix"
                >
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Matriz de Riesgos</p>
                    <p className="text-xs text-slate-500">Evaluación de riesgos</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={() => navigate('/procedures')}
                  className="w-full flex items-center gap-3 p-4 border border-slate-200 rounded-xl hover:bg-green-50 hover:border-green-200 transition-colors text-left"
                  data-testid="quick-procedures"
                >
                  <div className="p-2 bg-green-100 rounded-lg">
                    <FileText className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Procedimientos</p>
                    <p className="text-xs text-slate-500">Gestión documental</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>
              </CardContent>
            </Card>

            {/* Recent Scans */}
            <Card className="border-slate-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-semibold">Scans Recientes</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => navigate('/scan360')} data-testid="view-all-scans-btn">
                  Ver todos <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  {activity?.scans?.length > 0 ? (
                    <div className="space-y-3">
                      {activity.scans.map((scan) => (
                        <div key={scan.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                          <Scan className="w-5 h-5 mt-0.5 text-blue-500" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-slate-900 truncate">{scan.name}</p>
                            <p className="text-sm text-slate-500">{scan.location}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-slate-900">{scan.findings_count}</p>
                            <p className="text-xs text-slate-500">hallazgos</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-8">No hay scans recientes</p>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Recent Findings */}
            <Card className="border-slate-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-semibold">Hallazgos Recientes</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => navigate('/findings')} data-testid="view-all-findings-btn">
                  Ver todos <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  {activity?.findings?.length > 0 ? (
                    <div className="space-y-3">
                      {activity.findings.map((finding) => (
                        <div key={finding.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                          <AlertTriangle className="w-5 h-5 mt-0.5" style={{ color: getSeverityColor(finding.severity) }} />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-slate-900 truncate">{finding.category}</p>
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
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
