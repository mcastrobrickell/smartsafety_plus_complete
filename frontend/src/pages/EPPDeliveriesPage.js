import React, { useState, useEffect, useRef } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  Package,
  Plus,
  ArrowDownToLine,
  UserCheck,
  DollarSign,
  Warehouse,
  Download,
  Upload,
  FileSpreadsheet,
  Edit,
  Trash2,
  Search,
  FileText,
  Check,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function EPPDeliveriesPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [items, setItems] = useState([]);
  const [costCenters, setCostCenters] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('deliveries');
  
  const [showDeliveryDialog, setShowDeliveryDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showAdjustDialog, setShowAdjustDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  const [deliveryForm, setDeliveryForm] = useState({
    delivery_number: '',
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().slice(0, 5),
    group: '',
    responsible_name: '',
    responsible_rut: '',
    responsible_position: '',
    worker_name: '',
    worker_rut: '',
    worker_position: '',
    cost_center_id: '',
    cost_center_name: '',
    delivery_type: 'entrega',
    epp_item_id: '',
    quantity: 1,
    details: '',
    signature_confirmed: false
  });

  const [adjustForm, setAdjustForm] = useState({
    epp_item_id: '',
    new_stock: 0,
    reason: ''
  });

  const fileInputRef = useRef(null);
  const [importType, setImportType] = useState('items');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const [deliveriesRes, itemsRes, centersRes, inventoryRes] = await Promise.all([
        axios.get(`${API_URL}/api/epp/deliveries`),
        axios.get(`${API_URL}/api/epp/items`),
        axios.get(`${API_URL}/api/cost-centers`),
        axios.get(`${API_URL}/api/epp/stock/inventory`)
      ]);
      setDeliveries(deliveriesRes.data);
      setItems(itemsRes.data);
      setCostCenters(centersRes.data);
      setInventory(inventoryRes.data);
    } catch (error) {
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDelivery = async () => {
    if (!deliveryForm.worker_name || !deliveryForm.epp_item_id) {
      toast.error('Complete los campos requeridos');
      return;
    }

    try {
      const costCenter = costCenters.find(c => c.id === deliveryForm.cost_center_id);
      const response = await axios.post(`${API_URL}/api/epp/deliveries/create`, {
        ...deliveryForm,
        cost_center_name: costCenter?.name || deliveryForm.cost_center_name
      });
      toast.success('Entrega registrada correctamente');
      setShowDeliveryDialog(false);
      resetDeliveryForm();
      fetchAllData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrar entrega');
    }
  };

  const resetDeliveryForm = () => {
    setDeliveryForm({
      delivery_number: '',
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().slice(0, 5),
      group: '',
      responsible_name: '',
      responsible_rut: '',
      responsible_position: '',
      worker_name: '',
      worker_rut: '',
      worker_position: '',
      cost_center_id: '',
      cost_center_name: '',
      delivery_type: 'entrega',
      epp_item_id: '',
      quantity: 1,
      details: '',
      signature_confirmed: false
    });
  };

  const handleExportPDF = async (deliveryId = null) => {
    try {
      const token = localStorage.getItem('token');
      const endpoint = deliveryId 
        ? `${API_URL}/api/epp/delivery/${deliveryId}/pdf`
        : `${API_URL}/api/epp/deliveries/export-pdf`;
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al generar PDF');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = deliveryId ? `entrega-${deliveryId.substring(0,8)}.pdf` : 'entregas-epp.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('PDF generado correctamente');
    } catch (error) {
      toast.error('Error al generar PDF');
      console.error(error);
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
      if (importType === 'deliveries') endpoint = '/api/epp/import/deliveries';

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

  const openAdjustDialog = (item) => {
    setSelectedItem(item);
    setAdjustForm({
      epp_item_id: item.id,
      new_stock: item.current_stock,
      reason: ''
    });
    setShowAdjustDialog(true);
  };

  const getStockStatus = (item) => {
    if (item.current_stock <= 0) return { color: 'bg-red-100 text-red-800', label: 'Sin Stock' };
    if (item.current_stock < item.min_stock) return { color: 'bg-yellow-100 text-yellow-800', label: 'Stock Bajo' };
    return { color: 'bg-green-100 text-green-800', label: 'OK' };
  };

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="epp-deliveries-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar 
          title="Gestión de EPP - Entregas" 
          subtitle="Control de entregas, stock e importación de datos"
        >
          <Button variant="outline" onClick={() => setShowImportDialog(true)} className="gap-2">
            <Upload className="w-4 h-4" />
            Importar Excel
          </Button>
          <Button onClick={handleExportPDF} variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Exportar PDF
          </Button>
          <Button onClick={() => setShowDeliveryDialog(true)} className="bg-blue-500 hover:bg-blue-600 gap-2">
            <Plus className="w-4 h-4" />
            Nueva Entrega
          </Button>
        </TopBar>

        <div className="p-4 lg:p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="deliveries" className="gap-2">
                <UserCheck className="w-4 h-4" />
                Entregas
                <Badge variant="secondary">{deliveries.length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="inventory" className="gap-2">
                <Warehouse className="w-4 h-4" />
                Stock en Bodega
              </TabsTrigger>
            </TabsList>

            {/* Deliveries Tab */}
            <TabsContent value="deliveries">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Historial de Entregas</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {deliveries.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>N°</TableHead>
                            <TableHead>Fecha</TableHead>
                            <TableHead>Trabajador</TableHead>
                            <TableHead>RUT</TableHead>
                            <TableHead>EPP</TableHead>
                            <TableHead>Cant.</TableHead>
                            <TableHead>Tipo</TableHead>
                            <TableHead>C. Costo</TableHead>
                            <TableHead>Estado</TableHead>
                            <TableHead>Acciones</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {deliveries.map((delivery, index) => (
                            <TableRow key={delivery.id}>
                              <TableCell className="font-mono text-sm">
                                {delivery.delivery_number || (index + 1)}
                              </TableCell>
                              <TableCell>{delivery.date}</TableCell>
                              <TableCell className="font-medium">{delivery.worker_name}</TableCell>
                              <TableCell className="text-sm text-slate-500">{delivery.worker_rut || '-'}</TableCell>
                              <TableCell>{delivery.epp_item_name}</TableCell>
                              <TableCell>{delivery.quantity}</TableCell>
                              <TableCell>
                                <Badge className={delivery.delivery_type === 'reposicion' ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800'}>
                                  {delivery.delivery_type === 'reposicion' ? 'Reposición' : 'Entrega'}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-sm">{delivery.cost_center_name || '-'}</TableCell>
                              <TableCell>
                                {delivery.signature_confirmed ? (
                                  <Badge className="bg-green-100 text-green-800 gap-1">
                                    <Check className="w-3 h-3" /> Firmado
                                  </Badge>
                                ) : (
                                  <Badge className="bg-slate-100 text-slate-600">Pendiente</Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                <Button 
                                  size="icon" 
                                  variant="ghost"
                                  onClick={() => handleExportPDF(delivery.id)}
                                >
                                  <FileText className="w-4 h-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <UserCheck className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p className="text-slate-500">No hay entregas registradas</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Inventory Tab */}
            <TabsContent value="inventory">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Stock en Bodega</span>
                    <Button variant="outline" size="sm" onClick={fetchAllData} className="gap-2">
                      <RefreshCw className="w-4 h-4" />
                      Actualizar
                    </Button>
                  </CardTitle>
                  <CardDescription>Control de inventario con ajustes manuales</CardDescription>
                </CardHeader>
                <CardContent>
                  {inventory.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Código</TableHead>
                          <TableHead>Artículo</TableHead>
                          <TableHead>Unidad</TableHead>
                          <TableHead className="text-right">Stock Actual</TableHead>
                          <TableHead className="text-right">Stock Mínimo</TableHead>
                          <TableHead className="text-right">Valor Stock</TableHead>
                          <TableHead>Estado</TableHead>
                          <TableHead>Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {inventory.map((item) => {
                          const status = getStockStatus(item);
                          return (
                            <TableRow key={item.id}>
                              <TableCell className="font-mono">{item.code}</TableCell>
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell>{item.unit}</TableCell>
                              <TableCell className="text-right font-semibold">{item.current_stock}</TableCell>
                              <TableCell className="text-right text-slate-500">{item.min_stock}</TableCell>
                              <TableCell className="text-right">${item.stock_value?.toLocaleString() || 0}</TableCell>
                              <TableCell>
                                <Badge className={status.color}>{status.label}</Badge>
                              </TableCell>
                              <TableCell>
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  onClick={() => openAdjustDialog(item)}
                                  className="gap-1"
                                >
                                  <Edit className="w-3 h-3" />
                                  Ajustar
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-12">
                      <Warehouse className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p className="text-slate-500">No hay artículos en inventario</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* New Delivery Dialog */}
        <Dialog open={showDeliveryDialog} onOpenChange={setShowDeliveryDialog}>
          <DialogContent className="max-w-3xl max-h-[90vh]">
            <DialogHeader>
              <DialogTitle>Registrar Entrega de EPP</DialogTitle>
            </DialogHeader>
            <ScrollArea className="max-h-[70vh] pr-4">
              <div className="space-y-6 py-4">
                {/* Basic Info */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>N° Entrega (Manual)</Label>
                    <Input
                      placeholder="Ej: 001"
                      value={deliveryForm.delivery_number}
                      onChange={(e) => setDeliveryForm({...deliveryForm, delivery_number: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Fecha *</Label>
                    <Input
                      type="date"
                      value={deliveryForm.date}
                      onChange={(e) => setDeliveryForm({...deliveryForm, date: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Hora</Label>
                    <Input
                      type="time"
                      value={deliveryForm.time}
                      onChange={(e) => setDeliveryForm({...deliveryForm, time: e.target.value})}
                    />
                  </div>
                </div>

                {/* Responsible */}
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-3">Responsable de la Entrega</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre *</Label>
                      <Input
                        value={deliveryForm.responsible_name}
                        onChange={(e) => setDeliveryForm({...deliveryForm, responsible_name: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>RUT</Label>
                      <Input
                        placeholder="12.345.678-9"
                        value={deliveryForm.responsible_rut}
                        onChange={(e) => setDeliveryForm({...deliveryForm, responsible_rut: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Cargo</Label>
                      <Input
                        value={deliveryForm.responsible_position}
                        onChange={(e) => setDeliveryForm({...deliveryForm, responsible_position: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {/* Worker */}
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-3">Colaborador que Recibe</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre *</Label>
                      <Input
                        value={deliveryForm.worker_name}
                        onChange={(e) => setDeliveryForm({...deliveryForm, worker_name: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>RUT</Label>
                      <Input
                        placeholder="12.345.678-9"
                        value={deliveryForm.worker_rut}
                        onChange={(e) => setDeliveryForm({...deliveryForm, worker_rut: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Cargo</Label>
                      <Input
                        value={deliveryForm.worker_position}
                        onChange={(e) => setDeliveryForm({...deliveryForm, worker_position: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {/* Location & Type */}
                <div className="border-t pt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Faena / Centro de Costo</Label>
                      <Select 
                        value={deliveryForm.cost_center_id} 
                        onValueChange={(v) => setDeliveryForm({...deliveryForm, cost_center_id: v})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccione" />
                        </SelectTrigger>
                        <SelectContent>
                          {costCenters.map((cc) => (
                            <SelectItem key={cc.id} value={cc.id}>{cc.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Tipo de Entrega</Label>
                      <Select 
                        value={deliveryForm.delivery_type} 
                        onValueChange={(v) => setDeliveryForm({...deliveryForm, delivery_type: v})}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="entrega">Entrega</SelectItem>
                          <SelectItem value="reposicion">Reposición</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Grupo</Label>
                      <Input
                        value={deliveryForm.group}
                        onChange={(e) => setDeliveryForm({...deliveryForm, group: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {/* EPP Selection */}
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-3">EPP a Entregar</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Seleccione el EPP *</Label>
                      <Select 
                        value={deliveryForm.epp_item_id} 
                        onValueChange={(v) => setDeliveryForm({...deliveryForm, epp_item_id: v})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccione artículo" />
                        </SelectTrigger>
                        <SelectContent>
                          {items.map((item) => (
                            <SelectItem key={item.id} value={item.id}>
                              {item.code} - {item.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Cantidad *</Label>
                      <Input
                        type="number"
                        min="1"
                        value={deliveryForm.quantity}
                        onChange={(e) => setDeliveryForm({...deliveryForm, quantity: parseInt(e.target.value) || 1})}
                      />
                    </div>
                  </div>
                </div>

                {/* Details */}
                <div className="border-t pt-4">
                  <div className="space-y-2">
                    <Label>Detalles / Observaciones (opcional)</Label>
                    <Textarea
                      value={deliveryForm.details}
                      onChange={(e) => setDeliveryForm({...deliveryForm, details: e.target.value})}
                      placeholder="Ingrese detalles adicionales si es necesario..."
                      rows={3}
                    />
                  </div>
                </div>

                {/* Signature */}
                <div className="border-t pt-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="signature"
                      checked={deliveryForm.signature_confirmed}
                      onChange={(e) => setDeliveryForm({...deliveryForm, signature_confirmed: e.target.checked})}
                      className="w-4 h-4"
                    />
                    <Label htmlFor="signature">Trabajador firma conforme la recepción del EPP</Label>
                  </div>
                </div>
              </div>
            </ScrollArea>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDeliveryDialog(false)}>Cancelar</Button>
              <Button onClick={handleCreateDelivery} className="bg-blue-500 hover:bg-blue-600">
                Registrar Entrega
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Import Excel Dialog */}
        <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Importar desde Excel</DialogTitle>
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
                    <SelectItem value="deliveries">Entregas (Migración)</SelectItem>
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
                  id="excel-upload"
                />
                <label htmlFor="excel-upload" className="cursor-pointer">
                  <FileSpreadsheet className="w-10 h-10 mx-auto text-slate-400 mb-3" />
                  <p className="text-sm font-medium text-slate-700">Haga clic para seleccionar archivo</p>
                  <p className="text-xs text-slate-500 mt-1">Solo archivos Excel (.xlsx, .xls)</p>
                </label>
              </div>

              <div className="bg-slate-50 p-3 rounded-lg text-xs text-slate-600">
                <p className="font-semibold mb-1">Columnas esperadas:</p>
                {importType === 'items' && <p>codigo, nombre, categoria, tipo, marca, modelo, costo_unitario</p>}
                {importType === 'receptions' && <p>codigo_epp, cantidad, costo_unitario, documento, notas</p>}
                {importType === 'deliveries' && <p>numero, fecha, hora, trabajador, rut_trabajador, cargo_trabajador, responsable, codigo_epp, cantidad, tipo_entrega, centro_costo</p>}
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Adjust Stock Dialog */}
        <Dialog open={showAdjustDialog} onOpenChange={setShowAdjustDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Ajustar Stock</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {selectedItem && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="font-semibold">{selectedItem.code} - {selectedItem.name}</p>
                  <p className="text-sm text-slate-500">Stock actual: {selectedItem.current_stock}</p>
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
      </main>
    </div>
  );
}
