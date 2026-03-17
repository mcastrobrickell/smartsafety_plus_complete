import React, { useState, useEffect } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import {
  Grid3X3,
  Plus,
  Eye,
  Edit,
  Trash2,
  AlertTriangle,
  Download,
  CheckCircle,
  Clock
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PROBABILITY_LEVELS = [
  { value: 1, label: 'Raro', description: 'Puede ocurrir solo en circunstancias excepcionales' },
  { value: 2, label: 'Improbable', description: 'Podría ocurrir en algún momento' },
  { value: 3, label: 'Posible', description: 'Podría ocurrir en algún momento' },
  { value: 4, label: 'Probable', description: 'Probablemente ocurrirá en la mayoría de las circunstancias' },
  { value: 5, label: 'Casi Seguro', description: 'Se espera que ocurra en la mayoría de las circunstancias' }
];

const SEVERITY_LEVELS = [
  { value: 1, label: 'Insignificante', description: 'Sin lesiones' },
  { value: 2, label: 'Menor', description: 'Primeros auxilios menores' },
  { value: 3, label: 'Moderado', description: 'Tratamiento médico requerido' },
  { value: 4, label: 'Mayor', description: 'Lesiones graves, hospitalización' },
  { value: 5, label: 'Catastrófico', description: 'Muerte o incapacidad permanente' }
];

const getRiskLevel = (probability, severity) => {
  const level = probability * severity;
  if (level >= 15) return { label: 'Crítico', color: 'bg-red-600 text-white', bgColor: 'bg-red-100' };
  if (level >= 10) return { label: 'Alto', color: 'bg-orange-500 text-white', bgColor: 'bg-orange-100' };
  if (level >= 5) return { label: 'Medio', color: 'bg-yellow-500 text-white', bgColor: 'bg-yellow-100' };
  return { label: 'Bajo', color: 'bg-green-500 text-white', bgColor: 'bg-green-100' };
};

export default function RiskMatrixPage() {
  const [matrices, setMatrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showRiskDialog, setShowRiskDialog] = useState(false);
  const [selectedMatrix, setSelectedMatrix] = useState(null);
  const [matrixForm, setMatrixForm] = useState({ name: '', area: '', process: '', description: '' });
  const [riskForm, setRiskForm] = useState({
    hazard: '',
    risk_description: '',
    consequences: '',
    probability: 3,
    severity: 3,
    existing_controls: '',
    additional_controls: '',
    responsible: '',
    deadline: '',
    status: 'open'
  });

  useEffect(() => {
    fetchMatrices();
  }, []);

  const fetchMatrices = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/risk-matrix`);
      setMatrices(response.data);
    } catch (error) {
      toast.error('Error al cargar matrices');
    } finally {
      setLoading(false);
    }
  };

  const fetchMatrix = async (matrixId) => {
    try {
      const response = await axios.get(`${API_URL}/api/risk-matrix/${matrixId}`);
      setSelectedMatrix(response.data);
    } catch (error) {
      toast.error('Error al cargar matriz');
    }
  };

  const handleCreateMatrix = async () => {
    try {
      const params = new URLSearchParams(matrixForm);
      await axios.post(`${API_URL}/api/risk-matrix?${params.toString()}`);
      toast.success('Matriz creada');
      setShowCreateDialog(false);
      setMatrixForm({ name: '', area: '', process: '', description: '' });
      fetchMatrices();
    } catch (error) {
      toast.error('Error al crear matriz');
    }
  };

  const handleAddRisk = async () => {
    if (!selectedMatrix) return;
    try {
      await axios.post(`${API_URL}/api/risk-matrix/${selectedMatrix.id}/risks`, riskForm);
      toast.success('Riesgo agregado');
      setShowRiskDialog(false);
      setRiskForm({
        hazard: '', risk_description: '', consequences: '', probability: 3, severity: 3,
        existing_controls: '', additional_controls: '', responsible: '', deadline: '', status: 'open'
      });
      fetchMatrix(selectedMatrix.id);
    } catch (error) {
      toast.error('Error al agregar riesgo');
    }
  };

  const handleDeleteRisk = async (riskId) => {
    if (!selectedMatrix || !window.confirm('¿Eliminar este riesgo?')) return;
    try {
      await axios.delete(`${API_URL}/api/risk-matrix/${selectedMatrix.id}/risks/${riskId}`);
      toast.success('Riesgo eliminado');
      fetchMatrix(selectedMatrix.id);
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const exportPDF = async (matrixId) => {
    try {
      const response = await axios.get(`${API_URL}/api/reports/export-pdf?report_type=risk-matrix`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `matriz-riesgos.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Reporte exportado');
    } catch (error) {
      toast.error('Error al exportar');
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="risk-matrix-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Matriz de Riesgos" subtitle="Evaluación y control de riesgos operacionales">
          {selectedMatrix ? (
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="rounded-lg"
                onClick={() => setSelectedMatrix(null)}
              >
                Volver a Lista
              </Button>
              <Button
                variant="outline"
                className="rounded-lg gap-2"
                onClick={() => exportPDF(selectedMatrix.id)}
              >
                <Download className="w-4 h-4" />
                Exportar
              </Button>
            </div>
          ) : (
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button className="bg-blue-500 hover:bg-blue-600 rounded-lg gap-2" data-testid="create-matrix-btn">
                  <Plus className="w-4 h-4" />
                  Nueva Matriz
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Crear Matriz de Riesgos</DialogTitle>
                  <DialogDescription>Define el área y proceso a evaluar</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Nombre de la Matriz</Label>
                    <Input
                      placeholder="Ej: Matriz de Riesgos - Planta Norte"
                      value={matrixForm.name}
                      onChange={(e) => setMatrixForm({ ...matrixForm, name: e.target.value })}
                      className="rounded-lg"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Área</Label>
                      <Input
                        placeholder="Ej: Producción"
                        value={matrixForm.area}
                        onChange={(e) => setMatrixForm({ ...matrixForm, area: e.target.value })}
                        className="rounded-lg"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Proceso</Label>
                      <Input
                        placeholder="Ej: Soldadura"
                        value={matrixForm.process}
                        onChange={(e) => setMatrixForm({ ...matrixForm, process: e.target.value })}
                        className="rounded-lg"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Descripción (Opcional)</Label>
                    <Textarea
                      placeholder="Descripción del alcance de la evaluación..."
                      value={matrixForm.description}
                      onChange={(e) => setMatrixForm({ ...matrixForm, description: e.target.value })}
                      className="rounded-lg"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancelar</Button>
                  <Button onClick={handleCreateMatrix} className="bg-blue-500 hover:bg-blue-600">Crear Matriz</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </TopBar>

        <div className="p-8">
          {selectedMatrix ? (
            // Matrix Detail View
            <div className="space-y-6">
              {/* Matrix Header */}
              <Card className="border-slate-200">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-xl font-bold text-slate-900">{selectedMatrix.name}</h2>
                      <p className="text-slate-500">{selectedMatrix.area} - {selectedMatrix.process}</p>
                      {selectedMatrix.description && (
                        <p className="text-sm text-slate-400 mt-2">{selectedMatrix.description}</p>
                      )}
                    </div>
                    <Badge className={selectedMatrix.status === 'draft' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}>
                      {selectedMatrix.status === 'draft' ? 'Borrador' : 'Aprobada'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Level Legend */}
              <Card className="border-slate-200">
                <CardContent className="p-4">
                  <p className="text-sm font-medium text-slate-700 mb-3">Niveles de Riesgo (Probabilidad x Severidad)</p>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-green-500 rounded"></div>
                      <span className="text-sm">Bajo (1-4)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                      <span className="text-sm">Medio (5-9)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-orange-500 rounded"></div>
                      <span className="text-sm">Alto (10-14)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-red-600 rounded"></div>
                      <span className="text-sm">Crítico (15-25)</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Risks Table */}
              <Card className="border-slate-200">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Riesgos Identificados</CardTitle>
                  <Dialog open={showRiskDialog} onOpenChange={setShowRiskDialog}>
                    <DialogTrigger asChild>
                      <Button className="bg-blue-500 hover:bg-blue-600 rounded-lg gap-2" data-testid="add-risk-btn">
                        <Plus className="w-4 h-4" />
                        Agregar Riesgo
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Agregar Riesgo</DialogTitle>
                        <DialogDescription>Identificar y evaluar un nuevo riesgo</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label>Peligro/Fuente</Label>
                          <Input
                            placeholder="Ej: Superficie resbaladiza"
                            value={riskForm.hazard}
                            onChange={(e) => setRiskForm({ ...riskForm, hazard: e.target.value })}
                            className="rounded-lg"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Descripción del Riesgo</Label>
                          <Textarea
                            placeholder="Describe el riesgo potencial..."
                            value={riskForm.risk_description}
                            onChange={(e) => setRiskForm({ ...riskForm, risk_description: e.target.value })}
                            className="rounded-lg"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Consecuencias</Label>
                          <Textarea
                            placeholder="Posibles daños o lesiones..."
                            value={riskForm.consequences}
                            onChange={(e) => setRiskForm({ ...riskForm, consequences: e.target.value })}
                            className="rounded-lg"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Probabilidad</Label>
                            <Select 
                              value={riskForm.probability.toString()} 
                              onValueChange={(v) => setRiskForm({ ...riskForm, probability: parseInt(v) })}
                            >
                              <SelectTrigger className="rounded-lg">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {PROBABILITY_LEVELS.map((p) => (
                                  <SelectItem key={p.value} value={p.value.toString()}>
                                    {p.value} - {p.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Severidad</Label>
                            <Select 
                              value={riskForm.severity.toString()} 
                              onValueChange={(v) => setRiskForm({ ...riskForm, severity: parseInt(v) })}
                            >
                              <SelectTrigger className="rounded-lg">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {SEVERITY_LEVELS.map((s) => (
                                  <SelectItem key={s.value} value={s.value.toString()}>
                                    {s.value} - {s.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        
                        <div className="p-3 rounded-lg border" style={{ backgroundColor: getRiskLevel(riskForm.probability, riskForm.severity).bgColor }}>
                          <p className="text-sm font-medium">
                            Nivel de Riesgo: <span className="font-bold">{riskForm.probability * riskForm.severity}</span> - {getRiskLevel(riskForm.probability, riskForm.severity).label}
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>Controles Existentes</Label>
                          <Textarea
                            placeholder="Medidas de control actuales..."
                            value={riskForm.existing_controls}
                            onChange={(e) => setRiskForm({ ...riskForm, existing_controls: e.target.value })}
                            className="rounded-lg"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Controles Adicionales Propuestos</Label>
                          <Textarea
                            placeholder="Medidas adicionales necesarias..."
                            value={riskForm.additional_controls}
                            onChange={(e) => setRiskForm({ ...riskForm, additional_controls: e.target.value })}
                            className="rounded-lg"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Responsable</Label>
                            <Input
                              placeholder="Nombre del responsable"
                              value={riskForm.responsible}
                              onChange={(e) => setRiskForm({ ...riskForm, responsible: e.target.value })}
                              className="rounded-lg"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Fecha Límite</Label>
                            <Input
                              type="date"
                              value={riskForm.deadline}
                              onChange={(e) => setRiskForm({ ...riskForm, deadline: e.target.value })}
                              className="rounded-lg"
                            />
                          </div>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowRiskDialog(false)}>Cancelar</Button>
                        <Button onClick={handleAddRisk} className="bg-blue-500 hover:bg-blue-600">Agregar Riesgo</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  {selectedMatrix.risks?.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Peligro</TableHead>
                          <TableHead>Riesgo</TableHead>
                          <TableHead className="text-center">P</TableHead>
                          <TableHead className="text-center">S</TableHead>
                          <TableHead className="text-center">Nivel</TableHead>
                          <TableHead>Responsable</TableHead>
                          <TableHead>Estado</TableHead>
                          <TableHead className="text-right">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedMatrix.risks.map((risk) => {
                          const level = getRiskLevel(risk.probability, risk.severity);
                          return (
                            <TableRow key={risk.id}>
                              <TableCell className="font-medium">{risk.hazard}</TableCell>
                              <TableCell className="max-w-xs truncate">{risk.risk_description}</TableCell>
                              <TableCell className="text-center">{risk.probability}</TableCell>
                              <TableCell className="text-center">{risk.severity}</TableCell>
                              <TableCell className="text-center">
                                <Badge className={level.color}>{risk.risk_level}</Badge>
                              </TableCell>
                              <TableCell>{risk.responsible || '-'}</TableCell>
                              <TableCell>
                                <Badge className={risk.status === 'open' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}>
                                  {risk.status === 'open' ? 'Abierto' : 'Cerrado'}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="text-red-600"
                                  onClick={() => handleDeleteRisk(risk.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <AlertTriangle className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p>No hay riesgos identificados</p>
                      <Button
                        className="mt-4 bg-blue-500 hover:bg-blue-600 rounded-lg"
                        onClick={() => setShowRiskDialog(true)}
                      >
                        Agregar Primer Riesgo
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            // Matrices List View
            <>
              {loading ? (
                <div className="flex justify-center py-12">
                  <div className="spinner"></div>
                </div>
              ) : matrices.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {matrices.map((matrix) => (
                    <Card key={matrix.id} className="border-slate-200 hover:shadow-md transition-shadow cursor-pointer" onClick={() => fetchMatrix(matrix.id)}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{matrix.name}</CardTitle>
                            <p className="text-sm text-slate-500">{matrix.area} - {matrix.process}</p>
                          </div>
                          <Grid3X3 className="w-8 h-8 text-slate-300" />
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                            <span className="text-sm text-slate-600">{matrix.risks?.length || 0} riesgos</span>
                          </div>
                          <Badge className={matrix.status === 'draft' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}>
                            {matrix.status === 'draft' ? 'Borrador' : 'Aprobada'}
                          </Badge>
                        </div>
                        <Button variant="outline" className="w-full mt-4 rounded-lg">
                          <Eye className="w-4 h-4 mr-2" />
                          Ver Matriz
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="border-slate-200">
                  <CardContent className="text-center py-12">
                    <Grid3X3 className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-500">No hay matrices de riesgo creadas</p>
                    <Button
                      className="mt-4 bg-blue-500 hover:bg-blue-600 rounded-lg"
                      onClick={() => setShowCreateDialog(true)}
                    >
                      Crear Primera Matriz
                    </Button>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
