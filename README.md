# SmartSafety+ 

Gestión integral de seguridad operativa, prevención de riesgos y cumplimiento normativo industrial.

## Estructura del Proyecto

```
smartsafety_plus/
├── backend/
│   ├── config.py          # Configuración y conexión a DB
│   ├── server_modular.py  # Servidor principal (arquitectura modular)
│   ├── server.py          # Servidor original (monolítico)
│   ├── models/
│   │   └── schemas.py     # Modelos Pydantic
│   ├── routers/
│   │   ├── auth.py        # Autenticación
│   │   ├── epp.py         # Gestión de EPP
│   │   ├── incidents.py   # Incidentes e investigaciones
│   │   ├── scans.py       # Scan 360°
│   │   └── config.py      # Configuración y organización
│   └── utils/
│       ├── auth.py        # Utilidades de autenticación
│       └── pdf.py         # Generación de PDF
├── frontend/
│   ├── src/
│   │   ├── pages/         # Páginas de la aplicación
│   │   ├── components/    # Componentes reutilizables
│   │   └── context/       # Contextos de React
│   └── public/
└── memory/
    └── PRD.md             # Documento de requisitos
```

## Instalación

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configurar variables
uvicorn server_modular:app --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd frontend
yarn install
cp .env.example .env  # Configurar REACT_APP_BACKEND_URL
yarn start
```

## Características

- ✅ Scan 360° con IA (GPT-4o)
- ✅ Gestión de EPP completa
- ✅ Investigación de incidentes (ISO 45001)
- ✅ Matriz de riesgos
- ✅ Generación de PDF
- ✅ Notificaciones (Email/SMS)
- ✅ Dashboard con estadísticas

## Credenciales por Defecto

- Admin: admin@smartsafety.com / Admin123!
- SuperAdmin: superadmin@smartsafety.com / superadmin_password

## Tecnologías

- Backend: FastAPI, MongoDB, Python
- Frontend: React, TailwindCSS, Shadcn/UI
- Integraciones: OpenAI, Resend, Twilio
