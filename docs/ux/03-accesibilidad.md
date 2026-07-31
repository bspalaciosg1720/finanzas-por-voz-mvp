# Revisión de accesibilidad del prototipo

## Alcance

Revisión previa al piloto basada en WCAG AA para los elementos disponibles en el
prototipo. No sustituye pruebas con tecnologías de asistencia ni usuarios.

## Verificaciones implementadas

- Contraste programático de los pares de color principales.
- Foco visible en botones, campos y selectores.
- Controles interactivos críticos con altura mínima de 48 px.
- Etiquetas accesibles para campos editables de la confirmación.
- Campo de monto con `inputmode="numeric"`.
- Error de monto asociado mediante `aria-describedby`.
- Estado inválido mediante `aria-invalid`.
- Región activa para cambios de pantalla.
- Mensajes de estado mediante `role="status"`.
- Reducción de animaciones mediante `prefers-reduced-motion`.
- Tecla Escape para salir de flujos modales en escritorio.
- El significado financiero no depende únicamente del color.

## Verificaciones para el piloto

- [ ] El orden de lectura coincide con el orden visual.
- [ ] La confirmación se comprende sin depender de iconos.
- [ ] Los participantes encuentran el botón del micrófono.
- [ ] Los textos se leen cómodamente con brillo bajo.
- [ ] El flujo funciona con tamaño de fuente aumentado.
- [ ] Los mensajes de error indican cómo recuperarse.
- [ ] La onda de audio no se interpreta como progreso exacto.

## Pruebas posteriores necesarias

- VoiceOver en iOS.
- TalkBack en Android.
- Navegación con teclado en la futura versión web.
- Texto al 200%.
- Contraste en modo oscuro, si se implementa.
- Pruebas con personas con baja visión o dificultades motoras.

## Ejecutar auditoría de contraste

```powershell
python validation/accessibility_audit.py
```

