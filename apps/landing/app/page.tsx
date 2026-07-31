"use client";

import { useState } from "react";

const repoUrl = "https://github.com/bspalaciosg1720/finanzas-por-voz-mvp";

const features = [
  {
    number: "01",
    icon: "⌁",
    title: "Habla como siempre",
    copy: "Di “gasté 18 mil en almuerzo” y Clara entiende monto, categoría y fecha.",
  },
  {
    number: "02",
    icon: "✓",
    title: "Confirma con confianza",
    copy: "Revisa cada dato antes de guardar. Nada dudoso entra silenciosamente.",
  },
  {
    number: "03",
    icon: "↗",
    title: "Decide con claridad",
    copy: "Mira saldo, presupuestos y metas en una vista hecha para actuar.",
  },
];

const faqs = [
  {
    question: "¿Clara se conecta con mi banco?",
    answer:
      "En este MVP tú registras los movimientos por voz o manualmente. Las integraciones bancarias están contempladas para una etapa posterior.",
  },
  {
    question: "¿Qué pasa si entiende mal un monto?",
    answer:
      "Siempre verás una confirmación editable antes de guardar. Puedes corregir monto, categoría, tipo o fecha con un toque.",
  },
  {
    question: "¿Está pensada para Colombia?",
    answer:
      "Sí. El MVP entiende expresiones cotidianas en español y trabaja inicialmente con pesos colombianos.",
  },
  {
    question: "¿Cómo protege mi información?",
    answer:
      "El diseño separa los datos de cada usuario, evita movimientos duplicados y elimina el audio temporal después de procesarlo.",
  },
];

export default function LandingPage() {
  const [activeFaq, setActiveFaq] = useState<number | null>(0);
  const [demoState, setDemoState] = useState<"idle" | "listening" | "done">("idle");

  const runDemo = () => {
    if (demoState === "listening") return;
    setDemoState("listening");
    window.setTimeout(() => setDemoState("done"), 1300);
  };

  return (
    <main>
      <header className="nav-shell">
        <a className="brand" href="#inicio" aria-label="Clara, inicio">
          <span className="brand-mark" aria-hidden="true">C</span>
          <span>clara</span>
        </a>
        <nav aria-label="Navegación principal">
          <a href="#como-funciona">Cómo funciona</a>
          <a href="#beneficios">Beneficios</a>
          <a href="#preguntas">Preguntas</a>
        </nav>
        <a className="nav-cta" href={repoUrl} target="_blank" rel="noreferrer">
          Ver MVP <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="hero" id="inicio">
        <div className="hero-copy">
          <p className="eyebrow"><span /> Finanzas personales, sin fricción</p>
          <h1>Tus finanzas,<br /><em>en tus palabras.</em></h1>
          <p className="hero-lead">
            Registra gastos e ingresos hablando. Clara los organiza para que
            entiendas tu dinero sin formularios eternos ni hojas de cálculo.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#demo">
              Probar la experiencia <span aria-hidden="true">→</span>
            </a>
            <a className="text-link" href="#como-funciona">Ver cómo funciona <span>↓</span></a>
          </div>
          <div className="trust-row">
            <span><b>✓</b> Confirmas antes de guardar</span>
            <span><b>✓</b> Diseñada para COP</span>
          </div>
        </div>

        <div className="hero-visual" aria-label="Vista previa de la aplicación Clara">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="floating-pill pill-one"><span>↗</span><b>Meta al 68%</b></div>
          <div className="floating-pill pill-two"><span>✓</span><b>Movimiento guardado</b></div>
          <div className="phone">
            <div className="phone-speaker" />
            <div className="phone-top">
              <div><small>Buenos días,</small><strong>Valentina</strong></div>
              <div className="avatar">V</div>
            </div>
            <div className="balance-label">Tu saldo disponible</div>
            <div className="balance">$ 2.480.000</div>
            <div className="change">↗ 8,4% este mes</div>
            <div className="summary-grid">
              <div><span className="dot income" />Ingresos<strong>$3.200.000</strong></div>
              <div><span className="dot expense" />Gastos<strong>$720.000</strong></div>
            </div>
            <div className="phone-section-title"><b>Últimos movimientos</b><span>Ver todos</span></div>
            <div className="movement"><span className="movement-icon">☕</span><div><b>Almuerzo</b><small>Alimentación · Hoy</small></div><strong>− $18.000</strong></div>
            <div className="movement"><span className="movement-icon green">↙</span><div><b>Pago freelance</b><small>Ingresos · Ayer</small></div><strong className="positive">+ $850.000</strong></div>
            <div className="voice-bar"><span className="mini-wave">▮▯▮▮▯</span><b>¿Qué movimiento hiciste?</b><button aria-label="Grabar movimiento">●</button></div>
          </div>
        </div>
      </section>

      <section className="problem-strip">
        <p>Controlar tu dinero no debería sentirse como hacer contabilidad.</p>
        <div>
          <span><b>10 seg</b>para registrar</span>
          <span><b>1 toque</b>para confirmar</span>
          <span><b>0 hojas</b>de cálculo</span>
        </div>
      </section>

      <section className="section steps" id="como-funciona">
        <div className="section-heading">
          <p className="eyebrow"><span /> Así de simple</p>
          <h2>De una frase a una decisión<br /><em>en tres pasos.</em></h2>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card" key={feature.number}>
              <div className="feature-meta"><span>{feature.number}</span><i>{feature.icon}</i></div>
              <h3>{feature.title}</h3>
              <p>{feature.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="demo-section" id="demo">
        <div className="demo-copy">
          <p className="eyebrow light"><span /> Pruébalo tú</p>
          <h2>Una frase.<br />Todo organizado.</h2>
          <p>Así se siente registrar un gasto sin abandonar lo que estás haciendo.</p>
          <div className="privacy-note"><span>⌾</span><p><b>Tú tienes el control</b>Clara siempre te pide confirmar antes de guardar.</p></div>
        </div>
        <div className="demo-card">
          <div className="demo-card-top"><span>Clara</span><small>DEMO INTERACTIVA</small></div>
          <div className={`voice-demo ${demoState}`}>
            <button onClick={runDemo} aria-label="Iniciar demostración de voz">
              {demoState === "listening" ? "■" : "●"}
            </button>
            <div className="wave" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
            <p>{demoState === "idle" && "Toca para simular tu frase"}</p>
            <p>{demoState === "listening" && "Escuchando…"}</p>
            <p>{demoState === "done" && "“Gasté 18 mil en almuerzo hoy”"}</p>
          </div>
          <div className={`result-card ${demoState === "done" ? "visible" : ""}`}>
            <div><span>Tipo</span><b>Gasto</b></div>
            <div><span>Monto</span><b>$18.000 COP</b></div>
            <div><span>Categoría</span><b>Alimentación</b></div>
            <div><span>Fecha</span><b>Hoy</b></div>
            <button onClick={() => setDemoState("idle")}>Confirmar movimiento <span>✓</span></button>
          </div>
        </div>
      </section>

      <section className="section benefits" id="beneficios">
        <div className="section-heading split">
          <div><p className="eyebrow"><span /> Más que registrar</p><h2>Tu dinero empieza<br />a tener <em>sentido.</em></h2></div>
          <p>Clara convierte movimientos cotidianos en una vista clara de lo que puedes gastar, ahorrar y mejorar.</p>
        </div>
        <div className="benefit-board">
          <article className="benefit-main">
            <p className="card-kicker">PRESUPUESTOS QUE TE AVISAN A TIEMPO</p>
            <h3>Gasta con contexto,<br />no con culpa.</h3>
            <p>Define límites por categoría y recibe una señal antes de pasarte.</p>
            <div className="budget-widget">
              <div><span>Alimentación</span><b>$420.000 / $600.000</b></div>
              <div className="progress"><i /></div>
              <small><b>70%</b> utilizado · Vas por buen camino</small>
            </div>
          </article>
          <article className="benefit-small goal-card">
            <span className="round-icon">◎</span>
            <p className="card-kicker">METAS DE AHORRO</p>
            <h3>Mira cómo te acercas.</h3>
            <div className="goal-ring"><span>68%<small>completado</small></span></div>
          </article>
          <article className="benefit-small report-card">
            <span className="round-icon">▥</span>
            <p className="card-kicker">REPORTES CLAROS</p>
            <h3>Entiende tu mes de un vistazo.</h3>
            <div className="bars"><i /><i /><i /><i /><i /><i /><i /></div>
          </article>
        </div>
      </section>

      <section className="section faq" id="preguntas">
        <div>
          <p className="eyebrow"><span /> Sin letra pequeña</p>
          <h2>Preguntas<br /><em>frecuentes.</em></h2>
          <p className="faq-intro">Lo importante, explicado con claridad.</p>
        </div>
        <div className="accordion">
          {faqs.map((faq, index) => (
            <article className={activeFaq === index ? "open" : ""} key={faq.question}>
              <button onClick={() => setActiveFaq(activeFaq === index ? null : index)}>
                <span>{faq.question}</span><i>{activeFaq === index ? "−" : "+"}</i>
              </button>
              <p>{faq.answer}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="closing">
        <span className="closing-orb" />
        <p className="eyebrow light"><span /> Empieza por una frase</p>
        <h2>Menos tiempo registrando.<br /><em>Más claridad para decidir.</em></h2>
        <p>Conoce el MVP de Clara y descubre una forma más natural de cuidar tu dinero.</p>
        <a className="button button-light" href={repoUrl} target="_blank" rel="noreferrer">Explorar el proyecto <span>↗</span></a>
      </section>

      <footer>
        <a className="brand footer-brand" href="#inicio"><span className="brand-mark">C</span><span>clara</span></a>
        <p>Finanzas personales que hablan tu idioma.</p>
        <div><a href={repoUrl} target="_blank" rel="noreferrer">GitHub</a><a href="#preguntas">Privacidad</a><a href="#inicio">Volver arriba ↑</a></div>
      </footer>
    </main>
  );
}
