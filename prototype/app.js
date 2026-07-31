const scenarios = {
  lunch: {
    transcript: "Gasté dieciocho mil en almuerzo.",
    type: "GASTO",
    amount: "$18.000",
    category: "Alimentación",
    description: "Almuerzo",
    date: "Hoy, 12:40 p. m."
  },
  gas: {
    transcript: "Ayer compré gasolina por noventa mil.",
    type: "GASTO",
    amount: "$90.000",
    category: "Transporte",
    description: "Gasolina",
    date: "Ayer, 8:15 a. m."
  },
  salary: {
    transcript: "Me pagaron un millón de salario.",
    type: "INGRESO",
    amount: "$1.000.000",
    category: "Salario",
    description: "Pago de salario",
    date: "Hoy, 9:20 a. m."
  },
  "wrong-category": {
    transcript: "Compré gasolina por noventa mil.",
    type: "GASTO",
    amount: "$90.000",
    category: "Compras",
    description: "Gasolina",
    date: "Hoy, 8:15 a. m.",
    warning: "La categoría puede no coincidir con la descripción."
  },
  ambiguous: {
    transcript: "Gasté quince... cincuenta mil en mercado.",
    type: "GASTO",
    amount: null,
    choices: ["$15.000", "$50.000"],
    category: "Alimentación",
    description: "Mercado",
    date: "Hoy, 6:30 p. m."
  },
  "no-speech": {
    transcript: "",
    error: true
  }
};

const transactions = [
  ["Almuerzo", "Alimentación · Hoy, 12:40", "-$18.000", ""],
  ["Gasolina", "Transporte · Ayer, 8:15", "-$90.000", ""],
  ["Pago de salario", "Salario · 29 jul", "+$1.000.000", "income"]
];

const app = document.querySelector("#app");
const bottomNav = document.querySelector("#bottomNav");
const scenarioSelect = document.querySelector("#scenario");
const resetDemo = document.querySelector("#resetDemo");
const toast = document.querySelector("#toast");

let screen = "home";
let selectedAmount = null;
let scenario = scenarios[scenarioSelect.value];

function moneyRow([name, meta, amount, className]) {
  return `
    <div class="transaction-row">
      <span class="category-dot"></span>
      <div class="transaction-copy"><strong>${name}</strong><span>${meta}</span></div>
      <span class="amount ${className}">${amount}</span>
    </div>`;
}

function renderHome() {
  app.innerHTML = `
    <div class="top-row">
      <div><p class="helper">Jueves, 30 de julio</p><h2>Buenos días, Ana</h2></div>
      <div class="avatar">AL</div>
    </div>
    <section class="balance-card">
      <span class="muted">Saldo actual</span>
      <div class="balance">$3.420.500</div>
      <span class="change">↑ 4,8 % frente al mes pasado</span>
    </section>
    <div class="summary-grid">
      <div class="small-card"><span class="helper">Ingresos</span><strong>$4.200.000</strong></div>
      <div class="small-card"><span class="helper">Gastos</span><strong>$779.500</strong></div>
    </div>
    <div class="section-row"><h3>Movimientos recientes</h3><button data-action="transactions">Ver todos</button></div>
    <div class="content-card">${transactions.slice(0, 3).map(moneyRow).join("")}</div>
    <button class="mic" data-action="voice" aria-label="Registrar por voz">●</button>`;
}

function renderTransactions() {
  app.innerHTML = `
    <div class="top-row"><h2>Movimientos</h2><button class="icon-button">⌕</button></div>
    <p class="helper">Todos · Julio 2026</p>
    <div class="section-row"><h3>Últimos registros</h3></div>
    <div class="content-card">${transactions.map(moneyRow).join("")}</div>
    <button class="mic" data-action="voice" aria-label="Registrar por voz">●</button>`;
}

function renderPlaceholder(title, copy) {
  app.innerHTML = `
    <div class="top-row"><h2>${title}</h2></div>
    <div class="content-card" style="margin-top:24px;padding:22px">
      <h3>Vista conceptual</h3>
      <p class="muted" style="line-height:1.55">${copy}</p>
    </div>`;
}

function startVoice() {
  screen = "listening";
  bottomNav.hidden = true;
  app.innerHTML = `
    <div class="voice-screen">
      <div class="top-row"><button class="back-button" data-action="cancel">×</button><span></span></div>
      <div class="voice-copy">
        <p class="eyebrow">REGISTRO POR VOZ</p>
        <h2>Te escucho…</h2>
        <div class="wave" aria-label="Escuchando">
          <span></span><span></span><span></span><span></span><span></span><span></span><span></span>
        </div>
        <p class="transcript">${scenario.transcript || "Habla de forma natural"}</p>
      </div>
      <div>
        <button class="stop-button" data-action="process" aria-label="Detener">■</button>
        <p class="helper">Toca para detener</p>
      </div>
    </div>`;
}

function processVoice() {
  app.innerHTML = `
    <div class="voice-screen" style="justify-content:center">
      <div>
        <div class="wave"><span></span><span></span><span></span><span></span><span></span></div>
        <h2>Interpretando…</h2>
        <p class="muted">Organizando los datos del movimiento</p>
      </div>
    </div>`;
  window.setTimeout(() => scenario.error ? renderNoSpeech() : renderConfirmation(), 650);
}

function renderConfirmation() {
  screen = "confirmation";
  if (scenario.choices && !selectedAmount) {
    renderAmountChoice();
    return;
  }

  app.innerHTML = `
    <div class="top-row">
      <button class="back-button" data-action="retry">‹</button>
      <h3>Confirmar movimiento</h3>
      <span style="width:38px"></span>
    </div>
    <div class="confirm-amount">${selectedAmount || scenario.amount}</div>
    <span class="pill">${scenario.type}</span>
    ${scenario.warning ? `<div class="warning-card">Revisa la categoría antes de guardar.</div>` : ""}
    <div class="confirm-list">
      <button class="confirm-row" data-action="category" aria-label="Editar categoría, actual ${scenario.category}"><span>Categoría</span><span>${scenario.category} ›</span></button>
      <button class="confirm-row" aria-label="Editar fecha, actual ${scenario.date}"><span>Fecha</span><span>${scenario.date} ›</span></button>
      <button class="confirm-row" aria-label="Editar descripción, actual ${scenario.description}"><span>Descripción</span><span>${scenario.description} ›</span></button>
    </div>
    <div class="actions">
      <button class="primary-button" data-action="save">Confirmar y guardar</button>
      <button class="secondary-button" data-action="retry">Intentar de nuevo</button>
    </div>`;
}

function renderAmountChoice() {
  app.innerHTML = `
    <div class="top-row">
      <button class="back-button" data-action="retry">‹</button>
      <h3>Necesito confirmar</h3>
      <span style="width:38px"></span>
    </div>
    <div style="margin-top:35px">
      <p class="eyebrow">MONTO DUDOSO</p>
      <h2>¿Cuánto gastaste?</h2>
      <p class="muted">Escuché dos valores posibles en tu frase.</p>
      <div class="choice-grid">
        ${scenario.choices.map(value => `<button class="choice" data-amount="${value}">${value}</button>`).join("")}
      </div>
      <button class="primary-button" data-action="amount-confirm" disabled>Continuar</button>
      <button class="secondary-button" data-action="retry">Decirlo nuevamente</button>
    </div>`;
}

function renderCategoryPicker() {
  app.innerHTML = `
    <div class="top-row">
      <button class="back-button" data-action="back-confirm">‹</button>
      <h3>Elegir categoría</h3>
      <span style="width:38px"></span>
    </div>
    <div class="choice-grid" style="margin-top:24px">
      ${["Transporte", "Compras", "Alimentación", "Servicios", "Otros"]
        .map(category => `<button class="choice ${scenario.category === category ? "selected" : ""}" data-category="${category}">${category}</button>`)
        .join("")}
    </div>`;
}

function renderNoSpeech() {
  screen = "error";
  app.innerHTML = `
    <div class="error-screen">
      <div class="result-icon error">!</div>
      <h2>No pude escucharte</h2>
      <p>Acércate al micrófono o registra el movimiento manualmente.</p>
      <div class="actions" style="width:100%">
        <button class="primary-button" data-action="retry">Intentar de nuevo</button>
        <button class="secondary-button" data-action="manual">Registrar manualmente</button>
      </div>
    </div>`;
}

function renderManualForm(errorMessage = "") {
  screen = "manual";
  app.innerHTML = `
    <div class="top-row">
      <button class="back-button" data-action="cancel">‹</button>
      <h3>Nuevo movimiento</h3>
      <span style="width:38px"></span>
    </div>
    <form id="manualForm" class="manual-form" novalidate>
      <fieldset class="type-switch">
        <legend class="sr-only">Tipo de movimiento</legend>
        <label>
          <input type="radio" name="movementType" value="GASTO" checked>
          <span>Gasto</span>
        </label>
        <label>
          <input type="radio" name="movementType" value="INGRESO">
          <span>Ingreso</span>
        </label>
      </fieldset>

      <label class="field-label" for="manualAmount">Monto</label>
      <div class="money-input ${errorMessage ? "invalid" : ""}">
        <span>$</span>
        <input
          id="manualAmount"
          name="amount"
          inputmode="numeric"
          autocomplete="off"
          placeholder="0"
          aria-describedby="amountHelp"
          aria-invalid="${errorMessage ? "true" : "false"}"
        >
      </div>
      <p id="amountHelp" class="field-help ${errorMessage ? "error-text" : ""}">
        ${errorMessage || "Escribe el valor en pesos, sin centavos."}
      </p>

      <label class="field-label" for="manualCategory">Categoría</label>
      <select id="manualCategory" name="category" class="field-control">
        <option>Alimentación</option>
        <option>Transporte</option>
        <option>Salud</option>
        <option>Educación</option>
        <option>Vivienda</option>
        <option>Servicios</option>
        <option>Entretenimiento</option>
        <option>Compras</option>
        <option>Mascotas</option>
        <option>Viajes</option>
        <option>Otros</option>
      </select>

      <label class="field-label" for="manualDescription">Descripción <span>Opcional</span></label>
      <input id="manualDescription" name="description" class="field-control" placeholder="Ej. Almuerzo">

      <label class="field-label" for="manualDate">Fecha</label>
      <select id="manualDate" name="date" class="field-control">
        <option>Hoy</option>
        <option>Ayer</option>
      </select>

      <button class="primary-button form-submit" type="submit">Guardar movimiento</button>
    </form>`;
  document.querySelector("#manualAmount").focus();
}

function saveManual(form) {
  const data = new FormData(form);
  const rawAmount = String(data.get("amount") || "");
  const digits = rawAmount.replace(/\D/g, "");
  const amount = Number(digits);

  if (!digits || !Number.isSafeInteger(amount) || amount <= 0) {
    renderManualForm("Introduce un monto válido mayor que cero.");
    return;
  }

  scenario = {
    type: String(data.get("movementType")),
    amount: `$${new Intl.NumberFormat("es-CO").format(amount)}`,
    category: String(data.get("category")),
    description: String(data.get("description") || "") || "Sin descripción",
    date: String(data.get("date"))
  };
  selectedAmount = null;
  renderSuccess();
}

function renderSuccess() {
  screen = "success";
  app.innerHTML = `
    <div class="success-screen">
      <div class="result-icon">✓</div>
      <h2>Movimiento guardado</h2>
      <p>${scenario.type === "INGRESO" ? "Ingreso" : "Gasto"} de ${selectedAmount || scenario.amount} registrado correctamente.</p>
      <button class="primary-button" data-action="done" style="margin-top:18px">Volver al inicio</button>
    </div>`;
  showToast("Movimiento guardado");
}

function render() {
  bottomNav.hidden = false;
  document.querySelectorAll(".nav-item").forEach(button => {
    button.classList.toggle("active", button.dataset.nav === screen);
  });

  if (screen === "home") renderHome();
  if (screen === "transactions") renderTransactions();
  if (screen === "budget") renderPlaceholder("Presupuesto", "Límites mensuales y avance por categoría.");
  if (screen === "reports") renderPlaceholder("Reportes", "Resumen mensual y comparación con el período anterior.");
  if (screen === "profile") renderPlaceholder("Perfil", "Cuenta, categorías, metas, recordatorios y privacidad.");
}

function reset() {
  scenario = scenarios[scenarioSelect.value];
  selectedAmount = null;
  screen = "home";
  render();
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 1800);
}

document.addEventListener("keydown", event => {
  if (event.key !== "Escape" || bottomNav.hidden === false) return;
  screen = "home";
  render();
});

app.addEventListener("click", event => {
  const target = event.target.closest("button");
  if (!target) return;
  const action = target.dataset.action;

  if (action === "voice") startVoice();
  if (action === "process") processVoice();
  if (action === "cancel" || action === "done") {
    screen = "home";
    render();
  }
  if (action === "retry") startVoice();
  if (action === "save") renderSuccess();
  if (action === "transactions") {
    screen = "transactions";
    render();
  }
  if (action === "category") renderCategoryPicker();
  if (action === "back-confirm") renderConfirmation();
  if (action === "manual") renderManualForm();

  if (target.dataset.amount) {
    selectedAmount = target.dataset.amount;
    document.querySelectorAll("[data-amount]").forEach(choice => choice.classList.remove("selected"));
    target.classList.add("selected");
    document.querySelector("[data-action='amount-confirm']").disabled = false;
  }

  if (action === "amount-confirm" && selectedAmount) renderConfirmation();

  if (target.dataset.category) {
    scenario.category = target.dataset.category;
    scenario.warning = null;
    showToast(`Categoría cambiada a ${scenario.category}`);
    window.setTimeout(renderConfirmation, 250);
  }
});

app.addEventListener("submit", event => {
  if (event.target.id !== "manualForm") return;
  event.preventDefault();
  saveManual(event.target);
});

bottomNav.addEventListener("click", event => {
  const target = event.target.closest("[data-nav]");
  if (!target) return;
  screen = target.dataset.nav;
  render();
});

scenarioSelect.addEventListener("change", reset);
resetDemo.addEventListener("click", reset);

render();
