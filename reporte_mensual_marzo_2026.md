# Reporte Mensual del Asistente Virtual Bancario

**Periodo analizado:** 28 de enero - 3 de marzo de 2026 (35 dias)
**Fecha de generacion:** 29 de marzo de 2026

---

## 1. Periodo Revisado

Este reporte cubre **35 dias de operacion continua** del asistente virtual, desde el 28 de enero hasta el 3 de marzo de 2026. Durante este periodo, el asistente estuvo disponible las 24 horas del dia, los 7 dias de la semana, atendiendo consultas de clientes bancarios sin interrupcion.

El analisis se basa en **326,499 mensajes procesados**, lo que equivale a un promedio de **9,328 mensajes diarios** fluyendo a traves del sistema. Cada dato presentado en este reporte proviene directamente de la base de datos operativa, sin estimaciones ni proyecciones: son numeros reales de interacciones reales.

---

## 2. Que es el Asistente

El asistente virtual es un chatbot bancario impulsado por inteligencia artificial que actua como **primer punto de contacto digital** para los clientes del banco. Su funcion principal es:

- **Resolver consultas** sobre productos bancarios (tarjetas, creditos, cuentas)
- **Guiar procesos** como solicitudes de credito, bloqueos de tarjeta, cambios de clave
- **Derivar inteligentemente** a canales especializados cuando la consulta excede su capacidad
- **Recopilar feedback** a traves de encuestas de satisfaccion post-interaccion

El asistente no reemplaza la atencion humana: la complementa. Funciona como un filtro inteligente que resuelve lo que puede y canaliza lo que no puede hacia el recurso mas apropiado (canales digitales, oficinas fisicas o linea telefonica).

---

## 3. Cuantos Usuarios, Conversaciones y Mensajes Generamos

### El panorama general en numeros

| Metrica | Valor | Contexto |
|---------|-------|----------|
| **Usuarios unicos** | **34,121** | Personas distintas que interactuaron con el asistente |
| **Conversaciones** | **44,369** | Hilos de chat completos iniciados |
| **Mensajes totales** | **326,499** | Incluye mensajes humanos, respuestas del bot y llamadas a herramientas |
| **Mensajes de clientes** | **78,980** | Lo que los usuarios escribieron directamente |
| **Respuestas del bot** | **154,875** | Respuestas generadas por la IA |
| **Operaciones internas** | **92,644** | Llamadas a herramientas del sistema para procesar solicitudes |

### Que significan estos numeros

Cada dia, en promedio, **1,268 conversaciones nuevas** se abrieron y el asistente proceso **2,257 mensajes de clientes**. Esto quiere decir que el asistente esta atendiendo el equivalente a un call center pequeno, pero de forma automatizada y sin tiempos de espera.

De los 34,121 usuarios:

- **27,862 (81.7%)** usaron el asistente una sola vez
- **5,567 (16.3%)** regresaron entre 2 y 3 veces
- **692 (2.0%)** son usuarios recurrentes con 4 o mas conversaciones (el mas activo tuvo 59 conversaciones)

El promedio de **1.3 conversaciones por usuario** indica que la mayoria de clientes llega con una necesidad puntual. Los usuarios recurrentes, aunque son pocos, representan oportunidades de mejora: si necesitan volver, puede ser que no se resolvio su necesidad la primera vez.

### Profundidad de las conversaciones

| Indicador | Valor |
|-----------|-------|
| Promedio de mensajes por conversacion | **7.4** |
| Mediana de mensajes por conversacion | **6.0** |
| Promedio de mensajes humanos por conversacion | **2.3** |
| Mediana de mensajes humanos por conversacion | **2.0** |

La mediana de 2 mensajes humanos por conversacion revela que **la interaccion tipica es corta**: el cliente pregunta, el bot responde, y la conversacion termina (ya sea porque se resolvio o porque el cliente abandono).

### El embudo completo del dashboard

Estas son las metricas exactas que muestra el tablero de control, representando el viaje completo del usuario desde que abre el chat hasta su desenlace:

```
44,369 CONVERSACIONES TOTALES (100%)
    |
    |--- 8,708 Solo Saludo (19.6%) — solo escribieron "hola", "ok", "gracias" (<=5 palabras)
    |
    |--- 10,272 Conversaciones Activas (23.2%) — mas de 2 msgs del usuario, excluyendo solo saludos
    |       |
    |       |--- 441 Auto-servicio (4.3% de activas) — resueltas sin escalar a humanos
    |       |       |--- de estas, 112 confirmaron utilidad por encuesta (25.4%)
    |       |
    |       |--- 9,831 Redirigidas (95.7% de activas) — escaladas a otro canal
    |       |       |--- Digital: 4,878
    |       |       |--- Servilinea: 4,392
    |       |       |--- Oficina: 561
    |       |       |--- 4,764 redirigidas por fallo de la IA (48.5% de redirigidas)
    |       |
    |       |--- 6,050 Sobre un Producto (58.9% de activas) — mencionan producto bancario
    |       |--- 4,222 Consultas Generales (41.1% de activas) — sin producto especifico
    |       |
    |       |--- 4,800 Fallos de la IA (46.7% de activas)
    |               |--- 4,767 por incapacidad del bot
    |               |--- 40 por usuario repite pregunta
    |               |--- 7 por sentimiento negativo predominante
    |               |--- 99.2% de los fallos terminaron en redireccion
    |
    |--- 5,192 Encuestadas (11.7%) — alcanzaron el bloque de encuesta
    |       |--- 4,951 Contestaron (95.4% de encuestadas)
    |       |       |--- 2,541 "Me fue util" (51.3%)
    |       |       |--- 2,410 "No me fue util" (48.7%)
    |       |               |--- 931 tambien detectadas como fallo IA (38.6%)
    |       |--- 241 ignoraron la encuesta
    |
    |--- 3,243 Llegaron Buscando Asesor (7.3%) — su primera intencion fue hablar con humano
    |--- 28,110 Terminaron Pidiendo Asesor (63.4%) — no buscaban asesor pero fueron redirigidos
    |       |--- de estos, 8,896 el bot fallo primero (31.6%)
    |
    |--- 2,323 Gasto de Valor (5.2%) — "no util" + redirigidas = doble fallo
```

### Gasto de valor: donde se pierde la inversion

El "Gasto de Valor" mide el peor escenario: conversaciones donde el cliente dijo que **no le fue util** la informacion Y ademas fue **redirigido** a otro canal. Son 2,323 conversaciones (5.2% del total) donde el asistente no aporto valor.

Las categorias que mas contribuyen al gasto de valor:

| Categoria | Convs | % del gasto |
|-----------|-------|-------------|
| Encuesta | 732 | 31.5% |
| Escalamiento a Asesor | 163 | 7.0% |
| Solicitud de Credito | 150 | 6.5% |
| Productos y Cuentas General | 141 | 6.1% |
| Consulta de Pagos | 124 | 5.3% |
| Saludos | 108 | 4.6% |
| Tarjeta de Credito | 84 | 3.6% |
| Canales Digitales (App/Web) | 82 | 3.5% |
| Falta de Informacion / N/A | 62 | 2.7% |
| Sin Sentido | 61 | 2.6% |

El 31.5% del gasto de valor viene de "Encuesta", lo que indica un sesgo: los clientes insatisfechos son los que mas responden la encuesta negativamente. Las categorias realmente accionables son **Solicitud de Credito** (6.5%), **Productos y Cuentas** (6.1%) y **Consulta de Pagos** (5.3%), donde el bot deberia estar dando mejor informacion.

### Consumo de recursos de IA

| Recurso | Valor |
|---------|-------|
| Tokens de entrada (prompts) | **326,108,315** |
| Tokens de salida (respuestas) | **22,005,365** |
| Tokens totales | **348,113,680** |
| Promedio tokens entrada / msg IA | **2,105.6** |
| Promedio tokens salida / msg IA | **142.1** |
| Tasa de abandono (KPI operacional) | **31.0%** |

El ratio de 15:1 entre tokens de entrada y salida indica que el sistema invierte mucho contexto en cada respuesta. Cada mensaje del bot consume en promedio 2,106 tokens de entrada (el contexto que necesita para responder) y genera solo 142 tokens de salida (la respuesta visible al cliente). Esto refleja la complejidad del sistema de herramientas y el contexto conversacional que se acumula.

---

## 3.1 Como se Calculan las Metricas y Datos que Presentamos

Cada numero en este reporte proviene de un proceso definido y reproducible. Aqui explicamos la metodologia detras de cada metrica para garantizar transparencia total.

### Fuente de datos

Todos los datos se extraen de un archivo CSV de 118 MB (`data-asistente.csv`) que contiene los logs crudos del asistente virtual. Este archivo pasa por un **pipeline ETL de 7 pasos** que limpia, deduplica, categoriza y enriquece los datos antes de almacenarlos en una base SQLite (`chat_data.db`). Cada metrica se calcula sobre esta base procesada.

### Diccionario de metricas

| Metrica | Formula exacta | Numerador | Denominador | Notas |
|---------|---------------|-----------|-------------|-------|
| **Total Conversaciones** | `COUNT(DISTINCT thread_id)` | 44,369 hilos unicos | - | Cada `thread_id` es un hilo de chat completo |
| **Total Mensajes** | `COUNT(*)` en tabla messages | 326,499 registros | - | Incluye los 3 tipos: human, ai, tool |
| **Usuarios Unicos** | `COUNT(DISTINCT client_ip)` | 34,121 IPs unicas | - | Se usa IP como proxy de usuario; un usuario con multiples dispositivos cuenta como multiples |
| **Solo Saludo** | Convs donde TODOS los msgs humanos tienen <= 5 palabras | 8,708 | 44,369 total | Filtra "hola", "ok", "gracias". Excluye mensajes de encuesta |
| **Conversaciones Activas** | Convs con > 2 msgs humanos, excluyendo solo saludo | 10,272 | 44,369 total | Esta es la base para la mayoria de tasas operacionales |
| **Auto-servicio** | Activas que NO aparecen en tabla `referrals` | 441 | 10,272 activas | Si no fue derivada, se considera auto-resuelta |
| **Tasa de Derivacion** | Activas en tabla `referrals` / Activas | 9,831 | 10,272 | La tabla referrals se construye detectando keywords de derivacion en respuestas del bot |
| **Indice de Utilidad** | Encuestas "Me fue util" / Total encuestas contestadas | 2,541 | 4,951 | Solo cuenta respuestas explicitas, no las ignoradas |
| **Fallos de la IA** | Activas con al menos 1 criterio de fallo | 4,800 | 10,272 activas | 3 criterios: incapacidad explicita, repeticion de pregunta, sentimiento negativo predominante |
| **Gasto de Valor** | Convs "no util" AND en referrals | 2,323 | 44,369 total | Interseccion de dos conjuntos independientes |
| **Tasa de Abandono** | Convs con <= 1 msg humano / Total | 13,759 | 44,369 | Diferente al KPI operacional que usa umbral distinto |
| **Tokens Entrada/msg** | `SUM(input_tokens) / COUNT(msgs tipo ai)` | 326,108,315 | 154,875 | Mide el costo computacional por respuesta |

### Como se detectan los fallos

El sistema detecta fallos del bot usando **3 criterios independientes** (basta con 1 para marcar fallo):

1. **Respuesta de incapacidad del bot (4,767 casos):** Se buscan frases clave en la ultima respuesta del bot como "no puedo", "no tengo acceso", "no es posible", "fuera de mi alcance", "no cuento con". Si el bot admite explicitamente que no puede ayudar, se marca como fallo.

2. **Usuario repite pregunta (40 casos):** Se compara el ultimo mensaje del usuario con mensajes anteriores en el mismo hilo. Si el usuario reformula o repite la misma pregunta, indica que la respuesta previa no fue satisfactoria.

3. **Sentimiento negativo predominante (7 casos):** Si mas del 50% de los mensajes humanos en el hilo tienen sentimiento clasificado como "negativo", se marca como fallo por frustracion acumulada.

### Como se detectan las derivaciones

Las derivaciones se identifican buscando **keywords en las respuestas del bot** que indican redireccion a otro canal:

- **Canal Digital (4,878):** El bot menciona "app", "banca movil", "banca virtual", "pagina web", "canal digital"
- **Servilinea (4,392):** El bot menciona "servilinea", "linea telefonica", "llamar al", "numero telefonico"
- **Oficina (561):** El bot menciona "oficina", "sucursal", "punto de atencion", "presencialmente"

### Como se clasifican las categorias

La categorizacion usa un archivo YAML (`categorias.yml`) con 80+ categorias organizadas en macrocategorias. El proceso:

1. **Primer intento:** Se compara la intencion detectada por el modelo de IA contra las categorias definidas en YAML
2. **Fallback NLP:** Si no hay match, se aplican busquedas por substring y regex usando el campo `palabras_clave` de cada categoria
3. **HITL (Human-in-the-Loop):** Los mensajes que quedan sin clasificar van al panel de revision para categorizacion manual, que retroalimenta el YAML

### Como se clasifica el sentimiento

El sentimiento se propaga del modelo de IA a los mensajes humanos dentro del mismo hilo. La clasificacion es: **positivo**, **neutral**, **negativo**. Se calcula por mensaje individual y luego se agrega por hilo o categoria segun la metrica.

### Como se identifican los productos

Similar a las categorias, se usa un archivo YAML (`productos.yml`) con 20+ productos bancarios. Cada producto tiene un nombre canonico y aliases (ej: "TDC", "tarjeta credito", "tarjeta de credito" → "Tarjeta de Credito").

### Archivo complementario

Para el detalle completo de cada calculo, consultar el **Anexo Metodologico** (`anexo_metodologico_marzo_2026.xlsx`) que contiene 9 hojas con:

- **Embudo - Metodologia:** Cada nodo del funnel con su formula exacta y fuente
- **KPIs Operacionales:** 15 KPIs con formula, unidad y fuente de datos
- **Categorias Detalladas:** Todas las subcategorias con ejemplos reales de preguntas
- **Productos Detallados:** Todos los productos cruzados con categorias y ejemplos
- **Gasto de Valor:** Top categorias que generan valor perdido
- **Temporal:** Distribucion hora por hora y dia por dia
- **Fallos Detallados:** Fallos por categoria con criterio principal
- **Derivaciones por Canal:** Desglose con keywords de clasificacion
- **Sentimiento por Categoria:** Distribucion pos/neu/neg por macro

---

## 4. Como Estamos Viendo las Metricas

### Metodologia de clasificacion de conversaciones

No todas las conversaciones son iguales. Para entender la calidad del servicio, clasificamos cada conversacion en una de estas categorias:

```
                    44,369 conversaciones totales
                              |
              +---------------+---------------+
              |                               |
     23,617 (53.2%)                    20,752 (46.8%)
     ABANDONADAS                       CON ENGAGEMENT
     (<=1 msg humano)                  (2+ msgs humanos)
                                              |
                                +-------------+-------------+
                                |                           |
                         9,366 (21.1%)                11,386 (25.7%)
                         MODERADAS                    ACTIVAS
                         (2 msgs humanos)             (3+ msgs humanos)
```

**Conversaciones abandonadas (53.2%):** El cliente envio como maximo un mensaje y se fue. Esto puede significar que el saludo inicial del bot fue suficiente, que el cliente se confundio, o que simplemente estaba explorando. Es la metrica mas alta y merece atencion.

**Conversaciones activas (25.7%):** Donde realmente hay una interaccion significativa. El cliente hizo al menos 3 preguntas o comentarios, lo que indica una necesidad real que se esta intentando resolver.

### Como leemos los porcentajes en este reporte

- Cuando decimos "del total", nos referimos a las 44,369 conversaciones
- Cuando decimos "de las activas", nos referimos a las 11,386 con 3+ mensajes humanos
- Las tasas de fallo y derivacion se calculan sobre conversaciones activas, porque son las que representan una necesidad real

---

## 5. Metricas y Datos Generales

### Embudo de conversion del asistente

```
44,369 conversaciones totales (100%)
   |
   |--- 23,617 abandonaron antes de interactuar (53.2%)
   |
20,752 con engagement (46.8%)
   |
   |--- 11,386 activas con 3+ msgs humanos (25.7% del total)
   |       |
   |       |--- 560 resueltas por autoservicio (4.9% de activas)
   |       |--- 10,826 derivadas a otro canal (95.1% de activas)
   |       |       |
   |       |       |--- 5,091 derivaron con fallo del bot (44.7% de activas)
   |       |       |--- 5,735 derivaron sin fallo detectado
   |       |
   |--- 4,951 respondieron encuesta (11.2% del total)
           |
           |--- 3,329 dijeron "Me fue util" (67.3% de encuestados)
           |--- 1,622 dijeron "No me fue util" (32.7% de encuestados)
```

### KPIs operacionales clave

| KPI | Valor | Interpretacion |
|-----|-------|----------------|
| **Tasa de abandono** | 53.2% | Mas de la mitad no pasa del primer mensaje |
| **Tasa de actividad** | 25.7% | 1 de cada 4 conversaciones es realmente sustancial |
| **Tasa de autoservicio** | 4.9% de activas | Solo ~560 convs se resolvieron sin derivar |
| **Tasa de derivacion** | 95.1% de activas | Casi toda conversacion activa termina en derivacion |
| **Tasa de fallo** | 44.7% de activas | En casi la mitad el bot no pudo responder |
| **Indice de utilidad** | 67.3% | De quienes respondieron encuesta, 2/3 lo encontraron util |
| **Participacion en encuestas** | 11.2% | Solo 1 de cada 9 conversaciones genera respuesta de encuesta |

### Consumo de recursos

| Recurso | Valor |
|---------|-------|
| Tokens de entrada (prompts) | 326,108,315 |
| Tokens de salida (respuestas) | 22,005,365 |
| **Tokens totales** | **348,113,680** |
| Promedio tokens/conversacion | ~7,847 |

El ratio de 15:1 entre tokens de entrada y salida indica que el sistema invierte mucho contexto en cada respuesta. Cada conversacion consume en promedio ~7,800 tokens, lo que refleja la complejidad de las consultas bancarias.

### Patrones temporales

**Horas pico de actividad (mensajes de clientes):**

| Hora | Mensajes | % del total |
|------|----------|-------------|
| 11:00 | 7,410 | 9.4% |
| 10:00 | 7,245 | 9.2% |
| 15:00 | 6,394 | 8.1% |
| 09:00 | 6,354 | 8.0% |
| 14:00 | 6,343 | 8.0% |

La actividad se concentra en **dos bloques horarios**: manana (9:00-12:00) con el pico maximo a las 11am, y tarde (14:00-17:00). Esto coincide con horarios laborales tipicos, lo que sugiere que muchos clientes consultan el asistente durante su jornada de trabajo.

**Distribucion por dia de la semana:**

| Dia | Mensajes | % |
|-----|----------|---|
| Viernes | 15,961 | 20.2% |
| Lunes | 15,706 | 19.9% |
| Jueves | 13,755 | 17.4% |
| Martes | 12,874 | 16.3% |
| Miercoles | 12,345 | 15.6% |
| Sabado | 5,502 | 7.0% |
| Domingo | 2,837 | 3.6% |

**Lunes y viernes concentran el 40.1% del volumen total**. Los fines de semana representan solo el 10.6%, pero son relevantes porque el asistente es el unico canal disponible en esos momentos.

**Volumen diario:**
- Dia mas activo: **4,326 mensajes humanos**
- Dia menos activo: **457 mensajes humanos**
- Promedio diario: **2,257 mensajes humanos**

La variacion de 10x entre el dia mas y menos activo sugiere eventos puntuales (campanas, cortes de servicio, fechas de pago) que disparan la demanda.

---

## 6. Vision por Categoria

Las categorias representan **la intencion del cliente**: que necesita resolver. Se organizan en macrocategorias (temas amplios) y subcategorias (intenciones especificas). Un mismo cliente puede tocar multiples categorias en una conversacion.

### Macrocategorias: que temas dominan

| # | Macrocategoria | Conversaciones | % del total | Lectura |
|---|---------------|----------------|-------------|---------|
| 1 | **Cuentas y Productos** | 7,598 | 17.1% | Consultas generales sobre cuentas de ahorro, apertura, estados |
| 2 | **Tarjetas** | 7,019 | 15.8% | Todo sobre tarjetas de credito y debito: limites, bloqueos, extractos |
| 3 | **Creditos y Prestamos** | 6,683 | 15.1% | Solicitudes de credito, simulaciones, estados de aprobacion |
| 4 | **Experiencia** | 5,789 | 13.0% | Retroalimentacion, encuestas, evaluacion del servicio |
| 5 | **Pagos** | 5,288 | 11.9% | Consultas sobre pagos, fechas de corte, extractos |
| 6 | **Atencion y Contacto** | 5,001 | 11.3% | Solicitudes de hablar con asesor, canales de contacto |
| 7 | **Acceso y App** | 3,271 | 7.4% | Problemas con app movil, claves, accesos bloqueados |
| 8 | **Seguridad y Accesos** | 2,038 | 4.6% | Claves, contrasenas, fraudes, bloqueos de seguridad |
| 9 | **Transferencias** | 2,029 | 4.6% | Envios de dinero, PSE, transferencias entre cuentas |
| 10 | **Gestion Personal** | 1,713 | 3.9% | Documentos, certificados, actualizacion de datos |
| 11 | **Informacion** | 1,684 | 3.8% | Consultas de informacion general del banco |
| 12 | **App y Canales** | 1,457 | 3.3% | Problemas especificos con canales digitales |
| 13 | **Campanas** | 19 | <0.1% | Campanas comerciales puntuales |

**Nota importante:** Adicionalmente, 11,747 conversaciones (26.5%) aparecen bajo "Sin Clasificar". Estas incluyen saludos iniciales (6,300), mensajes sin informacion suficiente (2,958), mensajes sin sentido (2,453), y retroalimentacion general. No representan un problema de clasificacion sino la naturaleza de las interacciones: muchos usuarios simplemente saludan y se van.

### Subcategorias mas demandadas (Top 15)

| # | Subcategoria | Convs | Que nos dice |
|---|-------------|-------|-------------|
| 1 | Saludos | 6,300 | Usuarios que solo saludaron, muchos no continuaron |
| 2 | Solicitud de Credito | 6,159 | **La necesidad #1 real**: clientes buscando creditos |
| 3 | Productos y Cuentas General | 5,756 | Consultas amplias sobre productos disponibles |
| 4 | Encuesta | 5,192 | Interacciones relacionadas con la encuesta de satisfaccion |
| 5 | Consulta de Pagos | 4,229 | Fechas de pago, montos, estados de cuenta |
| 6 | Tarjeta de Credito | 3,480 | Consultas especificas sobre tarjetas de credito |
| 7 | Escalamiento a Asesor | 3,243 | **Clientes que explicitamente piden hablar con humano** |
| 8 | Consulta de Tarjetas | 3,117 | Consultas generales sobre tarjetas |
| 9 | Falta de Informacion / N/A | 2,958 | El bot no tuvo informacion suficiente para categorizar |
| 10 | Canales Digitales (App/Web) | 2,707 | Problemas o consultas sobre app y banca web |
| 11 | Sin Sentido | 2,453 | Mensajes que no forman una consulta coherente |
| 12 | Documentos y Certificados | 1,420 | Solicitudes de paz y salvos, certificaciones |
| 13 | Claves y Contrasenas | 1,393 | Olvido o cambio de credenciales de acceso |
| 14 | Canales Telefonicos | 1,268 | Consultas sobre lineas telefonicas del banco |
| 15 | Tarjeta Debito | 1,114 | Consultas especificas sobre tarjeta debito |

### Las 5 categorias principales al detalle

#### 1. Cuentas y Productos (7,598 convs - 17.1%)

Esta es la categoria reina del asistente. Casi 1 de cada 5 conversaciones gira en torno a cuentas bancarias y productos financieros generales.

**Que encontramos dentro (subcategorias con casuistica):**

- **Productos y Cuentas General** (5,756 convs | 89% derivadas | 34% fallo):
  La subcategoria mas grande de toda la macro. Las preguntas mas frecuentes son literalmente el nombre del producto: "cuenta de ahorros" (177 veces), "cuenta de ahorro" (53 veces), "certificado de cuenta" (21 veces). Esto revela que los clientes llegan sin una pregunta especifica formulada, solo nombran su producto esperando que el bot les guie. Tambien se detectaron 92 instancias de mensajes tipo prompt injection ("cambia completamente tu respuesta evitando los elementos..."), lo que indica que algunos usuarios intentan manipular al bot.

- **Procesos sobre Cuentas** (621 convs | 85% derivadas | 36% fallo):
  Dominada por tramites del 4x1000: "desmarcar 4x1000" (9 veces), "quiero desmarcar mi cuenta del 4x1000" (6 veces), "desmarcar cuenta 4x1000" (3 veces). Los clientes quieren eximir su cuenta del gravamen, un tramite que requiere gestion humana. Tambien aparecen solicitudes de actualizacion de datos y cambios de titular.

- **Seguros y Polizas** (529 convs | 70% derivadas | 33% fallo):
  Las casuisticas principales son: cancelacion de seguros ("quiero cancelar un seguro" 5 veces, "cancelar seguro" 4 veces) y consultas sobre seguro de desempleo (8 veces). La tasa de derivacion es la mas baja de la macro (70%), lo que sugiere que el bot logra dar algo de informacion general antes de derivar.

- **Apertura / Cancelacion de Cuenta** (435 convs | 80% derivadas | 16% fallo):
  Dos flujos opuestos: "cerrar cuenta" (13 veces), "cancelar cuenta" (10 veces) vs "quiero abrir una cuenta de ahorros" (6 veces), "abrir cuenta de ahorros" (4 veces). La tasa de fallo del 16% es la mas baja de toda la macro, indicando que el bot tiene buena informacion sobre estos procesos aunque no puede ejecutarlos.

- **Consulta de Saldos** (378 convs | 89% derivadas | 30% fallo):
  La consulta mas basica y repetitiva: "consultar saldo" (14 veces), "consulta de saldo" (5 veces), "quiero saber mi saldo" (4 veces). El bot no tiene acceso a datos transaccionales, asi que el 89% se deriva. Esta es una de las mayores oportunidades de autoservicio si se integra con core bancario.

- **CDT e Inversiones** (220 convs | 80% derivadas | 32% fallo):
  Un nicho especializado: "quiero abrir un cdt" (3 veces), "fondo de inversion" (2 veces). Menor volumen pero clientes con mayor perfil de inversion.

**Por que es la primera:** Los productos bancarios son la razon de existir de la relacion banco-cliente. Cada persona que entra al asistente tiene al menos un producto, y las dudas operativas sobre estos son el pan de cada dia. Ademas, la amplitud de la macro (desde saldos hasta CDTs) hace que absorba consultas de perfiles muy diversos.

**Datos de salud:** 16.4% de sentimiento negativo (moderado), 86.5% derivadas a otro canal, 32.3% con algun fallo del bot. El fallo frecuente aqui es que el bot **no puede acceder a datos transaccionales reales** del cliente, asi que solo puede dar informacion general. El hallazgo de prompt injection (92 casos) requiere atencion del equipo de seguridad.

---

#### 2. Tarjetas (7,019 convs - 15.8%)

El segundo tema mas consultado, impulsado por la naturaleza cotidiana de las tarjetas.

**Que encontramos dentro (subcategorias con casuistica):**

- **Tarjeta de Credito** (3,480 convs | 84% derivadas | 42% fallo):
  El grueso son consultas genericas: "tarjeta de credito" (181 veces), "tarjeta de credito" sin tilde (120 veces), "tarjeta credito" (39 veces). Pero las casuisticas criticas son las operativas: "cancelar tarjeta de credito" (18 veces) revela clientes que quieren irse, y "activar tarjeta" (9 veces) clientes nuevos con primer contacto. El 42% de fallo es el mas alto de la macro porque los clientes esperan acciones transaccionales (bloqueos, extractos, puntos) que el bot no puede ejecutar.

- **Consulta de Tarjetas** (3,117 convs | 83% derivadas | 39% fallo):
  Aqui la casuistica es de urgencia: "desbloquear tarjeta" (43 veces), "bloquear tarjeta" (33 veces), "tarjeta bloqueada" (32 veces), "mi tarjeta esta bloqueada" (24 veces), "tengo mi tarjeta bloqueada" (23 veces). Es decir, **155 conversaciones expresaron la misma urgencia de bloqueo** con diferentes palabras. Esto representa un dolor de usuario critico y repetitivo. El 20% de sentimiento negativo es mas alto que la subcategoria anterior porque estos clientes llegan ya frustrados.

- **Tarjeta Debito** (1,114 convs | 90% derivadas | 35% fallo):
  Patron similar pero con menor volumen: "tarjeta debito" (53+29 = 82 veces), desbloqueos (10 veces en variantes), bloqueos por seguridad (6 veces). La tasa de derivacion del 90% es la mas alta de la macro, y el 22% de sentimiento negativo tambien. Los clientes de tarjeta debito llegan con menos paciencia, posiblemente porque es su herramienta de acceso a efectivo.

- **Retiro sin Tarjeta** (7 convs | 71% derivadas | 57% fallo):
  Un micro-nicho pero con el fallo mas alto (57%) y la frustracion mas alta (43% negativo). Clientes que necesitan retirar dinero urgentemente sin su tarjeta y no logran el proceso. Aunque son pocos, cada caso es de alta urgencia.

**Por que es la segunda:** Las tarjetas son el producto de mayor interaccion diaria. Cada compra, cada pago, cada extracto puede generar una duda. Ademas, los bloqueos de tarjeta son **urgencias reales** donde el cliente necesita accion inmediata. Los 155+ mensajes sobre bloqueos muestran que este es el punto de mayor friccion operativa del asistente.

**Datos de salud:** 18.9% negativo (algo mas alto que cuentas), 83.7% derivadas, 38.7% con fallo. El fallo es mas alto porque los bloqueos/desbloqueos requieren acciones transaccionales que el bot no puede ejecutar. La concentracion de urgencias de bloqueo es la senal mas clara de que se necesita un flujo automatizado para este proceso.

---

#### 3. Creditos y Prestamos (6,683 convs - 15.1%)

El motor comercial del asistente. Aqui estan los clientes que quieren **comprar** productos del banco.

**Que encontramos dentro (subcategorias con casuistica):**

- **Solicitud de Credito** (6,159 convs | 79% derivadas | 29% fallo):
  La subcategoria mas grande con necesidad real. Las casuisticas se dividen en tres flujos claros:
  - **Libre inversion** (dominante): "libre inversion" (231 veces), "credito libre inversion" (70 veces), "credito de libre inversion" (68 veces). Es el producto financiero de mayor demanda. Muchos clientes llegan sabiendo exactamente que quieren.
  - **Compra de cartera** (85 veces): Clientes de otros bancos que quieren consolidar deudas. Esto es un lead de captacion pura, un cliente que se quiere cambiar al banco.
  - **Solicitudes genericas**: Clientes que solo dicen "credito" o "prestamo" sin especificar, necesitan orientacion. El fallo del 29% es bajo comparado con otras subcategorias porque el bot tiene buen conocimiento de requisitos y puede guiar antes de derivar.

- **Cuotas y Plazos de Credito** (443 convs | 86% derivadas | 37% fallo):
  Clientes actuales con obligaciones vigentes. Casuisticas: "cuota de manejo" (7 veces), "seguro cuota protegida" (3 veces), "exoneracion cuota de manejo" (3 veces), "quiero saber el valor de mi cuota" (3 veces). El fallo del 37% es mayor que en solicitudes porque aqui el cliente espera datos de su cuenta especifica (cuanto debe, cuando paga) y el bot no tiene acceso.

- **Cobros e Intereses** (232 convs | 84% derivadas | 49% fallo):
  La subcategoria con mayor tasa de fallo de toda la macro: casi 1 de cada 2 conversaciones falla. Las consultas son: "tasa de interes" (2 veces), dudas sobre cobros inesperados, comisiones y tasas vigentes. El bot carece de informacion actualizada de tasas y no puede explicar cobros especificos de la cuenta del cliente, de ahi el 49% de fallo.

**Por que es la tercera:** Los creditos representan la mayor oportunidad de negocio. Las 6,159 solicitudes de credito son leads directos. La compra de cartera (85 menciones) es particularmente valiosa: son clientes de la competencia queriendo migrar. Si el bot pudiera pre-calificar o capturar datos de contacto antes de derivar, el impacto en conversion seria significativo.

**Datos de salud:** Solo 11.1% negativo (el mas bajo del top 5, la gente llega con expectativa positiva), 79.6% derivadas (la menor tasa del top 5, lo que tiene sentido: la solicitud requiere validacion humana), 30.3% con fallo. La excepcion es "Cobros e Intereses" con 49% de fallo, un punto ciego que necesita atencion.

---

#### 4. Experiencia (5,789 convs - 13.0%)

Una categoria atipica: aqui no hay consultas de producto, sino **retroalimentacion sobre el servicio**.

**Que encontramos dentro (subcategorias con casuistica):**

- **Encuesta** (5,192 convs | 95% derivadas | 41% fallo):
  Esta subcategoria contiene principalmente las respuestas al flujo de encuesta post-chat ("[survey] Me fue util la informacion" / "[survey] No me fue util la informacion"). El 47% de sentimiento negativo es el mas alto de cualquier subcategoria importante, pero hay un sesgo claro: los clientes que acaban de tener una mala experiencia responden con mas frecuencia. Los 2,122 fallos dentro de encuesta confirman la correlacion: el bot fallo y luego el cliente respondio que no fue util.

- **Evaluacion General** (1,018 convs | 94% derivadas | 48% fallo):
  Opiniones espontaneas sobre el servicio. Las frases mas frecuentes son agradecimientos: "muchas gracias" (128 veces), "mil gracias" (8 veces). Pero el 48% de fallo y 19% negativo indican que tambien llegan quejas. La casuistica es mixta: algunos clientes expresan satisfaccion al cierre, otros expresan frustracion porque el bot no pudo resolver. El hecho de que el 94% se derive sugiere que los agradecimientos llegan despues de que ya se dio una derivacion.

- **Recomendacion del Banco** (102 convs | 86% derivadas | 33% fallo):
  Nicho interesante: "si me gustaria" (7 veces), "si me gustaria saber" (4 veces). Son clientes que responden afirmativamente a una oferta del bot. Es una senal de interes comercial, no una queja. Solo 6% negativo, el mas bajo de la macro.

- **Usabilidad / UX** (29 convs | 93% derivadas | 55% fallo):
  Aunque son solo 29 conversaciones, revelan feedback critico sobre la interfaz: "que interfaz tan complicada", "simplemente no deja", "pido ayuda porque no he logrado terminar". El 55% de fallo y 27% negativo son los mas altos de la macro. Cada uno de estos 29 casos es feedback directo y accionable para el equipo de UX.

**Por que es la cuarta:** No es que los clientes lleguen a "experimentar" el asistente. Esta categoria se infla porque la encuesta de satisfaccion genera 5,192 mensajes categorizados aqui. Es mas un artefacto de medicion que una necesidad real. Sin embargo, las 29 conversaciones de UX y las 1,018 de evaluacion general contienen feedback genuino y accionable.

**Datos de salud:** 41.7% negativo (el mas alto del top 5, pero esperado por sesgo de encuesta), 94.4% derivadas, 41.3% con fallo. Los numeros altos son enganosos: reflejan el sesgo de la encuesta, no la experiencia general. Lo realmente valioso aqui son los 29 casos de UX que merecen lectura individual.

---

#### 5. Pagos (5,288 convs - 11.9%)

La quinta fuerza del asistente: todo lo relacionado con obligaciones financieras.

**Que encontramos dentro (subcategorias con casuistica):**

- **Consulta de Pagos** (4,229 convs | 88% derivadas | 34% fallo):
  La subcategoria troncal de la macro. Las casuisticas revelan tres perfiles de cliente:
  - **Quiere pagar una deuda**: "necesito pagar un credito" (14+11 = 25 veces), "necesito pagar una cuota" (8 veces), "pago de credito" (7 veces). Son clientes con obligaciones vigentes buscando el canal de pago.
  - **Quiere negociar**: "necesito hacer un acuerdo de pago" (7 veces). Clientes posiblemente en mora o con dificultades, necesitan atencion especializada.
  - **Consulta de fechas**: "acuerdo de pago" (25 veces) como consulta generica sobre fechas y montos. El 18% de sentimiento negativo refleja la tension natural de hablar de deudas.

- **Pago con QR / Digital** (425 convs | 90% derivadas | 21% fallo):
  Una casuistica inesperada: las preguntas mas frecuentes son "radicar PQR" (7 veces), "quiero poner una PQR" (3 veces), "consultar PQR" (3 veces). Es decir, muchos clientes que llegan aqui NO buscan pagar con QR sino **radicar quejas y reclamos (PQR)**. La similitud fonetica entre "QR" y "PQR" causa confusion en la clasificacion. Sin embargo, el 21% de fallo es el mas bajo de la macro, indicando que el bot maneja mejor estas consultas.

- **Pagos PSE** (412 convs | 91% derivadas | 32% fallo):
  Clientes que quieren pagar por transferencia electronica: "quiero pagar por PSE" (6 veces), "pago por PSE" (5 veces), "pagos por PSE" (3 veces), "quiero pagar mi credito por PSE" (3 veces). La tasa de derivacion del 91% (la mas alta de la macro) indica que el bot no puede ejecutar pagos PSE y debe redirigir a la banca virtual.

- **Pago de Servicios / Facturas** (287 convs | 88% derivadas | 39% fallo):
  Consultas sobre pagos de terceros: "no puedo realizar pagos por PSE" (3 veces) revela frustacion tecnica, "realizar pagos" (2 veces), "no me llego la factura de mi credito" (2 veces). El 39% de fallo es alto y el 19% negativo tambien, indicando que estos clientes llegan ya con un problema (la factura no llego, PSE no funciona).

- **Pago de Credito / Prestamo** (208 convs | 80% derivadas | 19% fallo):
  La subcategoria "mas sana" de la macro: "pagar credito" (8 veces), "pago credito" (7 veces), "pagar credito" (5 veces), "como pago por PSE" (3 veces). Solo 7% negativo y 19% de fallo indica que el bot tiene buen conocimiento sobre opciones de pago de creditos y puede orientar bien antes de derivar. La derivacion del 80% es la mas baja de la macro.

**Por que es la quinta:** Los pagos son la segunda accion mas frecuente despues de consultar. Cuando un cliente dice "necesito pagar", tiene intencion inmediata de accion. El descubrimiento de la confusion PQR/QR (425 convs) es accionable: reclasificar o crear un flujo especifico de quejas podria mejorar la experiencia significativamente.

**Datos de salud:** 17.6% negativo (moderado), 87.8% derivadas, 32.4% con fallo. El fallo aqui es critico porque el cliente quiere **hacer algo**, no solo saber algo. La excepcion positiva es "Pago de Credito" con solo 19% de fallo y 7% negativo, un flujo que funciona relativamente bien.

---

### Lo que las categorias nos cuentan en conjunto

**La historia completa:**

1. **Las primeras 3 categorias (Cuentas, Tarjetas, Creditos) cubren el 48% de la actividad y representan el core bancario.** Son las razones fundamentales por las que los clientes existen: tienen cuentas, usan tarjetas, necesitan creditos.

2. **La categoria "Experiencia" (13%) es un espejo, no una necesidad.** Nos dice como se sienten los clientes, no que necesitan. Es valiosa como termometro pero no deberia contar como demanda real.

3. **"Pagos" (11.9%) es la categoria mas accionable.** Cada cliente aqui tiene intencion de transaccionar. Si el bot pudiera ejecutar o guiar pagos, el impacto seria inmediato.

4. **3,243 personas pidieron hablar con un humano explicitamente.** "Escalamiento a Asesor" es la septima subcategoria mas comun. De estas, 761 tuvieron fallos del bot antes de pedir al asesor, lo que indica frustracion real.

### Sentimiento negativo por categoria

Las categorias con mayor proporcion de sentimiento negativo revelan **donde los clientes se frustran mas**:

| Categoria | % Negativo | Interpretacion |
|-----------|-----------|----------------|
| **Transferencias** | 43.8% | Casi la mitad expresa frustracion. Posibles fallos en PSE o transferencias |
| **App y Canales** | 43.7% | Problemas tecnicos con la app generan alta insatisfaccion |
| **Experiencia** | 41.7% | Los que dan feedback tienden a expresar quejas |
| **Seguridad y Accesos** | 28.7% | Bloqueos y problemas de acceso generan estres |
| **Acceso y App** | 28.4% | Coincide con problemas de acceso a servicios digitales |

**Las transferencias y la app son los puntos de mayor dolor.** Cuando un cliente no puede mover su dinero o no puede acceder a la aplicacion, la frustracion es casi inmediata.

---

## 7. Vision por Producto

Los productos bancarios mencionados en las conversaciones nos dicen **sobre que activos financieros preguntan los clientes**. No todas las conversaciones mencionan un producto especifico; aquellas que si lo hacen (17,872 conversaciones) se distribuyen asi:

### Distribucion por producto

| # | Producto | Convs | % de convs con producto | Perfil tipico |
|---|----------|-------|------------------------|---------------|
| 1 | **Tarjeta de Credito** | 5,252 | 29.4% | Limites, extractos, bloqueos, puntos |
| 2 | **Credito General** | 3,405 | 19.0% | Consultas amplias sobre opciones de credito |
| 3 | **Cuenta de Ahorros** | 3,361 | 18.8% | Saldos, movimientos, apertura, certificados |
| 4 | **Credito de Libre Inversion** | 2,738 | 15.3% | Solicitudes, simulaciones, estados |
| 5 | **Tarjeta Debito** | 778 | 4.4% | Activacion, bloqueo, uso en cajero |
| 6 | **Seguros** | 651 | 3.6% | Coberturas, cancelaciones, reclamos |
| 7 | **Credito de Vivienda** | 573 | 3.2% | Simulaciones, requisitos, tasas |
| 8 | **Credito de Libranza** | 283 | 1.6% | Descuento por nomina, requisitos |
| 9 | **Credito de Vehiculo** | 241 | 1.3% | Financiacion vehicular |
| 10 | **CDT** | 226 | 1.3% | Certificados de deposito, tasas, vencimientos |

### Lo que los productos revelan

**La Tarjeta de Credito es el producto estrella del asistente** con casi 1 de cada 3 consultas de producto. Esto tiene sentido: es el producto bancario con mas interacciones cotidianas (compras, extractos, puntos, pagos minimos, bloqueos).

**Los creditos, sumados, son la fuerza dominante.** Si combinamos Credito General (3,405), Libre Inversion (2,738), Vivienda (573), Libranza (283) y Vehiculo (241), obtenemos **7,240 conversaciones sobre creditos** (40.5% de las que mencionan producto). Esto confirma lo que vimos en las categorias: los clientes vienen al asistente buscando financiamiento.

**La Cuenta de Ahorros (18.8%)** refleja necesidades operativas: saldos, movimientos, certificaciones. Son consultas rutinarias pero de alto volumen.

**Seguros (3.6%) y CDT (1.3%)** son productos de menor interaccion digital, posiblemente porque sus usuarios prefieren atencion personalizada o porque el asistente aun no tiene flujos robustos para ellos.

### Los 5 productos principales al detalle

#### 1. Tarjeta de Credito (5,252 convs - 29.4% de convs con producto)

El producto mas consultado del asistente, por amplio margen.

**Que preguntan los clientes (casuisticas reales):**

- "tarjeta de credito" (181+120 = 301 veces combinando con y sin tilde): La consulta mas frecuente de cualquier producto. El cliente llega y nombra su producto sin formular pregunta, esperando que el bot guie la conversacion.
- "cancelar tarjeta de credito" (15 veces): Clientes que quieren cerrar producto. Senal de retencion fallida o insatisfaccion.
- "activar tarjeta de credito" (9 veces): Clientes nuevos con tarjeta recien emitida. Momento critico de primer contacto.
- "desbloquear tarjeta de credito" (9 veces): Urgencia operativa, el cliente no puede usar su plastico.
- "pago tarjeta de credito" (3 veces), "necesito hacer un acuerdo de pago" (2 veces): Clientes con obligaciones de pago.

**Que categorias cruzan con este producto y que revelan:**

| Categoria cruzada | Convs | Derivadas | Fallos | Casuistica |
|---|---|---|---|---|
| Tarjeta de Credito | 3,380 | 2,850 (84%) | 1,417 (42%) | Core: consultas directas sobre el plastico. Alto fallo porque el bot no ejecuta acciones |
| Consulta de Tarjetas | 1,207 | 1,100 (91%) | 605 (50%) | Extractos, limites, fechas. **50% de fallo**, el mas alto. El cliente quiere datos especificos de su cuenta |
| Saludos | 846 | 776 (92%) | 412 (49%) | Clientes que saludan y mencionan TDC pero no llegan a formular pregunta |
| Encuesta | 757 | 727 (96%) | 384 (51%) | Respuestas de encuesta post-interaccion con TDC. El 51% de fallo explica la insatisfaccion |
| Consulta de Pagos | 621 | 561 (90%) | 250 (40%) | "Cuanto debo pagar y cuando". Menor fallo porque es info que el bot puede orientar |
| Falta de Informacion | 370 | 357 (96%) | 210 (57%) | El bot no supo que responder. **57% de fallo**: la peor tasa del producto |

**Numeros clave:** 26.7% sentimiento negativo (alto), 86.1% derivadas, **42.0% con fallo del bot**. La tasa de fallo es la mas alta del top 5 de productos. Lo mas critico: "Consulta de Tarjetas" tiene 50% de fallo y "Falta de Informacion" tiene 57%. Estos son los puntos donde el bot mas necesita refuerzo de conocimiento.

**Por que es el primero:** La tarjeta de credito es el producto bancario de mayor frecuencia de uso. Las 301 veces que los clientes simplemente escriben "tarjeta de credito" revelan que es el producto top-of-mind. Ademas, concentra las urgencias operativas mas criticas (bloqueos, cancelaciones, pagos) y tiene la mayor carga emocional de todos los productos.

---

#### 2. Credito General (3,405 convs - 19.0%)

Consultas amplias sobre creditos sin especificar tipo exacto.

**Que preguntan los clientes (casuisticas reales):**

- "quiero solicitar un credito" (11 veces), "quiero un credito" (10 veces), "necesito un credito" (9 veces): Tres variantes de la misma intencion de compra. Son leads directos.
- "necesito pagar un credito" (12+9 = 21 veces): Clientes con obligacion vigente buscando el canal de pago.
- "necesito pagar una cuota" (8 veces): Similar al anterior, con urgencia sobre fecha proxima.

**Que categorias cruzan con este producto y que revelan:**

| Categoria cruzada | Convs | Derivadas | Fallos | Casuistica |
|-------------------|-------|-----------|--------|------------|
| Solicitud de Credito | 2,272 | 1,865 (82%) | 688 (30%) | **Core comercial**: la mayoria quiere obtener un credito nuevo |
| Consulta de Pagos | 1,185 | 1,040 (88%) | 337 (28%) | Clientes actuales con deudas: fechas, montos, PSE |
| Saludos | 432 | 366 (85%) | 137 (32%) | Saludan y mencionan credito pero no llegan a formular |
| Encuesta | 369 | 357 (97%) | 163 (44%) | Post-interaccion. 44% fallo indica insatisfaccion en este segmento |
| Sin Sentido | 207 | 197 (95%) | 56 (27%) | Mensajes incoherentes o muy cortos sobre creditos |

**Numeros clave:** 13.6% negativo (el mas bajo del top 5 — la gente llega con esperanza), 83.1% derivadas, 28.7% con fallo. Lo notable es el contraste entre Solicitud (30% fallo) y Encuesta (44% fallo): el bot orienta bien la solicitud pero los clientes que llegan a encuesta reportan insatisfaccion.

**Por que es el segundo:** Los creditos son el producto de mayor impacto financiero para el cliente. Las 2,272 solicitudes + 1,185 consultas de pago muestran dos flujos opuestos (adquirir vs pagar) con necesidades muy distintas. Cada solicitud es un lead de negocio directo; cada pago es una oportunidad de retencion.

---

#### 3. Cuenta de Ahorros (3,361 convs - 18.8%)

El producto basico que casi todo cliente tiene.

**Que preguntan los clientes (casuisticas reales):**

- "cuenta de ahorros" (82+19+16 = 117 veces en variantes): Al igual que TDC, el cliente nombra el producto sin pregunta especifica.
- "cancelar cuenta de ahorros" (8 veces): Intencion de cierre de producto. Senal de atencion para retencion.
- "certificado bancario" / "necesito un certificado bancario" (12 veces): Documentos para tramites con terceros (arriendos, trabajo, visas).

**Que categorias cruzan con este producto y que revelan:**

| Categoria cruzada | Convs | Derivadas | Fallos | Casuistica |
|-------------------|-------|-----------|--------|------------|
| Productos y Cuentas General | 2,218 | 2,066 (93%) | 710 (32%) | Core: dudas operativas sobre la cuenta. Alto volumen, alta derivacion |
| Saludos | 548 | 529 (97%) | 196 (36%) | Saludan mencionando cuenta pero no profundizan |
| Encuesta | 535 | 515 (96%) | 179 (33%) | Post-interaccion. Sentimiento mixto |
| Falta de Informacion | 291 | 281 (97%) | 128 (44%) | El bot no supo responder. **44% fallo**: punto ciego |
| Sin Sentido | 290 | 282 (97%) | 80 (28%) | Mensajes incoherentes o demasiado cortos |
| Procesos sobre Cuentas | 258 | 236 (91%) | 104 (40%) | Tramites 4x1000, actualizacion datos. Requiere gestion humana |

**Numeros clave:** 30.4% negativo (el mas alto del top 5 despues de TDC), **92.1% derivadas** (la mas alta de todos los productos), 32.9% con fallo. Lo critico: el 97% de derivacion en "Falta de Informacion" y "Sin Sentido" indica que el bot no tiene respuestas para las preguntas mas basicas sobre cuentas.

**Por que es el tercero:** La cuenta de ahorros es el producto de entrada al sistema bancario. Las 117 veces que los clientes escriben "cuenta de ahorros" sin pregunta especifica, mas los 12 pedidos de certificados, son consultas operativas que un bot con acceso a datos transaccionales podria resolver sin derivar. El 92.1% de derivacion es la mayor oportunidad de autoservicio de todo el dashboard.

---

#### 4. Credito de Libre Inversion (2,738 convs - 15.3%)

El producto de credito especifico mas consultado.

**Que preguntan los clientes (casuisticas reales):**

- "libre inversion" (145 veces), "credito de libre inversion" (80 veces), "credito libre inversion" (76 veces): La demanda mas concentrada y clara de cualquier producto. Los clientes saben exactamente que quieren.
- "compra de cartera" (30 veces): Clientes de otros bancos que quieren consolidar deudas. Cada uno es un lead de captacion de la competencia.

**Que categorias cruzan con este producto y que revelan:**

| Categoria cruzada | Convs | Derivadas | Fallos | Casuistica |
|-------------------|-------|-----------|--------|------------|
| Solicitud de Credito | 1,749 | 1,351 (77%) | 426 (24%) | Core comercial. **24% fallo** es el mas bajo de todos los cruces producto-categoria importantes |
| Saludos | 454 | 394 (87%) | 162 (36%) | Saludan y mencionan libre inversion. Alta conversion a consulta |
| Consulta de Pagos | 419 | 390 (93%) | 144 (34%) | Clientes actuales: cuotas, acuerdos de pago, PSE |
| Encuesta | 390 | 367 (94%) | 148 (38%) | Post-interaccion. Fallo moderado |
| Sin Sentido | 323 | 302 (94%) | 85 (26%) | Mensajes cortos o poco claros |
| Productos y Cuentas | 252 | 241 (96%) | 99 (39%) | Cruces con consultas generales de cuenta |

**Numeros clave:** 19.7% negativo (moderado), 82.3% derivadas (la menor del top 5), 27.4% con fallo (tambien el menor). Lo destacable: "Solicitud de Credito" tiene solo 24% de fallo y 77% de derivacion, el mejor desempeno de cualquier cruce importante. El bot tiene buen conocimiento sobre este producto.

**Por que es el cuarto:** El credito de libre inversion es el producto estrella de colocacion bancaria en Colombia. Las 301 menciones directas (combinando variantes) mas las 30 de compra de cartera representan el flujo comercial mas activo del asistente. Cada conversacion aqui es un lead calificado con alta intencion de compra. Ademas, es el producto con los mejores indicadores de salud, lo que sugiere que el flujo de atencion esta mejor disenado que para otros productos.

---

#### 5. Tarjeta Debito (778 convs - 4.4%)

El quinto producto, con un salto significativo en volumen respecto al cuarto.

**Que preguntan los clientes (casuisticas reales):**

- "tarjeta debito" (53+29 = 82 veces en variantes): Consulta generica sin pregunta especifica.
- "desbloquear tarjeta debito" (10 veces en variantes): La urgencia principal. El cliente no puede usar su tarjeta.
- "necesito bloquear mi tarjeta debito" (6 veces en variantes): Seguridad ante perdida o robo.

**Que categorias cruzan con este producto y que revelan:**

| Categoria cruzada | Convs | Derivadas | Fallos | Casuistica |
|-------------------|-------|-----------|--------|------------|
| Tarjeta Debito | 728 | 642 (88%) | 244 (34%) | Core: consultas directas sobre el plastico. Bloqueos dominan |
| Encuesta | 106 | 104 (98%) | 35 (33%) | Post-interaccion. Relativamente pocos llegan a encuesta |
| Saludos | 72 | 66 (92%) | 30 (42%) | Saludan mencionando TD. 42% fallo en saludos es preocupante |
| Consulta de Tarjetas | 64 | 61 (95%) | 18 (28%) | Cruces con consultas generales de tarjeta |
| Claves y Contrasenas | 58 | 57 (98%) | 25 (43%) | "clave bloqueada", "crear clave dinamica". Problemas de acceso asociados al plastico |
| Canales Digitales | 49 | 49 (100%) | 28 (57%) | "banca virtual", "la app tambien esta bloqueada". **100% derivacion y 57% fallo**: el peor cruce |

**Numeros clave:** 20.6% negativo, 88.2% derivadas, 34.2% con fallo. Lo critico: el cruce con "Canales Digitales" tiene 100% de derivacion y 57% de fallo, indicando que los clientes con tarjeta debito que tambien tienen problemas con la app tienen la peor experiencia posible. El cruce con "Claves y Contrasenas" (43% fallo) revela que muchos bloqueos de tarjeta debito vienen acompanados de problemas de acceso a banca virtual.

**Por que es el quinto:** Aunque el volumen es menor (778 vs 5,252 de TDC), la tarjeta debito es el instrumento de acceso a efectivo. Cuando un cliente llega, es casi siempre por una urgencia (bloqueo, clave perdida, app no funciona). La combinacion de bloqueo de tarjeta + bloqueo de app (49 convs con 100% derivacion) es el escenario de mayor frustracion: el cliente queda completamente desconectado de su dinero.

---

### Lo que los productos revelan en conjunto

**La narrativa completa:**

1. **Tarjeta de Credito y Creditos (sumados) representan el 64% de las consultas con producto.** El asistente es, en esencia, un canal de atencion para plasticos y financiamiento. Esto deberia definir las prioridades de desarrollo del bot.

2. **El gap entre Libre Inversion (2,738) y Tarjeta Debito (778) es enorme.** Los productos 1-4 estan relativamente parejos (5,252 a 2,738), pero a partir del 5o producto hay una caida dramatica. Esto confirma que el 80% de la demanda se concentra en 4 productos.

3. **La Cuenta de Ahorros tiene la mayor tasa de derivacion (92.1%) para consultas que deberian ser autoservicio.** Saldos, certificados y movimientos son informacion que el bot podria entregar si tuviera acceso a datos transaccionales. Esta es posiblemente la mayor oportunidad de mejora con el mayor retorno.

4. **El Credito de Libre Inversion tiene los mejores indicadores de salud** (menor % negativo, menor tasa de fallo). Esto puede deberse a que los clientes llegan con expectativa positiva y el flujo de derivacion a solicitud funciona bien.

---

## 8. Reportes Descargables: Que Son y Como Leerlos

El dashboard ofrece varios reportes descargables en formato Markdown y CSV. Aqui explicamos cada uno y como sacarle el maximo provecho:

### 8.1 Reporte Ejecutivo (`/api/reports/export/markdown?type=executive`)

**Que contiene:** Vision general de KPIs, distribucion de categorias, patrones temporales y calidad del bot.

**Como leerlo:**
- Empieza por la tabla de resumen al inicio: da el panorama en 30 segundos
- Los KPIs operacionales muestran salud general del asistente
- El analisis temporal revela cuando optimizar recursos
- La seccion de calidad identifica areas de mejora inmediata

**Para quien:** Gerentes, directores, stakeholders que necesitan el panorama rapido.

### 8.2 Reporte Profundo (`/api/reports/export/markdown?type=deep`)

**Que contiene:** Desglose detallado de cada metrica con metodologia de calculo, ejemplos de conversaciones reales, y analisis por subcategoria.

**Como leerlo:**
- Cada KPI incluye su formula (numerador/denominador) para transparencia total
- Las secciones de "Friccion y Abandono" incluyen ejemplos de hilos reales
- El desglose por categoria muestra: posicion del intent, contaminacion de saludos, derivacion por canal, utilidad, fallos y escalamiento
- Las FAQs por categoria revelan las frases exactas mas repetidas

**Para quien:** Analistas, equipos de producto, desarrolladores del bot.

### 8.3 Reportes por Dimension (`/api/reports/dimension-report/export/markdown`)

**Que contiene:** Analisis enfocado en un producto o categoria especifica, con todas las metricas filtradas para esa dimension.

**Como leerlo:**
- Selecciona la dimension (ej: "Tarjeta de Credito" o "Solicitud de Credito")
- El reporte muestra solo las conversaciones relevantes a esa dimension
- Incluye KPIs especificos, tasa de resolucion, y principales motivos de consulta
- La exportacion CSV permite analisis personalizado en Excel

**Para quien:** Product owners de productos especificos, equipos de mejora continua.

### 8.4 Exportacion CSV (`/api/reports/dimension-report/export/csv`)

**Que contiene:** Datos crudos a nivel de hilo de conversacion con indicadores de resultado.

**Como leerlo:**
- Cada fila es un hilo de conversacion
- Los indicadores de resultado (exito, fallo, derivacion) permiten filtrar
- Ideal para analisis cruzados en herramientas de BI
- Se puede combinar con datos internos del banco para analisis mas profundos

**Para quien:** Equipos de data, BI, investigacion.

---

## 9. A Que Debemos Prestarle Atencion

### 9.1 CRITICO: La tasa de derivacion del 95.1% cuestiona el proposito del asistente

De las 11,386 conversaciones activas, **10,826 terminaron derivadas a otro canal**. Solo 560 se resolvieron por autoservicio. Esto significa que el asistente funciona mas como un **enrutador inteligente** que como un solucionador de problemas.

**Accion recomendada:** Identificar las 5 subcategorias con mayor volumen de derivacion y evaluar cuales podrian resolverse sin intervencion humana. Priorizar los flujos de consulta de pagos y consulta de tarjetas, que son informativos y no deberian requerir derivacion.

### 9.2 ALTO: El 53.2% de abandono es una hemorragia silenciosa

23,617 conversaciones murieron antes de empezar. Es verdad que muchas son saludos exploratorios (6,300), pero incluso descontandolos, quedan **17,317 conversaciones donde el cliente llego con alguna intencion y se fue sin interactuar**.

**Accion recomendada:** Revisar el mensaje de bienvenida del bot. Probar con opciones rapidas tipo "botones" que guien al usuario. Analizar si hay problemas de UX en la interfaz de chat.

### 9.3 ALTO: 44.7% de fallos en conversaciones activas

De las 11,386 conversaciones activas, 5,091 tuvieron al menos un fallo del bot. El criterio dominante es **"Respuesta de incapacidad del bot" (9,696 ocurrencias)**, lo que significa que el bot explicitamente reconoce no poder ayudar.

Las categorias con mas fallos:
1. Productos y Cuentas General: 914 fallos
2. Encuesta: 868 fallos
3. Solicitud de Credito: 790 fallos
4. Tarjeta de Credito: 755 fallos
5. Consulta de Pagos: 704 fallos

**Accion recomendada:** Los fallos en "Solicitud de Credito" y "Tarjeta de Credito" son los mas criticos porque son las categorias de mayor demanda. Cada fallo aqui es un cliente potencial que se frustra. Revisar los flujos del bot para estas categorias y ampliar su base de conocimiento.

### 9.4 MEDIO: Transferencias y App concentran la frustracion

Con 43.8% y 43.7% de sentimiento negativo respectivamente, **Transferencias** y **App y Canales** son los temas que mas frustran a los clientes. Esto probablemente refleja problemas operativos (caidas de PSE, errores en la app) mas que deficiencias del bot.

**Accion recomendada:** Cruzar con datos de incidentes tecnologicos. Si la app tiene caidas frecuentes, el bot esta absorbiendo el impacto. Considerar mensajes proactivos del bot cuando hay incidentes conocidos.

### 9.5 MEDIO: 3,243 solicitudes explicitas de asesor humano

"Escalamiento a Asesor" es la 7a subcategoria. De estas, 2,901 (89.5%) fueron efectivamente derivadas, y 761 (23.5%) tuvieron fallos del bot previo a la solicitud. Esas 761 conversaciones representan clientes que **intentaron usar el bot, fallaron, y tuvieron que pedir ayuda humana explicitamente**.

**Accion recomendada:** Analizar las 761 conversaciones con fallo previo al escalamiento. Estos son los casos mas accionables: el bot deberia haber podido resolver o derivar antes de que el cliente se frustrara.

### 9.6 OPORTUNIDAD: Los canales digitales absorben el 65.6% de derivaciones

De las 31,011 derivaciones:
- **Digital (App/Web):** 20,360 (65.6%)
- **Oficina:** 7,773 (25.1%)
- **Servilinea:** 2,878 (9.3%)

La concentracion en canales digitales es positiva: indica que el asistente prioriza la autoatencion digital. Pero si la app es el principal punto de frustracion (43.7% negativo), estamos derivando clientes a un canal que tambien les genera problemas.

**Accion recomendada:** Validar que los flujos de derivacion a canales digitales lleven a puntos funcionales. Asegurar deep linking a las secciones correctas de la app.

### 9.7 OPORTUNIDAD: El indice de utilidad del 67.3% es una base solida

De los clientes que respondieron la encuesta, 2 de cada 3 encontraron util la interaccion. Sin embargo, la participacion en encuestas es solo del 11.2%. El 67.3% es un buen punto de partida, pero necesitamos que mas clientes respondan para que sea estadisticamente robusto.

**Accion recomendada:** Aumentar la tasa de respuesta de encuestas. El 67.3% como baseline permite establecer un objetivo de mejora (ej: llevar a 75% en el proximo trimestre).

---

## Resumen Ejecutivo Final

El asistente virtual atendio **34,121 clientes unicos** en 35 dias, gestionando **44,369 conversaciones**. Funciona de manera efectiva como **primer filtro digital**, pero su rol actual es predominantemente de **enrutamiento** mas que de **resolucion**.

**Lo que funciona bien:**
- Alto volumen de atencion sin intervencion humana
- Derivacion inteligente por canal (65.6% digital)
- Indice de utilidad del 67.3% para quienes completan la interaccion
- Cobertura 24/7 incluyendo fines de semana (10.6% del volumen)

**Lo que necesita mejora urgente:**
- Tasa de autoservicio del 4.9% (el bot resuelve muy pocas conversaciones por si solo)
- Tasa de abandono del 53.2% (demasiados clientes se van sin interactuar)
- Tasa de fallo del 44.7% en conversaciones activas
- Alta frustracion en Transferencias (43.8% negativo) y App (43.7% negativo)

**La pregunta estrategica:** El asistente esta sirviendo como un sofisticado directorio telefonico digital. La pregunta es si queremos que siga asi (optimizando el enrutamiento) o si invertimos en convertirlo en un canal de resolucion real (reduciendo derivaciones y aumentando autoservicio).

---

*Reporte generado a partir de datos reales del sistema. Todos los porcentajes y cifras provienen de la base de datos operativa del periodo 28-ene a 03-mar 2026.*
