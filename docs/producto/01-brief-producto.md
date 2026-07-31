# Brief de producto

## Problema

Muchas personas intentan controlar sus finanzas, pero abandonan el hábito porque
registrar cada movimiento exige recordar datos y completar formularios. Las
aplicaciones existentes suelen pedir demasiados pasos justo después de una compra.

## Propuesta de valor

**Habla, confirma y controla tus finanzas.**

La persona dice una frase natural, la aplicación extrae el tipo de movimiento,
monto, categoría, descripción y fecha, y presenta una confirmación compacta antes
de guardar.

## Usuario inicial

Personas de 22 a 45 años que:

- administran sus finanzas personales desde el teléfono;
- reciben ingresos en pesos colombianos;
- quieren controlar gastos, pero no mantienen hojas de cálculo;
- realizan varios pagos pequeños durante la semana;
- ya usan notas, chats consigo mismas o aplicaciones bancarias para recordar pagos.

El MVP se enfocará inicialmente en Colombia, español y COP. Esta restricción
reduce ambigüedades de moneda, expresiones numéricas y formatos regionales.

## Trabajo principal del usuario

> Cuando hago un pago o recibo dinero, quiero registrarlo inmediatamente con el
> menor esfuerzo posible, para saber cuánto tengo y en qué estoy gastando sin
> reconstruir todo al final del mes.

## Principios de producto

1. Registrar debe tomar menos tiempo que abrir una nota.
2. Ninguna interpretación dudosa se guarda silenciosamente.
3. El usuario siempre conserva el control sobre monto, tipo, fecha y categoría.
4. La voz es el atajo principal, no la única forma de entrada.
5. Los resúmenes deben responder preguntas, no decorar el dashboard.
6. La privacidad del audio debe explicarse con lenguaje sencillo.

## Alcance funcional del MVP

### Imprescindible

- Registro, inicio de sesión y recuperación de contraseña.
- CRUD de ingresos y gastos.
- Dictado, transcripción, interpretación y confirmación.
- Categorías predeterminadas y personalizadas.
- Dashboard mensual.
- Búsqueda y filtros básicos.
- Presupuestos mensuales por categoría.
- Alertas al 80% y 100%.
- Metas de ahorro básicas.
- Reporte mensual y exportación CSV.
- Sincronización en la nube.

### Después del MVP

- Google y Apple OAuth.
- PDF y Excel con diseño avanzado.
- OCR de facturas.
- Integraciones bancarias.
- Presupuestos familiares.
- Múltiples monedas con conversión.
- Recomendaciones financieras.
- Aplicación web y modo empresarial.

## Historias críticas

### Registro por voz

Como usuario, quiero decir “gasté 18 mil en almuerzo” y revisar una confirmación,
para guardar el movimiento sin completar un formulario.

### Corrección

Como usuario, quiero tocar cualquier dato interpretado y corregirlo, para confiar
en que mi historial financiero es exacto.

### Consulta mensual

Como usuario, quiero ver saldo, ingresos, gastos y categoría principal del mes,
para entender mi situación en pocos segundos.

### Presupuesto

Como usuario, quiero definir un límite de alimentación y recibir una alerta antes
de superarlo, para ajustar mis decisiones durante el mes.

## Criterios no funcionales iniciales

- Confirmación visible en menos de 5 segundos bajo una conexión normal.
- Exactitud del monto de al menos 95% en el conjunto de prueba.
- Interfaz accesible con contraste WCAG AA.
- Operaciones monetarias sin números de punto flotante.
- Separación estricta de datos por usuario.
- Idempotencia para evitar movimientos duplicados.
- Audio eliminado después del procesamiento, salvo consentimiento explícito.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---:|---|
| Monto interpretado incorrectamente | Alto | Confirmación, umbrales y pruebas regionales |
| Usuario evita hablar en público | Alto | Entrada manual y textual igual de accesible |
| Flujo supera cinco segundos | Alto | Transcripción parcial y confirmación compacta |
| Clasificación poco confiable | Medio | Corrección en un toque y aprendizaje posterior |
| Desconfianza sobre privacidad | Alto | Consentimiento y eliminación automática de audio |
| Alcance excesivo | Alto | Criterios de entrada y salida de cada fase |

## Preguntas abiertas

- ¿En qué contextos reales las personas sí están dispuestas a hablar?
- ¿Prefieren confirmar siempre o guardar automáticamente con alta confianza?
- ¿“Saldo actual” debe ser calculado por movimientos o configurado inicialmente?
- ¿Qué expresiones locales para montos se deben soportar?
- ¿Qué categorías generan más correcciones?
- ¿Qué recordatorios se perciben como útiles y cuáles como intrusivos?

