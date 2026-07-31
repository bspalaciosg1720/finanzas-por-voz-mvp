# Estado del proyecto

Actualizado: 30 de julio de 2026.

## Fase actual

**Fase 6 — Calidad, privacidad, observabilidad y lanzamiento.**

El roadmap maestro comprende siete fases, de la 0 a la 6. Quedan cuatro fases
por completar.

Primer bloque completado: monorepo, API ejecutable, base Expo y controles de
calidad iniciales.

Segundo bloque completado: persistencia SQLAlchemy, migración Alembic, esquema
PostgreSQL, usuarios, categorías y sesiones JWT rotatorias. La ejecución real
contra PostgreSQL queda pendiente porque Docker no está instalado en el equipo;
el SQL del dialecto PostgreSQL y el ciclo upgrade/downgrade fueron verificados.

Tercer bloque completado: logging JSON, request ID, errores uniformes,
endurecimiento de staging y workflow CI. El workflow fue validado localmente,
pero su ejecución remota requiere publicar el repositorio en GitHub.

Cuarto bloque completado: sesiones por dispositivo y procedimiento automatizado
de backup/restauración. La prueba local de API está completa; la restauración
PostgreSQL se ejecutará en CI cuando el repositorio sea publicado.

Quinto bloque completado: verificación de correo, recuperación de contraseña,
tokens de acción con expiración y entrega desacoplada mediante archivo local o
SMTP.

Sexto bloque completado: autenticación móvil, almacenamiento seguro, rutas
protegidas, rotación automática y enlaces profundos de recuperación.

La Fase 1 fue aprobada para salida. Las verificaciones remotas de CI y staging
permanecen como condición obligatoria antes de cualquier despliegue.

La Fase 2 quedó completada con el dominio y CRUD idempotente de movimientos,
aislamiento por usuario, filtros, paginación, experiencia móvil y estados de
conexión. Incluye un dashboard real de saldo, ingresos, gastos, comparación
mensual, categoría principal y movimientos recientes. La API y la aplicación
móvil fueron validadas con 32 pruebas backend, lint y TypeScript.

La Fase 3 inició con un contrato que separa interpretación y persistencia. Ya
interpreta monto, tipo, categoría, descripción y fecha; devuelve confianza
heurística y ambigüedades, exige confirmación y no guarda automáticamente. La
suite local suma 36 pruebas aprobadas.

La captura móvil de voz ya gestiona permisos, errores, cancelación, un máximo de
15 segundos y eliminación del archivo temporal. Expo Doctor aprobó 21 de 21
controles. El audio aún no se envía ni transcribe; el adaptador de Speech-to-Text
es el siguiente bloque.

El flujo de confirmación ya funciona con una transcripción editable: interpreta,
permite corregir tipo, monto, categoría, descripción y fecha, y guarda mediante
idempotencia. La conexión con un proveedor remoto continúa bloqueada hasta
disponer de una credencial gestionada de servidor. Los demás requisitos externos
para terminar y lanzar el MVP están inventariados en
`docs/roadmap/requisitos-para-finalizar.md`.

El audio está limitado a 15 segundos y 5 MB. Las 150 frases sintéticas de Fase
0 forman parte de la regresión automatizada; la suite suma 186 pruebas
aprobadas.

La aplicación ya carga audio mediante multipart hacia un endpoint autenticado.
El backend valida formato, contenido y tamaño, cierra el archivo en todos los
resultados y usa adaptadores intercambiables deshabilitado/falso. El móvil borra
su archivo tras éxito o error y mantiene la alternativa editable. La suite suma
190 pruebas aprobadas.

La migración 0004 añade métricas de voz sin audio, transcripción, monto ni
descripción. Mide éxito, abandono, duración, ambigüedades y campos corregidos.
La finalización es idempotente y aislada por usuario. La suite suma 193 pruebas
aprobadas.

La Fase 4 inició en paralelo con presupuestos mensuales por categoría. El
backend incluye CRUD, aislamiento, umbral configurable, progreso mensual según
zona horaria y estados normal/advertencia/excedido. La migración 0005 fue
verificada y la suite suma 196 pruebas aprobadas.

La pantalla móvil de presupuestos ya incluye creación, edición, eliminación,
barras de progreso, umbral editable, estados normal/advertencia/excedido y
estados vacío/carga/error. TypeScript y la regresión backend permanecen limpios.

Las alertas de presupuesto se persisten una sola vez por presupuesto, mes y
nivel, incluso ante reintentos idempotentes. La aplicación muestra alertas no
leídas y permite descartarlas. La migración 0006 fue verificada y la suite suma
198 pruebas aprobadas.

El backend de metas de ahorro permite crear, editar y archivar metas, registrar
y retirar aportes, calcular avance y completar o reactivar automáticamente.
Restringe cada meta a la moneda principal y a su propietario. La migración 0007
fue verificada y la suite suma 201 pruebas aprobadas.

La sección móvil Presupuesto ahora permite alternar entre presupuestos y metas
sin superar cinco pestañas principales. Las metas incluyen creación, edición,
archivado, aportes, progreso, fecha objetivo y estados vacío/carga/error.

La implementación interna de la Fase 4 quedó completa. El backend registra,
lista y revoca dispositivos push sin exponer sus tokens en las respuestas; el
móvil solicita consentimiento explícito y registra el token únicamente cuando
existe un `projectId` válido. La entrega está desacoplada mediante adaptadores
deshabilitado/falso. La migración 0008 fue verificada, la suite suma 204 pruebas
aprobadas, TypeScript está limpio y Expo Doctor aprobó 21 de 21 controles.

La recepción de una notificación remota continúa pendiente de credenciales
Expo/EAS, un build de desarrollo y un dispositivo físico. Con esta salvedad, el
desarrollo activo pasa a la Fase 5.

La Fase 5 comenzó con `GET /reports/summary`: genera periodos diarios,
semanales, mensuales y anuales en la zona horaria del usuario, y devuelve
ingresos, gastos, balance, cantidad de movimientos y distribución de gastos por
categoría. Respeta moneda, propiedad, confirmación y borrado lógico. La
pantalla móvil permite alternar periodos y muestra comparación, balance y
categorías. La API también ofrece una exportación CSV UTF-8 compatible con
hojas de cálculo y consistente con el periodo seleccionado. Las exportaciones
Excel y PDF generan documentos nativos con los mismos límites, zona horaria,
moneda y aislamiento; las pruebas abren el libro `.xlsx` y validan el documento
PDF generado. La regresión completa suma 210 pruebas aprobadas y TypeScript
permanece limpio.

Los recordatorios de Fase 5 ya tienen preferencias revocables, horario local,
activación independiente para gastos diarios, ingresos semanales y alertas de
presupuesto, además de una evaluación que evita avisos cuando existe un
movimiento y deduplica por usuario, tipo y periodo. La migración 0009 fue
verificada y Perfil permite administrar las preferencias. En ese punto la suite
sumaba 214 pruebas aprobadas.

La implementación interna de la Fase 5 quedó completa. El comando
`finanzas-reminders` evalúa únicamente usuarios con preferencias activas,
entrega recordatorios diarios, semanales y alertas de presupuesto, y conserva
pendientes ante ausencia o fallo del canal. Los estados `pending/delivered`
evitan consumir avisos antes de confirmar su envío. La suite suma 217 pruebas
aprobadas; la activación del scheduler y el proveedor push real se validarán en
staging.

## Progreso por entregable

| Entregable | Estado |
|---|---|
| Brief y alcance | Completo |
| Hipótesis y experimentos | Completo |
| Métricas | Completo |
| Flujos | Completo |
| Mapa de recorrido hipotético | Completo, pendiente validar |
| Prototipo navegable | Completo |
| Protocolo de investigación | Completo |
| Filtro, consentimiento y reclutamiento | Completo |
| Checklist de sesión piloto | Completo |
| Revisión automatizada de accesibilidad | Completo |
| Dataset sintético | Completo |
| Línea base del parser | Completo |
| Contrato API preliminar | Completo, pendiente validación semántica en CI |
| Entrevistas con usuarios | Pendiente |
| Pruebas moderadas | Pendiente |
| Dataset de lenguaje real | Pendiente |
| Síntesis de evidencia | Pendiente |
| Decisión de salida | Pendiente |

## Semáforo

- **Viabilidad técnica preliminar:** verde.
- **Usabilidad:** amarillo, sin participantes.
- **Deseabilidad:** amarillo, sin entrevistas.
- **Privacidad:** amarillo, requiere validación de percepción y revisión legal.
- **Alcance:** verde provisional.

## Bloqueo para cerrar la fase

La Fase 0 se cerró condicionalmente mediante aceptación formal de riesgo. La
investigación con participantes continúa pendiente y debe ejecutarse en paralelo.

## Próxima decisión

Después de al menos cinco pruebas y ocho entrevistas:

```text
¿Cumple criterios?
├── Sí → iniciar Fase 1
├── Parcial → iterar prototipo una semana
└── No → redefinir segmento o propuesta
```
