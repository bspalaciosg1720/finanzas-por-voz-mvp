# Backlog preparado para la Fase 1

Este backlog no autoriza comenzar desarrollo. Se activa únicamente cuando la
Fase 0 cumple sus criterios de salida.

## Objetivo de la Fase 1

Construir los fundamentos seguros y observables sobre los que se implementarán
los movimientos y el registro por voz.

## Priorización

### P0 — Imprescindible

| ID | Historia técnica | Criterio de aceptación | Dependencia |
|---|---|---|---|
| F1-01 | Inicializar monorepo | Mobile y API ejecutan localmente | Alcance aprobado |
| F1-02 | Configurar CI | Lint, tipos y pruebas en cada cambio | F1-01 |
| F1-03 | Configurar ambientes | Desarrollo y pruebas no comparten secretos | F1-01 |
| F1-04 | Crear PostgreSQL y migraciones | Primera migración sube y baja correctamente | F1-01 |
| F1-05 | Registrar usuario | Correo único y contraseña segura | F1-04 |
| F1-06 | Iniciar y cerrar sesión | Tokens rotatorios y revocables | F1-05 |
| F1-07 | Recuperar contraseña | Token de un solo uso con expiración | F1-05 |
| F1-08 | Obtener perfil | Un usuario solo consulta sus datos | F1-06 |
| F1-09 | Crear categorías base | Semilla idempotente en español | F1-04 |
| F1-10 | Implementar design tokens | Colores, tipografía y espaciado centralizados | Diseño validado |
| F1-11 | Construir navegación móvil | Cinco secciones y estados accesibles | F1-10 |
| F1-12 | Integrar monitoreo de errores | Errores correlacionados sin datos sensibles | F1-02 |

### P1 — Importante

| ID | Historia técnica | Criterio de aceptación | Dependencia |
|---|---|---|---|
| F1-13 | Verificar correo | Enlace expira y no puede reutilizarse | F1-05 |
| F1-14 | Gestionar sesiones | Usuario revoca otro dispositivo | F1-06 |
| F1-15 | Crear categorías personalizadas | Nombre único por usuario activo | F1-09 |
| F1-16 | Configurar logs estructurados | Incluyen correlación, no tokens ni descripciones | F1-12 |
| F1-17 | Automatizar backups | Restauración probada en entorno aislado | F1-04 |

### P2 — Puede esperar

- Inicio con Google.
- Inicio con Apple.
- Avatar.
- Personalización visual.
- Localización adicional.

## Definition of Ready

Una historia puede comenzar cuando:

- tiene problema y usuario identificados;
- posee criterios de aceptación comprobables;
- no depende de una decisión de investigación pendiente;
- tiene diseño o contrato suficiente;
- incluye impacto de seguridad y privacidad;
- cabe dentro de un ciclo corto de implementación.

## Definition of Done

Una historia termina cuando:

- cumple criterios de aceptación;
- tiene pruebas proporcionales al riesgo;
- pasa análisis de tipos, formato y seguridad;
- funciona en desarrollo y staging;
- incluye estados de carga, vacío y error;
- actualiza documentación relevante;
- no introduce datos sensibles en logs o analítica.

## Riesgos de ejecución

| Riesgo | Control |
|---|---|
| Empezar backend antes de cerrar contratos | Diseñar contratos durante refinamiento |
| Acoplarse a un proveedor de voz | Definir interfaz de Speech-to-Text |
| Crear abstracciones innecesarias | Modularidad por dominio, no capas genéricas |
| Ignorar zonas horarias | Guardar UTC y conservar zona del usuario |
| Duplicar movimientos | Idempotency key desde el primer endpoint |
| Filtrar datos entre usuarios | Pruebas de autorización obligatorias |

