import React, { useState, useEffect } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';
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
  ChevronDown,
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
    <div className="flex min-h-screen bg-slate-50" data-testid="superadmin-page">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="font-bold">
                <span className="text-blue-600">Smart</span>
                <span className="text-orange-500">Safety+</span>
              </div>
              <div className="text-xs text-slate-500">Enterprise 2026</div>
            </div>
          </div>
        </div>

        {/* Super Admin Section */}
        <div className="p-4">
          <p className="text-xs font-semibold text-orange-500 uppercase tracking-wider mb-3">
            Super Admin
          </p>
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all ${
                item.active
                  ? 'bg-blue-500 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </div>

        {/* Organization Selector */}
        <div className="p-4 border-t border-slate-200">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Gestionar Empresa
          </p>
          <Select defaultValue="all">
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Seleccionar empresa" />
            </SelectTrigger>
            <SelectContent>
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
        <div className="p-4 border-t border-slate-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">S</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">Super Administrador</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <Button
            variant="outline"
            className="w-full justify-start gap-2 rounded-lg"
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
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <h1 className="text-3xl font-bold">
            <span className="text-green-500">SUPER ADMIN</span>
            <span className="text-blue-500"> PANEL</span>
          </h1>
          <p className="text-slate-500 mt-1">Administración global de SmartSafety+</p>
        </header>

        <div className="p-8 space-y-8">
          {/* Tabs */}
          <Tabs defaultValue="empresas" className="space-y-6">
            <TabsList className="bg-white border border-slate-200 p-1">
              <TabsTrigger value="empresas" className="gap-2 data-[state=active]:bg-slate-100">
                <Building2 className="w-4 h-4" />
                Empresas
              </TabsTrigger>
              <TabsTrigger value="modulos" className="gap-2 data-[state=active]:bg-slate-100">
                <Settings className="w-4 h-4" />
                Módulos
              </TabsTrigger>
              <TabsTrigger value="cobros" className="gap-2 data-[state=active]:bg-slate-100">
                <CreditCard className="w-4 h-4" />
                Control de Cobros
              </TabsTrigger>
              <TabsTrigger value="seguridad" className="gap-2 data-[state=active]:bg-slate-100">
                <Lock className="w-4 h-4" />
                Seguridad
              </TabsTrigger>
            </TabsList>

            <TabsContent value="empresas" className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="border-slate-200">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Organizaciones</p>
                        <p className="text-3xl font-bold text-slate-900 mt-1">
                          {stats?.total_organizations || organizations.length}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          {stats?.active_organizations || organizations.filter(o => o.is_active).length} activas
                        </p>
                      </div>
                      <Building2 className="w-10 h-10 text-slate-300" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-slate-200">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Usuarios Totales</p>
                        <p className="text-3xl font-bold text-slate-900 mt-1">
                          {stats?.total_users || 0}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">En todas las organizaciones</p>
                      </div>
                      <Users className="w-10 h-10 text-slate-300" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-slate-200">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Prevencionistas</p>
                        <p className="text-3xl font-bold text-slate-900 mt-1">
                          {stats?.total_preventionists || 0}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Personal gestionado</p>
                      </div>
                      <HardHat className="w-10 h-10 text-slate-300" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-slate-200">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Faenas Totales</p>
                        <p className="text-3xl font-bold text-slate-900 mt-1">
                          {stats?.total_locations || 0}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Centros de operación</p>
                      </div>
                      <MapPin className="w-10 h-10 text-slate-300" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Distribution by Plan */}
              <Card className="border-slate-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-500" />
                    Distribución por Plan
                  </CardTitle>
                  <p className="text-sm text-slate-500">Suscripciones activas</p>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center py-8">
                    <div className="text-center">
                      <p className="text-5xl font-bold text-slate-900">
                        {organizations.filter(o => o.is_active).length}
                      </p>
                      <p className="text-slate-500 mt-2">Profesional</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Organizations Table */}
              <Card className="border-slate-200">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Organizaciones Registradas</CardTitle>
                    <p className="text-sm text-slate-500 mt-1">Gestiona todas las empresas del sistema</p>
                  </div>
                  <Dialog open={showAddOrg} onOpenChange={setShowAddOrg}>
                    <DialogTrigger asChild>
                      <Button className="bg-blue-500 hover:bg-blue-600 rounded-lg gap-2" data-testid="add-org-btn">
                        <Plus className="w-4 h-4" />
                        Nueva Empresa
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Crear Nueva Organización</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label>Nombre de la Empresa</Label>
                          <Input
                            placeholder="Empresa Demo S.A."
                            value={orgForm.name}
                            onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                            className="rounded-lg"
                            data-testid="org-name-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>RUT</Label>
                          <Input
                            placeholder="76.123.456-7"
                            value={orgForm.rut}
                            onChange={(e) => setOrgForm({ ...orgForm, rut: e.target.value })}
                            className="rounded-lg"
                            data-testid="org-rut-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Plan</Label>
                          <Select value={orgForm.plan} onValueChange={(v) => setOrgForm({ ...orgForm, plan: v })}>
                            <SelectTrigger className="rounded-lg">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="basico">Básico</SelectItem>
                              <SelectItem value="profesional">Profesional (8 UF)</SelectItem>
                              <SelectItem value="enterprise">Enterprise</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowAddOrg(false)}>Cancelar</Button>
                        <Button onClick={handleCreateOrg} className="bg-blue-500 hover:bg-blue-600" data-testid="save-org-btn">
                          Crear Empresa
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <div className="spinner"></div>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Empresa</TableHead>
                          <TableHead>RUT</TableHead>
                          <TableHead>Plan</TableHead>
                          <TableHead>Límites</TableHead>
                          <TableHead>Inicio Actividades</TableHead>
                          <TableHead>Estado</TableHead>
                          <TableHead className="text-right">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {organizations.map((org) => (
                          <TableRow key={org.id}>
                            <TableCell className="font-medium">{org.name}</TableCell>
                            <TableCell>{org.rut || '-'}</TableCell>
                            <TableCell>
                              <Select defaultValue={org.plan || 'profesional'}>
                                <SelectTrigger className="w-40">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="basico">Básico</SelectItem>
                                  <SelectItem value="profesional">Profesional (8 UF)</SelectItem>
                                  <SelectItem value="enterprise">Enterprise</SelectItem>
                                </SelectContent>
                              </Select>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                <p>{org.user_limit || 80} colaboradores</p>
                                <p className="text-slate-500">{org.location_limit || 10} faenas</p>
                              </div>
                            </TableCell>
                            <TableCell>{org.start_date || 'Sin definir'}</TableCell>
                            <TableCell>
                              <Badge className={org.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}>
                                {org.is_active ? 'Activa' : 'Inactiva'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className={org.is_active ? 'text-yellow-600 border-yellow-300' : 'text-green-600 border-green-300'}
                                  onClick={() => handleToggleOrg(org.id, org.is_active ? 'deactivate' : 'activate')}
                                >
                                  <Power className="w-4 h-4 mr-1" />
                                  {org.is_active ? 'Desactivar' : 'Activar'}
                                </Button>
                                <Button size="sm" variant="outline" className="text-blue-600 border-blue-300">
                                  <RotateCcw className="w-4 h-4 mr-1" />
                                  Resetear
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-red-600 border-red-300"
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
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="modulos">
              <Card className="border-slate-200">
                <CardHeader>
                  <CardTitle>Gestión de Módulos</CardTitle>
                </CardHeader>
                <CardContent className="text-center py-12 text-slate-500">
                  Configuración de módulos disponibles próximamente
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="cobros">
              <Card className="border-slate-200">
                <CardHeader>
                  <CardTitle>Control de Cobros</CardTitle>
                </CardHeader>
                <CardContent className="text-center py-12 text-slate-500">
                  Sistema de facturación próximamente
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="seguridad">
              <Card className="border-slate-200">
                <CardHeader>
                  <CardTitle>Configuración de Seguridad</CardTitle>
                </CardHeader>
                <CardContent className="text-center py-12 text-slate-500">
                  Ajustes de seguridad global próximamente
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
