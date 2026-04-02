import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

/* ─── Particles ──────────────────────────────────────────────────────── */
function Particles({ count = 25 }) {
  const p = useRef(Array.from({ length: count }, (_, i) => ({
    id: i, left: Math.random() * 100, size: 1 + Math.random() * 2,
    dur: 8 + Math.random() * 12, delay: Math.random() * 10,
  }))).current;
  return <>{p.map(x => <div key={x.id} className="particle" style={{ left: `${x.left}%`, width: x.size, height: x.size, animationDuration: `${x.dur}s`, animationDelay: `${x.delay}s` }} />)}</>;
}

/* ─── Scroll Reveal ──────────────────────────────────────────────────── */
function useScrollReveal() {
  useEffect(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.reveal-scale').forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

/* ─── Mobile Menu ────────────────────────────────────────────────────── */
function MobileMenu({ open, onClose, onNav }) {
  if (!open) return null;
  return (
    <div style={{ position:'fixed',inset:0,background:'rgba(5,7,10,0.96)',backdropFilter:'blur(20px)',zIndex:1001,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'1.8rem' }}>
      <button onClick={onClose} style={{ position:'absolute',top:20,right:24,color:'#94A3B8',background:'none',border:'none',fontSize:'1.5rem',cursor:'pointer' }}><i className="fas fa-times"/></button>
      {['plataforma','ia','funcionalidades','precios','contacto'].map(id => (
        <a key={id} className="nav-link" style={{ fontSize:'1.1rem',cursor:'pointer' }} onClick={() => { onClose(); setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior:'smooth' }), 100); }}>
          {id.charAt(0).toUpperCase() + id.slice(1)}
        </a>
      ))}
      <button className="hero-btn-primary" style={{ marginTop:'1rem' }} onClick={() => { onClose(); onNav('/login'); }}>Iniciar Sesión</button>
    </div>
  );
}

/* ─── Animated Counter ───────────────────────────────────────────────── */
function Counter({ end, suffix = '', duration = 2000 }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        let start = 0; const step = end / (duration / 16);
        const timer = setInterval(() => { start += step; if (start >= end) { setVal(end); clearInterval(timer); } else setVal(Math.floor(start)); }, 16);
        obs.disconnect();
      }
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [end, duration]);
  return <span ref={ref}>{val}{suffix}</span>;
}

/* ═══════════════════════════════════════════════════════════════════════ */
export default function LandingPage() {
  const navigate = useNavigate();
  const [mobileMenu, setMobileMenu] = useState(false);
  useScrollReveal();
  const scrollTo = id => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div style={{ background:'#05070A',minHeight:'100vh',position:'relative',overflow:'hidden' }} data-testid="landing-page">

      {/* Background */}
      <div className="landing-grid-bg"/>
      <Particles count={25}/>
      <div className="side-line side-line-left"/>
      <div className="side-line side-line-right"/>

      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="logo-brand" style={{ cursor:'pointer' }} onClick={() => window.scrollTo({ top:0,behavior:'smooth' })}>
            <span className="logo-brand-smart">Smart</span><span className="logo-brand-safety">Safety</span><span className="logo-brand-plus">+</span>
          </div>
          <div className="nav-links" style={{ display:'flex',alignItems:'center',gap:'1.8rem' }}>
            <a className="nav-link" onClick={() => scrollTo('plataforma')}>Plataforma</a>
            <a className="nav-link" onClick={() => scrollTo('ia')}>IA</a>
            <a className="nav-link" onClick={() => scrollTo('funcionalidades')}>Funcionalidades</a>
            <a className="nav-link" onClick={() => scrollTo('precios')}>Precios</a>
            <button className="nav-btn-contact" onClick={() => scrollTo('contacto')}><i className="fas fa-envelope" style={{ marginRight:6 }}/>Contacto</button>
            <button className="hero-btn-primary" style={{ padding:'0.55rem 1.4rem',fontSize:'0.85rem' }} onClick={() => navigate('/login')} data-testid="login-nav-btn">Probar Gratis</button>
          </div>
          <button className="nav-hamburger" style={{ display:'none',background:'none',border:'none',color:'#94A3B8',fontSize:'1.4rem',cursor:'pointer' }} onClick={() => setMobileMenu(true)}><i className="fas fa-bars"/></button>
        </div>
      </nav>
      <MobileMenu open={mobileMenu} onClose={() => setMobileMenu(false)} onNav={navigate}/>
      <style>{`@media(max-width:768px){.nav-links{display:none!important}.nav-hamburger{display:block!important}}`}</style>

      {/* ═══ HERO ═══ */}
      <section className="hero-section" style={{ minHeight:'100vh',textAlign:'center',paddingTop:140 }}>
        <div className="hero-glow-cyan"/><div className="hero-glow-blue"/><div className="hero-scan-line"/>
        <div style={{ position:'relative',zIndex:10,maxWidth:900 }}>
          <div className="hero-badge reveal" style={{ marginBottom:'1.5rem' }}><i className="fas fa-bolt"/> Plataforma N°1 en Seguridad Industrial con IA</div>

          <h1 className="hero-h1 reveal" style={{ transitionDelay:'0.1s' }}>
            Reduce <span className="highlight">85%</span> tus Incidentes<br/>con Inteligencia Artificial
          </h1>

          <p className="hero-sub reveal" style={{ transitionDelay:'0.2s',maxWidth:650,margin:'0 auto 2rem' }}>
            SmartSafety+ detecta riesgos en segundos con visión por IA, predice incidentes antes de que ocurran,
            y genera planes de acción automáticos. Todo en tiempo real, desde cualquier dispositivo.
          </p>

          <div className="reveal" style={{ display:'flex',gap:'1rem',justifyContent:'center',flexWrap:'wrap',transitionDelay:'0.3s' }}>
            <button className="hero-btn-primary" style={{ padding:'1rem 2.5rem',fontSize:'1.05rem' }} onClick={() => navigate('/login')} data-testid="cta-btn">
              <i className="fas fa-rocket" style={{ marginRight:8 }}/>Comenzar Gratis
            </button>
            <button className="hero-btn-outline" style={{ padding:'1rem 2.5rem',fontSize:'1.05rem' }} onClick={() => scrollTo('plataforma')}>
              <i className="fas fa-play-circle" style={{ marginRight:8 }}/>Ver Demo
            </button>
          </div>

          {/* Trust badges */}
          <div className="reveal" style={{ display:'flex',justifyContent:'center',gap:'2.5rem',marginTop:'2.5rem',flexWrap:'wrap',transitionDelay:'0.4s' }}>
            {[
              { icon:'fa-shield-alt', text:'OSHA Compliant' },
              { icon:'fa-robot', text:'IA GPT-4o Vision' },
              { icon:'fa-bolt', text:'Alertas en Tiempo Real' },
              { icon:'fa-mobile-alt', text:'PWA Offline' },
            ].map(b => (
              <div key={b.text} style={{ display:'flex',alignItems:'center',gap:6,fontSize:'0.8rem',color:'#64748B' }}>
                <i className={`fas ${b.icon}`} style={{ color:'#22C55E',fontSize:'0.75rem' }}/><span>{b.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ STATS BAR ═══ */}
      <div style={{ background:'#0A0F1A',borderTop:'1px solid rgba(255,255,255,0.06)',borderBottom:'1px solid rgba(255,255,255,0.06)',padding:'2.5rem 20px',position:'relative',zIndex:5 }}>
        <div style={{ maxWidth:1000,margin:'0 auto',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'1rem',textAlign:'center' }}>
          {[
            { val: 85, suf: '%', label: 'Reducción de incidentes' },
            { val: 3, suf: 'x', label: 'Más rápido que manual' },
            { val: 500, suf: '+', label: 'Scans IA procesados' },
            { val: 99, suf: '%', label: 'Uptime garantizado' },
          ].map(s => (
            <div key={s.label} className="reveal">
              <div className="diff-number" style={{ fontSize:'2.5rem',marginBottom:4 }}><Counter end={s.val} suffix={s.suf}/></div>
              <div style={{ fontSize:'0.82rem',color:'#64748B' }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ═══ PLATAFORMA ═══ */}
      <section id="plataforma" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign:'center',marginBottom:'3rem' }}>
            <div className="section-label" style={{ justifyContent:'center' }}><i className="fas fa-layer-group"/> Plataforma</div>
            <h2 className="section-title">Una Plataforma Completa para <span style={{ color:'#FACC15' }}>Toda tu Operación</span></h2>
            <p className="section-sub" style={{ margin:'0 auto' }}>Desde la detección con IA hasta el reporte ejecutivo. Todo integrado, todo en tiempo real.</p>
          </div>

          {/* App Preview */}
          <div className="reveal-scale" style={{ background:'#111827',borderRadius:16,border:'1px solid rgba(255,255,255,0.06)',padding:'1.5rem',maxWidth:800,margin:'0 auto 3rem' }}>
            <div style={{ display:'flex',alignItems:'center',gap:6,marginBottom:12 }}>
              <div style={{ width:10,height:10,borderRadius:'50%',background:'#EF4444' }}/>
              <div style={{ width:10,height:10,borderRadius:'50%',background:'#FACC15' }}/>
              <div style={{ width:10,height:10,borderRadius:'50%',background:'#22C55E' }}/>
              <span style={{ marginLeft:8,fontSize:'0.8rem',color:'#64748B' }}>smartsafety.tecops.cl</span>
            </div>
            <div style={{ background:'#0A0F1A',borderRadius:12,padding:'2rem',border:'1px solid rgba(0,229,255,0.08)' }}>
              <div style={{ display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'1rem',textAlign:'center' }}>
                {[
                  { v:'24', l:'Scans Hoy', c:'#00E5FF' },
                  { v:'98%', l:'Cumplimiento', c:'#22C55E' },
                  { v:'3', l:'Críticos', c:'#EF4444' },
                  { v:'$2.1M', l:'EPP Gestionado', c:'#FACC15' },
                ].map(d => (
                  <div key={d.l}>
                    <div style={{ fontSize:'1.8rem',fontWeight:700,color:d.c,fontFamily:'Outfit' }}>{d.v}</div>
                    <div style={{ fontSize:'0.75rem',color:'#64748B' }}>{d.l}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Module Grid */}
          <div className="feature-cards-grid">
            {[
              { icon:'fa-camera-retro', color:'#00E5FF', bg:'rgba(0,229,255,0.15)', title:'Scan 360° con IA', desc:'Sube una foto y la IA detecta riesgos, genera hallazgos priorizados y sugiere acciones correctivas. Todo en segundos.' },
              { icon:'fa-hard-hat', color:'#FACC15', bg:'rgba(250,204,21,0.1)', title:'Gestión de EPP', desc:'Control total de inventario, entregas con firma digital, alertas de vencimiento, importación Excel, y reportes de costos.' },
              { icon:'fa-exclamation-triangle', color:'#EF4444', bg:'rgba(239,68,68,0.15)', title:'Incidentes + Investigación', desc:'Reporte, investigación ISO 45001, árbol de causas, acciones correctivas, y exportación PDF profesional.' },
              { icon:'fa-chart-line', color:'#22C55E', bg:'rgba(34,197,94,0.15)', title:'Dashboard en Tiempo Real', desc:'KPIs, tendencias, heatmap por zona, alertas WebSocket, y métricas actualizadas cada 30 segundos.' },
              { icon:'fa-th-large', color:'#A855F7', bg:'rgba(168,85,247,0.15)', title:'Matriz de Riesgos', desc:'Evaluación dinámica probabilidad×consecuencia, controles existentes, responsables, y estado por riesgo.' },
              { icon:'fa-search', color:'#2563EB', bg:'rgba(37,99,235,0.15)', title:'Búsqueda Global', desc:'Busca en incidentes, hallazgos, scans, EPP, procedimientos e investigaciones simultáneamente con Ctrl+K.' },
            ].map((item, i) => (
              <div key={item.title} className={`feature-card reveal stagger-${(i % 3) + 1}`}>
                <div className="feature-icon-box" style={{ background:item.bg,color:item.color }}><i className={`fas ${item.icon}`}/></div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ IA ENGINE ═══ */}
      <section id="ia" className="landing-section" style={{ background:'linear-gradient(180deg, transparent 0%, rgba(0,229,255,0.02) 50%, transparent 100%)' }}>
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign:'center',marginBottom:'3rem' }}>
            <div className="section-label" style={{ justifyContent:'center' }}><i className="fas fa-brain"/> Motor de IA</div>
            <h2 className="section-title">Inteligencia Artificial que <span style={{ color:'#00E5FF' }}>Previene, No Solo Detecta</span></h2>
            <p className="section-sub" style={{ margin:'0 auto' }}>4 capacidades de IA que transforman la seguridad reactiva en prevención proactiva.</p>
          </div>

          <div style={{ display:'grid',gridTemplateColumns:'repeat(2,1fr)',gap:'1.5rem' }}>
            {[
              { icon:'fa-camera', title:'Visión por IA (GPT-4o)', desc:'Analiza fotos de terreno y detecta riesgos, EPP faltante, obstrucciones, y genera hallazgos con referencia normativa OSHA.', tag:'SCAN 360°', tagColor:'#00E5FF' },
              { icon:'fa-chart-bar', title:'IA Predictiva', desc:'Analiza patrones históricos de hallazgos e incidentes para predecir zonas de riesgo, categorías críticas y tendencias.', tag:'PREDICCIÓN', tagColor:'#A855F7' },
              { icon:'fa-clipboard-check', title:'Plan de Acción Automático', desc:'Genera planes correctivos priorizados por riesgo y costo. Incluye responsable, plazo, referencia normativa y verificación.', tag:'ACCIÓN', tagColor:'#22C55E' },
              { icon:'fa-comments', title:'Chat IA sobre tus Datos', desc:'Pregunta en lenguaje natural: "¿cuántos críticos hay abiertos?" — La IA consulta tu base de datos y responde al instante.', tag:'CHAT', tagColor:'#FACC15' },
            ].map((item, i) => (
              <div key={item.title} className={`value-card reveal stagger-${(i % 4) + 1}`} style={{ padding:'2rem' }}>
                <div style={{ display:'flex',alignItems:'center',gap:'0.8rem',marginBottom:'1rem' }}>
                  <div className="value-icon" style={{ background:`${item.tagColor}20`,color:item.tagColor }}><i className={`fas ${item.icon}`}/></div>
                  <span style={{ fontSize:'0.65rem',fontWeight:700,letterSpacing:2,textTransform:'uppercase',color:item.tagColor,background:`${item.tagColor}15`,padding:'0.3rem 0.8rem',borderRadius:20,border:`1px solid ${item.tagColor}30` }}>{item.tag}</span>
                </div>
                <h3 style={{ fontFamily:'Outfit',fontSize:'1.15rem',fontWeight:700,color:'#F8FAFC',marginBottom:'0.4rem' }}>{item.title}</h3>
                <p style={{ fontSize:'0.88rem',color:'#94A3B8',lineHeight:1.7 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ FUNCIONALIDADES EXTRA ═══ */}
      <section id="funcionalidades" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign:'center',marginBottom:'3rem' }}>
            <div className="section-label" style={{ justifyContent:'center' }}><i className="fas fa-bolt"/> Tiempo Real</div>
            <h2 className="section-title">Alertas <span style={{ color:'#00E5FF' }}>Instantáneas</span>, Escalamiento Automático</h2>
          </div>

          <div style={{ display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'1.5rem' }}>
            {[
              { icon:'fa-wifi', title:'WebSocket en Vivo', desc:'Dashboard se actualiza instantáneamente cuando se detecta un hallazgo, se crea un incidente, o se completa un scan.' },
              { icon:'fa-bell', title:'Centro de Notificaciones', desc:'Notificaciones in-app con badge, leído/no leído, filtros por severidad. Más email y SMS automáticos.' },
              { icon:'fa-level-up-alt', title:'Escalamiento Automático', desc:'Hallazgo crítico >24h sin resolver → alerta a supervisor. >48h → escala a gerencia. Sin intervención manual.' },
              { icon:'fa-file-pdf', title:'PDFs Profesionales', desc:'Reporte ejecutivo con portada, resumen, gráficos, tablas. Logo de tu empresa. Listo para fiscalización.' },
              { icon:'fa-mobile-alt', title:'PWA + Offline', desc:'Instálala como app nativa. Funciona sin conexión en terreno. Se sincroniza cuando vuelves a tener red.' },
              { icon:'fa-shield-alt', title:'Seguridad Enterprise', desc:'Rate limiting, audit trail de cada acción, CORS restrictivo, JWT con expiración, roles granulares.' },
            ].map((item, i) => (
              <div key={item.title} className={`diff-card reveal stagger-${(i % 3) + 1}`} style={{ textAlign:'left',padding:'2rem' }}>
                <i className={`fas ${item.icon}`} style={{ fontSize:'1.3rem',color:'#00E5FF',marginBottom:'1rem',display:'block' }}/>
                <h3 style={{ fontFamily:'Outfit',fontSize:'1.05rem',fontWeight:700,color:'#F8FAFC',marginBottom:'0.5rem' }}>{item.title}</h3>
                <p style={{ fontSize:'0.85rem',color:'#94A3B8',lineHeight:1.6 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ PRECIOS ═══ */}
      <section id="precios" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign:'center',marginBottom:'3rem' }}>
            <div className="section-label" style={{ justifyContent:'center' }}><i className="fas fa-tags"/> Planes</div>
            <h2 className="section-title">Elige el Plan para tu <span style={{ color:'#FACC15' }}>Operación</span></h2>
          </div>

          <div style={{ display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'1.5rem',maxWidth:1000,margin:'0 auto' }}>
            {[
              { name:'Starter', price:'Gratis', period:'hasta 3 usuarios', color:'#94A3B8', features:['Scan 360° (10/mes)','Dashboard básico','Incidentes','EPP básico','1 organización'], cta:'Comenzar Gratis', popular:false },
              { name:'Professional', price:'$49', period:'USD/mes por usuario', color:'#00E5FF', features:['Scans ilimitados','IA Predictiva + Chat','Escalamiento automático','WebSocket tiempo real','PDFs profesionales','Búsqueda global','Soporte prioritario'], cta:'Probar 14 Días Gratis', popular:true },
              { name:'Enterprise', price:'Custom', period:'contactar ventas', color:'#FACC15', features:['Todo en Professional','Multi-organización','API dedicada','SLA 99.9%','Onboarding dedicado','Integraciones custom','Soporte 24/7'], cta:'Contactar Ventas', popular:false },
            ].map((plan, i) => (
              <div key={plan.name} className={`reveal stagger-${i+1}`} style={{
                background: plan.popular ? 'linear-gradient(145deg, #0A0F1A, #111827)' : '#0A0F1A',
                border: `1px solid ${plan.popular ? 'rgba(0,229,255,0.3)' : 'rgba(255,255,255,0.06)'}`,
                borderRadius:16, padding:'2.5rem 2rem', position:'relative',
                boxShadow: plan.popular ? '0 0 40px rgba(0,229,255,0.08)' : 'none',
              }}>
                {plan.popular && <div style={{ position:'absolute',top:-12,left:'50%',transform:'translateX(-50%)',background:'#00E5FF',color:'#05070A',fontSize:'0.65rem',fontWeight:700,letterSpacing:1,textTransform:'uppercase',padding:'0.3rem 1rem',borderRadius:20 }}>Más Popular</div>}
                <div style={{ fontSize:'0.75rem',fontWeight:600,letterSpacing:2,textTransform:'uppercase',color:plan.color,marginBottom:'0.5rem' }}>{plan.name}</div>
                <div style={{ fontFamily:'Outfit',fontSize:'2.5rem',fontWeight:800,color:'#F8FAFC' }}>{plan.price}</div>
                <div style={{ fontSize:'0.82rem',color:'#64748B',marginBottom:'1.5rem' }}>{plan.period}</div>
                <div style={{ borderTop:'1px solid rgba(255,255,255,0.06)',paddingTop:'1.5rem' }}>
                  {plan.features.map(f => (
                    <div key={f} style={{ display:'flex',alignItems:'center',gap:8,marginBottom:'0.7rem',fontSize:'0.88rem',color:'#94A3B8' }}>
                      <i className="fas fa-check" style={{ color:plan.color,fontSize:'0.7rem' }}/>{f}
                    </div>
                  ))}
                </div>
                <button onClick={() => navigate('/login')} style={{
                  width:'100%', marginTop:'1.5rem', padding:'0.8rem', borderRadius:8, fontWeight:700, fontSize:'0.9rem', cursor:'pointer', transition:'all 0.3s',
                  background: plan.popular ? '#00E5FF' : 'transparent',
                  color: plan.popular ? '#05070A' : plan.color,
                  border: plan.popular ? 'none' : `1px solid ${plan.color}40`,
                }}>{plan.cta}</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CONTACTO ═══ */}
      <section id="contacto" className="landing-section">
        <div className="landing-section-inner">
          <div className="reveal" style={{ textAlign:'center',marginBottom:'1rem' }}>
            <div className="section-label" style={{ justifyContent:'center' }}><i className="fas fa-paper-plane"/> Contacto</div>
            <h2 className="section-title">¿Listo para <span style={{ color:'#00E5FF' }}>Proteger</span> a tu Equipo?</h2>
            <p className="section-sub" style={{ margin:'0 auto' }}>Agenda una demo personalizada. Sin compromiso.</p>
          </div>

          <div className="contact-container reveal">
            <div className="contact-info">
              <h3>Conversemos</h3>
              <p>Nuestro equipo te ayuda a implementar SmartSafety+ en tu operación. Respuesta en menos de 24 horas.</p>
              <div className="contact-item"><i className="fas fa-envelope"/><span>contacto@smartsafety.cl</span></div>
              <div className="contact-item"><i className="fab fa-whatsapp"/><span>+56 9 1234 5678</span></div>
              <div className="contact-item"><i className="fas fa-map-marker-alt"/><span>Santiago, Chile</span></div>

              <div style={{ marginTop:'2rem',padding:'1.2rem',background:'rgba(0,229,255,0.06)',borderRadius:12,border:'1px solid rgba(0,229,255,0.15)' }}>
                <div style={{ fontSize:'0.7rem',fontWeight:600,letterSpacing:1,textTransform:'uppercase',color:'#00E5FF',marginBottom:'0.4rem' }}>Garantía</div>
                <div style={{ fontSize:'0.88rem',color:'#94A3B8',lineHeight:1.6 }}>14 días gratis en plan Professional. Sin tarjeta de crédito. Cancela cuando quieras.</div>
              </div>
            </div>

            <form onSubmit={e => e.preventDefault()} style={{ display:'flex',flexDirection:'column',gap:'1rem' }}>
              <div className="form-row">
                <div><label className="form-field-label">Nombre</label><input className="form-field-input" placeholder="Tu nombre"/></div>
                <div><label className="form-field-label">Empresa</label><input className="form-field-input" placeholder="Tu empresa"/></div>
              </div>
              <div><label className="form-field-label">Email</label><input className="form-field-input" type="email" placeholder="correo@empresa.cl"/></div>
              <div><label className="form-field-label">¿Cuántos trabajadores tienes?</label>
                <select className="form-field-input" style={{ appearance:'none' }}>
                  <option value="">Selecciona...</option>
                  <option>1 - 50</option><option>51 - 200</option><option>201 - 500</option><option>500+</option>
                </select>
              </div>
              <div><label className="form-field-label">Mensaje</label><textarea className="form-field-input" rows="3" placeholder="¿En qué podemos ayudarte?" style={{ resize:'vertical' }}/></div>
              <button type="submit" className="form-submit-btn"><i className="fas fa-paper-plane" style={{ marginRight:8 }}/>Agendar Demo</button>
            </form>
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="footer-top">
            <div className="footer-brand">
              <div className="logo-brand"><span className="logo-brand-smart">Smart</span><span className="logo-brand-safety">Safety</span><span className="logo-brand-plus">+</span></div>
              <p>Plataforma líder en gestión de seguridad operativa con inteligencia artificial.</p>
              <div className="footer-social">
                <a href="#"><i className="fab fa-linkedin-in"/></a>
                <a href="#"><i className="fab fa-instagram"/></a>
                <a href="#"><i className="fab fa-youtube"/></a>
              </div>
            </div>
            <div className="footer-col">
              <h4>Producto</h4>
              <a href="#" onClick={e => { e.preventDefault(); scrollTo('plataforma'); }}>Plataforma</a>
              <a href="#" onClick={e => { e.preventDefault(); scrollTo('ia'); }}>Motor de IA</a>
              <a href="#" onClick={e => { e.preventDefault(); scrollTo('precios'); }}>Precios</a>
              <a href="#" onClick={e => { e.preventDefault(); navigate('/login'); }}>Iniciar Sesión</a>
            </div>
            <div className="footer-col">
              <h4>Módulos</h4>
              <a href="#">Scan 360° con IA</a><a href="#">Gestión de EPP</a><a href="#">Incidentes</a><a href="#">IA Predictiva</a>
            </div>
            <div className="footer-col">
              <h4>Empresa</h4>
              <a href="#">Documentación</a><a href="#">Centro de Ayuda</a>
              <a href="#" onClick={e => { e.preventDefault(); scrollTo('contacto'); }}>Contacto</a>
            </div>
          </div>
          <div className="footer-bottom">© 2026 SmartSafety+ by TecOps SpA. Todos los derechos reservados.</div>
        </div>
      </footer>

      {/* WhatsApp */}
      <a href="https://wa.me/56912345678" target="_blank" rel="noopener noreferrer" className="whatsapp-float"><i className="fab fa-whatsapp"/></a>
    </div>
  );
}
