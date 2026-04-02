import React, { useState, useEffect, useRef } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  FileText,
  Plus,
  Upload,
  Brain,
  AlertTriangle,
  Shield,
  HardHat,
  Eye,
  Trash2,
  Loader2
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PROCEDURE_CATEGORIES = [
  'Trabajo en Altura',
  'Espacios Confinados',
  'Trabajos en Caliente',
  'Manejo de Químicos',
  'Izaje de Cargas',
  'Excavaciones',
  'Bloqueo/Etiquetado',
  'Emergencias',
  'General'
];

export default function ProceduresPage() {
  const [procedures, setProcedures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedProcedure, setSelectedProcedure] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    category: '',
    description: ''
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProcedures();
  }, []);

  const fetchProcedures = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/procedures`);
      setProcedures(response.data);
    } catch (error) {
      toast.error('Error al cargar procedimientos');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
        toast.error('Solo se permiten archivos TXT, PDF o DOC');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !formData.code || !formData.name || !formData.category) {
      toast.error('Completa todos los campos requeridos');
      return;
    }

    setUploading(true);
    try {
      const data = new FormData();
      data.append('code', formData.code);
      data.append('name', formData.name);
      data.append('category', formData.category);
      data.append('description', formData.description);
      data.append('file', selectedFile);

      const response = await axios.post(`${API_URL}/api/procedures`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success('Procedimiento creado y analizado con IA');
      setShowAddDialog(false);
      setFormData({ code: '', name: '', category: '', description: '' });
      setSelectedFile(null);
      fetchProcedures();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear procedimiento');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (procedureId) => {
    if (!window.confirm('¿Eliminar este procedimiento?')) return;
    try {
      await axios.delete(`${API_URL}/api/procedures/${procedureId}`);
      toast.success('Procedimiento eliminado');
      fetchProcedures();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const viewProcedure = async (procedureId) => {
    try {
      const response = await axios.get(`${API_URL}/api/procedures/${procedureId}`);
      setSelectedProcedure(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      toast.error('Error al cargar detalle');
    }
  };

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="procedures-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Procedimientos de Seguridad" subtitle="Gestión documental con análisis de IA">
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="btn-primary rounded-lg gap-2" data-testid="add-procedure-btn">
                <Plus className="w-4 h-4" />
                Nuevo Procedimiento
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Subir Procedimiento</DialogTitle>
                <DialogDescription>El documento será analizado por IA para identificar riesgos y controles</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Código</Label>
                    <Input
                      placeholder="PROC-001"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      className="rounded-lg"
                      data-testid="procedure-code-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Categoría</Label>
                    <Select value={formData.category} onValueChange={(v) => setFormData({ ...formData, category: v })}>
                      <SelectTrigger className="rounded-lg" data-testid="procedure-category-select">
                        <SelectValue placeholder="Seleccionar" />
                      </SelectTrigger>
                      <SelectContent>
                        {PROCEDURE_CATEGORIES.map((cat) => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Nombre del Procedimiento</Label>
                  <Input
                    placeholder="Procedimiento de Trabajo en Altura"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="rounded-lg"
                    data-testid="procedure-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Descripción (Opcional)</Label>
                  <Textarea
                    placeholder="Breve descripción del procedimiento..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Archivo del Procedimiento</Label>
                  <div
                    className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                      selectedFile ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-slate-400'
                    }`}
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="file-upload-zone"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.pdf,.doc,.docx"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    {selectedFile ? (
                      <div className="space-y-2">
                        <FileText className="w-10 h-10 mx-auto text-blue-500" />
                        <p className="text-sm text-slate-400">{selectedFile.name}</p>
                        <p className="text-xs text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="w-10 h-10 mx-auto text-slate-400" />
                        <p className="text-slate-400">Arrastra o haz clic para subir</p>
                        <p className="text-xs text-slate-400">TXT, PDF, DOC, DOCX</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-blue-800">Análisis con IA</p>
                      <p className="text-sm text-blue-600">El documento será analizado automáticamente para identificar riesgos, controles y EPP requerido.</p>
                    </div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)} className="rounded-lg">
                  Cancelar
                </Button>
                <Button
                  onClick={handleUpload}
                  disabled={uploading || !selectedFile}
                  className="btn-primary rounded-lg gap-2"
                  data-testid="upload-procedure-btn"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analizando...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Subir y Analizar
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TopBar>

        <div className="p-8 space-y-6">
          {/* Info Banner */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-blue-500 rounded-xl">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Integración con Scan 360°</h3>
                <p className="text-sm text-slate-400">
                  Los procedimientos analizados por IA mejoran la detección de riesgos en el Scan 360°. 
                  Al realizar un scan, puedes seleccionar el procedimiento aplicable para una inspección más precisa.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Procedures Grid */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="spinner"></div>
            </div>
          ) : procedures.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {procedures.map((proc) => (
                <Card key={proc.id} className="border-cyan-accent/10 hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant="outline" className="mb-2">{proc.category}</Badge>
                        <CardTitle className="text-lg">{proc.name}</CardTitle>
                        <p className="text-sm text-slate-500 font-mono">{proc.code}</p>
                      </div>
                      <FileText className="w-8 h-8 text-slate-300" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    {proc.ai_analysis && (
                      <p className="text-sm text-slate-400 mb-4 line-clamp-2">{proc.ai_analysis}</p>
                    )}
                    
                    <div className="space-y-2 mb-4">
                      {proc.risks_identified?.length > 0 && (
                        <div className="flex items-center gap-2 text-sm">
                          <AlertTriangle className="w-4 h-4 text-orange-500" />
                          <span className="text-slate-400">{proc.risks_identified.length} riesgos identificados</span>
                        </div>
                      )}
                      {proc.controls_required?.length > 0 && (
                        <div className="flex items-center gap-2 text-sm">
                          <Shield className="w-4 h-4 text-blue-500" />
                          <span className="text-slate-400">{proc.controls_required.length} controles requeridos</span>
                        </div>
                      )}
                      {proc.epp_required?.length > 0 && (
                        <div className="flex items-center gap-2 text-sm">
                          <HardHat className="w-4 h-4 text-green-500" />
                          <span className="text-slate-400">{proc.epp_required.length} EPP requeridos</span>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1 rounded-lg"
                        onClick={() => viewProcedure(proc.id)}
                        data-testid={`view-procedure-${proc.id}`}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Ver Detalle
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        className="text-red-600 border-red-200 rounded-lg"
                        onClick={() => handleDelete(proc.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="border-cyan-accent/10">
              <CardContent className="text-center py-12">
                <FileText className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                <p className="text-slate-500">No hay procedimientos registrados</p>
                <p className="text-sm text-slate-400 mt-2">Sube tu primer procedimiento para análisis con IA</p>
                <Button
                  className="mt-4 btn-primary rounded-lg"
                  onClick={() => setShowAddDialog(true)}
                >
                  Subir Procedimiento
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Detail Dialog */}
          <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
            <DialogContent className="max-w-2xl max-h-[80vh]">
              <DialogHeader>
                <DialogTitle>{selectedProcedure?.name}</DialogTitle>
                <DialogDescription>
                  {selectedProcedure?.code} | {selectedProcedure?.category}
                </DialogDescription>
              </DialogHeader>
              {selectedProcedure && (
                <ScrollArea className="max-h-[60vh]">
                  <div className="space-y-6 py-4">
                    {/* AI Summary */}
                    {selectedProcedure.ai_analysis && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Brain className="w-5 h-5 text-blue-600" />
                          <p className="font-medium text-blue-800">Resumen IA</p>
                        </div>
                        <p className="text-sm text-blue-700">{selectedProcedure.ai_analysis}</p>
                      </div>
                    )}

                    {/* Risks */}
                    {selectedProcedure.risks_identified?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-white mb-2 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-orange-500" />
                          Riesgos Identificados
                        </h4>
                        <ul className="space-y-1">
                          {selectedProcedure.risks_identified.map((risk, i) => (
                            <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-2"></span>
                              {risk}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Controls */}
                    {selectedProcedure.controls_required?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-white mb-2 flex items-center gap-2">
                          <Shield className="w-4 h-4 text-blue-500" />
                          Controles Requeridos
                        </h4>
                        <ul className="space-y-1">
                          {selectedProcedure.controls_required.map((control, i) => (
                            <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2"></span>
                              {control}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* EPP */}
                    {selectedProcedure.epp_required?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-white mb-2 flex items-center gap-2">
                          <HardHat className="w-4 h-4 text-green-500" />
                          EPP Requerido
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedProcedure.epp_required.map((epp, i) => (
                            <Badge key={i} variant="outline" className="bg-green-50 text-green-800 border-green-200">
                              {epp}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Content Preview */}
                    <div>
                      <h4 className="font-medium text-white mb-2">Contenido del Documento</h4>
                      <div className="p-4 bg-dark-bg rounded-lg text-sm text-slate-400 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {selectedProcedure.content?.substring(0, 2000)}
                        {selectedProcedure.content?.length > 2000 && '...'}
                      </div>
                    </div>
                  </div>
                </ScrollArea>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
