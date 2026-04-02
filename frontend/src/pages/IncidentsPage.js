import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import {
  AlertTriangle,
  Plus,
  Filter,
  MapPin,
  Clock,
  User,
  CheckCircle,
  XCircle,
  FileSearch,
  Shield
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const INCIDENT_CATEGORIES = [
  'Accidente Laboral',
  'Casi Accidente',
  'Acto Inseguro',
  'Condición Insegura',
  'Incidente Ambiental',
  'Incidente de Tránsito',
  'Otro'
];

const SEVERITIES = ['bajo', 'medio', 'alto', 'critico'];

export default function IncidentsPage() {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    severity: 'medio',
    category: '',
    location: ''
  });
  const [correctiveAction, setCorrectiveAction] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [incRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/incidents`),
        axios.get(`${API_URL}/api/incidents/stats`)
      ]);
      setIncidents(incRes.data);
      setStats(statsRes.data);
    } catch (error) {
      toast.error('Error al cargar incidentes');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      await axios.post(`${API_URL}/api/incidents`, formData);
      toast.success('Incidente reportado correctamente');
      setShowAddDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al reportar');
    }
  };

  const handleUpdateStatus = async (status) => {
    if (!selectedIncident) return;
    try {
      const params = new URLSearchParams();
      params.append('status', status);
      if (correctiveAction) {
        params.append('corrective_action', correctiveAction);
      }
      await axios.put(`${API_URL}/api/incidents/${selectedIncident.id}/status?${params.toString()}`);
      toast.success('Estado actualizado');
      setShowDetailDialog(false);
      setCorrectiveAction('');
      fetchData();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      severity: 'medio',
      category: '',
      location: ''
    });
  };

  const viewIncident = (incident) => {
    setSelectedIncident(incident);
    setCorrectiveAction(incident.corrective_action || '');
    setShowDetailDialog(true);
  };

  const startInvestigation = async (incidentId) => {
    try {
      const response = await axios.post(`${API_URL}/api/investigations?incident_id=${incidentId}`);
      toast.success('Investigación iniciada según ISO 45001');
      navigate(`/investigation/${response.data.investigation.id}`);
    } catch (error) {
      if (error.response?.data?.detail?.includes('already exists')) {
        // Get existing investigation
        const investigations = await axios.get(`${API_URL}/api/investigations`);
        const existing = investigations.data.find(i => i.incident_id === incidentId);
        if (existing) {
          navigate(`/investigation/${existing.id}`);
        }
      } else {
        toast.error(error.response?.data?.detail || 'Error al iniciar investigación');
      }
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
      open: 'badge-open',
      investigating: 'badge-pending',
      closed: 'badge-closed'
    };
    return classes[status] || 'badge-open';
  };

  const getStatusLabel = (status) => {
    const labels = {
      open: 'Abierto',
      investigating: 'Investigando',
      closed: 'Cerrado'
    };
    return labels[status] || status;
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (filterSeverity !== 'all' && inc.severity !== filterSeverity) return false;
    if (filterStatus !== 'all' && inc.status !== filterStatus) return false;
    return true;
  });

  const COLORS = {
    critico: '#EF4444',
    alto: '#F97316',
    medio: '#F59E0B',
    bajo: '#10B981'
  };

  const CATEGORY_COLORS = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', 
    '#EC4899', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
  ];

  const severityChartData = stats?.by_severity
    ? Object.entries(stats.by_severity).map(([name, value]) => ({ name, value }))
    : [];

  const categoryChartData = stats?.by_category
    ? Object.entries(stats.by_category).map(([name, value], index) => ({ 
        name, 
        value,
        fill: CATEGORY_COLORS[index % CATEGORY_COLORS.length]
      }))
    : [];

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="incidents-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Gestión de Incidentes">
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="bg-amber-500 hover:bg-amber-400 text-white rounded-sm gap-2" data-testid="report-incident-btn">
                <Plus className="w-4 h-4" />
                Reportar Incidente
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-['Manrope']">Nuevo Reporte de Incidente</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Título del Incidente</Label>
                  <Input
                    placeholder="Descripción breve del incidente"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="rounded-sm"
                    data-testid="incident-title-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Categoría</Label>
                    <Select value={formData.category} onValueChange={(v) => setFormData({ ...formData, category: v })}>
                      <SelectTrigger className="rounded-sm" data-testid="incident-category-select">
                        <SelectValue placeholder="Seleccionar" />
                      </SelectTrigger>
                      <SelectContent>
                        {INCIDENT_CATEGORIES.map((cat) => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Severidad</Label>
                    <Select value={formData.severity} onValueChange={(v) => setFormData({ ...formData, severity: v })}>
                      <SelectTrigger className="rounded-sm" data-testid="incident-severity-select">
                        <SelectValue placeholder="Seleccionar" />
                      </SelectTrigger>
                      <SelectContent>
                        {SEVERITIES.map((sev) => (
                          <SelectItem key={sev} value={sev} className="capitalize">{sev}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Ubicación</Label>
                  <Input
                    placeholder="Área o sector donde ocurrió"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="rounded-sm"
                    data-testid="incident-location-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Descripción Detallada</Label>
                  <Textarea
                    placeholder="Describe qué sucedió, cómo y las circunstancias..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="rounded-sm min-h-24"
                    data-testid="incident-description-input"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)} className="rounded-sm">
                  Cancelar
                </Button>
                <Button onClick={handleSubmit} className="bg-slate-900 hover:bg-slate-800 rounded-sm" data-testid="submit-incident-btn">
                  Reportar Incidente
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TopBar>

        <div className="p-8 space-y-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-white font-['Manrope']">{stats?.total || 0}</p>
                    <p className="text-sm text-slate-400">Incidentes Totales</p>
                  </div>
                  <AlertTriangle className="w-10 h-10 text-slate-300" />
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-blue-600 font-['Manrope']">{stats?.open || 0}</p>
                    <p className="text-sm text-slate-400">Abiertos</p>
                  </div>
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Clock className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-red-600 font-['Manrope']">{stats?.critical || 0}</p>
                    <p className="text-sm text-slate-400">Críticos</p>
                  </div>
                  <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-green-600 font-['Manrope']">
                      {incidents.filter(i => i.status === 'closed').length}
                    </p>
                    <p className="text-sm text-slate-400">Cerrados</p>
                  </div>
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-cyan-accent/10">
              <CardHeader>
                <CardTitle className="font-['Manrope']">Incidentes por Severidad</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={severityChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {severityChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#64748B'} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="border-cyan-accent/10">
              <CardHeader>
                <CardTitle className="font-['Manrope']">Incidentes por Categoría</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={categoryChartData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis 
                        type="number" 
                        stroke="#64748B" 
                        fontSize={12} 
                        allowDecimals={false}
                        tickFormatter={(value) => Math.round(value)}
                      />
                      <YAxis dataKey="name" type="category" width={120} stroke="#64748B" fontSize={11} />
                      <Tooltip formatter={(value) => Math.round(value)} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {categoryChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Incidents Table */}
          <Card className="border-cyan-accent/10">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-['Manrope']">Lista de Incidentes</CardTitle>
              <div className="flex gap-3">
                <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                  <SelectTrigger className="w-36 rounded-sm" data-testid="filter-severity">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Severidad" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    {SEVERITIES.map((sev) => (
                      <SelectItem key={sev} value={sev} className="capitalize">{sev}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="w-36 rounded-sm" data-testid="filter-status">
                    <SelectValue placeholder="Estado" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="open">Abierto</SelectItem>
                    <SelectItem value="investigating">Investigando</SelectItem>
                    <SelectItem value="closed">Cerrado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="spinner"></div>
                </div>
              ) : filteredIncidents.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Incidente</TableHead>
                      <TableHead>Categoría</TableHead>
                      <TableHead>Ubicación</TableHead>
                      <TableHead>Severidad</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Fecha</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredIncidents.map((incident) => (
                      <TableRow key={incident.id} data-testid={`incident-row-${incident.id}`}>
                        <TableCell>
                          <div>
                            <p className="font-medium text-white">{incident.title}</p>
                            <p className="text-xs text-slate-500 truncate max-w-xs">{incident.description}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="rounded-sm">{incident.category}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm text-slate-400">
                            <MapPin className="w-3 h-3" />
                            {incident.location}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getSeverityBadge(incident.severity)}>{incident.severity}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(incident.status)}>{getStatusLabel(incident.status)}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500">
                          {new Date(incident.reported_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewIncident(incident)}
                            className="rounded-sm"
                            data-testid={`view-incident-${incident.id}`}
                          >
                            Ver Detalles
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12">
                  <AlertTriangle className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-500">No hay incidentes que mostrar</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Detail Dialog */}
          <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-['Manrope']">Detalle del Incidente</DialogTitle>
              </DialogHeader>
              {selectedIncident && (
                <div className="space-y-4 py-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-lg">{selectedIncident.title}</h3>
                      <div className="flex gap-2 mt-2">
                        <Badge className={getSeverityBadge(selectedIncident.severity)}>
                          {selectedIncident.severity}
                        </Badge>
                        <Badge className={getStatusBadge(selectedIncident.status)}>
                          {getStatusLabel(selectedIncident.status)}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-4 h-4" />
                      <span>{selectedIncident.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Clock className="w-4 h-4" />
                      <span>{new Date(selectedIncident.reported_at).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400 col-span-2">
                      <User className="w-4 h-4" />
                      <span>Reportado por: {selectedIncident.reported_by}</span>
                    </div>
                  </div>

                  <div className="p-4 bg-dark-bg rounded-sm">
                    <p className="text-sm font-medium text-slate-700 mb-2">Descripción</p>
                    <p className="text-sm text-slate-400">{selectedIncident.description}</p>
                  </div>

                  {selectedIncident.status !== 'closed' && (
                    <div className="space-y-2">
                      <Label>Acción Correctiva</Label>
                      <Textarea
                        placeholder="Describe la acción correctiva tomada..."
                        value={correctiveAction}
                        onChange={(e) => setCorrectiveAction(e.target.value)}
                        className="rounded-sm"
                        data-testid="corrective-action-input"
                      />
                    </div>
                  )}

                  {selectedIncident.corrective_action && selectedIncident.status === 'closed' && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-sm">
                      <p className="text-sm font-medium text-green-800 mb-2">Acción Correctiva Aplicada</p>
                      <p className="text-sm text-green-700">{selectedIncident.corrective_action}</p>
                    </div>
                  )}
                </div>
              )}
              <DialogFooter className="gap-2">
                {selectedIncident && (
                  <Button
                    variant="outline"
                    onClick={() => startInvestigation(selectedIncident.id)}
                    className="rounded-sm gap-2 border-blue-300 text-blue-700 hover:bg-blue-50"
                    data-testid="start-investigation-btn"
                  >
                    <FileSearch className="w-4 h-4" />
                    {selectedIncident.investigation_id ? 'Ver Investigación' : 'Investigar (ISO 45001)'}
                  </Button>
                )}
                {selectedIncident?.status === 'open' && (
                  <Button
                    variant="outline"
                    onClick={() => handleUpdateStatus('investigating')}
                    className="rounded-sm"
                    data-testid="investigating-btn"
                  >
                    Marcar Investigando
                  </Button>
                )}
                {selectedIncident?.status !== 'closed' && (
                  <Button
                    onClick={() => handleUpdateStatus('closed')}
                    className="bg-green-600 hover:bg-green-700 rounded-sm gap-2"
                    data-testid="close-incident-btn"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Cerrar Incidente
                  </Button>
                )}
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
