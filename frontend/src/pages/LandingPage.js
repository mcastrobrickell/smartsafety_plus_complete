import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// ─── Particles ─────────────────────────────────────────────────────────
function Particles({ count = 30 }) {
  const particles = useRef(
    Array.from({ length: count }, (_, i) => ({
      id: i, left: Math.random() * 100, size: 1 + Math.random() * 2,
      duration: 8 + Math.random() * 12, delay: Math.random() * 10,
    }))
  ).current;
  return <>{particles.map((p) => (
    <div key={p.id} className="particle" style={{ left: `${p.left}%`, width: `${p.size}px`, height: `${p.size}px`, animationDuration: `${p.duration}s`, animationDelay: `${p.delay}s` }} />
  ))}</>;
}

// ─── Scroll Reveal ─────────────────────────────────────────────────────
function useScrollReveal() {
  useEffect(() => {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale').forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

// ─── Animated Counter ──────────────────────────────────────────────────
function Counter({ end, suffix = '', duration = 2000 }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let start = 0;
        const step = end / (duration / 16);
        const timer = setInterval(() => {
          start += step;
          if (start >= end) { setVal(end); clearInterval(timer); }
          else setVal(Math.floor(start));
        }, 16);
        obs.disconnect();
      }
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [end, duration]);
  return <span ref={ref}>{val}{suffix}</span>;
}

// ─── Mobile Menu ───────────────────────────────────────────────────────
function MobileMenu({ open, onClose, onNavigate }) {
  if (!open) return null;
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(5,7,10,0.95)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', zIndex: 1001, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2rem' }}>
      <button onClick={onClose} style={{ position: 'absolute', top: 20, right: 24, color: '#94A3B8', background: 'none', border: 'none', fontSize: '1.6rem', cursor: 'pointer' }}><i className="fas fa-times" /></button>
      {['plataforma', 'ia', 'modulos', 'planes', 'contacto'].map((id) => (
        <a key={id} className="nav-link" style={{ fontSize: '1.2rem', cursor: 'pointer' }} onClick={() => { onClose(); setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }), 100); }}>
          {id === 'ia' ? 'Inteligencia Artificial' : id.charAt(0).toUpperCase() + id.slice(1)}
        </a>
      ))}
      <button className="hero-btn-primary" style={{ marginTop: '1rem' }} onClick={() => { onClose(); onNavigate('/login'); }}>Probar Gratis</button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
export default function LandingPage() {
  const navigate = useNavigate();
  const [mobileMenu, setMobileMenu] = useState(false);
  const [form, setForm] = useState({ nombre: '', empresa: '', email: '', telefono: '', mensaje: '' });
  const [formStatus, setFormStatus] = useState(null); // null | 'sending' | 'sent' | 'error'
  useScrollReveal();
  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  const handleFormChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!form.nombre || !form.email || !form.mensaje) return;
    setFormStatus('sending');
    try {
      // Send to backend or external service
      const msg = `Contacto SmartSafety+%0ANombre: ${form.nombre}%0AEmpresa: ${form.empresa}%0AEmail: ${form.email}%0ATel: ${form.telefono}%0AMensaje: ${form.mensaje}`;
      window.open(`https://wa.me/56966814830?text=${msg}`, '_blank');
      setFormStatus('sent');
      setForm({ nombre: '', empresa: '', email: '', telefono: '', mensaje: '' });
      setTimeout(() => setFormStatus(null), 5000);
    } catch {
      setFormStatus('error');
      setTimeout(() => setFormStatus(null), 4000);
    }
  };

  return (
    <div style={{ background: '#05070A', minHeight: '100vh', position: 'relative', overflow: 'hidden' }} data-testid="landing-page">

      {/* ── Background ─────────────────────────────────────────────── */}
      <div className="landing-grid-bg" />
      <Particles count={30} />
      <div className="side-line side-line-left" />
      <div className="side-line side-line-right" />
      <div className="side-dot" style={{ animationDelay: '0s', left: 27 }} />
      <div className="side-dot" style={{ animationDelay: '4s', left: 27 }} />
      <div className="side-dot" style={{ animationDelay: '2s', right: 27, left: 'auto' }} />
      <div className="side-dot" style={{ animationDelay: '6s', right: 27, left: 'auto' }} />

      {/* ── Navigation ─────────────────────────────────────────────── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="logo-brand" style={{ cursor: 'pointer' }} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <span className="logo-brand-smart">Smart</span>
            <span className="logo-brand-safety">Safety</span>
            <span className="logo-brand-plus">+</span>
          </div>
          <div className="nav-links" style={{ display: 'flex', alignItems: 'center', gap: '1.8rem' }}>
            <a className="nav-link" onClick={() => scrollTo('plataforma')}>Plataforma</a>
            <a className="nav-link" onClick={() => scrollTo('ia')}>IA</a>
            <a className="nav-link" onClick={() => scrollTo('modulos')}>Módulos</a>
            <a className="nav-link" onClick={() => scrollTo('planes')}>Planes</a>
            <button className="nav-btn-contact" onClick={() => scrollTo('contacto')}>
              <i className="fas fa-envelope" style={{ marginRight: 6 }} />Contacto
            </button>
            <button className="hero-btn-primary" style={{ padding: '0.55rem 1.4rem', fontSize: '0.85rem' }} onClick={() => navigate('/login')} data-testid="login-nav-btn">
              Iniciar Sesión
            </button>
          </div>
          <button className="nav-hamburger" style={{ display: 'none', background: 'none', border: 'none', color: '#94A3B8', fontSize: '1.4rem', cursor: 'pointer' }} onClick={() => setMobileMenu(true)}>
            <i className="fas fa-bars" />
          </button>
        </div>
      </nav>
      <MobileMenu open={mobileMenu} onClose={() => setMobileMenu(false)} onNavigate={navigate} />
      <style>{`@media(max-width:768px){.nav-links{display:none!important}.nav-hamburger{display:block!important}}`}</style>

      {/* ════════════════════════════════════════════════════════════════
          HERO
      ════════════════════════════════════════════════════════════════ */}
      <section className="hero-section">
        <div className="hero-glow-cyan" />
        <div className="hero-glow-blue" />
        <div className="hero-scan-line" />
        <div style={{ position: 'relative', zIndex: 10, maxWidth: 850 }}>
          <div className="hero-badge reveal" style={{ marginBottom: '1.5rem' }}>
            <i className="fas fa-shield-alt" /> Plataforma de Seguridad con IA · v2.1
          </div>
          <h1 className="hero-h1 reveal" style={{ transitionDelay: '0.1s' }}>
            Tu equipo protegido.<br />
            Tu operación <span className="highlight">bajo control</span>.
          </h1>
          <p className="hero-sub reveal" style={{ transitionDelay: '0.2s' }}>
            SmartSafety+ detecta riesgos con visión artificial, predice incidentes antes de que ocurran,
            y automatiza toda la gestión de seguridad operativa en una sola plataforma.
          </p>
          <div className="reveal" style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', transitionDelay: '0.3s' }}>
            <button className="hero-btn-primary" onClick={() => navigate('/login')} data-testid="cta-btn" style={{ padding: '1rem 2.5rem', fontSize: '1.05rem' }}>
              <i className="fas fa-rocket" style={{ marginRight: 8 }} /> Comenzar Ahora — Es Gratis
            </button>
            <button className="hero-btn-outline" onClick={() => scrollTo('plataforma')}>
              <i className="fas fa-play-circle" style={{ marginRight: 6 }} /> Ver Cómo Funciona
            </button>
          </div>
          <div className="reveal" style={{ display: 'flex', justifyContent: 'center', gap: '2.5rem', marginTop: '2.5rem', flexWrap: 'wrap', transitionDelay: '0.4s' }}>
            {[
              { icon: 'fa-robot', text: 'IA Predictiva' },
              { icon: 'fa-bolt', text: 'Tiempo Real' },
              { icon: 'fa-shield-alt', text: 'ISO 45001' },
              { icon: 'fa-mobile-alt', text: 'PWA Offline' },
            ].map((item) => (
              <div key={item.text} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: '#64748B' }}>
                <i className={`fas ${item.icon}`} style={{ color: '#22C55E', fontSize: '0.8rem' }} />
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Neon Separator ─────────────────────────────────────────── */}
      <div style={{ width: '50%', margin: '0 auto', height: 2, background: 'linear-gradient(90deg, transparent, #00E5FF, transparent)', boxShadow: '0 0 10px #00E5FF', position: 'relative', zIndex: 5 }} />

      {/* ════════════════════════════════════════════════════════════════
          STATS TICKER
      ════════════════════════════════════════════════════════════════ */}
      <section className="landing-section" style={{ padding: '60px 20px' }}>
        <div className="landing-section-inner">
          <div className="diff-grid reveal" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            {[
              { end: 85, suffix: '%', title: 'Reducción de Incidentes', desc: 'En el primer año de uso' },
              { end: 3, suffix: 'seg', title: 'Detección de Riesgos', desc: 'Análisis IA en segundos' },
              { end: 100, suffix: '%', title: 'Trazabilidad', desc: 'Audit trail completo' },
              { end: 24, suffix: '/7', title: 'Monitoreo Continuo', desc: 'Escalamiento automático' },
            ].map((item, i) => (
              <div key={item.title} className={`diff-card stagger-${i + 1}`} style={{ padding: '2rem 1rem' }}>
                <div className="diff-number"><Counter end={item.end} suffix={item.suffix} /></div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          HOW IT WORKS (3 steps)
      ════════════════════════════════════════════════════════════════ */}
      <section id="plataforma" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}><i className="fas fa-magic" /> Así de Simple</div>
            <h2 className="section-title">Tres pasos para una operación <span style={{ color: '#00E5FF' }}>más segura</span></h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem' }}>
            {[
              { num: '01', icon: 'fa-camera', color: '#00E5FF', bg: 'rgba(0,229,255,0.12)', title: 'Captura', desc: 'Toma una foto del área de trabajo desde tu celular. La app funciona incluso sin conexión.' },
              { num: '02', icon: 'fa-brain', color: '#A855F7', bg: 'rgba(168,85,247,0.12)', title: 'IA Analiza', desc: 'Nuestra IA inspecciona la imagen en segundos: detecta riesgos, clasifica severidad y referencia normativa.' },
              { num: '03', icon: 'fa-chart-line', color: '#22C55E', bg: 'rgba(34,197,94,0.12)', title: 'Actúa', desc: 'Recibe el plan de acción priorizado, asigna responsables y recibe alertas hasta que se resuelva.' },
            ].map((item, i) => (
              <div key={item.num} className={`feature-card reveal stagger-${i + 1}`} style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                <div style={{ fontSize: '3rem', fontWeight: 800, fontFamily: 'Outfit', background: `linear-gradient(135deg, ${item.color}, #2563EB)`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '1rem' }}>{item.num}</div>
                <div className="feature-icon-box" style={{ background: item.bg, color: item.color, margin: '0 auto 1rem' }}>
                  <i className={`fas ${item.icon}`} />
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          AI ENGINE
      ════════════════════════════════════════════════════════════════ */}
      <section id="ia" className="landing-section" style={{ background: 'linear-gradient(180deg, rgba(168,85,247,0.04) 0%, transparent 100%)' }}>
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div className="section-label" style={{ justifyContent: 'center', color: '#A855F7' }}><i className="fas fa-brain" /> Motor de Inteligencia Artificial</div>
            <h2 className="section-title">No solo detecta. <span style={{ color: '#A855F7' }}>Predice y actúa</span>.</h2>
            <p className="section-sub" style={{ margin: '0 auto' }}>4 capacidades de IA que transforman datos en decisiones de seguridad.</p>
          </div>
          <div className="feature-cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {[
              { icon: 'fa-camera-retro', color: '#00E5FF', bg: 'rgba(0,229,255,0.12)', title: 'Scan 360° con Visión IA', desc: 'Sube una foto y la IA detecta EPP faltante, vías obstruidas, riesgos eléctricos, y más. Genera hallazgos con referencia normativa OSHA y acción correctiva.' },
              { icon: 'fa-chart-area', color: '#A855F7', bg: 'rgba(168,85,247,0.12)', title: 'Predicción de Riesgos', desc: 'Analiza patrones históricos de hallazgos e incidentes para predecir zonas críticas y tipos de riesgo más probables. Prevención antes del accidente.' },
              { icon: 'fa-tasks', color: '#FACC15', bg: 'rgba(250,204,21,0.1)', title: 'Planes de Acción Automáticos', desc: 'La IA genera planes correctivos priorizados por severidad y costo. Incluye plazos, responsables sugeridos, indicadores de verificación y referencia ISO.' },
              { icon: 'fa-comments', color: '#22C55E', bg: 'rgba(34,197,94,0.12)', title: 'Asistente IA de Datos', desc: 'Pregunta en lenguaje natural: "¿Cuántos incidentes críticos hay abiertos?" "¿Qué zona tiene más hallazgos?" Responde consultando tus datos en tiempo real.' },
            ].map((item, i) => (
              <div key={item.title} className={`feature-card reveal stagger-${(i % 4) + 1}`}>
                <div className="feature-icon-box" style={{ background: item.bg, color: item.color }}><i className={`fas ${item.icon}`} /></div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          MODULES
      ════════════════════════════════════════════════════════════════ */}
      <section id="modulos" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}><i className="fas fa-th-large" /> Módulos</div>
            <h2 className="section-title">Todo en <span style={{ color: '#FACC15' }}>una sola plataforma</span></h2>
            <p className="section-sub" style={{ margin: '0 auto' }}>8 módulos integrados que cubren el ciclo completo de seguridad operativa.</p>
          </div>
          <div className="value-cards-grid">
            {[
              { icon: 'fa-camera-retro', title: 'Scan 360° con IA', desc: 'Análisis de imágenes con visión artificial. Detecta riesgos y genera hallazgos automáticamente.' },
              { icon: 'fa-hard-hat', title: 'Gestión de EPP', desc: 'Inventario, entregas, certificaciones, vencimientos, importación Excel y reportes de costos.' },
              { icon: 'fa-exclamation-triangle', title: 'Incidentes', desc: 'Reporte, seguimiento y cierre. Investigación ISO 45001 con árbol de causas y acciones correctivas.' },
              { icon: 'fa-search', title: 'Hallazgos', desc: 'Gestión centralizada con filtros por severidad, estado y categoría. Escalamiento automático.' },
              { icon: 'fa-th-large', title: 'Matriz de Riesgo', desc: 'Evaluación probabilidad × consecuencia. Controles existentes y adicionales con responsables.' },
              { icon: 'fa-clipboard-list', title: 'Procedimientos', desc: 'Biblioteca de documentos con análisis IA automático de riesgos, controles y EPP requerido.' },
              { icon: 'fa-chart-bar', title: 'Dashboard en Tiempo Real', desc: 'KPIs, tendencias, heatmap por ubicación, gráficos interactivos y alertas WebSocket.' },
              { icon: 'fa-file-pdf', title: 'Reportes Ejecutivos', desc: 'PDFs profesionales con portada, resumen ejecutivo, métricas y detalle por módulo.' },
              { icon: 'fa-bell', title: 'Notificaciones', desc: 'Centro in-app con badge, email (Resend), SMS (Twilio) y push notifications.' },
              { icon: 'fa-search-plus', title: 'Búsqueda Global', desc: 'Ctrl+K para buscar en incidentes, hallazgos, scans, procedimientos, EPP e investigaciones.' },
              { icon: 'fa-arrows-alt', title: 'Comparación Temporal', desc: 'Compara scans del mismo lugar en distintas fechas. Ve qué mejoró, qué empeoró, qué es nuevo.' },
              { icon: 'fa-user-shield', title: 'Audit Trail', desc: 'Log de cada acción: quién hizo qué, cuándo, desde dónde. Listo para fiscalización.' },
            ].map((item, i) => (
              <div key={item.title} className={`value-card reveal stagger-${(i % 4) + 1}`}>
                <div className="value-icon"><i className={`fas ${item.icon}`} /></div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          REAL-TIME + SECURITY
      ════════════════════════════════════════════════════════════════ */}
      <section className="landing-section" style={{ background: 'linear-gradient(180deg, rgba(0,229,255,0.03) 0%, transparent 100%)' }}>
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}><i className="fas fa-bolt" /> Tiempo Real + Seguridad</div>
            <h2 className="section-title">Información <span style={{ color: '#00E5FF' }}>cuando importa</span></h2>
          </div>
          <div className="feature-cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
            {[
              { icon: 'fa-broadcast-tower', color: '#00E5FF', bg: 'rgba(0,229,255,0.12)', title: 'WebSocket en Vivo', desc: 'Cuando se detecta un hallazgo crítico o se reporta un incidente, todos los dashboards conectados se actualizan instantáneamente.' },
              { icon: 'fa-level-up-alt', color: '#EF4444', bg: 'rgba(239,68,68,0.12)', title: 'Escalamiento Automático', desc: 'Hallazgo crítico >24h sin resolver → alerta al supervisor. >48h → escalamiento al administrador. Sin intervención manual.' },
              { icon: 'fa-lock', color: '#22C55E', bg: 'rgba(34,197,94,0.12)', title: 'Seguridad Enterprise', desc: 'CORS restrictivo, rate limiting por IP, JWT con expiración, roles granulares, y audit trail de cada acción.' },
              { icon: 'fa-wifi', color: '#FACC15', bg: 'rgba(250,204,21,0.1)', title: 'PWA con Modo Offline', desc: 'Instálala en tu celular como app nativa. Funciona sin conexión en terreno — sincroniza cuando recupera red.' },
            ].map((item, i) => (
              <div key={item.title} className={`feature-card reveal stagger-${(i % 3) + 1}`}>
                <div className="feature-icon-box" style={{ background: item.bg, color: item.color }}><i className={`fas ${item.icon}`} /></div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          COMPLIANCE BADGES
      ════════════════════════════════════════════════════════════════ */}
      <section className="landing-section" style={{ padding: '60px 20px' }}>
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}><i className="fas fa-certificate" /> Cumplimiento Normativo</div>
            <h2 className="section-title">Alineado con los <span style={{ color: '#22C55E' }}>estándares que importan</span></h2>
          </div>
          <div className="reveal" style={{ display: 'flex', justifyContent: 'center', gap: '2rem', flexWrap: 'wrap' }}>
            {[
              { name: 'ISO 45001:2018', desc: 'Sistema de Gestión SST' },
              { name: 'OSHA', desc: 'Estándares de Seguridad' },
              { name: 'NCh ISO 45001', desc: 'Norma Chilena' },
              { name: 'DS 594', desc: 'Condiciones Ambientales' },
              { name: 'Ley 16.744', desc: 'Accidentes del Trabajo' },
            ].map((item) => (
              <div key={item.name} style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12, padding: '1.2rem 1.8rem', textAlign: 'center', minWidth: 160 }}>
                <div style={{ color: '#22C55E', fontFamily: 'Outfit', fontWeight: 700, fontSize: '0.95rem', marginBottom: 4 }}>{item.name}</div>
                <div style={{ color: '#64748B', fontSize: '0.78rem' }}>{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          PRICING
      ════════════════════════════════════════════════════════════════ */}
      <section id="planes" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}><i className="fas fa-tag" /> Planes</div>
            <h2 className="section-title">Elige el plan para tu <span style={{ color: '#FACC15' }}>operación</span></h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', maxWidth: 1000, margin: '0 auto' }}>
            {[
              { name: 'Starter', price: 'Gratis', period: 'para siempre', color: '#94A3B8', features: ['Hasta 3 usuarios', 'Scan 360° (10/mes)', 'Gestión de incidentes', 'Dashboard básico', 'Reportes PDF'], cta: 'Comenzar Gratis', highlight: false },
              { name: 'Profesional', price: '$49.990', period: '/mes por empresa', color: '#00E5FF', features: ['Hasta 25 usuarios', 'Scan 360° ilimitado', 'IA Predictiva + Chat IA', 'Planes de acción automáticos', 'WebSocket tiempo real', 'Notificaciones email + SMS', 'Escalamiento automático', 'Búsqueda global'], cta: 'Elegir Plan', highlight: true },
              { name: 'Enterprise', price: 'Cotizar', period: 'según operación', color: '#A855F7', features: ['Usuarios ilimitados', 'Todo lo del Profesional', 'Multi-empresa', 'API dedicada', 'Soporte prioritario 24/7', 'Deploy on-premise', 'Integraciones custom', 'SLA garantizado'], cta: 'Contactar Ventas', highlight: false },
            ].map((plan) => (
              <div key={plan.name} className={`feature-card reveal`} style={{
                padding: '2.5rem 2rem',
                border: plan.highlight ? `2px solid ${plan.color}` : '1px solid rgba(255,255,255,0.06)',
                position: 'relative',
                ...(plan.highlight ? { boxShadow: `0 0 40px rgba(0,229,255,0.1)` } : {})
              }}>
                {plan.highlight && (
                  <div style={{ position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)', background: '#00E5FF', color: '#05070A', fontSize: '0.7rem', fontWeight: 700, padding: '0.3rem 1rem', borderRadius: 50, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Más Popular
                  </div>
                )}
                <div style={{ color: plan.color, fontFamily: 'Outfit', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: 1, marginBottom: '0.5rem' }}>{plan.name}</div>
                <div style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '2.2rem', color: '#F8FAFC', marginBottom: 0 }}>{plan.price}</div>
                <div style={{ color: '#64748B', fontSize: '0.85rem', marginBottom: '1.5rem' }}>{plan.period}</div>
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1.5rem' }}>
                  {plan.features.map((f) => (
                    <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.7rem', fontSize: '0.88rem', color: '#94A3B8' }}>
                      <i className="fas fa-check-circle" style={{ color: plan.color, fontSize: '0.75rem' }} />
                      {f}
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => plan.name === 'Enterprise' ? scrollTo('contacto') : navigate('/login')}
                  style={{
                    width: '100%', marginTop: '1.5rem', padding: '0.85rem',
                    background: plan.highlight ? '#00E5FF' : 'transparent',
                    color: plan.highlight ? '#05070A' : plan.color,
                    border: plan.highlight ? 'none' : `1px solid ${plan.color}40`,
                    borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer',
                    transition: 'all 0.3s',
                  }}
                >{plan.cta}</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          CTA BANNER
      ════════════════════════════════════════════════════════════════ */}
      <section className="landing-section" style={{ padding: '80px 20px' }}>
        <div className="reveal" style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', background: 'linear-gradient(135deg, rgba(0,229,255,0.08), rgba(168,85,247,0.08))', border: '1px solid rgba(0,229,255,0.15)', borderRadius: 20, padding: '3.5rem 2rem' }}>
          <h2 style={{ fontFamily: 'Outfit', fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 700, color: '#F8FAFC', marginBottom: '1rem' }}>
            ¿Listo para proteger a tu equipo<br />con inteligencia artificial?
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '1.05rem', maxWidth: 500, margin: '0 auto 2rem', lineHeight: 1.7 }}>
            Crea tu cuenta gratuita en 30 segundos. Sin tarjeta de crédito. Sin compromiso.
          </p>
          <button className="hero-btn-primary" onClick={() => navigate('/login')} style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}>
            <i className="fas fa-rocket" style={{ marginRight: 8 }} /> Empezar Ahora
          </button>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          CONTACT FORM
      ════════════════════════════════════════════════════════════════ */}
      <section id="contacto" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}><i className="fas fa-paper-plane" /> Contacto</div>
            <h2 className="section-title">Agenda una <span style={{ color: '#00E5FF' }}>demo personalizada</span></h2>
            <p className="section-sub" style={{ margin: '0 auto' }}>Escríbenos y te respondemos en menos de 24 horas.</p>
          </div>

          <div className="contact-container reveal">
            <div className="contact-info">
              <h3>Conversemos</h3>
              <p>Nuestro equipo está disponible para ayudarte a implementar SmartSafety+ en tu operación.</p>
              <div className="contact-item">
                <i className="fas fa-envelope" />
                <span>contacto@tecops.cl</span>
              </div>
              <div className="contact-item">
                <i className="fas fa-phone-alt" />
                <span>+56 9 6681 4830</span>
              </div>
              <div className="contact-item">
                <i className="fas fa-map-marker-alt" />
                <span>La Concepción 81, of. 214, Providencia</span>
              </div>
              <div className="contact-item">
                <i className="fab fa-whatsapp" />
                <a href="https://wa.me/56966814830" target="_blank" rel="noopener noreferrer" style={{ color: '#25D366', textDecoration: 'none', fontWeight: 600 }}>
                  Escríbenos por WhatsApp
                </a>
              </div>
            </div>

            <form onSubmit={handleFormSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-row">
                <div>
                  <label className="form-field-label">Nombre *</label>
                  <input className="form-field-input" name="nombre" value={form.nombre} onChange={handleFormChange} placeholder="Tu nombre" required />
                </div>
                <div>
                  <label className="form-field-label">Empresa</label>
                  <input className="form-field-input" name="empresa" value={form.empresa} onChange={handleFormChange} placeholder="Tu empresa" />
                </div>
              </div>
              <div className="form-row">
                <div>
                  <label className="form-field-label">Email *</label>
                  <input className="form-field-input" name="email" type="email" value={form.email} onChange={handleFormChange} placeholder="correo@empresa.cl" required />
                </div>
                <div>
                  <label className="form-field-label">Teléfono</label>
                  <input className="form-field-input" name="telefono" value={form.telefono} onChange={handleFormChange} placeholder="+56 9 1234 5678" />
                </div>
              </div>
              <div>
                <label className="form-field-label">Mensaje *</label>
                <textarea className="form-field-input" name="mensaje" rows="4" value={form.mensaje} onChange={handleFormChange} placeholder="¿En qué podemos ayudarte? Cuéntanos sobre tu operación..." style={{ resize: 'vertical' }} required />
              </div>
              <button type="submit" className="form-submit-btn" disabled={formStatus === 'sending'} style={{ opacity: formStatus === 'sending' ? 0.7 : 1 }}>
                {formStatus === 'sending' ? (
                  <><i className="fas fa-spinner fa-spin" style={{ marginRight: 8 }} /> Enviando...</>
                ) : formStatus === 'sent' ? (
                  <><i className="fas fa-check-circle" style={{ marginRight: 8 }} /> ¡Mensaje Enviado!</>
                ) : (
                  <><i className="fab fa-whatsapp" style={{ marginRight: 8 }} /> Enviar por WhatsApp</>
                )}
              </button>
              {formStatus === 'sent' && (
                <p style={{ color: '#22C55E', fontSize: '0.85rem', textAlign: 'center', margin: 0 }}>
                  Gracias por contactarnos. Te responderemos pronto.
                </p>
              )}
              {formStatus === 'error' && (
                <p style={{ color: '#EF4444', fontSize: '0.85rem', textAlign: 'center', margin: 0 }}>
                  Error al enviar. Intenta directamente por WhatsApp.
                </p>
              )}
            </form>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════
          FOOTER
      ════════════════════════════════════════════════════════════════ */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="footer-top">
            <div className="footer-brand">
              <div className="logo-brand">
                <span className="logo-brand-smart">Smart</span>
                <span className="logo-brand-safety">Safety</span>
                <span className="logo-brand-plus">+</span>
              </div>
              <p>Gestión integral de seguridad operativa y prevención de riesgos con inteligencia artificial.</p>
              <div className="footer-social">
                <a href="https://www.linkedin.com/company/tecops" target="_blank" rel="noopener noreferrer"><i className="fab fa-linkedin-in" /></a>
                <a href="https://wa.me/56966814830" target="_blank" rel="noopener noreferrer"><i className="fab fa-whatsapp" /></a>
                <a href="mailto:contacto@tecops.cl"><i className="fas fa-envelope" /></a>
              </div>
            </div>

            <div className="footer-col">
              <h4>Plataforma</h4>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('plataforma'); }}>Cómo Funciona</a>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('ia'); }}>Motor de IA</a>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('modulos'); }}>Módulos</a>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('planes'); }}>Planes y Precios</a>
            </div>

            <div className="footer-col">
              <h4>Módulos</h4>
              <a href="#">Scan 360° con IA</a>
              <a href="#">Gestión de EPP</a>
              <a href="#">Incidentes & Investigación</a>
              <a href="#">Dashboard & Reportes</a>
            </div>

            <div className="footer-col">
              <h4>Contacto</h4>
              <a href="mailto:contacto@tecops.cl"><i className="fas fa-envelope" style={{ marginRight: 6, fontSize: '0.75rem' }} />contacto@tecops.cl</a>
              <a href="tel:+56966814830"><i className="fas fa-phone-alt" style={{ marginRight: 6, fontSize: '0.75rem' }} />+56 9 6681 4830</a>
              <a href="https://maps.google.com/?q=La+Concepcion+81+Providencia" target="_blank" rel="noopener noreferrer"><i className="fas fa-map-marker-alt" style={{ marginRight: 6, fontSize: '0.75rem' }} />La Concepción 81, of. 214</a>
              <a href="https://wa.me/56966814830" target="_blank" rel="noopener noreferrer"><i className="fab fa-whatsapp" style={{ marginRight: 6, fontSize: '0.75rem' }} />WhatsApp Directo</a>
            </div>
          </div>

          <div className="footer-bottom">
            © 2026 SmartSafety+ by TecOps SpA. Todos los derechos reservados.
          </div>
        </div>
      </footer>

      {/* ── WhatsApp Float ─────────────────────────────────────────── */}
      <a href="https://wa.me/56966814830" target="_blank" rel="noopener noreferrer" className="whatsapp-float" aria-label="Contactar por WhatsApp">
        <i className="fab fa-whatsapp" />
      </a>
    </div>
  );
}
