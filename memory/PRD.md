# SmartSafety+ - PRD (Product Requirements Document)

## Original Problem Statement
Crear SmartSafety+ - Gestión integral de seguridad operativa, prevención de riesgos y cumplimiento normativo industrial, alineado con **ISO 45001:2018** e integrado con el ecosistema Smart+.

## Latest Updates (December 26, 2025)

### 🔴 P0 CRÍTICO - Autenticación Arreglada ✅
- **Bug**: Incompatibilidad `passlib` vs `bcrypt` en Docker/Producción
- **Fix**: Se cambió a `bcrypt` nativo puro
- **Cambio**: `user["password"]` → `user["hashed_password"]` en endpoint login
- **passlib removido de requirements.txt**
- **Estado**: VERIFICADO y TESTEADO (100% tests pasados)

### 🎨 Template Dark-Tech Aplicado ✅
- **Background**: #05070A (dark-bg)
- **Surface**: #0A0F1A (dark-surface)
- **Inputs**: #111827 (dark-input)
- **Acento Principal**: #00E5FF (cyan-accent)
- **Secundario**: #2563EB (blue-secondary)
- **Éxito**: #22C55E (success-green)
- **Fuentes**: Outfit (headings) + IBM Plex Sans (body)
- **Efectos**: Grid de fondo, glow radial, glassmorphism en cards

**Archivos actualizados:**
- `/app/frontend/src/index.css` - CSS completo Dark-Tech
- `/app/frontend/tailwind.config.js` - Colores y configuración
- `/app/frontend/src/pages/LandingPage.js` - Landing con tema oscuro
- `/app/frontend/src/pages/LoginPage.js` - Login con tema oscuro

## Core Features Implemented ✅
1. Scan 360° con IA (GPT-4o via Emergent LLM Key)
2. Gestión de EPP completa (recepciones, entregas, stock, ajustes)
3. Investigación de incidentes (ISO 45001:2018)
4. Árbol de causas interactivo
5. Matriz de riesgos
6. Generación de PDF
7. Notificaciones Email (Resend)
8. Configuración de organización (logo + nombre)
9. Importación Excel (items, recepciones, entregas)

## Credentials de Prueba
- **SuperAdmin**: superadmin@smartsafety.com / SuperAdmin123!
- **Admin**: admin@smartsafety.com / Admin123!

## Tech Stack
- **Backend**: FastAPI, Motor (MongoDB Async), bcrypt nativo, OpenAI directo
- **Frontend**: React, Tailwind CSS, Shadcn UI, CRACO
- **Deploy**: Railway + MongoDB Atlas
- **Dominio**: tecops.cl (producción)

## Pending Tasks

### P1 - Priority High
- [ ] Completar integración Twilio para alertas SMS (actualmente stub/mock)
- [ ] Aplicar tema Dark-Tech a dashboards internos (Superadmin, Admin, etc.)

### P2 - Priority Medium  
- [ ] Dashboard unificado ecosistema Smart+
- [ ] Consolidar modularización backend (server.py vs server_modular.py)

### P3 - Future
- [ ] Integración de notificaciones push
- [ ] Reportes avanzados con filtros personalizados
- [ ] PWA/Mobile app

## Test Reports
- `/app/test_reports/iteration_6.json` - Último reporte (100% pass rate)

## Deployment
- **Preview**: https://risk-scan-ai-1.preview.emergentagent.com
- **Production**: Railway con MongoDB Atlas
- **Repo**: GitHub (usuario debe hacer push manual)
