import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Shield,
  Building2,
  Users,
  Settings,
  CreditCard,
  Lock,
  Plus,
  Power,
  RotateCcw,
  Trash2,
  LogOut,
  LayoutDashboard,
  TrendingUp,
  HardHat,
  MapPin
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SuperAdminPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddOrg, setShowAddOrg] = useState(false);
  const [orgForm, setOrgForm] = useState({ name: '', rut: '', plan: 'profesional' });

  useEffect(() => {
    if (user?.role !== 'superadmin') {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const [orgsRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/organizations`),
        axios.get(`${API_URL}/api/superadmin/stats`)
      ]);
      setOrganizations(orgsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrg = async () => {
    try {
      await axios.post(`${API_URL}/api/organizations`, orgForm);
      toast.success('Organización creada');
      setShowAddOrg(false);
      setOrgForm({ name: '', rut: '', plan: 'profesional' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear');
    }
  };

  const handleToggleOrg = async (orgId, action) => {
    try {
      await axios.put(`${API_URL}/api/organizations/${orgId}/${action}`);
      toast.success(`Organización ${action === 'activate' ? 'activada' : 'desactivada'}`);
      fetchData();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const handleDeleteOrg = async (orgId) => {
    if (!window.confirm('¿Eliminar esta organización?')) return;
    try {
      await axios.delete(`${API_URL}/api/organizations/${orgId}`);
      toast.success('Organización eliminada');
      fetchData();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarItems = [
    { id: 'panel', label: 'Panel de Control', icon: LayoutDashboard, active: true }
  ];

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="superadmin-page">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-surface border-r border-cyan-accent/10 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-cyan-accent/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-tech rounded-xl flex items-center justify-center shadow-glow-cyan">
              <Shield className="w-6 h-6 text-dark-bg" />
            </div>
            <div>
              <div className="font-bold font-display">
                <span className="text-cyan-accent">Smart</span>
                <span className="logo-gradient">Safety+</span>
              </div>
              <div className="text-xs text-slate-500">Enterprise 2026</div>
            </div>
          </div>
        </div>

        {/* Super Admin Section */}
        <div className="p-4">
          <p className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-3">
            Super Admin
          </p>
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all ${
                item.active
                  ? 'bg-gradient-to-r from-cyan-accent/20 to-transparent border-l-2 border-cyan-accent text-cyan-accent'
                  : 'text-slate-400 hover:bg-cyan-accent/5 hover:text-cyan-accent'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </div>

        {/* Organization Selector */}
        <div className="p-4 border-t border-cyan-accent/10">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Gestionar Empresa
          </p>
          <Select defaultValue="all">
            <SelectTrigger className="w-full bg-dark-input border-cyan-accent/20 text-white">
              <SelectValue placeholder="Seleccionar empresa" />
            </SelectTrigger>
            <SelectContent className="bg-dark-surface border-cyan-accent/20">
              <SelectItem value="all">Todas las empresas</SelectItem>
              {organizations.map((org) => (
                <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Spacer */}
        <div className="flex-1"></div>

        {/* User Info */}
        <div className="p-4 border-t border-cyan-accent/10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-success-green rounded-full flex items-center justify-center">
              <span className="text-dark-bg font-semibold text-sm">S</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">Super Administrador</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <Button
            className="w-full justify-start gap-2 btn-outline"
            onClick={handleLogout}
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            Cerrar Sesión
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="bg-dark-surface/80 backdrop-blur-xl border-b border-cyan-accent/10 px-8 py-6">
          <h1 className="text-3xl font-bold font-display">
            <span className="text-success-green">SUPER ADMIN</span>
            <span className="text-cyan-accent"> PANEL</span>
          </h1>
          <p className="text-slate-400 mt-1">Administración global de SmartSafety+</p>
        </header>

        <div className="p-8 space-y-8">
          {/* Tabs */}
          <Tabs defaultValue="empresas" className="space-y-6">
            <TabsList className="bg-dark-surface border border-cyan-accent/10 p-1">
              <TabsTrigger value="empresas" className="gap-2 data-[state=active]:bg-cyan-accent/10 data-[state=active]:text-cyan-accent text-slate-400">
                <Building2 className="w-4 h-4" />
                Empresas
              </TabsTrigger>
              <TabsTrigger value="modulos" className="gap-2 data-[state=active]:bg-cyan-accent/10 data-[state=active]:text-cyan-accent text-slate-400">
                <Settings className="w-4 h-4" />
                Módulos
              </TabsTrigger>
              <TabsTrigger value="cobros" className="gap-2 data-[state=active]:bg-cyan-accent/10 data-[state=active]:text-cyan-accent text-slate-400">
                <CreditCard className="w-4 h-4" />
                Control de Cobros
              </TabsTrigger>
              <TabsTrigger value="seguridad" className="gap-2 data-[state=active]:bg-cyan-accent/10 data-[state=active]:text-cyan-accent text-slate-400">
                <Lock className="w-4 h-4" />
                Seguridad
              </TabsTrigger>
            </TabsList>

            <TabsContent value="empresas" className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="card-dark p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Organizaciones</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {stats?.total_organizations || organizations.length}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {stats?.active_organizations || organizations.filter(o => o.is_active).length} activas
                      </p>
                    </div>
                    <Building2 className="w-10 h-10 text-slate-400" />
                  </div>
                </div>

                <div className="card-dark p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Usuarios Totales</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {stats?.total_users || 0}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">En todas las organizaciones</p>
                    </div>
                    <Users className="w-10 h-10 text-slate-400" />
                  </div>
                </div>

                <div className="card-dark p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Prevencionistas</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {stats?.total_preventionists || 0}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">Personal gestionado</p>
                    </div>
                    <HardHat className="w-10 h-10 text-slate-400" />
                  </div>
                </div>

                <div className="card-dark p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Faenas Totales</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {stats?.total_locations || 0}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">Centros de operación</p>
                    </div>
                    <MapPin className="w-10 h-10 text-slate-400" />
                  </div>
                </div>
              </div>

              {/* Distribution by Plan */}
              <div className="card-dark">
                <div className="p-6 border-b border-cyan-accent/10">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2 font-display">
                    <TrendingUp className="w-5 h-5 text-cyan-accent" />
                    Distribución por Plan
                  </h3>
                  <p className="text-sm text-slate-500">Suscripciones activas</p>
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-center py-8">
                    <div className="text-center">
                      <p className="text-5xl font-bold text-cyan-accent text-glow-cyan">
                        {organizations.filter(o => o.is_active).length}
                      </p>
                      <p className="text-slate-400 mt-2">Profesional</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Organizations Table */}
              <div className="card-dark">
                <div className="p-6 border-b border-cyan-accent/10 flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-white font-display">Organizaciones Registradas</h3>
                    <p className="text-sm text-slate-500 mt-1">Gestiona todas las empresas del sistema</p>
                  </div>
                  <Dialog open={showAddOrg} onOpenChange={setShowAddOrg}>
                    <DialogTrigger asChild>
                      <Button className="btn-primary gap-2" data-testid="add-org-btn">
                        <Plus className="w-4 h-4" />
                        Nueva Empresa
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-dark-surface border-cyan-accent/20">
                      <DialogHeader>
                        <DialogTitle className="text-white font-display">Crear Nueva Organización</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">Nombre de la Empresa</Label>
                          <Input
                            placeholder="Empresa Demo S.A."
                            value={orgForm.name}
                            onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                            className="form-input"
                            data-testid="org-name-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">RUT</Label>
                          <Input
                            placeholder="76.123.456-7"
                            value={orgForm.rut}
                            onChange={(e) => setOrgForm({ ...orgForm, rut: e.target.value })}
                            className="form-input"
                            data-testid="org-rut-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Plan</Label>
                          <Select value={orgForm.plan} onValueChange={(v) => setOrgForm({ ...orgForm, plan: v })}>
                            <SelectTrigger className="form-input">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-dark-surface border-cyan-accent/20">
                              <SelectItem value="basico">Básico</SelectItem>
                              <SelectItem value="profesional">Profesional (8 UF)</SelectItem>
                              <SelectItem value="enterprise">Enterprise</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowAddOrg(false)} className="btn-outline">Cancelar</Button>
                        <Button onClick={handleCreateOrg} className="btn-primary" data-testid="save-org-btn">
                          Crear Empresa
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
                <div className="p-6">
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <div className="spinner"></div>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-cyan-accent/10">
                            <TableHead className="text-cyan-accent">Empresa</TableHead>
                            <TableHead className="text-cyan-accent">RUT</TableHead>
                            <TableHead className="text-cyan-accent">Plan</TableHead>
                            <TableHead className="text-cyan-accent">Límites</TableHead>
                            <TableHead className="text-cyan-accent">Inicio Actividades</TableHead>
                            <TableHead className="text-cyan-accent">Estado</TableHead>
                            <TableHead className="text-right text-cyan-accent">Acciones</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {organizations.map((org) => (
                            <TableRow key={org.id} className="border-cyan-accent/5 hover:bg-cyan-accent/5">
                              <TableCell className="font-medium text-white">{org.name}</TableCell>
                              <TableCell className="text-slate-400">{org.rut || '-'}</TableCell>
                              <TableCell>
                                <Select defaultValue={org.plan || 'profesional'}>
                                  <SelectTrigger className="w-40 bg-dark-input border-cyan-accent/20 text-white">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent className="bg-dark-surface border-cyan-accent/20">
                                    <SelectItem value="basico">Básico</SelectItem>
                                    <SelectItem value="profesional">Profesional (8 UF)</SelectItem>
                                    <SelectItem value="enterprise">Enterprise</SelectItem>
                                  </SelectContent>
                                </Select>
                              </TableCell>
                              <TableCell className="text-slate-400">
                                <div className="text-sm">
                                  <p>{org.user_limit || 80} colaboradores</p>
                                  <p className="text-slate-500">{org.location_limit || 10} faenas</p>
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-400">{org.start_date || 'Sin definir'}</TableCell>
                              <TableCell>
                                <Badge className={org.is_active ? 'badge-low' : 'badge-closed'}>
                                  {org.is_active ? 'Activa' : 'Inactiva'}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className={org.is_active 
                                      ? 'text-yellow-400 border-yellow-400/30 hover:bg-yellow-400/10' 
                                      : 'text-success-green border-success-green/30 hover:bg-success-green/10'}
                                    onClick={() => handleToggleOrg(org.id, org.is_active ? 'deactivate' : 'activate')}
                                  >
                                    <Power className="w-4 h-4 mr-1" />
                                    {org.is_active ? 'Desactivar' : 'Activar'}
                                  </Button>
                                  <Button size="sm" variant="outline" className="text-cyan-accent border-cyan-accent/30 hover:bg-cyan-accent/10">
                                    <RotateCcw className="w-4 h-4 mr-1" />
                                    Resetear
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="text-red-400 border-red-400/30 hover:bg-red-400/10"
                                    onClick={() => handleDeleteOrg(org.id)}
                                  >
                                    <Trash2 className="w-4 h-4 mr-1" />
                                    Eliminar
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                          {organizations.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                                No hay organizaciones registradas
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="modulos">
              <div className="card-dark">
                <div className="p-6 border-b border-cyan-accent/10">
                  <h3 className="text-lg font-semibold text-white font-display">Gestión de Módulos</h3>
                </div>
                <div className="p-6 text-center py-12 text-slate-500">
                  Configuración de módulos disponibles próximamente
                </div>
              </div>
            </TabsContent>

            <TabsContent value="cobros">
              <div className="card-dark">
                <div className="p-6 border-b border-cyan-accent/10">
                  <h3 className="text-lg font-semibold text-white font-display">Control de Cobros</h3>
                </div>
                <div className="p-6 text-center py-12 text-slate-500">
                  Sistema de facturación próximamente
                </div>
              </div>
            </TabsContent>

            <TabsContent value="seguridad">
              <div className="card-dark">
                <div className="p-6 border-b border-cyan-accent/10">
                  <h3 className="text-lg font-semibold text-white font-display">Configuración de Seguridad</h3>
                </div>
                <div className="p-6 text-center py-12 text-slate-500">
                  Ajustes de seguridad global próximamente
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
