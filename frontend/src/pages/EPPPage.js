import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import {
  Package,
  Plus,
  ArrowDownToLine,
  ArrowRightLeft,
  Truck,
  UserCheck,
  RotateCcw,
  DollarSign,
  Warehouse,
  Settings,
  Edit,
  Trash2,
  Upload,
  FileSpreadsheet,
  RefreshCw,
  ExternalLink,
  Download
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function EPPPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [stock, setStock] = useState([]);
  const [movements, setMovements] = useState([]);
  const [costCenters, setCostCenters] = useState([]);
  const [categories, setCategories] = useState([]);
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('items');
  
  // Dialogs
  const [showItemDialog, setShowItemDialog] = useState(false);
  const [showReceptionDialog, setShowReceptionDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showCategoryDialog, setShowCategoryDialog] = useState(false);
  const [showCostCenterDialog, setShowCostCenterDialog] = useState(false);
  const [showAdjustDialog, setShowAdjustDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  // Form states
  const [itemForm, setItemForm] = useState({
    code: '', name: '', category_id: '', type_id: '', brand: '', model: '', unit_cost: 0, certification_number: '', certification_expiry: ''
  });
  const [receptionForm, setReceptionForm] = useState({
    epp_item_id: '', quantity: 0, unit_cost: 0, cost_center_id: '', warehouse_location: '', document_number: '', notes: ''
  });
  const [adjustForm, setAdjustForm] = useState({
    epp_item_id: '', new_stock: 0, reason: ''
  });

  const fileInputRef = useRef(null);
  const [importType, setImportType] = useState('items');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const [itemsRes, stockRes, movementsRes, centersRes, catsRes, typesRes] = await Promise.all([
        axios.get(`${API_URL}/api/epp/items`),
        axios.get(`${API_URL}/api/epp/stock`),
        axios.get(`${API_URL}/api/epp/movements`),
        axios.get(`${API_URL}/api/cost-centers`),
        axios.get(`${API_URL}/api/config/categories?config_type=epp_category`),
        axios.get(`${API_URL}/api/config/categories?config_type=epp_type`)
      ]);
      setItems(itemsRes.data);
      setStock(stockRes.data);
      setMovements(movementsRes.data);
      setCostCenters(centersRes.data);
      setCategories(catsRes.data);
      setTypes(typesRes.data);
    } catch (error) {
      console.error('Fetch error:', error);
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateItem = async () => {
    if (!itemForm.code || !itemForm.name) {
      toast.error('Complete código y nombre');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/epp/items`, itemForm);
      toast.success('Artículo EPP creado');
      setShowItemDialog(false);
      setItemForm({ code: '', name: '', category_id: '', type_id: '', brand: '', model: '', unit_cost: 0, certification_number: '', certification_expiry: '' });
      fetchAllData();
    } catch (error) {
      toast.error('Error al crear artículo');
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('¿Eliminar este artículo?')) return;
    try {
      await axios.delete(`${API_URL}/api/epp/items/${itemId}`);
      toast.success('Artículo eliminado');
      fetchAllData();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const handleReception = async () => {
    if (!receptionForm.epp_item_id || receptionForm.quantity <= 0) {
      toast.error('Seleccione artículo y cantidad válida');
      return;
    }
    try {
      const params = new URLSearchParams(receptionForm);
      await axios.post(`${API_URL}/api/epp/movements/reception?${params.toString()}`);
      toast.success('Recepción registrada');
      setShowReceptionDialog(false);
      setReceptionForm({ epp_item_id: '', quantity: 0, unit_cost: 0, cost_center_id: '', warehouse_location: '', document_number: '', notes: '' });
      fetchAllData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error en recepción');
    }
  };

  const handleImportExcel = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      let endpoint = '/api/epp/import/items';
      if (importType === 'receptions') endpoint = '/api/epp/import/receptions';

      const response = await axios.post(`${API_URL}${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success(`Importados: ${response.data.imported} registros`);
      if (response.data.errors?.length > 0) {
        toast.warning(`${response.data.errors.length} errores encontrados`);
      }
      setShowImportDialog(false);
      fetchAllData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al importar archivo');
    }

    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleAdjustStock = async () => {
    if (!adjustForm.epp_item_id || !adjustForm.reason) {
      toast.error('Complete todos los campos');
      return;
    }

    try {
      await axios.post(`${API_URL}/api/epp/stock/adjust`, null, {
        params: {
          epp_item_id: adjustForm.epp_item_id,
          new_stock: adjustForm.new_stock,
          reason: adjustForm.reason
        }
      });
      toast.success('Stock ajustado correctamente');
      setShowAdjustDialog(false);
      setAdjustForm({ epp_item_id: '', new_stock: 0, reason: '' });
      fetchAllData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al ajustar stock');
    }
  };

  const openAdjustDialog = (stockItem) => {
    const item = items.find(i => i.id === stockItem.epp_item_id);
    setSelectedItem({ ...stockItem, name: item?.name, code: item?.code });
    setAdjustForm({
      epp_item_id: stockItem.epp_item_id,
      new_stock: stockItem.quantity,
      reason: ''
    });
    setShowAdjustDialog(true);
  };

  const handleCreateCategory = async (type, name, description) => {
    try {
      await axios.post(`${API_URL}/api/config/categories`, {
        type: type,
        name: name,
        description: description
      });
      toast.success('Categoría creada');
      fetchAllData();
    } catch (error) {
      toast.error('Error al crear categoría');
    }
  };

  const handleCreateCostCenter = async (code, name, description) => {
    try {
      await axios.post(`${API_URL}/api/cost-centers`, {
        code: code,
        name: name,
        description: description
      });
      toast.success('Centro de costo creado');
      fetchAllData();
    } catch (error) {
      toast.error('Error al crear centro de costo');
    }
  };

  const getMovementTypeLabel = (type) => {
    const labels = {
      reception: 'Recepción',
      distribution: 'Distribución',
      dispatch: 'Despacho',
      delivery: 'Entrega',
      return: 'Devolución'
    };
    return labels[type] || type;
  };

  const getMovementTypeBadge = (type) => {
    const colors = {
      reception: 'bg-green-100 text-green-800',
      distribution: 'bg-blue-100 text-blue-800',
      dispatch: 'bg-purple-100 text-purple-800',
      delivery: 'bg-orange-100 text-orange-800',
      return: 'bg-slate-100 text-slate-800'
    };
    return colors[type] || 'bg-slate-100 text-slate-800';
  };

  const getStockStatus = (stockItem) => {
    if (stockItem.quantity <= 0) return { color: 'bg-red-100 text-red-800', label: 'Sin Stock' };
    if (stockItem.quantity < stockItem.min_stock) return { color: 'bg-yellow-100 text-yellow-800', label: 'Stock Bajo' };
    return { color: 'bg-green-100 text-green-800', label: 'OK' };
  };

  const totalStockValue = stock.reduce((acc, s) => {
    const item = items.find(i => i.id === s.epp_item_id);
    return acc + (s.quantity * (item?.unit_cost || 0));
  }, 0);

  const lowStockItems = stock.filter(s => s.quantity < s.min_stock);

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="epp-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Gestión de EPP" subtitle="Catálogo, stock y recepciones">
          <Button variant="outline" onClick={() => setShowImportDialog(true)} className="gap-2" data-testid="import-excel-btn">
            <Upload className="w-4 h-4" />
            <span className="hidden sm:inline">Importar Excel</span>
          </Button>
          <Button variant="outline" onClick={() => setShowCostCenterDialog(true)} className="gap-2" data-testid="config-cost-centers-btn">
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Centros de Costo</span>
          </Button>
          <Button onClick={() => navigate('/epp/entregas')} className="bg-blue-500 hover:bg-blue-600 gap-2" data-testid="go-to-deliveries-btn">
            <ExternalLink className="w-4 h-4" />
            <span className="hidden sm:inline">Ir a Entregas</span>
          </Button>
        </TopBar>

        <div className="p-4 lg:p-8">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card className="border-slate-200">
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Artículos Catálogo</p>
                    <p className="text-2xl lg:text-3xl font-bold text-blue-600 mt-1">{items.length}</p>
                  </div>
                  <Package className="w-8 lg:w-10 h-8 lg:h-10 text-slate-300" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200">
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Valor Total Stock</p>
                    <p className="text-2xl lg:text-3xl font-bold text-green-600 mt-1">${totalStockValue.toLocaleString()}</p>
                  </div>
                  <DollarSign className="w-8 lg:w-10 h-8 lg:h-10 text-slate-300" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200">
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Stock Bajo</p>
                    <p className="text-2xl lg:text-3xl font-bold text-orange-600 mt-1">{lowStockItems.length}</p>
                  </div>
                  <Warehouse className="w-8 lg:w-10 h-8 lg:h-10 text-slate-300" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200">
              <CardContent className="p-4 lg:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs lg:text-sm text-slate-500">Movimientos</p>
                    <p className="text-2xl lg:text-3xl font-bold text-slate-900 mt-1">{movements.length}</p>
                  </div>
                  <ArrowRightLeft className="w-8 lg:w-10 h-8 lg:h-10 text-slate-300" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-white border border-slate-200 p-1 flex-wrap h-auto">
              <TabsTrigger value="items" className="gap-2 text-xs lg:text-sm">
                <Package className="w-4 h-4" />
                <span className="hidden sm:inline">Catálogo</span>
                <Badge variant="secondary" className="ml-1">{items.length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="stock" className="gap-2 text-xs lg:text-sm">
                <Warehouse className="w-4 h-4" />
                <span className="hidden sm:inline">Stock</span>
              </TabsTrigger>
              <TabsTrigger value="receptions" className="gap-2 text-xs lg:text-sm">
                <ArrowDownToLine className="w-4 h-4" />
                <span className="hidden sm:inline">Recepciones</span>
              </TabsTrigger>
              <TabsTrigger value="movements" className="gap-2 text-xs lg:text-sm">
                <ArrowRightLeft className="w-4 h-4" />
                <span className="hidden sm:inline">Movimientos</span>
              </TabsTrigger>
            </TabsList>

            {/* Items/Catalog Tab */}
            <TabsContent value="items">
              <Card className="border-slate-200">
                <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <CardTitle>Catálogo de Artículos EPP</CardTitle>
                    <CardDescription>Productos registrados en el sistema</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setShowCategoryDialog(true)} className="gap-2" data-testid="config-categories-btn">
                      <Settings className="w-4 h-4" />
                      Categorías
                    </Button>
                    <Dialog open={showItemDialog} onOpenChange={setShowItemDialog}>
                      <DialogTrigger asChild>
                        <Button className="bg-blue-500 hover:bg-blue-600 gap-2" data-testid="add-item-btn">
                          <Plus className="w-4 h-4" />
                          Nuevo
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-lg">
                        <DialogHeader>
                          <DialogTitle>Nuevo Artículo EPP</DialogTitle>
                          <DialogDescription>Agregar producto al catálogo</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label>Código *</Label>
                              <Input
                                placeholder="EPP-001"
                                value={itemForm.code}
                                onChange={(e) => setItemForm({ ...itemForm, code: e.target.value })}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Nombre *</Label>
                              <Input
                                placeholder="Casco de Seguridad"
                                value={itemForm.name}
                                onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })}
                              />
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label>Categoría</Label>
                              <Select value={itemForm.category_id} onValueChange={(v) => setItemForm({ ...itemForm, category_id: v })}>
                                <SelectTrigger>
                                  <SelectValue placeholder="Seleccionar" />
                                </SelectTrigger>
                                <SelectContent>
                                  {categories.map((c) => (
                                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-2">
                              <Label>Tipo</Label>
                              <Select value={itemForm.type_id} onValueChange={(v) => setItemForm({ ...itemForm, type_id: v })}>
                                <SelectTrigger>
                                  <SelectValue placeholder="Seleccionar" />
                                </SelectTrigger>
                                <SelectContent>
                                  {types.map((t) => (
                                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label>Marca</Label>
                              <Input
                                placeholder="3M"
                                value={itemForm.brand}
                                onChange={(e) => setItemForm({ ...itemForm, brand: e.target.value })}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Costo Unitario ($)</Label>
                              <Input
                                type="number"
                                min="0"
                                step="0.01"
                                value={itemForm.unit_cost}
                                onChange={(e) => setItemForm({ ...itemForm, unit_cost: parseFloat(e.target.value) || 0 })}
                              />
                            </div>
                          </div>
                          <div className="space-y-2">
                            <Label>N° Certificación</Label>
                            <Input
                              placeholder="CERT-2024-001"
                              value={itemForm.certification_number}
                              onChange={(e) => setItemForm({ ...itemForm, certification_number: e.target.value })}
                            />
                          </div>
                        </div>
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setShowItemDialog(false)}>Cancelar</Button>
                          <Button onClick={handleCreateItem} className="bg-blue-500 hover:bg-blue-600">Crear Artículo</Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-12"><div className="spinner"></div></div>
                  ) : items.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Código</TableHead>
                            <TableHead>Nombre</TableHead>
                            <TableHead className="hidden md:table-cell">Marca</TableHead>
                            <TableHead className="text-right">Costo Unit.</TableHead>
                            <TableHead className="hidden lg:table-cell">Certificación</TableHead>
                            <TableHead className="text-center">Acciones</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {items.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell className="font-mono text-sm">{item.code}</TableCell>
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell className="hidden md:table-cell">{item.brand || '-'}</TableCell>
                              <TableCell className="text-right">${item.unit_cost?.toLocaleString() || 0}</TableCell>
                              <TableCell className="hidden lg:table-cell">{item.certification_number || '-'}</TableCell>
                              <TableCell className="text-center">
                                <Button 
                                  size="icon" 
                                  variant="ghost" 
                                  className="text-red-500 hover:text-red-700"
                                  onClick={() => handleDeleteItem(item.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Package className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay artículos registrados</p>
                      <Button className="mt-4 bg-blue-500 hover:bg-blue-600" onClick={() => setShowItemDialog(true)}>
                        Crear Primer Artículo
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Stock Tab */}
            <TabsContent value="stock">
              <Card className="border-slate-200">
                <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <CardTitle>Stock en Bodega</CardTitle>
                    <CardDescription>Control de inventario por ubicación con ajustes manuales</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={fetchAllData} className="gap-2">
                    <RefreshCw className="w-4 h-4" />
                    Actualizar
                  </Button>
                </CardHeader>
                <CardContent>
                  {stock.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Artículo</TableHead>
                            <TableHead className="hidden md:table-cell">Centro de Costo</TableHead>
                            <TableHead className="hidden lg:table-cell">Ubicación</TableHead>
                            <TableHead className="text-center">Cantidad</TableHead>
                            <TableHead className="text-center hidden sm:table-cell">Mín.</TableHead>
                            <TableHead className="text-right hidden md:table-cell">Valor</TableHead>
                            <TableHead>Estado</TableHead>
                            <TableHead className="text-center">Ajustar</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {stock.map((s) => {
                            const item = items.find(i => i.id === s.epp_item_id);
                            const cc = costCenters.find(c => c.id === s.cost_center_id);
                            const value = s.quantity * (item?.unit_cost || 0);
                            const status = getStockStatus(s);
                            return (
                              <TableRow key={s.id} className={s.quantity < s.min_stock ? 'bg-red-50' : ''}>
                                <TableCell className="font-medium">{item?.name || 'N/A'}</TableCell>
                                <TableCell className="hidden md:table-cell">{cc?.name || 'Bodega Central'}</TableCell>
                                <TableCell className="hidden lg:table-cell">{s.warehouse_location || '-'}</TableCell>
                                <TableCell className="text-center font-semibold">{s.quantity}</TableCell>
                                <TableCell className="text-center text-slate-500 hidden sm:table-cell">{s.min_stock}</TableCell>
                                <TableCell className="text-right font-medium hidden md:table-cell">${value.toLocaleString()}</TableCell>
                                <TableCell>
                                  <Badge className={status.color}>{status.label}</Badge>
                                </TableCell>
                                <TableCell className="text-center">
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => openAdjustDialog(s)}
                                    className="gap-1"
                                  >
                                    <Edit className="w-3 h-3" />
                                    <span className="hidden sm:inline">Ajustar</span>
                                  </Button>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Warehouse className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay stock registrado</p>
                      <p className="text-sm mt-2">Registre recepciones para generar stock</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Receptions Tab */}
            <TabsContent value="receptions">
              <Card className="border-slate-200">
                <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <CardTitle>Recepciones de EPP</CardTitle>
                    <CardDescription>Registro de ingreso de mercadería a bodega</CardDescription>
                  </div>
                  <Dialog open={showReceptionDialog} onOpenChange={setShowReceptionDialog}>
                    <DialogTrigger asChild>
                      <Button className="bg-green-600 hover:bg-green-700 gap-2" data-testid="reception-btn">
                        <ArrowDownToLine className="w-4 h-4" />
                        Nueva Recepción
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Recepción de EPP</DialogTitle>
                        <DialogDescription>Registrar ingreso de EPP a bodega</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label>Artículo EPP *</Label>
                          <Select value={receptionForm.epp_item_id} onValueChange={(v) => setReceptionForm({ ...receptionForm, epp_item_id: v })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Seleccionar artículo" />
                            </SelectTrigger>
                            <SelectContent>
                              {items.map((item) => (
                                <SelectItem key={item.id} value={item.id}>{item.code} - {item.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Cantidad *</Label>
                            <Input
                              type="number"
                              min="1"
                              value={receptionForm.quantity}
                              onChange={(e) => setReceptionForm({ ...receptionForm, quantity: parseInt(e.target.value) || 0 })}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Costo Unitario ($)</Label>
                            <Input
                              type="number"
                              min="0"
                              step="0.01"
                              value={receptionForm.unit_cost}
                              onChange={(e) => setReceptionForm({ ...receptionForm, unit_cost: parseFloat(e.target.value) || 0 })}
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Centro de Costo</Label>
                          <Select value={receptionForm.cost_center_id} onValueChange={(v) => setReceptionForm({ ...receptionForm, cost_center_id: v })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Seleccionar centro" />
                            </SelectTrigger>
                            <SelectContent>
                              {costCenters.map((cc) => (
                                <SelectItem key={cc.id} value={cc.id}>{cc.code} - {cc.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Ubicación Bodega</Label>
                            <Input
                              placeholder="Ej: A-01-03"
                              value={receptionForm.warehouse_location}
                              onChange={(e) => setReceptionForm({ ...receptionForm, warehouse_location: e.target.value })}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>N° Documento</Label>
                            <Input
                              placeholder="Factura/Guía"
                              value={receptionForm.document_number}
                              onChange={(e) => setReceptionForm({ ...receptionForm, document_number: e.target.value })}
                            />
                          </div>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowReceptionDialog(false)}>Cancelar</Button>
                        <Button onClick={handleReception} className="bg-green-600 hover:bg-green-700">Registrar Recepción</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  {movements.filter(m => m.movement_type === 'reception').length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Fecha</TableHead>
                            <TableHead>Artículo</TableHead>
                            <TableHead className="text-center">Cantidad</TableHead>
                            <TableHead className="text-right hidden sm:table-cell">Costo Unit.</TableHead>
                            <TableHead className="text-right">Costo Total</TableHead>
                            <TableHead className="hidden md:table-cell">Documento</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {movements.filter(m => m.movement_type === 'reception').map((m) => {
                            const item = items.find(i => i.id === m.epp_item_id);
                            const displayName = m.epp_item_name || item?.name || 'Artículo eliminado';
                            const displayCode = m.epp_item_code || item?.code || '';
                            return (
                              <TableRow key={m.id}>
                                <TableCell className="text-sm">{new Date(m.created_at).toLocaleDateString()}</TableCell>
                                <TableCell className="font-medium">
                                  {displayCode && <span className="text-slate-500 mr-1">[{displayCode}]</span>}
                                  {displayName}
                                </TableCell>
                                <TableCell className="text-center">{m.quantity}</TableCell>
                                <TableCell className="text-right hidden sm:table-cell">${m.unit_cost?.toLocaleString() || 0}</TableCell>
                                <TableCell className="text-right font-medium">${m.total_cost?.toLocaleString() || 0}</TableCell>
                                <TableCell className="hidden md:table-cell">{m.document_number || '-'}</TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <ArrowDownToLine className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay recepciones registradas</p>
                      <Button className="mt-4 bg-green-600 hover:bg-green-700" onClick={() => setShowReceptionDialog(true)}>
                        Registrar Primera Recepción
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Movements Tab */}
            <TabsContent value="movements">
              <Card className="border-slate-200">
                <CardHeader>
                  <CardTitle>Historial de Movimientos</CardTitle>
                  <CardDescription>Registro completo de operaciones logísticas</CardDescription>
                </CardHeader>
                <CardContent>
                  {movements.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Fecha</TableHead>
                            <TableHead>Tipo</TableHead>
                            <TableHead>Artículo</TableHead>
                            <TableHead className="text-center">Cantidad</TableHead>
                            <TableHead className="text-right hidden sm:table-cell">Costo Total</TableHead>
                            <TableHead className="hidden md:table-cell">Documento</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {movements.map((m) => {
                            const item = items.find(i => i.id === m.epp_item_id);
                            const displayName = m.epp_item_name || item?.name || 'Artículo eliminado';
                            return (
                              <TableRow key={m.id}>
                                <TableCell className="text-sm">{new Date(m.created_at).toLocaleString()}</TableCell>
                                <TableCell>
                                  <Badge className={getMovementTypeBadge(m.movement_type)}>
                                    {getMovementTypeLabel(m.movement_type)}
                                  </Badge>
                                </TableCell>
                                <TableCell className="font-medium">{displayName}</TableCell>
                                <TableCell className="text-center">{m.quantity}</TableCell>
                                <TableCell className="text-right font-medium hidden sm:table-cell">${m.total_cost?.toLocaleString() || 0}</TableCell>
                                <TableCell className="hidden md:table-cell">{m.document_number || '-'}</TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <ArrowRightLeft className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay movimientos registrados</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Import Excel Dialog */}
          <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Importar desde Excel</DialogTitle>
                <DialogDescription>Cargue archivos Excel para importar datos masivos</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Tipo de Importación</Label>
                  <Select value={importType} onValueChange={setImportType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="items">Artículos EPP</SelectItem>
                      <SelectItem value="receptions">Recepciones</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleImportExcel}
                    className="hidden"
                    ref={fileInputRef}
                    id="excel-upload-epp"
                  />
                  <label htmlFor="excel-upload-epp" className="cursor-pointer">
                    <FileSpreadsheet className="w-10 h-10 mx-auto text-slate-400 mb-3" />
                    <p className="text-sm font-medium text-slate-700">Haga clic para seleccionar archivo</p>
                    <p className="text-xs text-slate-500 mt-1">Solo archivos Excel (.xlsx, .xls)</p>
                  </label>
                </div>

                <div className="bg-slate-50 p-3 rounded-lg text-xs text-slate-600">
                  <p className="font-semibold mb-1">Columnas esperadas:</p>
                  {importType === 'items' && <p>codigo, nombre, categoria, tipo, marca, modelo, costo_unitario</p>}
                  {importType === 'receptions' && <p>codigo_epp, cantidad, costo_unitario, documento, notas</p>}
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Adjust Stock Dialog */}
          <Dialog open={showAdjustDialog} onOpenChange={setShowAdjustDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Ajustar Stock</DialogTitle>
                <DialogDescription>Corregir inventario manualmente</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {selectedItem && (
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="font-semibold">{selectedItem.code} - {selectedItem.name}</p>
                    <p className="text-sm text-slate-500">Stock actual: {selectedItem.quantity}</p>
                  </div>
                )}
                <div className="space-y-2">
                  <Label>Nuevo Stock</Label>
                  <Input
                    type="number"
                    min="0"
                    value={adjustForm.new_stock}
                    onChange={(e) => setAdjustForm({...adjustForm, new_stock: parseInt(e.target.value) || 0})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Motivo del Ajuste *</Label>
                  <Textarea
                    value={adjustForm.reason}
                    onChange={(e) => setAdjustForm({...adjustForm, reason: e.target.value})}
                    placeholder="Ej: Corrección de inventario físico, Pérdida, Daño..."
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAdjustDialog(false)}>Cancelar</Button>
                <Button onClick={handleAdjustStock} className="bg-orange-500 hover:bg-orange-600">
                  Aplicar Ajuste
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Configuration Dialogs */}
          <ConfigDialog
            open={showCategoryDialog}
            onOpenChange={setShowCategoryDialog}
            title="Configurar Categorías EPP"
            items={categories}
            onAdd={(name, desc) => handleCreateCategory('epp_category', name, desc)}
            itemLabel="Categoría"
          />

          <ConfigDialog
            open={showCostCenterDialog}
            onOpenChange={setShowCostCenterDialog}
            title="Configurar Centros de Costo"
            items={costCenters}
            onAdd={(code, name) => handleCreateCostCenter(code, name, '')}
            itemLabel="Centro de Costo"
            hasCode
          />
        </div>
      </main>
    </div>
  );
}

// Config Dialog Component
function ConfigDialog({ open, onOpenChange, title, items, onAdd, itemLabel, hasCode }) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [desc, setDesc] = useState('');

  const handleAdd = () => {
    if (hasCode) {
      if (!code || !name) return;
      onAdd(code, name);
    } else {
      if (!name) return;
      onAdd(name, desc);
    }
    setName('');
    setCode('');
    setDesc('');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>Gestionar configuración personalizada</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            {hasCode && (
              <div className="space-y-2">
                <Label>Código</Label>
                <Input
                  placeholder="CC-001"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                />
              </div>
            )}
            <div className={`space-y-2 ${hasCode ? '' : 'col-span-2'}`}>
              <Label>Nombre</Label>
              <Input
                placeholder={`Nombre del ${itemLabel}`}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>
          <Button onClick={handleAdd} className="w-full bg-blue-500 hover:bg-blue-600">
            <Plus className="w-4 h-4 mr-2" />
            Agregar {itemLabel}
          </Button>

          <div className="border-t pt-4">
            <p className="text-sm font-medium text-slate-700 mb-2">{itemLabel}s existentes:</p>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {items.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                  <span className="text-sm">
                    {item.code && <span className="font-mono mr-2">{item.code}</span>}
                    {item.name}
                  </span>
                  <Badge className="bg-green-100 text-green-800">Activo</Badge>
                </div>
              ))}
              {items.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-4">No hay {itemLabel}s configurados</p>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
