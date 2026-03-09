# El Viaje de la Información: Storytelling de la Data en Asistente Tablero

Este documento narra cómo los datos de miles de clientes bancarios se transforman en decisiones estratégicas a través de nuestro pipeline de análisis.

---

## 1. El Origen: La Voz del Cliente (Ingesta)
Todo comienza con una interacción. Cada mensaje que un cliente envía a través del chatbot es capturado y almacenado. Sin embargo, los datos crudos son ruidosos.
- **Limpieza de Identidad:** Eliminamos duplicados y protegemos la integridad de cada ID de conversación (`thread_id`).
- **Sentimiento Dinámico:** No solo leemos palabras; usamos NLP para entender si el cliente está frustrado, neutral o satisfecho, propagando este sentimiento a lo largo de toda la charla.

## 2. El Refinado: Protección de la Intención (NLP & YAML)
Aquí es donde ocurre la magia. Hemos implementado una lógica de **"Prioridad de Intención"** para asegurar que la voz real del usuario no se pierda:
- **Intento sobre Ruido:** Si un usuario saluda y luego pide su saldo, ignoramos el "Hola" como categoría principal y priorizamos la "Consulta de Saldo".
- **Blindaje contra Encuestas:** Las etiquetas técnicas como `[survey]` solían "ensuciar" las categorías. Ahora, nuestro motor de reglas protege el mensaje original: solo si no hay un tema de negocio detectado, clasificamos el mensaje como "Encuesta".

## 3. El Embudo Estratégico (Strategic Funnel)
Visualizamos la salud del asistente a través de un funnel de 4 etapas críticas:
1. **Interacciones Totales:** El 100% de la carga que recibe el sistema.
2. **Conversaciones Activas:** Filtramos el ruido. Solo contamos hilos con más de 3 mensajes humanos, donde realmente hay una intención de diálogo.
3. **Autogestión (Self-Service):** ¿Cuántos de esos usuarios resolvieron su duda sin ser redirigidos a un humano? Aquí medimos la autonomía de la IA.
4. **Utilidad Real:** El paso final. De los que se autogestionaron, ¿cuántos marcaron la respuesta como "Útil"? Este es el verdadero éxito.

## 4. Las Ventanas de Observación (Vistas del Dashboard)
Nuestra data se narra desde diferentes ángulos para cubrir todas las necesidades del negocio:

- **Dashboard (Resumen General):** La vista ejecutiva. Aquí vive el Funnel, el Heatmap de actividad por horas y el control de "Gasto de Valor".
- **Categorías & Productos:** El mapa detallado. Permite ver qué temas (Transferencias, Pagos, Tarjetas) dominan la conversación y cómo se siente el usuario respecto a cada producto.
- **Gaps y Redirecciones:** La vista de mejora continua. Revela qué no sabe la IA y a dónde enviamos a los usuarios cuando fallamos. Es la brújula para el equipo de contenido.
- **Analítica Profunda (Deep Dive):** Un zoom a los volúmenes humanos por categoría y la relación entre el tema de la consulta y la utilidad final percibida.
- **HITL (Entrenamiento):** El puente humano. Permite a los expertos corregir y etiquetar mensajes para que el sistema aprenda y sea más preciso cada día.

## 5. La Taxonomía del Negocio (Categorización)
Para que la historia sea coherente, todos hablamos el mismo idioma. Nuestra data se organiza en:

### Macro-categorías Principales:
- **Transferencias:** Envíos de dinero, Transfiya, fallos en transferencias.
- **Pagos:** Servicios públicos, créditos, impuestos, PSE/QR.
- **Tarjetas:** Consultas y gestiones de Tarjetas de Crédito y Débito.
- **Créditos y Préstamos:** Solicitudes, cuotas, intereses y libranzas.
- **Cuentas y Productos:** Saldos, aperturas, cancelaciones y CDTs.
- **Seguridad y Accesos:** Claves, fraudes, bloqueos y tokens.
- **App y Canales:** Problemas técnicos, canales físicos y digitales.
- **Gestión Personal:** Actualización de datos, certificados y radicados.
- **Información:** PQRs, vacantes, asesoría comercial y dudas generales.
- **Experiencia:** Recomendaciones, usabilidad y feedback general.

### Productos del Ecosistema:
- **Tarjetas:** Crédito, Débito.
- **Cuentas:** Ahorros, Corriente, CDT, Fondos de Inversión.
- **Créditos:** Libre Inversión, Vivienda, Vehículo, Libranza, Estudiantil, Empresarial, Rotativo.
- **Otros:** Seguros, Leasing, Remesas.

## 6. El Gasto de Valor
Nuestra métrica de control de calidad más estricta. Un **"Gasto de Valor"** ocurre cuando un hilo de conversación falla doblemente:
- La IA no pudo resolver (Gap).
- El usuario nos calificó negativamente (No Útil).
Estos casos son nuestra prioridad #1 para el entrenamiento del modelo.

---

Este ecosistema asegura que cada clic en el dashboard esté respaldado por una lógica que prioriza lo que el cliente **realmente necesita**, transformando datos fríos en una historia clara de eficiencia y mejora continua.
