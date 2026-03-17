import React, { useState, useEffect } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import {
  FileText,
  Filter,
  CheckCircle,
  Clock,
  AlertTriangle,
  Eye
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function FindingsPage() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');

  useEffect(() => {
    fetchFindings();
  }, []);

  const fetchFindings = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/findings`);
      setFindings(response.data);
    } catch (error) {
      toast.error('Error al cargar hallazgos');
    } finally {
      setLoading(false);
    }
  };

  const updateFindingStatus = async (findingId, status) => {
    try {
      await axios.put(`${API_URL}/api/findings/${findingId}/status?status=${status}`);
      toast.success('Estado actualizado');
      fetchFindings();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const getSeverityBadge = (severity) => {
    const classes = {
      bajo: 'badge-low',
      medio: 'badge-medium',
      alto: 'badge-high',
      critico: 'badge-critical'
    };
    return classes[severity?.toLowerCase()] || 'badge-medium';
  };

  const getStatusBadge = (status) => {
    const classes = {
      pending: 'badge-pending',
      in_progress: 'badge-open',
      resolved: 'badge-low'
    };
    return classes[status] || 'badge-pending';
  };

  const getStatusLabel = (status) => {
    const labels = {
      pending: 'Pendiente',
      in_progress: 'En Progreso',
      resolved: 'Resuelto'
    };
    return labels[status] || status;
  };

  const categories = [...new Set(findings.map(f => f.category))];

  const filteredFindings = findings.filter((finding) => {
    if (filterSeverity !== 'all' && finding.severity !== filterSeverity) return false;
    if (filterStatus !== 'all' && finding.status !== filterStatus) return false;
    if (filterCategory !== 'all' && finding.category !== filterCategory) return false;
    return true;
  });

  const stats = {
    total: findings.length,
    pending: findings.filter(f => f.status === 'pending').length,
    in_progress: findings.filter(f => f.status === 'in_progress').length,
    resolved: findings.filter(f => f.status === 'resolved').length,
    critical: findings.filter(f => f.severity === 'critico').length
  };

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="findings-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Hallazgos de Seguridad" />

        <div className="p-8 space-y-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-2xl font-bold text-slate-900 font-['Manrope']">{stats.total}</p>
                <p className="text-sm text-slate-600">Total Hallazgos</p>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-2xl font-bold text-yellow-600 font-['Manrope']">{stats.pending}</p>
                <p className="text-sm text-slate-600">Pendientes</p>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-2xl font-bold text-blue-600 font-['Manrope']">{stats.in_progress}</p>
                <p className="text-sm text-slate-600">En Progreso</p>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-2xl font-bold text-green-600 font-['Manrope']">{stats.resolved}</p>
                <p className="text-sm text-slate-600">Resueltos</p>
              </CardContent>
            </Card>
            <Card className="stat-card border-red-200 bg-red-50">
              <CardContent className="p-4">
                <p className="text-2xl font-bold text-red-600 font-['Manrope']">{stats.critical}</p>
                <p className="text-sm text-red-700">Críticos</p>
              </CardContent>
            </Card>
          </div>

          {/* Findings Table */}
          <Card className="border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-['Manrope']">Lista de Hallazgos</CardTitle>
              <div className="flex gap-3">
                <Select value={filterCategory} onValueChange={setFilterCategory}>
                  <SelectTrigger className="w-40 rounded-sm" data-testid="filter-category">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Categoría" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    {categories.map((cat) => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                  <SelectTrigger className="w-36 rounded-sm" data-testid="filter-severity">
                    <SelectValue placeholder="Severidad" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    <SelectItem value="bajo">Bajo</SelectItem>
                    <SelectItem value="medio">Medio</SelectItem>
                    <SelectItem value="alto">Alto</SelectItem>
                    <SelectItem value="critico">Crítico</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="w-36 rounded-sm" data-testid="filter-status">
                    <SelectValue placeholder="Estado" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="pending">Pendiente</SelectItem>
                    <SelectItem value="in_progress">En Progreso</SelectItem>
                    <SelectItem value="resolved">Resuelto</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="spinner"></div>
                </div>
              ) : filteredFindings.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Categoría</TableHead>
                      <TableHead className="max-w-md">Descripción</TableHead>
                      <TableHead>Severidad</TableHead>
                      <TableHead>Confianza</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Fecha</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredFindings.map((finding) => (
                      <TableRow key={finding.id} data-testid={`finding-row-${finding.id}`}>
                        <TableCell>
                          <Badge variant="outline" className="rounded-sm">{finding.category}</Badge>
                        </TableCell>
                        <TableCell className="max-w-md">
                          <p className="text-sm text-slate-900 truncate">{finding.description}</p>
                          {finding.corrective_action && (
                            <p className="text-xs text-slate-500 mt-1 truncate">
                              Acción: {finding.corrective_action}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={getSeverityBadge(finding.severity)}>{finding.severity}</Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-slate-600">{finding.confidence}%</span>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(finding.status)}>{getStatusLabel(finding.status)}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500">
                          {new Date(finding.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            {finding.status === 'pending' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => updateFindingStatus(finding.id, 'in_progress')}
                                className="rounded-sm gap-1"
                                data-testid={`start-finding-${finding.id}`}
                              >
                                <Clock className="w-3 h-3" />
                                Iniciar
                              </Button>
                            )}
                            {finding.status !== 'resolved' && (
                              <Button
                                size="sm"
                                onClick={() => updateFindingStatus(finding.id, 'resolved')}
                                className="bg-green-600 hover:bg-green-700 rounded-sm gap-1"
                                data-testid={`resolve-finding-${finding.id}`}
                              >
                                <CheckCircle className="w-3 h-3" />
                                Resolver
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-500">No hay hallazgos que mostrar</p>
                  <p className="text-sm text-slate-400 mt-2">Los hallazgos se generan automáticamente al realizar un Scan 360°</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Critical Findings Alert */}
          {stats.critical > 0 && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-red-100 rounded-sm">
                    <AlertTriangle className="w-6 h-6 text-red-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-red-800 font-['Manrope']">
                      {stats.critical} Hallazgo(s) Crítico(s) Requieren Atención Inmediata
                    </h3>
                    <p className="text-sm text-red-700 mt-1">
                      Estos hallazgos representan riesgos significativos para la seguridad y deben ser abordados con prioridad.
                    </p>
                    <Button
                      className="mt-4 bg-red-600 hover:bg-red-700 rounded-sm"
                      onClick={() => { setFilterSeverity('critico'); setFilterStatus('all'); }}
                      data-testid="view-critical-findings-btn"
                    >
                      Ver Hallazgos Críticos
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
