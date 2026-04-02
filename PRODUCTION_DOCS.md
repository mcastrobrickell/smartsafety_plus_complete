# SmartSafety+ - Documentación de Producción

## 🌐 URLs de Producción

| Servicio | URL |
|----------|-----|
| **Frontend** | https://smartsafety.tecops.cl |
| **Backend API** | https://api.smartsafety.tecops.cl |
| **GitHub Repo** | https://github.com/mcastrobrickell/smartsafety_plus_complete |

---

## 🔐 Credenciales de Acceso

| Email | Password | Rol |
|-------|----------|-----|
| admin@smartsafety.com | Admin123! | admin |
| superadmin@smartsafety.com | SuperAdmin123! | superadmin |

---

## ⚙️ Configuración Railway

### Backend (smartsafety_plus_complete)

**Root Directory**: `backend`

**Variables de Entorno**:
```
MONGO_URL=mongodb+srv://mcastrobrickell:Mc40723999%40@cluster0.0n7cxru.mongodb.net/smartsafety_plus_complete?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE
DB_NAME=smartsafety_plus_complete
PORT=8001
JWT_SECRET=[tu_secreto]
CORS_ORIGINS=https://smartsafety.tecops.cl,https://api.smartsafety.tecops.cl
EMERGENT_LLM_KEY=sk-emergent-cF804Ef1d7c03871c3
RESEND_API_KEY=re_hmJfDT4v_Afahu2XZs7HiWqnvMHZM3Gy6
SENDER_EMAIL=Smart Plan <onboarding@tecops.cl>
CONTACT_EMAILS=mcastrobrickell@gmail.com
```

### Frontend (smartsafety_plus_complete - Frontend)

**Root Directory**: `frontend`

**Build Command**: `npm install --legacy-peer-deps && npm run build`

**Start Command**: `npx serve -s build -l $PORT`

**Variables de Entorno**:
```
REACT_APP_BACKEND_URL=https://api.smartsafety.tecops.cl
```

---

## 🌍 Configuración DNS (DonWeb/Ferozo)

| Tipo | Nombre | Destino |
|------|--------|---------|
| CNAME | smartsafety | smartsafetypluscomplete-production.up.railway.app |
| CNAME | api.smartsafety | smartsafetypluscomplete-production.up.railway.app |

---

## 🗄️ Base de Datos MongoDB Atlas

- **Cluster**: cluster0.0n7cxru.mongodb.net
- **Database**: smartsafety_plus_complete
- **Usuario**: mcastrobrickell
- **Network Access**: 0.0.0.0/0 (Allow from Anywhere)

---

## 📁 Estructura del Proyecto

```
smartsafety_plus_complete/
├── backend/
│   ├── server.py           # API FastAPI
│   ├── requirements.txt    # Dependencias Python
│   ├── Procfile           # Comando de inicio Railway
│   ├── config.py          # Configuración
│   ├── models/            # Modelos Pydantic
│   ├── routers/           # Endpoints API
│   └── utils/             # Utilidades
├── frontend/
│   ├── src/               # Código React
│   ├── public/            # Archivos estáticos
│   ├── package.json       # Dependencias Node
│   └── craco.config.js    # Configuración build
└── README.md
```

---

## ✨ Funcionalidades Implementadas

- ✅ **Scan 360° con IA** - Análisis de imágenes con GPT-4o
- ✅ **Gestión de EPP** - Control completo de equipos de protección
- ✅ **Investigación de Incidentes** - Formato ISO 45001
- ✅ **Árbol de Causas Interactivo** - Visualización de análisis causal
- ✅ **Matriz de Riesgos** - Evaluación y control
- ✅ **Generación de PDF** - Reportes automáticos
- ✅ **Notificaciones Email** - Integración con Resend
- ✅ **Dashboard** - Estadísticas en tiempo real
- ✅ **Configuración de Organización** - Logo y nombre personalizables

---

## 🛠️ Tecnologías

| Componente | Tecnología |
|------------|------------|
| Backend | FastAPI, Python 3.11+ |
| Frontend | React 18, TailwindCSS, Shadcn/UI |
| Base de Datos | MongoDB Atlas |
| IA | OpenAI GPT-4o |
| Email | Resend |
| Hosting | Railway |
| DNS | DonWeb/Ferozo |

---

## 📞 Soporte

**Email**: mcastrobrickell@gmail.com

---

## 📅 Última Actualización

**Fecha**: 18 de Marzo de 2026

**Cambios realizados**:
- Despliegue completo en Railway
- Configuración de dominios personalizados
- Corrección de dependencias frontend
- Configuración MongoDB Atlas con SSL
- Creación de usuarios iniciales
