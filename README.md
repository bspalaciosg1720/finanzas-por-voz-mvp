# Finanzas por Voz

MVP móvil para registrar ingresos y gastos mediante lenguaje natural.

## Estado

El desarrollo interno de las fases 1 a 5 está completo: autenticación,
movimientos, voz con confirmación, presupuestos, metas, reportes, exportaciones,
notificaciones y recordatorios. El proyecto se encuentra en la **Fase 6:
calidad, privacidad, observabilidad y lanzamiento**.

La publicación todavía requiere infraestructura y validaciones externas:
PostgreSQL de staging, credenciales de transcripción y notificaciones, builds en
dispositivos físicos, CI remoto, revisión legal y pruebas con usuarios. Consulta
[Requisitos para finalizar](docs/roadmap/requisitos-para-finalizar.md).

## Documentación

- [Brief de producto](docs/producto/01-brief-producto.md)
- [Hipótesis y experimentos](docs/producto/02-hipotesis-experimentos.md)
- [Investigación con usuarios](docs/investigacion/01-plan-entrevistas.md)
- [Guion de prueba del prototipo](docs/investigacion/02-prueba-usabilidad.md)
- [Flujos del MVP](docs/ux/01-flujos-mvp.md)
- [Métricas del MVP](docs/producto/03-metricas.md)
- [Backlog de la Fase 0](docs/roadmap/fase-0.md)
- [Prototipo navegable](prototype/README.md)
- [Dataset inicial de voz](dataset/README.md)
- [Protocolo de sesiones](docs/investigacion/06-protocolo-sesion.md)
- [Validación técnica del parser](validation/README.md)
- [Estado del proyecto](docs/roadmap/estado-proyecto.md)
- [Backlog preparado para la Fase 1](docs/roadmap/backlog-fase-1.md)
- [Mapa del recorrido](docs/ux/02-mapa-recorrido.md)
- [Decisiones de producto](docs/producto/04-decisiones.md)
- [Analizador de sesiones](research/README.md)
- [Filtro de participantes](docs/investigacion/08-filtro-participantes.md)
- [Consentimiento de investigación](docs/investigacion/09-consentimiento.md)
- [Kit de reclutamiento](docs/investigacion/10-kit-reclutamiento.md)
- [Checklist del piloto](docs/investigacion/11-checklist-piloto.md)
- [Revisión de accesibilidad](docs/ux/03-accesibilidad.md)
- [Contrato preliminar de API](contracts/README.md)
- [ADR: monolito modular](docs/architecture/adr-001-modular-monolith.md)
- [ADR: confirmación de voz](docs/architecture/adr-002-voice-confirmation.md)
- [Aceptación de riesgo de la Fase 0](docs/decisions/risk-acceptance-phase-0.md)
- [Plan de la Fase 1](docs/roadmap/fase-1.md)
- [Decisión de salida de la Fase 1](docs/decisions/phase-1-exit.md)
- [Plan de la Fase 2](docs/roadmap/fase-2.md)
- [Auditoría de dependencias](docs/security/dependency-audit.md)
- [Observabilidad](docs/architecture/observability.md)
- [Backup y restauración](docs/operations/backup-restore.md)
- [Recuperación de cuenta](docs/architecture/account-recovery.md)

## Aplicaciones

- [API FastAPI](apps/api/README.md)
- [Aplicación móvil Expo](apps/mobile/README.md)

## Decisión de alcance

La primera versión validará tres trabajos:

1. Registrar un movimiento por voz.
2. Entender el estado financiero del mes.
3. Detectar el avance de un presupuesto por categoría.

Las integraciones bancarias, el OCR, las recomendaciones mediante IA, los
presupuestos compartidos y el modo empresarial quedan fuera del MVP.
