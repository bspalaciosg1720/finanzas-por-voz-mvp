# Flujos del MVP

## Flujo de activación

```text
Bienvenida
→ Crear cuenta
→ Verificar correo
→ Elegir país, moneda y zona horaria
→ Conocer el registro por voz
→ Registrar un movimiento de prueba
→ Ver dashboard
```

El permiso de micrófono se solicita cuando el usuario intenta usarlo, no al abrir
la aplicación por primera vez.

## Registro por voz

```text
Inicio
→ Pulsar micrófono
→ Conceder permiso, si aplica
→ Escuchar
→ Detectar silencio o pulsar detener
→ Transcribir
→ Interpretar
→ Mostrar confirmación
→ Confirmar
→ Guardar
→ Actualizar dashboard y presupuesto
```

### Estados necesarios

- listo;
- solicitando permiso;
- escuchando;
- procesando;
- interpretación completa;
- interpretación dudosa;
- sin conexión;
- audio no reconocido;
- error recuperable;
- guardado;
- pendiente de sincronización.

## Corrección de interpretación

```text
Confirmación
→ Tocar monto, tipo, categoría, descripción o fecha
→ Editar en modal inferior
→ Aplicar
→ Revisar confirmación actualizada
→ Guardar
```

## Registro manual

```text
Inicio o Movimientos
→ Pulsar “+”
→ Elegir gasto o ingreso
→ Introducir monto
→ Seleccionar categoría
→ Añadir descripción y fecha opcionales
→ Guardar
```

## Presupuesto

```text
Presupuesto
→ Crear presupuesto
→ Elegir categoría
→ Definir límite mensual
→ Definir alerta, 80% por defecto
→ Guardar
→ Ver progreso
```

## Recuperación de errores

| Situación | Respuesta |
|---|---|
| Permiso denegado | Explicar motivo y ofrecer ajustes o entrada manual |
| Sin voz detectada | Permitir intentar de nuevo |
| Usuario no desea reintentar | Ofrecer formulario manual compacto |
| Sin internet | Conservar audio temporal o usar entrada manual |
| Monto ausente | Preguntar únicamente por el monto |
| Dos montos | Mostrar alternativas |
| Categoría incierta | Sugerir hasta tres categorías |
| Error al guardar | Conservar borrador y reintentar |
| Petición duplicada | Devolver el movimiento ya creado |
