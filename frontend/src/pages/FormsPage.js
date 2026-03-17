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
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { Slider } from '../components/ui/slider';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  ClipboardList,
  Plus,
  FileText,
  CheckSquare,
  Search,
  Send,
  Clock,
  MapPin,
  User,
  ChevronRight,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const FORM_TYPE_ICONS = {
  inspection: FileText,
  checklist: CheckSquare,
  audit: Search,
  survey: ClipboardList
};

const FORM_TYPE_COLORS = {
  inspection: 'bg-blue-100 text-blue-700',
  checklist: 'bg-green-100 text-green-700',
  audit: 'bg-purple-100 text-purple-700',
  survey: 'bg-orange-100 text-orange-700'
};

export default function FormsPage() {
  const [templates, setTemplates] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('templates');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showFormDialog, setShowFormDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({});
  const [formLocation, setFormLocation] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [templatesRes, submissionsRes] = await Promise.all([
        axios.get(`${API_URL}/api/ecosystem/smartforms/templates`),
        axios.get(`${API_URL}/api/ecosystem/smartforms/submissions`)
      ]);
      setTemplates(templatesRes.data);
      setSubmissions(submissionsRes.data);
    } catch (error) {
      toast.error('Error al cargar formularios');
    } finally {
      setLoading(false);
    }
  };

  const openForm = (template) => {
    setSelectedTemplate(template);
    setFormData({});
    setFormLocation('');
    setShowFormDialog(true);
  };

  const handleFieldChange = (fieldId, value) => {
    setFormData(prev => ({ ...prev, [fieldId]: value }));
  };

  const handleSubmitForm = async () => {
    if (!selectedTemplate) return;

    // Validate required fields
    const missingRequired = selectedTemplate.fields
      .filter(f => f.required && !formData[f.id])
      .map(f => f.label);

    if (missingRequired.length > 0) {
      toast.error(`Campos requeridos: ${missingRequired.join(', ')}`);
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/ecosystem/smartforms/submit`, null, {
        params: {
          template_id: selectedTemplate.id,
          location: formLocation || undefined
        },
        headers: { 'Content-Type': 'application/json' },
        data: { data: formData }
      });

      toast.success('Formulario enviado correctamente');
      setShowFormDialog(false);
      setSelectedTemplate(null);
      setFormData({});
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al enviar formulario');
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (field) => {
    const value = formData[field.id];

    switch (field.type) {
      case 'text':
        return (
          <Input
            placeholder={field.placeholder || `Ingrese ${field.label.toLowerCase()}`}
            value={value || ''}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            className="rounded-lg"
          />
        );

      case 'textarea':
        return (
          <Textarea
            placeholder={field.placeholder || `Ingrese ${field.label.toLowerCase()}`}
            value={value || ''}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            rows={3}
            className="rounded-lg"
          />
        );

      case 'select':
        return (
          <Select value={value || ''} onValueChange={(v) => handleFieldChange(field.id, v)}>
            <SelectTrigger className="rounded-lg">
              <SelectValue placeholder="Seleccione una opción" />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((opt) => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'checkbox':
        return (
          <div className="flex items-center gap-2">
            <Checkbox
              id={field.id}
              checked={value || false}
              onCheckedChange={(checked) => handleFieldChange(field.id, checked)}
            />
            <label htmlFor={field.id} className="text-sm text-slate-600 cursor-pointer">
              {field.description || 'Marcar si aplica'}
            </label>
          </div>
        );

      case 'date':
        return (
          <Input
            type="date"
            value={value || ''}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            className="rounded-lg"
          />
        );

      case 'range':
        return (
          <div className="space-y-2">
            <Slider
              value={[value || field.min || 1]}
              onValueChange={([v]) => handleFieldChange(field.id, v)}
              min={field.min || 1}
              max={field.max || 5}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-500">
              <span>{field.min || 1}</span>
              <span className="font-medium text-blue-600">{value || field.min || 1}</span>
              <span>{field.max || 5}</span>
            </div>
          </div>
        );

      case 'file':
        return (
          <Input
            type="file"
            accept={field.accept || '*'}
            multiple={field.multiple || false}
            onChange={(e) => handleFieldChange(field.id, e.target.files)}
            className="rounded-lg"
          />
        );

      default:
        return (
          <Input
            value={value || ''}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            className="rounded-lg"
          />
        );
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50" data-testid="forms-page">
      <Sidebar />
      <main className="flex-1">
        <TopBar 
          title="Formularios Dinámicos" 
          subtitle="Inspecciones y checklists integrados con SmartForms+"
        />

        <div className="p-4 lg:p-8">
          {/* Integration Banner */}
          <Card className="border-green-200 bg-green-50 mb-6">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-green-500 rounded-xl">
                <ClipboardList className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-900">Integración SmartForms+</h3>
                <p className="text-sm text-slate-600">
                  Utiliza formularios dinámicos para inspecciones, checklists y auditorías. 
                  Los datos se sincronizan automáticamente con el ecosistema Smart+.
                </p>
              </div>
            </CardContent>
          </Card>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="templates" className="gap-2">
                <FileText className="w-4 h-4" />
                Plantillas
              </TabsTrigger>
              <TabsTrigger value="submissions" className="gap-2">
                <CheckSquare className="w-4 h-4" />
                Respuestas
                {submissions.length > 0 && (
                  <Badge variant="secondary" className="ml-1">{submissions.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            {/* Templates Tab */}
            <TabsContent value="templates">
              {loading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {templates.map((template) => {
                    const Icon = FORM_TYPE_ICONS[template.form_type] || FileText;
                    const colorClass = FORM_TYPE_COLORS[template.form_type] || 'bg-slate-100 text-slate-700';
                    
                    return (
                      <Card 
                        key={template.id} 
                        className="border-slate-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                        onClick={() => openForm(template)}
                      >
                        <CardContent className="p-5">
                          <div className="flex items-start justify-between mb-3">
                            <div className={`p-2 rounded-lg ${colorClass}`}>
                              <Icon className="w-5 h-5" />
                            </div>
                            <Badge variant="outline" className="capitalize">
                              {template.form_type}
                            </Badge>
                          </div>
                          <h3 className="font-semibold text-slate-900 mb-1">{template.name}</h3>
                          <p className="text-sm text-slate-500 mb-3 line-clamp-2">
                            {template.description}
                          </p>
                          <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>{template.fields?.length || 0} campos</span>
                            <ChevronRight className="w-4 h-4" />
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </TabsContent>

            {/* Submissions Tab */}
            <TabsContent value="submissions">
              {submissions.length > 0 ? (
                <div className="space-y-3">
                  {submissions.map((sub) => {
                    const template = templates.find(t => t.id === sub.form_template_id);
                    return (
                      <Card key={sub.id} className="border-slate-200">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-blue-100 rounded-lg">
                                <FileText className="w-4 h-4 text-blue-600" />
                              </div>
                              <div>
                                <p className="font-medium text-slate-900">
                                  {template?.name || 'Formulario'}
                                </p>
                                <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {new Date(sub.created_at).toLocaleString()}
                                  </span>
                                  {sub.location && (
                                    <span className="flex items-center gap-1">
                                      <MapPin className="w-3 h-3" />
                                      {sub.location}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <Badge className={
                              sub.status === 'approved' ? 'bg-green-100 text-green-800' :
                              sub.status === 'rejected' ? 'bg-red-100 text-red-800' :
                              sub.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                              'bg-slate-100 text-slate-800'
                            }>
                              {sub.status === 'submitted' ? 'Enviado' :
                               sub.status === 'reviewed' ? 'Revisado' :
                               sub.status === 'approved' ? 'Aprobado' :
                               sub.status === 'rejected' ? 'Rechazado' : sub.status}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="border-slate-200">
                  <CardContent className="p-12 text-center">
                    <CheckSquare className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-500">No hay formularios completados</p>
                    <Button 
                      className="mt-4 bg-blue-500 hover:bg-blue-600"
                      onClick={() => setActiveTab('templates')}
                    >
                      Ver Plantillas
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>

          {/* Form Fill Dialog */}
          <Dialog open={showFormDialog} onOpenChange={setShowFormDialog}>
            <DialogContent className="max-w-2xl max-h-[90vh]">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <ClipboardList className="w-5 h-5 text-blue-500" />
                  {selectedTemplate?.name}
                </DialogTitle>
                <DialogDescription>{selectedTemplate?.description}</DialogDescription>
              </DialogHeader>
              
              <ScrollArea className="max-h-[60vh] pr-4">
                <div className="space-y-5 py-4">
                  {/* Location field */}
                  <div className="space-y-2">
                    <Label className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      Ubicación
                    </Label>
                    <Input
                      placeholder="Ej: Bodega Principal, Sector A"
                      value={formLocation}
                      onChange={(e) => setFormLocation(e.target.value)}
                      className="rounded-lg"
                    />
                  </div>

                  {/* Dynamic fields */}
                  {selectedTemplate?.fields?.map((field) => (
                    <div key={field.id} className="space-y-2">
                      <Label className="flex items-center gap-1">
                        {field.label}
                        {field.required && <span className="text-red-500">*</span>}
                      </Label>
                      {renderField(field)}
                    </div>
                  ))}
                </div>
              </ScrollArea>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowFormDialog(false)}>
                  Cancelar
                </Button>
                <Button 
                  onClick={handleSubmitForm} 
                  disabled={submitting}
                  className="bg-blue-500 hover:bg-blue-600 gap-2"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Enviar Formulario
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
