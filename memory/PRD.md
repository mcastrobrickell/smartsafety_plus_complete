# SmartSafety+ - PRD (Product Requirements Document)

## Original Problem Statement
Crear SmartSafety+ - Gestión integral de seguridad operativa, prevención de riesgos y cumplimiento normativo industrial, alineado con **ISO 45001:2018** e integrado con el ecosistema Smart+.

## Core Features Implemented ✅
1. **Scan 360° con IA**: Analizar imágenes con GPT-4o
2. **Gestión de EPP**: Flujo logístico completo con catálogo, stock, recepciones y entregas
3. **Reportes de Incidentes**: Módulo completo con investigación ISO 45001
4. **Dashboard Visión 360**: Panel con estadísticas responsive
5. **Matriz de Riesgos**: Evaluación y control
6. **Análisis de Procedimientos**: IA para detección de riesgos
7. **Categorías Configurables**: Gestión por administrador
8. **Exportación PDF Real**: Reportes profesionales
9. **Notificaciones Email/SMS**: Resend y Twilio
10. **Integración Ecosistema Smart+**: SmartPlan+ y SmartForms+
11. **Investigación de Incidentes ISO 45001**: Formato RG-35
12. **Configuración de Organización**: Logo y nombre personalizables

## Latest Updates (December 17, 2025)

### Bug Fixes - EPP Module ✅

#### 1. Recepciones mostraban "N/A" en artículos
- **Causa**: Los movimientos de recepción no guardaban el nombre del artículo, y al eliminar artículos se perdía la referencia
- **Solución**: 
  - Modelo `EPPMovement` ahora incluye `epp_item_name` y `epp_item_code`
  - El endpoint `/api/epp/movements` enriquece movimientos antiguos con nombres de items existentes
  - Frontend muestra "Artículo eliminado" cuando el item ya no existe
  - Nuevas recepciones guardan nombre y código del artículo

#### 2. PDF de entregas mostraba "Not authenticated"
- **Causa**: `window.open()` no envía el token JWT
- **Solución**: Cambiado a `fetch()` con header Authorization + descarga vía Blob
- **Resultado**: PDF se descarga correctamente como `entrega-{id}.pdf`

### Previous Updates
- Dashboard - Gráfico corregido (números enteros, leyenda "Cantidad")
- Configuración de Organización (logo + nombre)
- Árbol de Causas Interactivo
- Módulo de EPP Refactorizado

## Credentials
- **Admin**: admin@smartsafety.com / Admin123!
- **SuperAdmin**: superadmin@smartsafety.com / superadmin_password

## Configured Services
- **Email (Resend)**: ✅ Funcionando
- **SMS (Twilio)**: ⏳ Requiere credenciales
- **IA (GPT-4o)**: ✅ Funcionando

## Architecture Summary

### Backend (FastAPI + MongoDB)
Key endpoints:
- `/api/epp/movements` - Ahora enriquece con nombres de items
- `/api/epp/delivery/{id}/pdf` - Genera PDF autenticado
- `/api/organization/current` - Configuración de organización

### Frontend (React + Tailwind + Shadcn/UI)
- 13 páginas principales
- PDF via fetch + Blob download (no window.open)

## Pending Tasks

### P1 - Priority High
- [ ] Completar integración Twilio para alertas SMS

### P2 - Priority Medium
- [ ] Dashboard unificado ecosistema Smart+
- [ ] Refactorizar `server.py` con APIRouter

### P3 - Future
- [ ] Integración de notificaciones push
- [ ] Reportes avanzados con filtros personalizados

## Data Model Updates
```python
class EPPMovement:
    epp_item_id: str
    epp_item_name: Optional[str]  # NEW - Historical reference
    epp_item_code: Optional[str]  # NEW - Historical reference
    movement_type: str
    quantity: int
    # ...rest
```

## Test Results (December 17, 2025)
- ✅ Recepciones muestran nombres de artículos correctamente
- ✅ PDF de entregas descarga sin error de autenticación
- ✅ Artículos eliminados muestran "Artículo eliminado"
