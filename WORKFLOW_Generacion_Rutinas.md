# Workflow — Generación Manual de Rutinas
## Cómo usar Claude para entregar una rutina completa a cada cliente

---

## RESUMEN DEL FLUJO

```
Cliente compra en Shopify
        ↓
Le llega el formulario automáticamente (Google Forms)
        ↓
Vos recibís la respuesta por email / Google Sheets
        ↓
Abrís una conversación nueva en claude.ai
        ↓
Pegás el MENSAJE DE INICIO (Paso 1)
        ↓
Claude muestra el análisis de salud → vos validás
        ↓
Claude genera el .docx y el .html
        ↓
Descargás los archivos → los enviás al cliente
```

**Tiempo estimado por cliente: 5-10 minutos**

---

## PASO 1 — ABRIR UNA CONVERSACIÓN NUEVA

Siempre empezar una conversación **nueva** en claude.ai para cada cliente.
No reusar conversaciones anteriores — Claude no mezcla contextos entre clientes.

Ir a: **claude.ai → New conversation**

---

## PASO 2 — PEGAR EL MENSAJE DE INICIO

Copiar el bloque completo de abajo, reemplazar los campos entre `[ ]` con los datos reales del formulario, y enviarlo como primer mensaje.

---

### ✂️ MENSAJE DE INICIO — COPIAR DESDE AQUÍ

```
Sos un asistente especializado en programación de entrenamiento físico personalizado con enfoque en salud y evidencia científica.

Tu tarea es analizar las respuestas del formulario de un cliente y generar dos archivos:
1. Un documento Word (.docx) — plan explicativo con contexto de salud, justificación científica, estructura de sesión, cardio, nutrición y señales de alerta.
2. Un archivo HTML interactivo — rutina visual con ejercicios por bloque, progresión Mes 1/Mes 2, calentamiento collapsible y botones de video.

PRINCIPIO FUNDAMENTAL: antes de seleccionar cualquier ejercicio, analizar contraindicaciones. Ningún ejercicio que pueda agravar una condición declarada puede aparecer en la rutina. Si el cliente menciona un ejercicio favorito que está contraindicado, excluirlo y explicar por qué en el plan.

ESPECIFICACIONES TÉCNICAS:
- Docx: Arial, colores violeta (#3B0764 H1 / #7C3AED H2 / #F3E8FF filas alternas / #EDE9FE cajas info / #FEE2E2 cajas alerta)
- HTML: mismo estilo que el template de Luz (dark theme, Roboto, colores bloque-a #a78bfa / bloque-b #f5a35a)
- Exactamente 5 ejercicios por bloque
- Tono: español rioplatense, cercano pero con fundamento científico
- Cada recomendación clave tiene su referencia de PubMed o journal indexado

VIDEOS DISPONIBLES EN BIBLIOTECA (usar estas URLs exactas):
- Calentamiento Tren Inferior: https://youtube.com/shorts/2EL3xEkT0a8
- Calentamiento Tren Superior: https://youtube.com/shorts/idM-SRw55SA
- Leg Press Bilateral: https://youtube.com/shorts/hyubDuOS7WM
- Extensión de Rodilla en Máquina: https://youtube.com/shorts/iQ92TuvBqRo
- Curl de Isquiotibiales (sentada): https://youtube.com/shorts/_lgE0gPvbik
- Hip Thrust: https://youtube.com/shorts/_i6qpcI1Nw4
- Abducción de cadera en máquina: https://youtube.com/shorts/ZBQk4FRQdFQ
- Elevación de pantorrillas bilateral: https://youtube.com/shorts/_OewEscCsbo
- Pull Down / Jalón al Pecho: https://youtube.com/shorts/bNmvKpJSWKM
- Dominada Asistida: https://youtube.com/shorts/_EtpfDHPfHc
- Remo con Mancuerna (1 brazo): https://youtube.com/shorts/QEamGpgkTSo
- Press con Mancuernas: https://youtube.com/shorts/WbCEvFA0NJs
- Face Pull con Polea: https://youtube.com/shorts/IeOqdw9WI90
- Curl de Bíceps con Mancuernas: https://youtube.com/shorts/MKWBV29S6c0
- Fondos en Paralelas: https://youtube.com/shorts/oVs-HluNKP0

Si el plan requiere un ejercicio que no está en esta lista, no incluir url y el sistema hará búsqueda automática en YouTube.

ANTES DE GENERAR LOS ARCHIVOS: mostrame un resumen del análisis de salud (máximo 10 líneas) con las condiciones detectadas, contraindicaciones aplicadas y ejercicios excluidos. Esperá mi confirmación antes de proceder.

---

RESPUESTAS DEL FORMULARIO:

Nombre: [NOMBRE COMPLETO]
Edad: [EDAD]
Altura: [CM]
Peso actual: [KG]
Objetivo principal: [bajar porcentaje de grasa / recomposición corporal / aumentar masa muscular]
Frecuencia de entrenamiento: [baja 2 días / media 3-4 días / alta 5+ días]
Nivel de experiencia: [principiante / intermedio / avanzado]
Equipamiento disponible: [gimnasio completo / mancuernas en casa / bandas / peso corporal]
Condiciones de salud o lesiones: [DESCRIPCIÓN LIBRE DEL CLIENTE]
Tipos de entrenamiento y ejercicios que le gustan: [TEXTO LIBRE]
Restricciones alimentarias: [sin gluten / sin lácteos / vegano / keto / ninguna / otras]
Hábitos actuales de alimentación: [DESCRIPCIÓN LIBRE]
```

---

### ✂️ FIN DEL MENSAJE DE INICIO

---

## PASO 3 — VALIDAR EL ANÁLISIS DE SALUD

Claude va a responder primero con un resumen de 10 líneas con:
- Condiciones detectadas
- Contraindicaciones aplicadas
- Ejercicios excluidos y sus reemplazos

**Revisá este resumen antes de confirmar.** Si algo no tiene sentido o querés hacer un ajuste, decíselo antes de que genere los archivos.

Ejemplos de respuesta tuya para continuar:
- `"Todo correcto, procedé"`
- `"Cambiá el curl de isquiotibiales por la versión acostada, no sentada"`
- `"Agregá una advertencia extra sobre el hombro, tuvo una lesión hace 3 meses"`

---

## PASO 4 — DESCARGA DE ARCHIVOS

Claude va a generar ambos archivos en secuencia. Cuando terminen de procesarse aparece el botón de descarga para cada uno.

Descargar en este orden:
1. `Plan_Entrenamiento_[Nombre].docx`
2. `Rutina_[Nombre].html`

Guardarlos en tu carpeta de clientes con el nombre del cliente y la fecha.

---

## PASO 5 — ENVÍO AL CLIENTE

Opciones de entrega:
- **Email directo** — adjuntar ambos archivos
- **Google Drive** — subir a una carpeta compartida y enviar el link
- **WeTransfer** — para archivos más pesados si sumás más material

El cliente puede abrir el `.html` directamente en cualquier navegador — no necesita instalar nada. El `.docx` se abre con Word, Google Docs o cualquier procesador de texto.

---

## CUANDO AGREGAR UN VIDEO NUEVO A LA BIBLIOTECA

Cuando grabés un tutorial nuevo y lo subas a YouTube:

1. Abrí el archivo `PROMPT_Generador_Rutinas.md`
2. Buscá la sección **"Mapa de videos disponibles"**
3. Agregá la línea con el ejercicio y la URL
4. La próxima vez que uses el prompt, incluí la URL nueva en el bloque de videos del mensaje de inicio

---

## CHEQUEO RÁPIDO ANTES DE ENVIAR

Antes de mandar los archivos al cliente, revisar en 2 minutos:

- [ ] El nombre del cliente está correcto en el título del HTML y el docx
- [ ] Los ejercicios del HTML corresponden a las condiciones declaradas (ninguno contraindicado)
- [ ] Los botones "Ver tutorial" funcionan (hacer click en uno o dos)
- [ ] El docx abre sin errores en Word o Google Docs
- [ ] La estructura semanal coincide con la frecuencia elegida por el cliente

---

## MANEJO DE CASOS ESPECIALES

**Si el cliente declara una condición grave (enfermedad autoinmune descompensada, cirugía reciente, cardiopatía, etc.)**
Claude va a incluir una alerta roja al inicio del documento indicando que el plan no debe iniciarse sin autorización médica. Revisá ese bloque antes de enviar y decidís si agregar una nota personal tuya.

**Si el cliente no completó algún campo del formulario**
Indicárselo a Claude en el mensaje de inicio:
`"El campo de condiciones de salud quedó vacío, asumir sin condiciones declaradas"`

**Si el cliente pidió ejercicios específicos que están contraindicados**
Claude los va a excluir y explicar por qué en el plan. Ese texto ya queda en el documento — no hace falta que lo expliques vos por separado.

**Si necesitás hacer un ajuste después de que Claude generó los archivos**
Decile exactamente qué cambiar:
`"En el Bloque A del Mes 2, reemplazá el Hip Thrust con Barra por Elevación de pantorrillas con carga"`
Claude regenera solo el archivo afectado.

---

## CUANDO ESCALE Y QUIERAS AUTOMATIZAR

Cuando el volumen de clientes justifique automatizar, el flujo ya está diseñado para eso:

1. El prompt del mensaje de inicio → se convierte en el system prompt de la API
2. Los datos del formulario → se inyectan automáticamente desde Google Sheets vía n8n
3. La generación de archivos → corre en un servidor con el código ya existente
4. La entrega → automatizada por email

Todo el trabajo ya está hecho. La automatización en ese momento es conectar las piezas, no rediseñar el proceso.

---

*Workflow v1.0 — Para actualizar la biblioteca de videos o las reglas de contraindicaciones, editar el archivo `PROMPT_Generador_Rutinas.md`*
