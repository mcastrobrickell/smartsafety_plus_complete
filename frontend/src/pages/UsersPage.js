import React, { useState, useEffect } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import {
  Users,
  UserPlus,
  Edit,
  Trash2,
  Shield,
  Mail,
  Calendar
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ROLES = [
  { value: 'admin', label: 'Administrador' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'inspector', label: 'Inspector' },
  { value: 'viewer', label: 'Solo Lectura' }
];

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'inspector'
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

  const handleUpdateRole = async () => {
    if (!selectedUser) return;
    try {
      await axios.put(`${API_URL}/api/users/${selectedUser.id}/role?role=${selectedUser.newRole}`);
      toast.success('Rol actualizado');
      setShowEditDialog(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      toast.error('Error al actualizar rol');
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
      role: 'inspector'
    });
  };

  const openEditDialog = (user) => {
    setSelectedUser({ ...user, newRole: user.role });
    setShowEditDialog(true);
  };

  const getRoleBadge = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      supervisor: 'bg-blue-100 text-blue-800',
      inspector: 'bg-green-100 text-green-800',
      viewer: 'bg-slate-100 text-slate-800'
    };
    return colors[role] || 'bg-slate-100 text-slate-800';
  };

  const getRoleLabel = (role) => {
    const labels = {
      admin: 'Administrador',
      supervisor: 'Supervisor',
      inspector: 'Inspector',
      viewer: 'Solo Lectura'
    };
    return labels[role] || role;
  };

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="users-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Gestión de Usuarios">
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="bg-amber-500 hover:bg-amber-400 text-slate-900 rounded-sm gap-2" data-testid="add-user-btn">
                <UserPlus className="w-4 h-4" />
                Nuevo Usuario
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-['Manrope']">Crear Nuevo Usuario</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Nombre Completo</Label>
                  <Input
                    placeholder="Juan Pérez"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="rounded-sm"
                    data-testid="user-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Correo Electrónico</Label>
                  <Input
                    type="email"
                    placeholder="correo@empresa.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="rounded-sm"
                    data-testid="user-email-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Contraseña</Label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="rounded-sm"
                    data-testid="user-password-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Rol</Label>
                  <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                    <SelectTrigger className="rounded-sm" data-testid="user-role-select">
                      <SelectValue placeholder="Seleccionar rol" />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLES.map((role) => (
                        <SelectItem key={role.value} value={role.value}>{role.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)} className="rounded-sm">
                  Cancelar
                </Button>
                <Button onClick={handleCreate} className="bg-slate-900 hover:bg-slate-800 rounded-sm" data-testid="create-user-btn">
                  Crear Usuario
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TopBar>

        <div className="p-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="stat-card">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 bg-slate-100 rounded-sm">
                  <Users className="w-6 h-6 text-slate-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900 font-['Manrope']">{users.length}</p>
                  <p className="text-sm text-slate-600">Usuarios Totales</p>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-sm">
                  <Shield className="w-6 h-6 text-purple-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-purple-600 font-['Manrope']">
                    {users.filter(u => u.role === 'admin').length}
                  </p>
                  <p className="text-sm text-slate-600">Administradores</p>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-sm">
                  <Users className="w-6 h-6 text-blue-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-blue-600 font-['Manrope']">
                    {users.filter(u => u.role === 'supervisor').length}
                  </p>
                  <p className="text-sm text-slate-600">Supervisores</p>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-sm">
                  <Users className="w-6 h-6 text-green-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600 font-['Manrope']">
                    {users.filter(u => u.role === 'inspector').length}
                  </p>
                  <p className="text-sm text-slate-600">Inspectores</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Users Table */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="font-['Manrope']">Lista de Usuarios</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="spinner"></div>
                </div>
              ) : users.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuario</TableHead>
                      <TableHead>Correo</TableHead>
                      <TableHead>Rol</TableHead>
                      <TableHead>Fecha Registro</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id} data-testid={`user-row-${user.id}`}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center">
                              <span className="text-white font-semibold text-sm">
                                {user.name?.charAt(0)?.toUpperCase() || 'U'}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-slate-900">{user.name}</p>
                              {user.id === currentUser?.id && (
                                <span className="text-xs text-slate-500">(Tú)</span>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 text-sm text-slate-600">
                            <Mail className="w-4 h-4" />
                            {user.email}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getRoleBadge(user.role)}>{getRoleLabel(user.role)}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 text-sm text-slate-500">
                            <Calendar className="w-4 h-4" />
                            {new Date(user.created_at).toLocaleDateString()}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={user.is_active ? 'badge-low' : 'badge-closed'}>
                            {user.is_active ? 'Activo' : 'Inactivo'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => openEditDialog(user)}
                              data-testid={`edit-user-${user.id}`}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            {user.id !== currentUser?.id && (
                              <Button
                                size="icon"
                                variant="ghost"
                                className="text-red-600 hover:text-red-700"
                                onClick={() => handleDelete(user.id)}
                                data-testid={`delete-user-${user.id}`}
                              >
                                <Trash2 className="w-4 h-4" />
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
                  <Users className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-500">No hay usuarios registrados</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Edit Role Dialog */}
          <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-['Manrope']">Editar Rol de Usuario</DialogTitle>
              </DialogHeader>
              {selectedUser && (
                <div className="space-y-4 py-4">
                  <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-sm">
                    <div className="w-12 h-12 bg-slate-900 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold">
                        {selectedUser.name?.charAt(0)?.toUpperCase() || 'U'}
                      </span>
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{selectedUser.name}</p>
                      <p className="text-sm text-slate-500">{selectedUser.email}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Nuevo Rol</Label>
                    <Select 
                      value={selectedUser.newRole} 
                      onValueChange={(v) => setSelectedUser({ ...selectedUser, newRole: v })}
                    >
                      <SelectTrigger className="rounded-sm" data-testid="edit-role-select">
                        <SelectValue placeholder="Seleccionar rol" />
                      </SelectTrigger>
                      <SelectContent>
                        {ROLES.map((role) => (
                          <SelectItem key={role.value} value={role.value}>{role.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowEditDialog(false)} className="rounded-sm">
                  Cancelar
                </Button>
                <Button onClick={handleUpdateRole} className="bg-slate-900 hover:bg-slate-800 rounded-sm" data-testid="save-role-btn">
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
