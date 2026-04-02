import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// ─── Particle Generator ────────────────────────────────────────────────
function Particles({ count = 30 }) {
  const particles = useRef(
    Array.from({ length: count }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      size: 1 + Math.random() * 2,
      duration: 8 + Math.random() * 12,
      delay: Math.random() * 10,
    }))
  ).current;

  return (
    <>
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: `${p.left}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </>
  );
}

// ─── Scroll Reveal Hook ────────────────────────────────────────────────
function useScrollReveal() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -30px 0px' }
    );

    const els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
    els.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);
}

// ─── Mobile Menu ───────────────────────────────────────────────────────
function MobileMenu({ open, onClose, onNavigate }) {
  if (!open) return null;
  return (
    <div
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(5,7,10,0.95)', backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        zIndex: 1001, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: '2rem',
      }}
    >
      <button onClick={onClose} style={{ position: 'absolute', top: 20, right: 24, color: '#94A3B8', background: 'none', border: 'none', fontSize: '1.6rem', cursor: 'pointer' }}>
        <i className="fas fa-times" />
      </button>
      {['funcionalidades', 'soluciones', 'diferenciadores', 'contacto'].map((id) => (
        <a key={id} className="nav-link" style={{ fontSize: '1.2rem', cursor: 'pointer' }}
          onClick={() => {
            onClose();
            setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }), 100);
          }}>
          {id.charAt(0).toUpperCase() + id.slice(1)}
        </a>
      ))}
      <button className="hero-btn-primary" style={{ marginTop: '1rem' }} onClick={() => { onClose(); onNavigate('/login'); }}>
        Iniciar Sesión
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// LANDING PAGE
// ═══════════════════════════════════════════════════════════════════════
export default function LandingPage() {
  const navigate = useNavigate();
  const [mobileMenu, setMobileMenu] = useState(false);
  useScrollReveal();

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div style={{ background: '#05070A', minHeight: '100vh', position: 'relative', overflow: 'hidden' }} data-testid="landing-page">

      {/* ── Background Effects ─────────────────────────────────────── */}
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

          <div className="nav-links" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
            <a className="nav-link" onClick={() => scrollTo('funcionalidades')}>Funcionalidades</a>
            <a className="nav-link" onClick={() => scrollTo('soluciones')}>Soluciones</a>
            <a className="nav-link" onClick={() => scrollTo('diferenciadores')}>Diferenciadores</a>
            <button className="nav-btn-contact" onClick={() => scrollTo('contacto')}>
              <i className="fas fa-envelope" style={{ marginRight: 6 }} />Contacto
            </button>
            <button className="hero-btn-primary" style={{ padding: '0.55rem 1.4rem', fontSize: '0.85rem' }}
              onClick={() => navigate('/login')} data-testid="login-nav-btn">
              Iniciar Sesión
            </button>
          </div>

          {/* Hamburger (mobile) */}
          <button
            className="nav-hamburger"
            style={{ display: 'none', background: 'none', border: 'none', color: '#94A3B8', fontSize: '1.4rem', cursor: 'pointer' }}
            onClick={() => setMobileMenu(true)}
          >
            <i className="fas fa-bars" />
          </button>
        </div>
      </nav>
      <MobileMenu open={mobileMenu} onClose={() => setMobileMenu(false)} onNavigate={navigate} />

      <style>{`
        @media (max-width: 768px) {
          .nav-links { display: none !important; }
          .nav-hamburger { display: block !important; }
        }
      `}</style>

      {/* ── Hero Section ───────────────────────────────────────────── */}
      <section className="hero-section">
        <div className="hero-glow-cyan" />
        <div className="hero-glow-blue" />
        <div className="hero-scan-line" />

        <div style={{ position: 'relative', zIndex: 10, maxWidth: 800 }}>
          <div className="hero-badge reveal" style={{ marginBottom: '1.5rem' }}>
            <i className="fas fa-shield-alt" />
            Gestión de Seguridad con IA
          </div>

          <h1 className="hero-h1 reveal" style={{ transitionDelay: '0.1s' }}>
            Prevención de Riesgos<br />
            <span className="highlight">Inteligente</span> y<br />
            Automatizada
          </h1>

          <p className="hero-sub reveal" style={{ transitionDelay: '0.2s' }}>
            Gestión integral de seguridad operativa con análisis de imágenes 360° impulsado por IA.
            Detecta riesgos, gestiona EPP y genera reportes automáticos en tiempo real.
          </p>

          <div className="reveal" style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', transitionDelay: '0.3s' }}>
            <button className="hero-btn-primary" onClick={() => navigate('/login')} data-testid="cta-btn">
              <i className="fas fa-arrow-right" style={{ marginRight: 8 }} />
              Ingresar al Sistema
            </button>
            <button className="hero-btn-outline" onClick={() => scrollTo('funcionalidades')}>
              Ver Funcionalidades
            </button>
          </div>

          <div className="reveal" style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '2rem', flexWrap: 'wrap', transitionDelay: '0.4s' }}>
            {[
              { icon: 'fa-robot', text: 'Análisis con IA' },
              { icon: 'fa-file-pdf', text: 'Reportes Automáticos' },
              { icon: 'fa-check-circle', text: 'OSHA Compliant' },
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

      {/* ── Funcionalidades ────────────────────────────────────────── */}
      <section id="funcionalidades" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>
              <i className="fas fa-cubes" /> Funcionalidades
            </div>
            <h2 className="section-title">
              Todo lo que Necesitas para la <span style={{ color: '#FACC15' }}>Seguridad Operativa</span>
            </h2>
            <p className="section-sub" style={{ margin: '0 auto' }}>
              Módulos especializados que trabajan en conjunto para proteger a tu equipo y cumplir normativa.
            </p>
          </div>

          <div className="feature-cards-grid">
            {[
              { icon: 'fa-camera-retro', color: '#00E5FF', bg: 'rgba(0,229,255,0.15)', title: 'Scan 360° con IA', desc: 'Análisis automático de imágenes para detectar riesgos, condiciones inseguras y generar hallazgos con priorización inteligente.' },
              { icon: 'fa-hard-hat', color: '#FACC15', bg: 'rgba(250,204,21,0.1)', title: 'Gestión de EPP', desc: 'Control completo de inventario, certificaciones, entregas y vencimientos de Equipos de Protección Personal.' },
              { icon: 'fa-exclamation-triangle', color: '#EF4444', bg: 'rgba(239,68,68,0.15)', title: 'Reporte de Incidentes', desc: 'Sistema completo de reportes con seguimiento, investigación y acciones correctivas automáticas.' },
              { icon: 'fa-chart-line', color: '#22C55E', bg: 'rgba(34,197,94,0.15)', title: 'Dashboard Tiempo Real', desc: 'Métricas de seguridad actualizadas en tiempo real con alertas automáticas y KPIs configurables.' },
              { icon: 'fa-th-large', color: '#A855F7', bg: 'rgba(168,85,247,0.15)', title: 'Matriz de Riesgo', desc: 'Evaluación de riesgos con matriz dinámica de probabilidad vs consecuencia y planes de mitigación.' },
              { icon: 'fa-clipboard-list', color: '#2563EB', bg: 'rgba(37,99,235,0.15)', title: 'Procedimientos & Docs', desc: 'Biblioteca de procedimientos seguros, instructivos y documentación normativa centralizada.' },
            ].map((item, i) => (
              <div key={item.title} className={`feature-card reveal stagger-${(i % 3) + 1}`}>
                <div className="feature-icon-box" style={{ background: item.bg, color: item.color }}>
                  <i className={`fas ${item.icon}`} />
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Soluciones ─────────────────────────────────────────────── */}
      <section id="soluciones" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal">
            <div className="section-label">
              <i className="fas fa-lightbulb" /> Soluciones
            </div>
            <h2 className="section-title">
              ¿Por qué elegir <span style={{ color: '#FACC15' }}>SmartSafety+</span>?
            </h2>
            <p className="section-sub">
              Soluciones diseñadas para desafíos reales de seguridad operativa en industria y construcción.
            </p>
          </div>

          <div className="value-cards-grid">
            {[
              { icon: 'fa-brain', title: 'IA Especializada', desc: 'Modelos entrenados específicamente en normativa OSHA, NCh y estándares de seguridad industrial.' },
              { icon: 'fa-clock', title: 'Respuesta Inmediata', desc: 'Detección y notificación de riesgos en segundos, no en días. Prevención proactiva real.' },
              { icon: 'fa-users-cog', title: 'Multi-Empresa', desc: 'Arquitectura multi-tenant que permite gestionar múltiples empresas y proyectos desde un solo lugar.' },
              { icon: 'fa-mobile-alt', title: 'Acceso Total', desc: 'Aplicación responsive que funciona en terreno desde cualquier dispositivo con o sin conexión.' },
              { icon: 'fa-file-export', title: 'Reportes Automáticos', desc: 'Generación automática de informes PDF profesionales listos para fiscalización y auditoría.' },
              { icon: 'fa-lock', title: 'Seguridad de Datos', desc: 'Encriptación end-to-end, roles granulares y cumplimiento de estándares de protección de datos.' },
            ].map((item, i) => (
              <div key={item.title} className={`value-card reveal stagger-${(i % 4) + 1}`}>
                <div className="value-icon">
                  <i className={`fas ${item.icon}`} />
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Diferenciadores ────────────────────────────────────────── */}
      <section id="diferenciadores" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>
              <i className="fas fa-trophy" /> Diferenciadores
            </div>
            <h2 className="section-title">
              Resultados que <span style={{ color: '#00E5FF' }}>Importan</span>
            </h2>
            <p className="section-sub" style={{ margin: '0 auto' }}>
              Métricas reales de empresas que confían en SmartSafety+ para proteger a su gente.
            </p>
          </div>

          <div className="diff-grid">
            {[
              { num: '85%', title: 'Reducción de Incidentes', desc: 'Disminución promedio de incidentes reportados en el primer año de uso.' },
              { num: '3x', title: 'Más Rápido', desc: 'Velocidad de detección de riesgos comparado con inspecciones manuales tradicionales.' },
              { num: '100%', title: 'Trazabilidad', desc: 'Registro completo de cada acción, hallazgo e incidente para auditoría y fiscalización.' },
            ].map((item, i) => (
              <div key={item.title} className={`diff-card reveal stagger-${i + 1}`}>
                <div className="diff-number">{item.num}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Contacto ───────────────────────────────────────────────── */}
      <section id="contacto" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '1rem' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>
              <i className="fas fa-paper-plane" /> Contacto
            </div>
            <h2 className="section-title">
              ¿Listo para <span style={{ color: '#00E5FF' }}>Comenzar</span>?
            </h2>
            <p className="section-sub" style={{ margin: '0 auto' }}>
              Contáctanos y agenda una demo personalizada para tu empresa.
            </p>
          </div>

          <div className="contact-container reveal">
            <div className="contact-info">
              <h3>Conversemos</h3>
              <p>
                Nuestro equipo está disponible para ayudarte a implementar SmartSafety+ en tu operación.
                Escríbenos y te respondemos en menos de 24 horas.
              </p>
              <div className="contact-item">
                <i className="fas fa-envelope" />
                <span>contacto@smartsafety.cl</span>
              </div>
              <div className="contact-item">
                <i className="fab fa-whatsapp" />
                <span>+56 9 1234 5678</span>
              </div>
              <div className="contact-item">
                <i className="fas fa-map-marker-alt" />
                <span>Santiago, Chile</span>
              </div>
            </div>

            <form onSubmit={(e) => e.preventDefault()} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-row">
                <div>
                  <label className="form-field-label">Nombre</label>
                  <input className="form-field-input" placeholder="Tu nombre" />
                </div>
                <div>
                  <label className="form-field-label">Empresa</label>
                  <input className="form-field-input" placeholder="Tu empresa" />
                </div>
              </div>
              <div>
                <label className="form-field-label">Email</label>
                <input className="form-field-input" type="email" placeholder="correo@empresa.cl" />
              </div>
              <div>
                <label className="form-field-label">Mensaje</label>
                <textarea className="form-field-input" rows="4" placeholder="¿En qué podemos ayudarte?" style={{ resize: 'vertical' }} />
              </div>
              <button type="submit" className="form-submit-btn">
                <i className="fas fa-paper-plane" style={{ marginRight: 8 }} />
                Enviar Mensaje
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────── */}
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
                <a href="#"><i className="fab fa-linkedin-in" /></a>
                <a href="#"><i className="fab fa-instagram" /></a>
                <a href="#"><i className="fab fa-youtube" /></a>
              </div>
            </div>

            <div className="footer-col">
              <h4>Plataforma</h4>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('funcionalidades'); }}>Funcionalidades</a>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('soluciones'); }}>Soluciones</a>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('diferenciadores'); }}>Diferenciadores</a>
              <a href="#" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Iniciar Sesión</a>
            </div>

            <div className="footer-col">
              <h4>Módulos</h4>
              <a href="#">Scan 360° con IA</a>
              <a href="#">Gestión de EPP</a>
              <a href="#">Incidentes</a>
              <a href="#">Matriz de Riesgo</a>
            </div>

            <div className="footer-col">
              <h4>Soporte</h4>
              <a href="#">Documentación</a>
              <a href="#">Centro de Ayuda</a>
              <a href="#" onClick={(e) => { e.preventDefault(); scrollTo('contacto'); }}>Contacto</a>
            </div>
          </div>

          <div className="footer-bottom">
            © 2026 SmartSafety+. Todos los derechos reservados. Gestión integral de seguridad operativa.
          </div>
        </div>
      </footer>

      {/* ── WhatsApp Float ─────────────────────────────────────────── */}
      <a href="https://wa.me/56912345678" target="_blank" rel="noopener noreferrer" className="whatsapp-float">
        <i className="fab fa-whatsapp" />
      </a>
    </div>
  );
}
