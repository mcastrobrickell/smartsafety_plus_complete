import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import {
  FileText,
  AlertTriangle,
  User,
  Calendar,
  MapPin,
  Clock,
  CheckCircle,
  XCircle,
  Save,
  Download,
  Plus,
  ChevronRight,
  Shield,
  ClipboardList,
  Users,
  Camera,
  GitBranch,
  Target,
  Loader2,
  ArrowLeft,
  Upload,
  Image,
  Trash2,
  PenTool,
  Check
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const INCIDENT_TYPES = [
  { value: 'SEGURIDAD', label: 'Seguridad', color: 'bg-red-100 text-red-800' },
  { value: 'OPERACIONAL', label: 'Operacional', color: 'bg-blue-100 text-blue-800' },
  { value: 'AMBIENTAL', label: 'Ambiental', color: 'bg-green-100 text-green-800' },
  { value: 'DOCUMENTAL', label: 'Documental', color: 'bg-purple-100 text-purple-800' },
  { value: 'VEHICULAR', label: 'Vehicular', color: 'bg-orange-100 text-orange-800' },
  { value: 'SALUD', label: 'Salud', color: 'bg-pink-100 text-pink-800' }
];

const ISO_CLAUSES = [
  { value: '4.1', label: '4.1 - Contexto de la organización' },
  { value: '5.4', label: '5.4 - Consulta y participación de trabajadores' },
  { value: '6.1.2', label: '6.1.2 - Identificación de peligros' },
  { value: '6.1.3', label: '6.1.3 - Requisitos legales' },
  { value: '7.2', label: '7.2 - Competencia' },
  { value: '7.3', label: '7.3 - Toma de conciencia' },
  { value: '8.1', label: '8.1 - Planificación y control operacional' },
  { value: '8.2', label: '8.2 - Preparación y respuesta ante emergencias' },
  { value: '9.1.2', label: '9.1.2 - Evaluación del cumplimiento' },
  { value: '10.2', label: '10.2 - Incidentes, no conformidades y acciones correctivas' }
];

export default function InvestigationPage() {
  const { investigationId } = useParams();
  const navigate = useNavigate();
  const [investigation, setInvestigation] = useState(null);
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('background');
  const [showActionDialog, setShowActionDialog] = useState(false);
  
  const [formData, setFormData] = useState({
    incident_description: '',
    incident_date: '',
    incident_time: '',
    incident_types: [],
    incident_location: '',
    work_site: '',
    witnesses: '',
    supervisor_name: '',
    consequences: '',
    affected_worker: {
      name: '',
      rut: '',
      position: '',
      age: '',
      seniority_company: ''
    },
    narrative: '',
    facts_list: '',
    immediate_causes: [],
    basic_causes: [],
    root_causes: [],
    task_observation: {},
    document_review: {}
  });

  const [newAction, setNewAction] = useState({
    description: '',
    action_type: 'corrective',
    responsible: '',
    due_date: '',
    priority: 'medium',
    iso_clause: ''
  });

  const [photos, setPhotos] = useState([]);
  const [showSignatureDialog, setShowSignatureDialog] = useState(false);
  const [signature, setSignature] = useState({ name: '', position: '', date: '' });

  useEffect(() => {
    if (investigationId) {
      fetchInvestigation();
    }
  }, [investigationId]);

  const fetchInvestigation = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/investigations/${investigationId}`);
      setInvestigation(response.data.investigation);
      setIncident(response.data.incident);
      
      // Populate form with existing data
      const inv = response.data.investigation;
      setFormData({
        incident_description: inv.incident_description || '',
        incident_date: inv.incident_date || '',
        incident_time: inv.incident_time || '',
        incident_types: inv.incident_types || [],
        incident_location: inv.incident_location || '',
        work_site: inv.work_site || '',
        witnesses: inv.witnesses || '',
        supervisor_name: inv.supervisor_name || '',
        consequences: inv.consequences || '',
        affected_worker: inv.affected_worker || { name: '', rut: '', position: '', age: '', seniority_company: '' },
        narrative: inv.narrative || '',
        facts_list: inv.facts_list || '',
        immediate_causes: inv.immediate_causes || [],
        basic_causes: inv.basic_causes || [],
        root_causes: inv.root_causes || [],
        task_observation: inv.task_observation || {},
        document_review: inv.document_review || {}
      });
    } catch (error) {
      toast.error('Error al cargar investigación');
      navigate('/incidents');
    } finally {
      setLoading(false);
    }
  };

  const saveInvestigation = async () => {
    setSaving(true);
    try {
      await axios.put(`${API_URL}/api/investigations/${investigationId}`, formData);
      toast.success('Investigación guardada');
      fetchInvestigation();
    } catch (error) {
      toast.error('Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const addCorrectiveAction = async () => {
    try {
      await axios.post(`${API_URL}/api/investigations/${investigationId}/corrective-action`, newAction);
      toast.success('Acción correctiva agregada');
      setShowActionDialog(false);
      setNewAction({ description: '', action_type: 'corrective', responsible: '', due_date: '', priority: 'medium', iso_clause: '' });
      fetchInvestigation();
    } catch (error) {
      toast.error('Error al agregar acción');
    }
  };

  const updateStatus = async (status) => {
    try {
      await axios.put(`${API_URL}/api/investigations/${investigationId}/status?status=${status}`);
      toast.success(`Estado actualizado: ${status}`);
      fetchInvestigation();
    } catch (error) {
      toast.error('Error al actualizar estado');
    }
  };

  const exportPDF = () => {
    window.open(`${API_URL}/api/investigations/${investigationId}/export-pdf`, '_blank');
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        setPhotos(prev => [...prev, {
          id: Date.now() + Math.random(),
          name: file.name,
          data: event.target.result,
          description: ''
        }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removePhoto = (photoId) => {
    setPhotos(prev => prev.filter(p => p.id !== photoId));
  };

  const updatePhotoDescription = (photoId, description) => {
    setPhotos(prev => prev.map(p => p.id === photoId ? { ...p, description } : p));
  };

  const handleApproveWithSignature = async () => {
    if (!signature.name || !signature.position) {
      toast.error('Complete nombre y cargo para firmar');
      return;
    }
    
    try {
      // Save signature data
      await axios.put(`${API_URL}/api/investigations/${investigationId}`, {
        ...formData,
        approved_signature: {
          name: signature.name,
          position: signature.position,
          date: new Date().toISOString()
        }
      });
      
      // Update status to approved
      await axios.put(`${API_URL}/api/investigations/${investigationId}/status?status=approved`);
      
      toast.success('Investigación aprobada y firmada');
      setShowSignatureDialog(false);
      fetchInvestigation();
    } catch (error) {
      toast.error('Error al aprobar');
    }
  };

  const toggleIncidentType = (type) => {
    setFormData(prev => ({
      ...prev,
      incident_types: prev.incident_types.includes(type)
        ? prev.incident_types.filter(t => t !== type)
        : [...prev.incident_types, type]
    }));
  };

  const addCause = (type, value) => {
    if (!value.trim()) return;
    setFormData(prev => ({
      ...prev,
      [type]: [...prev[type], value.trim()]
    }));
  };

  const removeCause = (type, index) => {
    setFormData(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index)
    }));
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </main>
      </div>
    );
  }

  const statusColors = {
    draft: 'bg-slate-100 text-slate-800',
    in_progress: 'bg-blue-100 text-blue-800',
    review: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    closed: 'bg-purple-100 text-purple-800'
  };

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="investigation-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar 
          title="Investigación de Incidente"
          subtitle="ISO 45001:2018 - Sistema de Gestión de SST"
        >
          <Badge className={statusColors[investigation?.status] || 'bg-slate-100'}>
            {investigation?.status?.toUpperCase()}
          </Badge>
          <Button variant="outline" onClick={() => navigate('/incidents')} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Volver
          </Button>
          <Button onClick={saveInvestigation} disabled={saving} className="bg-blue-500 hover:bg-blue-600 gap-2">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Guardar
          </Button>
          <Button onClick={exportPDF} variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            PDF
          </Button>
        </TopBar>

        <div className="p-4 lg:p-6">
          {/* ISO 45001 Banner */}
          <Card className="border-blue-200 bg-blue-50 mb-6">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-blue-500 rounded-xl">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-900">Investigación según ISO 45001:2018</h3>
                <p className="text-sm text-slate-600">
                  Cláusula 10.2: Incidentes, no conformidades y acciones correctivas
                </p>
              </div>
              <div className="flex gap-2">
                {investigation?.status === 'draft' && (
                  <Button onClick={() => updateStatus('in_progress')} size="sm" className="bg-blue-500">
                    Iniciar Investigación
                  </Button>
                )}
                {investigation?.status === 'in_progress' && (
                  <Button onClick={() => updateStatus('review')} size="sm" variant="outline">
                    Enviar a Revisión
                  </Button>
                )}
                {investigation?.status === 'review' && (
                  <Dialog open={showSignatureDialog} onOpenChange={setShowSignatureDialog}>
                    <DialogTrigger asChild>
                      <Button size="sm" className="bg-green-500 gap-2">
                        <PenTool className="w-4 h-4" />
                        Aprobar y Firmar
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Firma Digital de Aprobación</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                          <p className="text-sm text-green-800">
                            Al firmar, usted certifica que ha revisado esta investigación y que las acciones correctivas son adecuadas según ISO 45001:2018.
                          </p>
                        </div>
                        <div className="space-y-2">
                          <Label>Nombre Completo *</Label>
                          <Input
                            value={signature.name}
                            onChange={(e) => setSignature({ ...signature, name: e.target.value })}
                            placeholder="Nombre del aprobador"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Cargo *</Label>
                          <Input
                            value={signature.position}
                            onChange={(e) => setSignature({ ...signature, position: e.target.value })}
                            placeholder="Cargo en la organización"
                          />
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500">
                            Fecha de firma: {new Date().toLocaleDateString('es-CL', { 
                              year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' 
                            })}
                          </p>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowSignatureDialog(false)}>Cancelar</Button>
                        <Button onClick={handleApproveWithSignature} className="bg-green-500 hover:bg-green-600 gap-2">
                          <Check className="w-4 h-4" />
                          Firmar y Aprobar
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                )}
                {investigation?.approved_signature && (
                  <Badge className="bg-green-100 text-green-800 gap-1">
                    <Check className="w-3 h-3" />
                    Firmado por: {investigation.approved_signature.name}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-7 mb-6">
              <TabsTrigger value="background" className="gap-2 text-xs sm:text-sm">
                <FileText className="w-4 h-4 hidden sm:block" />
                Antecedentes
              </TabsTrigger>
              <TabsTrigger value="worker" className="gap-2 text-xs sm:text-sm">
                <User className="w-4 h-4 hidden sm:block" />
                Trabajador
              </TabsTrigger>
              <TabsTrigger value="analysis" className="gap-2 text-xs sm:text-sm">
                <ClipboardList className="w-4 h-4 hidden sm:block" />
                Análisis
              </TabsTrigger>
              <TabsTrigger value="photos" className="gap-2 text-xs sm:text-sm">
                <Camera className="w-4 h-4 hidden sm:block" />
                Fotos
              </TabsTrigger>
              <TabsTrigger value="tree" className="gap-2 text-xs sm:text-sm">
                <GitBranch className="w-4 h-4 hidden sm:block" />
                Árbol
              </TabsTrigger>
              <TabsTrigger value="causes" className="gap-2 text-xs sm:text-sm">
                <Target className="w-4 h-4 hidden sm:block" />
                Causas
              </TabsTrigger>
              <TabsTrigger value="actions" className="gap-2 text-xs sm:text-sm">
                <CheckCircle className="w-4 h-4 hidden sm:block" />
                Acciones
              </TabsTrigger>
            </TabsList>

            {/* Tab 1: Antecedentes */}
            <TabsContent value="background">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">1. Antecedentes del Incidente</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Descripción del Incidente *</Label>
                      <Textarea
                        placeholder="Describa detalladamente lo acontecido..."
                        value={formData.incident_description}
                        onChange={(e) => setFormData({ ...formData, incident_description: e.target.value })}
                        rows={4}
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Fecha del Incidente *</Label>
                        <Input
                          type="date"
                          value={formData.incident_date}
                          onChange={(e) => setFormData({ ...formData, incident_date: e.target.value })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Hora del Incidente</Label>
                        <Input
                          type="time"
                          value={formData.incident_time}
                          onChange={(e) => setFormData({ ...formData, incident_time: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Tipo de Incidente *</Label>
                      <div className="flex flex-wrap gap-2">
                        {INCIDENT_TYPES.map((type) => (
                          <Badge
                            key={type.value}
                            className={`cursor-pointer ${
                              formData.incident_types.includes(type.value)
                                ? type.color
                                : 'bg-slate-100 text-slate-600'
                            }`}
                            onClick={() => toggleIncidentType(type.value)}
                          >
                            {type.label}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Lugar del Incidente *</Label>
                      <Input
                        placeholder="Ubicación específica"
                        value={formData.incident_location}
                        onChange={(e) => setFormData({ ...formData, incident_location: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Faena / Proyecto</Label>
                      <Input
                        placeholder="Nombre de la faena"
                        value={formData.work_site}
                        onChange={(e) => setFormData({ ...formData, work_site: e.target.value })}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Información Adicional</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Consecuencias / Parte del Cuerpo Lesionada</Label>
                      <Textarea
                        placeholder="Describa las consecuencias del incidente..."
                        value={formData.consequences}
                        onChange={(e) => setFormData({ ...formData, consequences: e.target.value })}
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Testigos</Label>
                      <Input
                        placeholder="Nombres de testigos"
                        value={formData.witnesses}
                        onChange={(e) => setFormData({ ...formData, witnesses: e.target.value })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Nombre y Cargo de Jefatura Directa</Label>
                      <Input
                        placeholder="Supervisor / Jefe directo"
                        value={formData.supervisor_name}
                        onChange={(e) => setFormData({ ...formData, supervisor_name: e.target.value })}
                      />
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <Label>Construcción del Relato (Narrativa)</Label>
                      <Textarea
                        placeholder="¿Cuándo? + ¿Dónde? + ¿Qué? + ¿Cuál? + ¿Cuánto?"
                        value={formData.narrative}
                        onChange={(e) => setFormData({ ...formData, narrative: e.target.value })}
                        rows={4}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Tab 2: Trabajador Afectado */}
            <TabsContent value="worker">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <User className="w-5 h-5" />
                    2. Antecedentes del Trabajador Afectado
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre Completo *</Label>
                      <Input
                        value={formData.affected_worker.name}
                        onChange={(e) => setFormData({
                          ...formData,
                          affected_worker: { ...formData.affected_worker, name: e.target.value }
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>RUT</Label>
                      <Input
                        placeholder="12.345.678-9"
                        value={formData.affected_worker.rut}
                        onChange={(e) => setFormData({
                          ...formData,
                          affected_worker: { ...formData.affected_worker, rut: e.target.value }
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Edad</Label>
                      <Input
                        type="number"
                        value={formData.affected_worker.age}
                        onChange={(e) => setFormData({
                          ...formData,
                          affected_worker: { ...formData.affected_worker, age: e.target.value }
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Cargo *</Label>
                      <Input
                        value={formData.affected_worker.position}
                        onChange={(e) => setFormData({
                          ...formData,
                          affected_worker: { ...formData.affected_worker, position: e.target.value }
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Antigüedad en la Empresa</Label>
                      <Input
                        placeholder="Ej: 2 años"
                        value={formData.affected_worker.seniority_company}
                        onChange={(e) => setFormData({
                          ...formData,
                          affected_worker: { ...formData.affected_worker, seniority_company: e.target.value }
                        })}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab 3: Análisis */}
            <TabsContent value="analysis">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">5.2 Pauta de Observación de la Tarea</CardTitle>
                    <CardDescription>Evaluación según ISO 45001</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      { key: 'task_own', label: '¿La tarea era propia de su puesto de trabajo?' },
                      { key: 'task_habitual', label: '¿La tarea es habitual?' },
                      { key: 'task_normal', label: '¿La tarea se desarrolló de manera normal?' },
                      { key: 'accident_possible', label: '¿De forma habitual era posible que ocurriera?' },
                      { key: 'received_instructions', label: '¿Había recibido instrucciones sobre la tarea?' },
                      { key: 'used_epp', label: '¿Utilizaba EPP al realizar la tarea?' }
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <span className="text-sm">{item.label}</span>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant={formData.task_observation[item.key] === true ? 'default' : 'outline'}
                            className={formData.task_observation[item.key] === true ? 'bg-green-500' : ''}
                            onClick={() => setFormData({
                              ...formData,
                              task_observation: { ...formData.task_observation, [item.key]: true }
                            })}
                          >
                            Sí
                          </Button>
                          <Button
                            size="sm"
                            variant={formData.task_observation[item.key] === false ? 'default' : 'outline'}
                            className={formData.task_observation[item.key] === false ? 'bg-red-500' : ''}
                            onClick={() => setFormData({
                              ...formData,
                              task_observation: { ...formData.task_observation, [item.key]: false }
                            })}
                          >
                            No
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">5.3 Revisión Documental</CardTitle>
                    <CardDescription>Verificación de documentación SST</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      { key: 'has_risk_matrix', label: '¿Cuenta con Matriz de Riesgos?' },
                      { key: 'has_procedure', label: '¿Cuenta con Procedimiento?' },
                      { key: 'has_ast', label: '¿Cuenta con AST (Análisis Seguro de Tarea)?' },
                      { key: 'has_epp_checklist', label: '¿Cuenta con Check List de EPP?' },
                      { key: 'has_training', label: '¿Tiene capacitación acorde a la tarea?' },
                      { key: 'has_medical_exam', label: '¿Cuenta con exámenes pre-ocupacionales?' }
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <span className="text-sm">{item.label}</span>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant={formData.document_review[item.key] === true ? 'default' : 'outline'}
                            className={formData.document_review[item.key] === true ? 'bg-green-500' : ''}
                            onClick={() => setFormData({
                              ...formData,
                              document_review: { ...formData.document_review, [item.key]: true }
                            })}
                          >
                            Sí
                          </Button>
                          <Button
                            size="sm"
                            variant={formData.document_review[item.key] === false ? 'default' : 'outline'}
                            className={formData.document_review[item.key] === false ? 'bg-red-500' : ''}
                            onClick={() => setFormData({
                              ...formData,
                              document_review: { ...formData.document_review, [item.key]: false }
                            })}
                          >
                            No
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Tab 4: Fotos */}
            <TabsContent value="photos">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Camera className="w-5 h-5" />
                    6. Evidencia Fotográfica
                  </CardTitle>
                  <CardDescription>Adjunte fotografías del lugar, condiciones y evidencias del incidente</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Upload area */}
                    <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handlePhotoUpload}
                        className="hidden"
                        id="photo-upload"
                      />
                      <label htmlFor="photo-upload" className="cursor-pointer">
                        <Upload className="w-10 h-10 mx-auto text-slate-400 mb-3" />
                        <p className="text-sm font-medium text-slate-700">Haga clic para subir fotos</p>
                        <p className="text-xs text-slate-500 mt-1">PNG, JPG hasta 5MB</p>
                      </label>
                    </div>

                    {/* Photos grid */}
                    {photos.length > 0 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {photos.map((photo) => (
                          <div key={photo.id} className="relative group border rounded-lg overflow-hidden">
                            <img 
                              src={photo.data} 
                              alt={photo.name}
                              className="w-full h-48 object-cover"
                            />
                            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                size="icon"
                                variant="destructive"
                                className="h-8 w-8"
                                onClick={() => removePhoto(photo.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                            <div className="p-3 bg-white">
                              <Input
                                placeholder="Descripción de la foto..."
                                value={photo.description}
                                onChange={(e) => updatePhotoDescription(photo.id, e.target.value)}
                                className="text-sm"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {photos.length === 0 && (
                      <div className="text-center py-8 text-slate-400">
                        <Image className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No hay fotos adjuntas</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab 5: Árbol de Causas */}
            <TabsContent value="tree">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <GitBranch className="w-5 h-5" />
                    9. Árbol de Causas Interactivo
                  </CardTitle>
                  <CardDescription>Visualización del análisis causal - Haga clic en las causas para editarlas o eliminarlas</CardDescription>
                </CardHeader>
                <CardContent>
                  <InteractiveCauseTree
                    incident={formData.incident_description}
                    immediateCauses={formData.immediate_causes}
                    basicCauses={formData.basic_causes}
                    rootCauses={formData.root_causes}
                    onUpdateCauses={(type, causes) => setFormData({ ...formData, [type]: causes })}
                    onAddCause={(type) => {
                      const input = prompt(`Agregar nueva ${type === 'immediate_causes' ? 'Causa Inmediata' : type === 'basic_causes' ? 'Causa Básica' : 'Causa Raíz'}:`);
                      if (input?.trim()) {
                        setFormData({ ...formData, [type]: [...formData[type], input.trim()] });
                        toast.success('Causa agregada');
                      }
                    }}
                    onRemoveCause={(type, index) => {
                      const updated = formData[type].filter((_, i) => i !== index);
                      setFormData({ ...formData, [type]: updated });
                      toast.success('Causa eliminada');
                    }}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab 6: Causas */}
            <TabsContent value="causes">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="border-red-200">
                  <CardHeader className="bg-red-50">
                    <CardTitle className="text-base text-red-800">Causas Inmediatas</CardTitle>
                    <CardDescription>Actos y condiciones subestándar</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="space-y-3">
                      {formData.immediate_causes.map((cause, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-red-50 rounded">
                          <span className="text-sm">{cause}</span>
                          <Button size="icon" variant="ghost" onClick={() => removeCause('immediate_causes', index)}>
                            <XCircle className="w-4 h-4 text-red-500" />
                          </Button>
                        </div>
                      ))}
                      <div className="flex gap-2">
                        <Input
                          placeholder="Agregar causa inmediata..."
                          id="immediate-cause-input"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              addCause('immediate_causes', e.target.value);
                              e.target.value = '';
                            }
                          }}
                        />
                        <Button
                          size="icon"
                          onClick={() => {
                            const input = document.getElementById('immediate-cause-input');
                            addCause('immediate_causes', input.value);
                            input.value = '';
                          }}
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-orange-200">
                  <CardHeader className="bg-orange-50">
                    <CardTitle className="text-base text-orange-800">Causas Básicas</CardTitle>
                    <CardDescription>Factores personales y del trabajo</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="space-y-3">
                      {formData.basic_causes.map((cause, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                          <span className="text-sm">{cause}</span>
                          <Button size="icon" variant="ghost" onClick={() => removeCause('basic_causes', index)}>
                            <XCircle className="w-4 h-4 text-orange-500" />
                          </Button>
                        </div>
                      ))}
                      <div className="flex gap-2">
                        <Input
                          placeholder="Agregar causa básica..."
                          id="basic-cause-input"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              addCause('basic_causes', e.target.value);
                              e.target.value = '';
                            }
                          }}
                        />
                        <Button
                          size="icon"
                          onClick={() => {
                            const input = document.getElementById('basic-cause-input');
                            addCause('basic_causes', input.value);
                            input.value = '';
                          }}
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-purple-200">
                  <CardHeader className="bg-purple-50">
                    <CardTitle className="text-base text-purple-800">Causas Raíz</CardTitle>
                    <CardDescription>Deficiencias en el SG-SST</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="space-y-3">
                      {formData.root_causes.map((cause, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-purple-50 rounded">
                          <span className="text-sm">{cause}</span>
                          <Button size="icon" variant="ghost" onClick={() => removeCause('root_causes', index)}>
                            <XCircle className="w-4 h-4 text-purple-500" />
                          </Button>
                        </div>
                      ))}
                      <div className="flex gap-2">
                        <Input
                          placeholder="Agregar causa raíz..."
                          id="root-cause-input"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              addCause('root_causes', e.target.value);
                              e.target.value = '';
                            }
                          }}
                        />
                        <Button
                          size="icon"
                          onClick={() => {
                            const input = document.getElementById('root-cause-input');
                            addCause('root_causes', input.value);
                            input.value = '';
                          }}
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Tab 5: Acciones Correctivas */}
            <TabsContent value="actions">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Acciones Correctivas y Preventivas</CardTitle>
                    <CardDescription>ISO 45001:2018 - Cláusula 10.2</CardDescription>
                  </div>
                  <Dialog open={showActionDialog} onOpenChange={setShowActionDialog}>
                    <DialogTrigger asChild>
                      <Button className="bg-green-500 hover:bg-green-600 gap-2">
                        <Plus className="w-4 h-4" />
                        Nueva Acción
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Agregar Acción Correctiva</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label>Descripción de la Acción *</Label>
                          <Textarea
                            value={newAction.description}
                            onChange={(e) => setNewAction({ ...newAction, description: e.target.value })}
                            placeholder="Describa la acción a implementar..."
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Tipo de Acción</Label>
                            <Select value={newAction.action_type} onValueChange={(v) => setNewAction({ ...newAction, action_type: v })}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="immediate">Inmediata</SelectItem>
                                <SelectItem value="corrective">Correctiva</SelectItem>
                                <SelectItem value="preventive">Preventiva</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Prioridad</Label>
                            <Select value={newAction.priority} onValueChange={(v) => setNewAction({ ...newAction, priority: v })}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="low">Baja</SelectItem>
                                <SelectItem value="medium">Media</SelectItem>
                                <SelectItem value="high">Alta</SelectItem>
                                <SelectItem value="critical">Crítica</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Responsable *</Label>
                            <Input
                              value={newAction.responsible}
                              onChange={(e) => setNewAction({ ...newAction, responsible: e.target.value })}
                              placeholder="Nombre del responsable"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Fecha Límite *</Label>
                            <Input
                              type="date"
                              value={newAction.due_date}
                              onChange={(e) => setNewAction({ ...newAction, due_date: e.target.value })}
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Cláusula ISO 45001</Label>
                          <Select value={newAction.iso_clause} onValueChange={(v) => setNewAction({ ...newAction, iso_clause: v })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Seleccione cláusula" />
                            </SelectTrigger>
                            <SelectContent>
                              {ISO_CLAUSES.map((clause) => (
                                <SelectItem key={clause.value} value={clause.value}>{clause.label}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowActionDialog(false)}>Cancelar</Button>
                        <Button onClick={addCorrectiveAction} className="bg-green-500 hover:bg-green-600">
                          Agregar Acción
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  {investigation?.corrective_actions?.length > 0 ? (
                    <div className="space-y-3">
                      {investigation.corrective_actions.map((action, index) => (
                        <div key={action.id || index} className="p-4 border rounded-lg">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium">{action.description}</p>
                              <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                                <span>Responsable: {action.responsible}</span>
                                <span>Fecha: {action.due_date}</span>
                                {action.iso_clause && (
                                  <Badge variant="outline">ISO {action.iso_clause}</Badge>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className={
                                action.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                action.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                action.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-green-100 text-green-800'
                              }>
                                {action.priority}
                              </Badge>
                              <Badge className={
                                action.status === 'completed' ? 'bg-green-100 text-green-800' :
                                action.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                'bg-slate-100 text-slate-800'
                              }>
                                {action.status}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p className="text-slate-500">No hay acciones correctivas definidas</p>
                      <p className="text-sm text-slate-400">Agregue acciones para corregir las causas identificadas</p>
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

// Interactive Cause Tree Component
function InteractiveCauseTree({ incident, immediateCauses, basicCauses, rootCauses, onAddCause, onRemoveCause }) {
  const [hoveredCause, setHoveredCause] = useState(null);
  const [editingCause, setEditingCause] = useState(null);

  const CauseNode = ({ cause, index, type, bgClass, borderClass, textClass }) => {
    const isHovered = hoveredCause === `${type}-${index}`;
    
    return (
      <div
        className={`relative group cursor-pointer transition-all duration-200 ${bgClass} border ${borderClass} ${textClass} px-4 py-2 rounded-lg text-sm max-w-xs
          ${isHovered ? 'shadow-lg scale-105 ring-2 ring-offset-2' : 'hover:shadow-md'}
          ${type === 'immediate_causes' ? 'ring-red-400' : type === 'basic_causes' ? 'ring-orange-400' : 'ring-purple-400'}
        `}
        onMouseEnter={() => setHoveredCause(`${type}-${index}`)}
        onMouseLeave={() => setHoveredCause(null)}
        data-testid={`cause-node-${type}-${index}`}
      >
        <span className="pr-6">{cause}</span>
        
        {/* Delete button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (window.confirm('¿Eliminar esta causa?')) {
              onRemoveCause(type, index);
            }
          }}
          className="absolute top-1 right-1 p-1 rounded-full bg-white/80 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100"
          title="Eliminar causa"
        >
          <XCircle className="w-4 h-4 text-red-500" />
        </button>
      </div>
    );
  };

  const AddCauseButton = ({ type, label }) => (
    <button
      onClick={() => onAddCause(type)}
      className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-dashed border-slate-300 rounded-lg hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
      data-testid={`add-cause-${type}`}
    >
      <Plus className="w-3 h-3" />
      Agregar {label}
    </button>
  );

  const Connector = ({ hasChildren }) => (
    <div className="flex flex-col items-center">
      <div className={`w-0.5 h-6 ${hasChildren ? 'bg-slate-400' : 'bg-slate-200'}`}></div>
      {hasChildren && (
        <div className="w-3 h-3 border-l-2 border-b-2 border-slate-400 transform rotate-[-45deg] -mt-1.5"></div>
      )}
    </div>
  );

  const hasCauses = immediateCauses.length > 0 || basicCauses.length > 0 || rootCauses.length > 0;

  return (
    <div className="p-6 bg-gradient-to-b from-slate-50 to-white rounded-xl border border-slate-200">
      {/* Cause Tree Visualization */}
      <div className="flex flex-col items-center space-y-2">
        
        {/* Incident (Top) - Fixed position */}
        <div className="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-4 rounded-xl shadow-lg max-w-lg text-center transform transition-transform hover:scale-102">
          <div className="flex items-center justify-center gap-2 mb-1">
            <AlertTriangle className="w-5 h-5" />
            <p className="font-bold text-sm tracking-wide">INCIDENTE</p>
          </div>
          <p className="text-xs opacity-90 leading-relaxed">{incident?.substring(0, 100) || 'Sin descripción'}...</p>
        </div>
        
        <Connector hasChildren={immediateCauses.length > 0} />
        
        {/* Immediate Causes */}
        <div className="w-full">
          <div className="text-center mb-3">
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-red-50 rounded-full">
              <div className="w-2 h-2 bg-red-400 rounded-full"></div>
              <p className="text-xs text-red-700 font-semibold tracking-wide">CAUSAS INMEDIATAS</p>
              <Badge variant="outline" className="text-red-600 border-red-300 text-[10px] px-1.5">{immediateCauses.length}</Badge>
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-3 min-h-[40px]">
            {immediateCauses.map((cause, idx) => (
              <CauseNode 
                key={idx} 
                cause={cause} 
                index={idx} 
                type="immediate_causes"
                bgClass="bg-red-50"
                borderClass="border-red-200"
                textClass="text-red-800"
              />
            ))}
            <AddCauseButton type="immediate_causes" label="Inmediata" />
          </div>
        </div>
        
        {(immediateCauses.length > 0 || basicCauses.length > 0) && <Connector hasChildren={basicCauses.length > 0} />}
        
        {/* Basic Causes */}
        <div className="w-full">
          <div className="text-center mb-3">
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-orange-50 rounded-full">
              <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
              <p className="text-xs text-orange-700 font-semibold tracking-wide">CAUSAS BÁSICAS</p>
              <Badge variant="outline" className="text-orange-600 border-orange-300 text-[10px] px-1.5">{basicCauses.length}</Badge>
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-3 min-h-[40px]">
            {basicCauses.map((cause, idx) => (
              <CauseNode 
                key={idx} 
                cause={cause} 
                index={idx} 
                type="basic_causes"
                bgClass="bg-orange-50"
                borderClass="border-orange-200"
                textClass="text-orange-800"
              />
            ))}
            <AddCauseButton type="basic_causes" label="Básica" />
          </div>
        </div>
        
        {(basicCauses.length > 0 || rootCauses.length > 0) && <Connector hasChildren={rootCauses.length > 0} />}
        
        {/* Root Causes */}
        <div className="w-full">
          <div className="text-center mb-3">
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-purple-50 rounded-full">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <p className="text-xs text-purple-700 font-semibold tracking-wide">CAUSAS RAÍZ</p>
              <Badge variant="outline" className="text-purple-600 border-purple-300 text-[10px] px-1.5">{rootCauses.length}</Badge>
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-3 min-h-[40px]">
            {rootCauses.map((cause, idx) => (
              <CauseNode 
                key={idx} 
                cause={cause} 
                index={idx} 
                type="root_causes"
                bgClass="bg-purple-50"
                borderClass="border-purple-200"
                textClass="text-purple-800"
              />
            ))}
            <AddCauseButton type="root_causes" label="Raíz" />
          </div>
        </div>
      </div>
      
      {/* Legend & Instructions */}
      <div className="mt-8 pt-4 border-t border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gradient-to-r from-red-500 to-red-600 rounded shadow"></div>
              <span className="text-slate-600">Incidente</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-50 border border-red-200 rounded"></div>
              <span className="text-slate-600">Causas Inmediatas</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-50 border border-orange-200 rounded"></div>
              <span className="text-slate-600">Causas Básicas</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-50 border border-purple-200 rounded"></div>
              <span className="text-slate-600">Causas Raíz</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 italic">
            Pase el cursor sobre una causa para ver opciones • Clic en + para agregar
          </p>
        </div>
      </div>
    </div>
  );
}
