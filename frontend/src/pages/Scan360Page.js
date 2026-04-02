import React, { useState, useEffect, useRef } from 'react';
import { Sidebar, TopBar } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import {
  Scan,
  Upload,
  Camera,
  AlertTriangle,
  CheckCircle,
  Clock,
  MapPin,
  FileText,
  Eye,
  Loader2,
  Trash2
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function Scan360Page() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedScan, setSelectedScan] = useState(null);
  const [scanDetails, setScanDetails] = useState(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [formData, setFormData] = useState({ name: '', location: '' });
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/scans`);
      setScans(response.data);
    } catch (error) {
      toast.error('Error al cargar scans');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        toast.error('Solo se permiten imágenes JPEG, PNG o WEBP');
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !formData.name || !formData.location) {
      toast.error('Completa todos los campos');
      return;
    }

    setUploading(true);
    try {
      const data = new FormData();
      data.append('name', formData.name);
      data.append('location', formData.location);
      data.append('image', selectedFile);

      const response = await axios.post(`${API_URL}/api/scans/analyze`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success(`Análisis completado: ${response.data.findings_count} hallazgos detectados`);
      setShowUploadDialog(false);
      setFormData({ name: '', location: '' });
      setSelectedFile(null);
      setPreviewUrl(null);
      fetchScans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al analizar imagen');
    } finally {
      setUploading(false);
    }
  };

  const viewScanDetails = async (scan) => {
    try {
      const response = await axios.get(`${API_URL}/api/scans/${scan.id}`);
      setScanDetails(response.data);
      setSelectedScan(scan);
    } catch (error) {
      toast.error('Error al cargar detalles');
    }
  };

  const handleDeleteScan = async (scanId, e) => {
    e.stopPropagation(); // Prevent triggering the card click
    
    if (!window.confirm('¿Estás seguro de eliminar este scan? También se eliminarán todos los hallazgos asociados.')) {
      return;
    }
    
    try {
      await axios.delete(`${API_URL}/api/scans/${scanId}`);
      toast.success('Scan eliminado correctamente');
      
      // Clear selection if deleted scan was selected
      if (selectedScan?.id === scanId) {
        setSelectedScan(null);
        setScanDetails(null);
      }
      
      fetchScans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar scan');
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critico: 'badge-critical',
      alto: 'badge-high',
      medio: 'badge-medium',
      bajo: 'badge-low'
    };
    return colors[severity?.toLowerCase()] || 'badge-medium';
  };

  const getRiskLevelStyle = (level) => {
    const styles = {
      critico: 'bg-red-100 text-red-800 border-red-200',
      alto: 'bg-orange-100 text-orange-800 border-orange-200',
      medio: 'bg-amber-100 text-amber-800 border-amber-200',
      bajo: 'bg-green-100 text-green-800 border-green-200'
    };
    return styles[level?.toLowerCase()] || styles.medio;
  };

  return (
    <div className="flex min-h-screen bg-dark-bg" data-testid="scan360-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar title="Scan 360° - Análisis de Seguridad">
          <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
            <DialogTrigger asChild>
              <Button className="bg-amber-500 hover:bg-amber-400 text-white rounded-sm gap-2" data-testid="new-scan-btn">
                <Scan className="w-4 h-4" />
                Nuevo Scan
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-['Manrope']">Nuevo Análisis de Seguridad</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Nombre del Scan</Label>
                  <Input
                    placeholder="Ej: Bodega Principal - Sector A"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="rounded-sm"
                    data-testid="scan-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Ubicación</Label>
                  <Input
                    placeholder="Ej: Nave Industrial 2, Piso 1"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="rounded-sm"
                    data-testid="scan-location-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Imagen 360° / Industrial</Label>
                  <div
                    className={`border-2 border-dashed rounded-sm p-6 text-center cursor-pointer transition-colors ${
                      previewUrl ? 'border-amber-500 bg-amber-50' : 'border-slate-300 hover:border-slate-400'
                    }`}
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="image-upload-zone"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleFileSelect}
                      className="hidden"
                      data-testid="image-file-input"
                    />
                    {previewUrl ? (
                      <div className="space-y-3">
                        <img src={previewUrl} alt="Preview" className="max-h-48 mx-auto rounded" />
                        <p className="text-sm text-slate-400">{selectedFile?.name}</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="w-10 h-10 mx-auto text-slate-400" />
                        <p className="text-slate-400">Arrastra o haz clic para subir</p>
                        <p className="text-xs text-slate-400">JPEG, PNG o WEBP</p>
                      </div>
                    )}
                  </div>
                </div>
                <Button
                  className="w-full bg-slate-900 hover:bg-slate-800 rounded-sm gap-2"
                  onClick={handleUpload}
                  disabled={uploading || !selectedFile}
                  data-testid="analyze-btn"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analizando con IA...
                    </>
                  ) : (
                    <>
                      <Scan className="w-4 h-4" />
                      Analizar Imagen
                    </>
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </TopBar>

        <div className="p-8">
          {/* Info Banner */}
          <Card className="border-amber-200 bg-amber-50 mb-8">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-amber-500 rounded-sm">
                <Camera className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white font-['Manrope']">Análisis de Seguridad con IA</h3>
                <p className="text-sm text-slate-400">
                  Sube una imagen industrial o 360° para detectar automáticamente riesgos de seguridad, 
                  incumplimientos de EPP y condiciones inseguras según estándares OSHA.
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Scans List */}
            <div className="lg:col-span-2">
              <Card className="border-cyan-accent/10">
                <CardHeader>
                  <CardTitle className="font-['Manrope']">Historial de Scans</CardTitle>
                  <CardDescription>Análisis de seguridad realizados</CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <div className="spinner"></div>
                    </div>
                  ) : scans.length > 0 ? (
                    <div className="space-y-3">
                      {scans.map((scan) => (
                        <div
                          key={scan.id}
                          className={`p-4 border rounded-sm cursor-pointer transition-all ${
                            selectedScan?.id === scan.id
                              ? 'border-amber-500 bg-amber-50'
                              : 'border-cyan-accent/10 hover:border-slate-300 hover:bg-dark-bg'
                          }`}
                          onClick={() => viewScanDetails(scan)}
                          data-testid={`scan-item-${scan.id}`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3">
                              <div className={`p-2 rounded-sm ${
                                scan.critical_count > 0 ? 'bg-red-100' : 'bg-green-100'
                              }`}>
                                {scan.critical_count > 0 ? (
                                  <AlertTriangle className="w-5 h-5 text-red-600" />
                                ) : (
                                  <CheckCircle className="w-5 h-5 text-green-600" />
                                )}
                              </div>
                              <div>
                                <p className="font-semibold text-white">{scan.name}</p>
                                <div className="flex items-center gap-2 text-sm text-slate-500 mt-1">
                                  <MapPin className="w-3 h-3" />
                                  <span>{scan.location}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-slate-500 mt-1">
                                  <Clock className="w-3 h-3" />
                                  <span>{new Date(scan.scanned_at).toLocaleString()}</span>
                                </div>
                              </div>
                            </div>
                            <div className="text-right flex flex-col items-end gap-2">
                              <div>
                                <p className="text-lg font-bold text-white">{scan.findings_count}</p>
                                <p className="text-xs text-slate-500">hallazgos</p>
                                {scan.critical_count > 0 && (
                                  <Badge className="badge-critical mt-1">{scan.critical_count} críticos</Badge>
                                )}
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-slate-400 hover:text-red-600 hover:bg-red-50"
                                onClick={(e) => handleDeleteScan(scan.id, e)}
                                data-testid={`delete-scan-${scan.id}`}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Scan className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                      <p className="text-slate-500">No hay scans realizados</p>
                      <Button
                        className="mt-4 bg-amber-500 hover:bg-amber-400 text-white rounded-sm"
                        onClick={() => setShowUploadDialog(true)}
                      >
                        Realizar Primer Scan
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Scan Details Panel */}
            <div>
              <Card className="border-cyan-accent/10 sticky top-24">
                <CardHeader>
                  <CardTitle className="font-['Manrope']">Detalles del Scan</CardTitle>
                </CardHeader>
                <CardContent>
                  {scanDetails ? (
                    <div className="space-y-4">
                      {/* Risk Level */}
                      {scanDetails.scan.risk_level && (
                        <div className={`p-4 rounded-sm border ${getRiskLevelStyle(scanDetails.scan.risk_level)}`}>
                          <p className="text-sm font-medium">Nivel de Riesgo General</p>
                          <p className="text-xl font-bold capitalize">{scanDetails.scan.risk_level}</p>
                        </div>
                      )}

                      {/* Summary */}
                      {scanDetails.scan.summary && (
                        <div className="p-4 bg-dark-bg rounded-sm">
                          <p className="text-sm font-medium text-slate-700 mb-2">Resumen del Análisis</p>
                          <p className="text-sm text-slate-400">{scanDetails.scan.summary}</p>
                        </div>
                      )}

                      {/* Findings */}
                      <div>
                        <p className="text-sm font-medium text-slate-700 mb-3">Hallazgos Detectados</p>
                        <ScrollArea className="h-72">
                          {scanDetails.findings.length > 0 ? (
                            <div className="space-y-3">
                              {scanDetails.findings.map((finding) => (
                                <div key={finding.id} className="p-3 border border-cyan-accent/10 rounded-sm">
                                  <div className="flex items-start justify-between mb-2">
                                    <Badge className={getSeverityColor(finding.severity)}>
                                      {finding.severity}
                                    </Badge>
                                    <span className="text-xs text-slate-500">{finding.confidence}%</span>
                                  </div>
                                  <p className="text-sm font-medium text-white">{finding.category}</p>
                                  <p className="text-xs text-slate-400 mt-1">{finding.description}</p>
                                  {finding.corrective_action && (
                                    <div className="mt-2 p-2 bg-blue-50 rounded text-xs text-blue-800">
                                      <strong>Acción:</strong> {finding.corrective_action}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-slate-500 text-center py-4">No se detectaron hallazgos</p>
                          )}
                        </ScrollArea>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Eye className="w-10 h-10 mx-auto text-slate-300 mb-3" />
                      <p className="text-slate-500 text-sm">Selecciona un scan para ver los detalles</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
