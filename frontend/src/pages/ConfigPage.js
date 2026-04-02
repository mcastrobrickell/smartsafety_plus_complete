import React, { useState, useEffect } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Switch } from '../components/ui/switch';
import {
  Settings,
  Plus,
  Edit,
  Trash2,
  Tag,
  AlertTriangle,
  HardHat,
  Building2,
  Save,
  Upload,
  Image,
  X
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CATEGORY_TYPES = [
  { value: 'risk', label: 'Tipos de Riesgo', icon: AlertTriangle, color: 'text-orange-500' },
  { value: 'epp', label: 'Categorias EPP', icon: HardHat, color: 'text-blue-500' },
  { value: 'incident', label: 'Tipos de Incidente', icon: Tag, color: 'text-red-500' },
  { value: 'area', label: 'Areas de Trabajo', icon: Building2, color: 'text-green-500' }
];

export default function ConfigPage() {
  const [categories, setCategories] = useState([]);
  const [costCenters, setCostCenters] = useState([]);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('organization');
  const [showCategoryDialog, setShowCategoryDialog] = useState(false);
  const [showCostCenterDialog, setShowCostCenterDialog] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingCostCenter, setEditingCostCenter] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [orgName, setOrgName] = useState('');
  
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    type: 'risk',
    description: '',
    is_active: true
  });
  
  const [costCenterForm, setCostCenterForm] = useState({
    code: '',
    name: '',
    description: '',
    is_active: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [catRes, ccRes, orgRes] = await Promise.all([
        axios.get(`${API_URL}/api/config/categories`),
        axios.get(`${API_URL}/api/cost-centers`),
        axios.get(`${API_URL}/api/organization/current`)
      ]);
      setCategories(catRes.data);
      setCostCenters(ccRes.data);
      setOrganization(orgRes.data);
      setOrgName(orgRes.data?.name || '');
    } catch (error) {
      toast.error('Error al cargar configuracion');
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Solo se permiten imágenes PNG, JPEG o WebP');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('El archivo no debe superar 2MB');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/api/organization/current/logo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Logo subido correctamente');
      setOrganization({ ...organization, logo_url: response.data.logo_url });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al subir logo');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteLogo = async () => {
    if (!window.confirm('¿Eliminar el logo de la organización?')) return;

    try {
      await axios.delete(`${API_URL}/api/organization/current/logo`);
      toast.success('Logo eliminado');
      setOrganization({ ...organization, logo_url: null });
    } catch (error) {
      toast.error('Error al eliminar logo');
    }
  };

  const handleUpdateOrgName = async () => {
    if (!orgName.trim()) {
      toast.error('El nombre no puede estar vacío');
      return;
    }

    try {
      const response = await axios.put(`${API_URL}/api/organization/current`, { name: orgName });
      toast.success('Nombre actualizado');
      setOrganization(response.data);
    } catch (error) {
      toast.error('Error al actualizar nombre');
    }
  };

  // Categories CRUD
  const handleSaveCategory = async () => {
    try {
      if (editingCategory) {
        await axios.put(`${API_URL}/api/config/categories/${editingCategory.id}`, categoryForm);
        toast.success('Categoria actualizada');
      } else {
        await axios.post(`${API_URL}/api/config/categories`, categoryForm);
        toast.success('Categoria creada');
      }
      setShowCategoryDialog(false);
      resetCategoryForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar');
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (!window.confirm('¿Eliminar esta categoria?')) return;
    try {
      await axios.delete(`${API_URL}/api/config/categories/${categoryId}`);
      toast.success('Categoria eliminada');
      fetchData();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const editCategory = (category) => {
    setEditingCategory(category);
    setCategoryForm({
      name: category.name,
      type: category.type,
      description: category.description || '',
      is_active: category.is_active !== false
    });
    setShowCategoryDialog(true);
  };

  const resetCategoryForm = () => {
    setEditingCategory(null);
    setCategoryForm({ name: '', type: 'risk', description: '', is_active: true });
  };

  // Cost Centers CRUD
  const handleSaveCostCenter = async () => {
    try {
      if (editingCostCenter) {
        await axios.put(`${API_URL}/api/cost-centers/${editingCostCenter.id}`, costCenterForm);
        toast.success('Centro de costo actualizado');
      } else {
        await axios.post(`${API_URL}/api/cost-centers`, costCenterForm);
        toast.success('Centro de costo creado');
      }
      setShowCostCenterDialog(false);
      resetCostCenterForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar');
    }
  };

  const handleDeleteCostCenter = async (centerId) => {
    if (!window.confirm('¿Eliminar este centro de costo?')) return;
    try {
      await axios.delete(`${API_URL}/api/cost-centers/${centerId}`);
      toast.success('Centro de costo eliminado');
      fetchData();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const editCostCenter = (center) => {
    setEditingCostCenter(center);
    setCostCenterForm({
      code: center.code,
      name: center.name,
      description: center.description || '',
      is_active: center.is_active !== false
    });
    setShowCostCenterDialog(true);
  };

  const resetCostCenterForm = () => {
    setEditingCostCenter(null);
    setCostCenterForm({ code: '', name: '', description: '', is_active: true });
  };

  const getCategoryTypeInfo = (type) => {
    return CATEGORY_TYPES.find(t => t.value === type) || CATEGORY_TYPES[0];
  };

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="config-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar 
          title="Configuracion del Sistema" 
          subtitle="Gestiona categorias, tipos y centros de costo"
        />

        <div className="p-8">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full max-w-lg grid-cols-3 mb-6">
              <TabsTrigger value="organization" className="gap-2">
                <Image className="w-4 h-4" />
                Organización
              </TabsTrigger>
              <TabsTrigger value="categories" className="gap-2">
                <Tag className="w-4 h-4" />
                Categorías
              </TabsTrigger>
              <TabsTrigger value="cost-centers" className="gap-2">
                <Building2 className="w-4 h-4" />
                Centros de Costo
              </TabsTrigger>
            </TabsList>

            {/* Organization Tab */}
            <TabsContent value="organization" className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white">Configuración de la Organización</h2>
                <p className="text-sm text-slate-500">Personaliza el logo y nombre de tu organización</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Logo Upload Card */}
                <Card className="border-cyan-accent/10">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Image className="w-5 h-5 text-blue-500" />
                      Logo de la Organización
                    </CardTitle>
                    <CardDescription>
                      Sube el logo que aparecerá en reportes y documentos PDF
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Logo Preview */}
                    <div className="flex justify-center">
                      {organization?.logo_url ? (
                        <div className="relative group">
                          <img
                            src={`${API_URL}${organization.logo_url}`}
                            alt="Logo de la organización"
                            className="max-h-32 max-w-full object-contain rounded-lg border border-cyan-accent/10 p-2"
                            data-testid="org-logo-preview"
                          />
                          <button
                            onClick={handleDeleteLogo}
                            className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                            data-testid="delete-logo-btn"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="w-32 h-32 bg-slate-100 rounded-lg flex items-center justify-center border-2 border-dashed border-slate-300">
                          <Image className="w-12 h-12 text-slate-300" />
                        </div>
                      )}
                    </div>

                    {/* Upload Button */}
                    <div className="flex justify-center">
                      <label className="cursor-pointer">
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          onChange={handleLogoUpload}
                          className="hidden"
                          data-testid="logo-upload-input"
                        />
                        <Button
                          variant="outline"
                          className="gap-2"
                          disabled={uploading}
                          asChild
                        >
                          <span>
                            <Upload className="w-4 h-4" />
                            {uploading ? 'Subiendo...' : organization?.logo_url ? 'Cambiar Logo' : 'Subir Logo'}
                          </span>
                        </Button>
                      </label>
                    </div>

                    <p className="text-xs text-slate-500 text-center">
                      Formatos: PNG, JPEG, WebP. Máx: 2MB
                    </p>
                  </CardContent>
                </Card>

                {/* Organization Name Card */}
                <Card className="border-cyan-accent/10">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-green-500" />
                      Datos de la Organización
                    </CardTitle>
                    <CardDescription>
                      Configura el nombre que aparecerá en los reportes
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Nombre de la Organización</Label>
                      <Input
                        value={orgName}
                        onChange={(e) => setOrgName(e.target.value)}
                        placeholder="Nombre de tu empresa"
                        className="rounded-lg"
                        data-testid="org-name-input"
                      />
                    </div>
                    <Button 
                      onClick={handleUpdateOrgName} 
                      className="w-full btn-primary gap-2"
                      data-testid="save-org-name-btn"
                    >
                      <Save className="w-4 h-4" />
                      Guardar Nombre
                    </Button>

                    {organization && (
                      <div className="pt-4 border-t border-cyan-accent/10">
                        <p className="text-xs text-slate-500">
                          Última actualización: {organization.updated_at ? new Date(organization.updated_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Categories Tab */}
            <TabsContent value="categories" className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold text-white">Categorias Configurables</h2>
                  <p className="text-sm text-slate-500">Define los tipos de riesgos, EPP, incidentes y areas</p>
                </div>
                <Dialog open={showCategoryDialog} onOpenChange={(open) => {
                  setShowCategoryDialog(open);
                  if (!open) resetCategoryForm();
                }}>
                  <DialogTrigger asChild>
                    <Button className="btn-primary rounded-lg gap-2" data-testid="add-category-btn">
                      <Plus className="w-4 h-4" />
                      Nueva Categoria
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editingCategory ? 'Editar Categoria' : 'Nueva Categoria'}</DialogTitle>
                      <DialogDescription>Define una nueva categoria para el sistema</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label>Tipo de Categoria</Label>
                        <Select value={categoryForm.type} onValueChange={(v) => setCategoryForm({ ...categoryForm, type: v })}>
                          <SelectTrigger className="rounded-lg" data-testid="category-type-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CATEGORY_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                <div className="flex items-center gap-2">
                                  <type.icon className={`w-4 h-4 ${type.color}`} />
                                  {type.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Nombre</Label>
                        <Input
                          placeholder="Ej: Trabajo en Altura"
                          value={categoryForm.name}
                          onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                          className="rounded-lg"
                          data-testid="category-name-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Descripcion (Opcional)</Label>
                        <Input
                          placeholder="Breve descripcion..."
                          value={categoryForm.description}
                          onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Activa</Label>
                        <Switch
                          checked={categoryForm.is_active}
                          onCheckedChange={(checked) => setCategoryForm({ ...categoryForm, is_active: checked })}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowCategoryDialog(false)}>Cancelar</Button>
                      <Button onClick={handleSaveCategory} className="btn-primary gap-2">
                        <Save className="w-4 h-4" />
                        {editingCategory ? 'Guardar Cambios' : 'Crear Categoria'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              {/* Categories by Type */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {CATEGORY_TYPES.map((type) => {
                  const typeCategories = categories.filter(c => c.type === type.value);
                  return (
                    <Card key={type.value} className="border-cyan-accent/10">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          <type.icon className={`w-5 h-5 ${type.color}`} />
                          {type.label}
                          <Badge variant="outline" className="ml-auto">{typeCategories.length}</Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {typeCategories.length > 0 ? (
                          <div className="space-y-2">
                            {typeCategories.map((cat) => (
                              <div key={cat.id} className="flex items-center justify-between p-3 bg-dark-bg rounded-lg">
                                <div className="flex items-center gap-3">
                                  <div className={`w-2 h-2 rounded-full ${cat.is_active !== false ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                                  <div>
                                    <p className="font-medium text-white">{cat.name}</p>
                                    {cat.description && (
                                      <p className="text-xs text-slate-500">{cat.description}</p>
                                    )}
                                  </div>
                                </div>
                                <div className="flex gap-1">
                                  <Button size="icon" variant="ghost" onClick={() => editCategory(cat)}>
                                    <Edit className="w-4 h-4 text-slate-500" />
                                  </Button>
                                  <Button size="icon" variant="ghost" onClick={() => handleDeleteCategory(cat.id)}>
                                    <Trash2 className="w-4 h-4 text-red-500" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-400 text-center py-4">Sin categorias definidas</p>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>

            {/* Cost Centers Tab */}
            <TabsContent value="cost-centers" className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold text-white">Centros de Costo</h2>
                  <p className="text-sm text-slate-500">Gestiona los centros de costo para el seguimiento de EPP</p>
                </div>
                <Dialog open={showCostCenterDialog} onOpenChange={(open) => {
                  setShowCostCenterDialog(open);
                  if (!open) resetCostCenterForm();
                }}>
                  <DialogTrigger asChild>
                    <Button className="btn-primary rounded-lg gap-2" data-testid="add-cost-center-btn">
                      <Plus className="w-4 h-4" />
                      Nuevo Centro de Costo
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editingCostCenter ? 'Editar Centro de Costo' : 'Nuevo Centro de Costo'}</DialogTitle>
                      <DialogDescription>Define un centro de costo para el seguimiento</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Codigo</Label>
                          <Input
                            placeholder="CC-001"
                            value={costCenterForm.code}
                            onChange={(e) => setCostCenterForm({ ...costCenterForm, code: e.target.value })}
                            className="rounded-lg"
                            data-testid="cost-center-code-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Nombre</Label>
                          <Input
                            placeholder="Planta Norte"
                            value={costCenterForm.name}
                            onChange={(e) => setCostCenterForm({ ...costCenterForm, name: e.target.value })}
                            className="rounded-lg"
                            data-testid="cost-center-name-input"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Descripcion (Opcional)</Label>
                        <Input
                          placeholder="Descripcion del centro de costo..."
                          value={costCenterForm.description}
                          onChange={(e) => setCostCenterForm({ ...costCenterForm, description: e.target.value })}
                          className="rounded-lg"
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Activo</Label>
                        <Switch
                          checked={costCenterForm.is_active}
                          onCheckedChange={(checked) => setCostCenterForm({ ...costCenterForm, is_active: checked })}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowCostCenterDialog(false)}>Cancelar</Button>
                      <Button onClick={handleSaveCostCenter} className="btn-primary gap-2">
                        <Save className="w-4 h-4" />
                        {editingCostCenter ? 'Guardar Cambios' : 'Crear Centro'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              <Card className="border-cyan-accent/10">
                <CardContent className="p-0">
                  {costCenters.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Codigo</TableHead>
                          <TableHead>Nombre</TableHead>
                          <TableHead>Descripcion</TableHead>
                          <TableHead>Estado</TableHead>
                          <TableHead className="text-right">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {costCenters.map((center) => (
                          <TableRow key={center.id}>
                            <TableCell className="font-mono">{center.code}</TableCell>
                            <TableCell className="font-medium">{center.name}</TableCell>
                            <TableCell className="text-slate-500">{center.description || '-'}</TableCell>
                            <TableCell>
                              <Badge className={center.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}>
                                {center.is_active !== false ? 'Activo' : 'Inactivo'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <Button size="icon" variant="ghost" onClick={() => editCostCenter(center)}>
                                <Edit className="w-4 h-4 text-slate-500" />
                              </Button>
                              <Button size="icon" variant="ghost" onClick={() => handleDeleteCostCenter(center.id)}>
                                <Trash2 className="w-4 h-4 text-red-500" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-12">
                      <Building2 className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p className="text-slate-500">No hay centros de costo definidos</p>
                      <Button
                        className="mt-4 btn-primary rounded-lg"
                        onClick={() => setShowCostCenterDialog(true)}
                      >
                        Crear Primer Centro de Costo
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
