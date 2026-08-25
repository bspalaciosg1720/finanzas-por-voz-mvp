# Deudas y salud financiera

## Decisión

Los cálculos de salud financiera y salida de deudas se ejecutan con código
determinístico dentro del monolito modular. Una integración futura con IA podrá
explicar estos resultados, pero no calcular saldos, tasas, puntajes ni plazos.

## Deudas

Cada deuda conserva saldo inicial y actual, pago mínimo, moneda, tasa anual
opcional en puntos básicos y fechas opcionales. Los pagos mantienen su propio
historial y reducen el saldo en una transacción de base de datos.

Las estrategias disponibles son:

- bola de nieve: menor saldo primero;
- avalancha: mayor tasa conocida primero.

Las proyecciones aplican interés mensual mediante aritmética decimal. Si falta
alguna tasa, se muestra el orden de prioridad pero no se estiman intereses ni
fecha de finalización.

## Salud financiera

El puntaje se normaliza usando únicamente componentes con datos disponibles.
El desglose y las limitaciones se incluyen en la respuesta para evitar una
precisión aparente. La carga de deuda usa la proporción entre pagos mínimos e
ingreso mensual; nunca se recomienda usar dinero de necesidades esenciales
para efectuar abonos extraordinarios.

El historial guarda una instantánea mensual con la versión de la fórmula y el
desglose utilizado. Las simulaciones son operaciones de solo lectura y siempre
devuelven `applied: false`.

## Fondo y calendario

El fondo de emergencia diferencia depósitos y retiros. Un retiro aumenta el
valor pendiente por reponer, pero no se convierte en una deuda ni genera
intereses. La cobertura se obtiene dividiendo el saldo del fondo entre los
gastos esenciales del periodo.

El calendario genera vencimientos mensuales a partir de obligaciones
registradas. Cada obligación exige una categoría de gasto válida y cada pago
conserva una copia de esa categoría, de modo que reclasificar la obligación no
reescriba el historial ni los cálculos anteriores. Los pagos confirmados se
conservan por separado y generan su movimiento de caja con la misma categoría.

## Asistente opcional

El asistente está desactivado por defecto. Sin una configuración externa,
responde usando el motor local de reglas. Cuando se habilita OpenAI, recibe
solamente indicadores estructurados, usa la API Responses con `store: false` y
no recibe movimientos individuales. Si el proveedor falla, vuelve a la
explicación determinística.

## Patrones financieros

`GET /financial-health/patterns` analiza entre tres y seis meses cerrados. El
motor compara importes almacenados mediante código y puede detectar crecimiento
sostenido del gasto, caída del ahorro, déficit frecuente y aumentos por
categoría. Cada resultado incluye los periodos, importes y porcentaje usados;
un mes en curso nunca se compara como si estuviera completo.

El crecimiento histórico de la deuda no se estima a partir del saldo actual:
se informa como limitación hasta disponer de suficientes instantáneas mensuales.
La IA no participa en la detección ni calcula porcentajes.

## Perfil de ingresos

`GET /financial-health/income-profile` analiza de tres a doce meses cerrados y
publica promedio, mediana, variabilidad y todos los importes mensuales usados.
Con al menos tres meses observados clasifica el ingreso como estable o variable.
Para ingresos variables, la base conservadora es el cuartil inferior; para los
estables, el menor valor entre promedio y mediana. Esta referencia nunca se
presenta como dinero ya recibido ni reemplaza el flujo de caja real del mes.

`GET /financial-health/extra-income` marca como posible excedente la parte del
ingreso mensual que supera al menos 20 % la base conservadora. También acepta
un `amount_minor` explícito para analizar una bonificación conocida. La
propuesta prioriza reponer el fondo utilizado, completar hasta un mes de gastos
esenciales, destinar 70 % del remanente a deuda y conservar el resto para metas.
El resultado siempre lleva `applied: false`: consultar o simular nunca crea
movimientos ni cambia saldos.

## Alertas priorizadas

`GET /financial-alerts` reúne vencimientos de los próximos tres días,
presupuestos en riesgo, patrones relevantes y deudas cercanas a terminar. Las
reglas asignan prioridad por riesgo y la respuesta muestra como máximo tres
alertas por defecto. Las claves estables eliminan duplicados dentro de cada
periodo.

Descartar una alerta guarda únicamente su clave mediante
`POST /financial-alerts/dismiss`. Un nuevo vencimiento o periodo genera otra
clave, evitando tanto la repetición constante como el silenciamiento permanente
de situaciones futuras. Esta bandeja funciona sin permisos de push; la entrega
remota existente puede integrarse después sobre los mismos resultados.

## Estrategias opcionales y adaptativas

`GET /financial-strategies/analysis` evalúa catorce estrategias mediante datos
reales y devuelve para cada una: estado, recomendación, prioridad, razón,
beneficio, impacto estimado y limitaciones. `GET` y `PATCH` sobre
`/financial-strategies/config` administran preferencias por usuario. Todas se
desactivan o configuran sin alterar la fórmula de Salud Financiera.

- Base cero combina ingreso de planificación, sobres, pagos mínimos y aportes
  mensuales planeados, mostrando el dinero sin asignar o el exceso.
- Los sobres digitales reutilizan presupuestos y sus alertas; no existe una
  contabilidad paralela.
- El presupuesto variable utiliza la base conservadora ya calculada y mantiene
  separado el ingreso realmente recibido.
- Los ingresos extraordinarios admiten porcentajes configurables para deuda,
  ahorro, metas y uso personal, que siempre deben sumar 100 %.
- La deuda híbrida simula primero la deuda más pequeña y después ordena las
  restantes por tasa, sin inventar tasas ausentes.
- Las metas con `goal_type=sinking_fund` guardan un aporte mensual planeado para
  gastos previsibles.
- Colchón de caja, días sin gasto, espera de compras, fugas y costo de
  oportunidad producen comparaciones informativas; nunca bloquean compras.
- La prioridad global conserva el orden: necesidades, pagos próximos, mínimos,
  reserva, deuda prioritaria, ahorro, metas y gasto discrecional.
- Las etapas `stabilize`, `protect`, `debt_freedom`, `build` y `grow` dependen de
  flujo disponible, cobertura de emergencia y deuda actual.

“Págate primero” requiere activación explícita y una meta del mismo usuario. Al
crear un ingreso confirmado, calcula un aporte por porcentaje o monto, limitado
por el dinero que queda después de gastos esenciales, mínimos de deuda y ahorro
ya realizado. El ingreso y el aporte usan claves únicas relacionadas: repetir
la solicitud de ingreso no duplica el ahorro. Para preservar consistencia, un
ingreso con aporte automático debe desvincular primero ese aporte antes de ser
editado o eliminado.

La política de minimización se apoya en los controles de datos documentados por
OpenAI: <https://developers.openai.com/api/docs/guides/your-data>.

## Movimientos vinculados

Los pagos y transferencias creados desde otros módulos generan un movimiento de
libro mayor dentro de la misma transacción de base de datos. El movimiento
conserva un rol financiero explícito:

- `regular`: ingreso o consumo ordinario;
- `debt_payment`: pago de deuda;
- `savings_transfer`: aporte o retiro de ahorro;
- `obligation_payment`: pago de una obligación programada.

Los movimientos vinculados aparecen en el historial de caja, pero deuda y
transferencias de ahorro se excluyen de los totales de consumo, categorías y
regla 50/30/20. Solo pueden corregirse desde el módulo que los originó para
evitar que el movimiento y su saldo asociado queden desincronizados.

Las correcciones se ejecutan atómicamente. Editar un pago actualiza el saldo y
su movimiento; eliminarlo restaura el saldo y anula el movimiento. En el fondo
de emergencia, cada corrección reproduce cronológicamente el historial completo
y se rechaza si hubiera causado un retiro superior al saldo disponible en esa
fecha. Los aportes a metas y pagos programados siguen la misma política de
actualización o anulación vinculada.

Crear pagos de deuda, pagos de obligaciones o movimientos del fondo exige un
`Idempotency-Key` UUID. Repetir la misma solicitud con la misma clave devuelve
el registro original sin volver a modificar saldos; reutilizarla con otros
datos produce un conflicto. La misma restricción única que protege los
movimientos manuales resuelve también estos eventos vinculados.
