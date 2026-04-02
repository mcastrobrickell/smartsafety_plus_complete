import React, { useState, useEffect } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Users,
  UserPlus,
  Edit,
  Trash2,
  Shield,
  Mail,
  Phone,
  Calendar,
  HardHat,
  Briefcase,
  MapPin,
  FileText,
  Download
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ROLES = [
  { value: 'admin', label: 'Administrador' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'prevencionista', label: 'Prevencionista' },
  { value: 'inspector', label: 'Inspector' },
  { value: 'viewer', label: 'Solo Lectura' }
];

const SPECIALIZATIONS = [
  'Seguridad Industrial',
  'Higiene Ocupacional',
  'Medio Ambiente',
  'Ergonomía',
  'Psicosociología',
  'Prevención General'
];

export default function ProfilesPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [activeTab, setActiveTab] = useState('admins');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'prevencionista',
    phone: '',
    specialization: '',
    certifications: '',
    location: ''
  });
  const { user: currentUser } = useAuth();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await axios.post(`${API_URL}/api/auth/register`, formData);
      toast.success('Usuario creado correctamente');
      setShowAddDialog(false);
      resetForm();
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear usuario');
    }
  };

  const handleUpdate = async () => {
    if (!selectedUser) return;
    try {
      await axios.put(`${API_URL}/api/users/${selectedUser.id}/profile`, {
        name: formData.name,
        role: formData.role,
        phone: formData.phone,
        specialization: formData.specialization,
        certifications: formData.certifications,
        location: formData.location
      });
      toast.success('Perfil actualizado');
      setShowEditDialog(false);
      fetchUsers();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('¿Eliminar este usuario?')) return;
    if (userId === currentUser?.id) {
      toast.error('No puedes eliminar tu propia cuenta');
      return;
    }
    try {
      await axios.delete(`${API_URL}/api/users/${userId}`);
      toast.success('Usuario eliminado');
      fetchUsers();
    } catch (error) {
      toast.error('Error al eliminar usuario');
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      name: '',
      role: 'prevencionista',
      phone: '',
      specialization: '',
      certifications: '',
      location: ''
    });
  };

  const openEditDialog = (user) => {
    setSelectedUser(user);
    setFormData({
      email: user.email,
      password: '',
      name: user.name,
      role: user.role,
      phone: user.phone || '',
      specialization: user.specialization || '',
      certifications: user.certifications || '',
      location: user.location || ''
    });
    setShowEditDialog(true);
  };

  const getRoleBadge = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      supervisor: 'bg-blue-100 text-blue-800',
      prevencionista: 'bg-orange-100 text-orange-800',
      inspector: 'bg-green-100 text-green-800',
      viewer: 'bg-slate-100 text-slate-800'
    };
    return colors[role] || 'bg-slate-100 text-slate-800';
  };

  const getRoleLabel = (role) => {
    const labels = {
      admin: 'Administrador',
      supervisor: 'Supervisor',
      prevencionista: 'Prevencionista',
      inspector: 'Inspector',
      viewer: 'Solo Lectura'
    };
    return labels[role] || role;
  };

  const admins = users.filter(u => u.role === 'admin' || u.role === 'supervisor');
  const preventionists = users.filter(u => u.role === 'prevencionista' || u.role === 'inspector');

  const exportPDF = async (userId) => {
    try {
      const response = await axios.get(`${API_URL}/api/users/${userId}/export-pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `perfil-${userId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF exportado');
    } catch (error) {
      toast.error('Error al exportar PDF');
    }
  };

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="profiles-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Gestión de Perfiles">
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="btn-primary rounded-lg gap-2" data-testid="add-profile-btn">
                <UserPlus className="w-4 h-4" />
                Nuevo Usuario
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Crear Nuevo Usuario</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2 col-span-2">
                    <Label>Nombre Completo</Label>
                    <Input
                      placeholder="Juan Pérez"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="rounded-lg"
                      data-testid="profile-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Correo Electrónico</Label>
                    <Input
                      type="email"
                      placeholder="correo@empresa.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="rounded-lg"
                      data-testid="profile-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Contraseña</Label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="rounded-lg"
                      data-testid="profile-password-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Rol</Label>
                    <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                      <SelectTrigger className="rounded-lg" data-testid="profile-role-select">
                        <SelectValue placeholder="Seleccionar rol" />
                      </SelectTrigger>
                      <SelectContent>
                        {ROLES.map((role) => (
                          <SelectItem key={role.value} value={role.value}>{role.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Teléfono</Label>
                    <Input
                      placeholder="+56 9 1234 5678"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="rounded-lg"
                    />
                  </div>
                  {(formData.role === 'prevencionista' || formData.role === 'inspector') && (
                    <>
                      <div className="space-y-2">
                        <Label>Especialización</Label>
                        <Select value={formData.specialization} onValueChange={(v) => setFormData({ ...formData, specialization: v })}>
                          <SelectTrigger className="rounded-lg">
                            <SelectValue placeholder="Seleccionar" />
                          </SelectTrigger>
                          <SelectContent>
                            {SPECIALIZATIONS.map((spec) => (
                              <SelectItem key={spec} value={spec}>{spec}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Ubicación/Faena</Label>
                        <Input
                          placeholder="Planta Norte"
                          value={formData.location}
                          onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                      <div className="space-y-2 col-span-2">
                        <Label>Certificaciones</Label>
                        <Textarea
                          placeholder="Lista de certificaciones separadas por coma"
                          value={formData.certifications}
                          onChange={(e) => setFormData({ ...formData, certifications: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)} className="rounded-lg">
                  Cancelar
                </Button>
                <Button onClick={handleCreate} className="btn-primary rounded-lg" data-testid="save-profile-btn">
                  Crear Usuario
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TopBar>

        <div className="p-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-dark-surface border border-cyan-accent/10 p-1">
              <TabsTrigger value="admins" className="gap-2 data-[state=active]:bg-slate-100">
                <Shield className="w-4 h-4" />
                Administradores ({admins.length})
              </TabsTrigger>
              <TabsTrigger value="preventionists" className="gap-2 data-[state=active]:bg-slate-100">
                <HardHat className="w-4 h-4" />
                Prevencionistas ({preventionists.length})
              </TabsTrigger>
            </TabsList>

            {/* Admins Tab */}
            <TabsContent value="admins">
              <Card className="border-cyan-accent/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-500" />
                    Usuarios Administradores
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <div className="spinner"></div>
                    </div>
                  ) : admins.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {admins.map((user) => (
                        <Card key={user.id} className="border-cyan-accent/10 hover:shadow-md transition-shadow">
                          <CardContent className="p-6">
                            <div className="flex items-start gap-4">
                              <Avatar className="w-14 h-14">
                                <AvatarFallback className="bg-purple-500 text-white text-lg">
                                  {user.name?.charAt(0)?.toUpperCase() || 'A'}
                                </AvatarFallback>
                              </Avatar>
                              <div className="flex-1 min-w-0">
                                <h3 className="font-semibold text-white truncate">{user.name}</h3>
                                <Badge className={`${getRoleBadge(user.role)} mt-1`}>
                                  {getRoleLabel(user.role)}
                                </Badge>
                              </div>
                            </div>
                            <div className="mt-4 space-y-2 text-sm">
                              <div className="flex items-center gap-2 text-slate-400">
                                <Mail className="w-4 h-4" />
                                <span className="truncate">{user.email}</span>
                              </div>
                              {user.phone && (
                                <div className="flex items-center gap-2 text-slate-400">
                                  <Phone className="w-4 h-4" />
                                  <span>{user.phone}</span>
                                </div>
                              )}
                              <div className="flex items-center gap-2 text-slate-500">
                                <Calendar className="w-4 h-4" />
                                <span>{new Date(user.created_at).toLocaleDateString()}</span>
                              </div>
                            </div>
                            <div className="flex gap-2 mt-4">
                              <Button
                                size="sm"
                                variant="outline"
                                className="flex-1 rounded-lg"
                                onClick={() => openEditDialog(user)}
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                Editar
                              </Button>
                              {user.id !== currentUser?.id && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-red-600 border-red-200 rounded-lg"
                                  onClick={() => handleDelete(user.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Users className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay administradores registrados</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Preventionists Tab */}
            <TabsContent value="preventionists">
              <Card className="border-cyan-accent/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HardHat className="w-5 h-5 text-orange-500" />
                    Prevencionistas e Inspectores
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <div className="spinner"></div>
                    </div>
                  ) : preventionists.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Prevencionista</TableHead>
                          <TableHead>Rol</TableHead>
                          <TableHead>Especialización</TableHead>
                          <TableHead>Ubicación</TableHead>
                          <TableHead>Contacto</TableHead>
                          <TableHead className="text-right">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {preventionists.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell>
                              <div className="flex items-center gap-3">
                                <Avatar className="w-10 h-10">
                                  <AvatarFallback className="bg-orange-500 text-white">
                                    {user.name?.charAt(0)?.toUpperCase() || 'P'}
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="font-medium text-white">{user.name}</p>
                                  <p className="text-xs text-slate-500">{user.email}</p>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge className={getRoleBadge(user.role)}>
                                {getRoleLabel(user.role)}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {user.specialization || (
                                <span className="text-slate-400">Sin definir</span>
                              )}
                            </TableCell>
                            <TableCell>
                              {user.location ? (
                                <div className="flex items-center gap-1 text-sm">
                                  <MapPin className="w-3 h-3" />
                                  {user.location}
                                </div>
                              ) : (
                                <span className="text-slate-400">-</span>
                              )}
                            </TableCell>
                            <TableCell>
                              {user.phone || <span className="text-slate-400">-</span>}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="rounded-lg"
                                  onClick={() => openEditDialog(user)}
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="rounded-lg"
                                  onClick={() => exportPDF(user.id)}
                                >
                                  <Download className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-red-600 border-red-200 rounded-lg"
                                  onClick={() => handleDelete(user.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <HardHat className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay prevencionistas registrados</p>
                      <Button
                        className="mt-4 btn-primary rounded-lg"
                        onClick={() => {
                          setFormData({ ...formData, role: 'prevencionista' });
                          setShowAddDialog(true);
                        }}
                      >
                        Agregar Prevencionista
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Edit Dialog */}
          <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Editar Perfil</DialogTitle>
              </DialogHeader>
              {selectedUser && (
                <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                  <div className="flex items-center gap-4 p-4 bg-dark-bg rounded-lg">
                    <Avatar className="w-14 h-14">
                      <AvatarFallback className="bg-blue-500 text-white text-lg">
                        {selectedUser.name?.charAt(0)?.toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-semibold text-white">{selectedUser.name}</p>
                      <p className="text-sm text-slate-500">{selectedUser.email}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2 col-span-2">
                      <Label>Nombre</Label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="rounded-lg"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Rol</Label>
                      <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                        <SelectTrigger className="rounded-lg">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ROLES.map((role) => (
                            <SelectItem key={role.value} value={role.value}>{role.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Teléfono</Label>
                      <Input
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="rounded-lg"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Especialización</Label>
                      <Select value={formData.specialization} onValueChange={(v) => setFormData({ ...formData, specialization: v })}>
                        <SelectTrigger className="rounded-lg">
                          <SelectValue placeholder="Seleccionar" />
                        </SelectTrigger>
                        <SelectContent>
                          {SPECIALIZATIONS.map((spec) => (
                            <SelectItem key={spec} value={spec}>{spec}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Ubicación</Label>
                      <Input
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        className="rounded-lg"
                      />
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label>Certificaciones</Label>
                      <Textarea
                        value={formData.certifications}
                        onChange={(e) => setFormData({ ...formData, certifications: e.target.value })}
                        className="rounded-lg"
                      />
                    </div>
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowEditDialog(false)} className="rounded-lg">
                  Cancelar
                </Button>
                <Button onClick={handleUpdate} className="btn-primary rounded-lg">
                  Guardar Cambios
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
