# DIAGRAMA DE ARQUITECTURA DEL SISTEMA
## Sistema Distribuido de Liquidación de Sueldos

### DESCRIPCIÓN DEL DIAGRAMA

El diagrama representa la arquitectura completa del sistema distribuido implementado para el TP3 de DevOps y Redes.

---

## COMPONENTES DEL SISTEMA

### 1. CLIENTES (Color Celeste)

**Cliente Web**
- Dashboard HTML/JavaScript
- Se sirve mediante servidor HTTP Python en puerto 8080
- Se comunica con el backend vía HTTP/JSON

**Cliente Mobile**
- Aplicación móvil (representación conceptual)
- Acceso vía API REST

**Cliente Python**
- Script en Python (cliente.py)
- Se conecta directamente a los servidores socket vía TCP
- No requiere API REST como intermediario

---

### 2. GATEWAY API REST (Color Naranja)

**Flask API - Puerto 5000**
- Punto de entrada para clientes web y móviles
- Convierte peticiones HTTP/JSON a comunicación Socket TCP
- Endpoints implementados:
  - POST /api/liquidacion
  - POST /api/reporte
  - POST /api/archivo-bancario
  - POST /api/cargas-sociales
  - GET /health
- Archivo: src/api/rest_api.py

---

### 3. SERVIDORES SOCKET (Color Violeta)

**Socket Server 1 - Puerto 9001**
**Socket Server 2 - Puerto 9002**
**Socket Server 3 - Puerto 9003**

- Escuchan conexiones TCP
- Implementan pool de hilos para manejar múltiples clientes simultáneamente
- Reciben tareas y las publican en las colas de RabbitMQ correspondientes
- Balanceo de carga: Los clientes pueden conectarse a cualquier servidor
- Archivo: src/servidor/socket_server.py

---

### 4. RABBITMQ (Color Verde)

**Puerto 5672 | Management: 15672**

**Colas implementadas:**

1. **Cola: liquidacion**
   - Tareas de cálculo de liquidaciones de sueldos
   
2. **Cola: reportes**
   - Tareas de generación de reportes (PDFs, recibos)
   
3. **Cola: archivos_bancarios**
   - Tareas de generación de archivos bancarios
   
4. **Cola: cargas_sociales**
   - Tareas de cálculo de cargas sociales y declaraciones juradas

**Función:**
- Desacopla los servidores de los workers
- Garantiza que las tareas no se pierdan
- Permite escalabilidad horizontal

---

### 5. WORKERS ESPECIALIZADOS (Color Rosa)

**Worker Liquidación - Pool: 5 hilos**
- Consume de cola: liquidacion
- Funciones:
  - Cálculo de sueldo bruto
  - Cálculo de deducciones
  - Cálculo de sueldo neto
  - Cálculo de cargas sociales patronales
- Archivo: src/workers/worker_liquidacion.py

**Worker Reportes - Pool: 5 hilos**
- Consume de cola: reportes
- Funciones:
  - Generación de recibos de sueldo (PDF)
  - Reportes sindicales
  - Papeles de trabajo
- Archivo: src/workers/worker_reportes.py

**Worker Archivos - Pool: 3 hilos**
- Consume de cola: archivos_bancarios
- Funciones:
  - Generación de archivos TXT formato bancario
  - Formato posicional estándar argentino
  - Validación de CBU
- Archivo: src/workers/worker_archivos.py

**Worker Cargas - Pool: 3 hilos**
- Consume de cola: cargas_sociales
- Funciones:
  - Declaraciones juradas ARCA/AFIP
  - Liquidaciones para obras sociales
  - Cálculo de aportes patronales
- Archivo: src/workers/worker_cargas.py

---

### 6. ALMACENAMIENTO (Color Amarillo)

**PostgreSQL - Puerto 5432**
- Base de datos principal del sistema
- Tablas implementadas:
  - empresas
  - empleados
  - convenios
  - conceptos
  - liquidaciones
  - tareas
- Todos los workers leen y escriben en esta base de datos

**MinIO / S3**
- Almacenamiento de archivos generados
- PDFs de recibos de sueldo
- Archivos bancarios TXT
- Reportes sindicales
- Actualmente simulado (los archivos se guardan localmente)

---

## FLUJO DE DATOS

### Flujo 1: Cliente Web/Mobile
```
Cliente Web/Mobile → API REST (HTTP/JSON) → Socket Server (TCP) → 
RabbitMQ (Cola) → Worker (Procesa) → PostgreSQL/S3 (Guarda)
```

### Flujo 2: Cliente Python
```
Cliente Python → Socket Server (TCP directo) → RabbitMQ (Cola) → 
Worker (Procesa) → PostgreSQL/S3 (Guarda)
```

---

## CARACTERÍSTICAS TÉCNICAS

### Concurrencia
- **Servidores Socket**: Pool de hilos para manejar múltiples conexiones
- **Workers**: Pool de hilos (3-5 según especialización)
- **Total**: Sistema puede procesar múltiples tareas en paralelo

### Escalabilidad
- **Horizontal**: Se pueden agregar más servidores socket o workers
- **Vertical**: Se puede aumentar el pool de hilos en cada componente

### Alta disponibilidad
- **3 servidores socket**: Si uno falla, los otros continúan operando
- **RabbitMQ**: Garantiza entrega de mensajes
- **Workers independientes**: Si uno falla, no afecta a los demás

### Desacoplamiento
- Clientes no conocen a los workers
- Servidores socket no conocen a los workers
- RabbitMQ actúa como intermediario asíncrono

---

## PUERTOS UTILIZADOS

| Componente | Puerto | Protocolo |
|------------|--------|-----------|
| API REST | 5000 | HTTP |
| Socket Server 1 | 9001 | TCP |
| Socket Server 2 | 9002 | TCP |
| Socket Server 3 | 9003 | TCP |
| RabbitMQ | 5672 | AMQP |
| RabbitMQ Management | 15672 | HTTP |
| PostgreSQL | 5432 | TCP |
| Frontend HTTP | 8080 | HTTP |

---

## ARCHIVOS DEL DIAGRAMA

- **arquitectura-sistema-limpio.svg**: Imagen vectorial del diagrama (versión limpia)
- **arquitectura-sistema.mermaid**: Código Mermaid (puede visualizarse en GitHub)
- **DIAGRAMA-EXPLICACION.md**: Este documento explicativo

---

## DIFERENCIAS CON EL DIAGRAMA ORIGINAL

### Cambios implementados:

1. **API REST agregada**: No estaba en el enunciado, fue agregada para acceso web/mobile
2. **3 servidores socket**: El enunciado pedía "servidores workers", implementamos 3 servidores socket + 4 workers especializados
3. **4 workers especializados**: Mayor granularidad que lo pedido en el enunciado
4. **Puertos específicos**: El diagrama ahora muestra todos los puertos reales utilizados
5. **Pool de hilos especificado**: Cada componente muestra su cantidad de hilos
6. **Colas específicas**: 4 colas nombradas en lugar de una genérica
7. **Cliente Python directo**: Además del acceso web, hay acceso directo por socket

### Lo que cumple con el enunciado:

- Clientes (móviles, web)
- Balanceador de carga (3 servidores socket que distribuyen)
- Servidores workers (implementado como servidores + workers separados)
- Cola de mensajes (RabbitMQ con 4 colas)
- Almacenamiento distribuido (PostgreSQL + S3)

---

## MEJORAS EN ESTA VERSIÓN DEL DIAGRAMA

### Organización visual:
- Componentes organizados en 6 columnas verticales
- Flujo de izquierda a derecha (cliente → almacenamiento)
- Separación clara entre capas del sistema

### Flechas mejoradas:
- Flechas sólidas para conexiones principales
- Flechas punteadas para conexiones alternativas/redundantes
- Sin superposiciones confusas
- Trayectorias más directas

### Información adicional:
- Notas de flujo de datos en la parte inferior
- Leyenda de componentes clave
- Nota técnica explicativa

---

**Autor:** Ayelen Rojas  
**Materia:** DevOps y Redes  
**Trabajo Práctico:** TP3 - Sistema Distribuido Cliente-Servidor  
**Fecha:** Noviembre 2025