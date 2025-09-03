
🚀 Viaje al Corazón del Dato: Un Pipeline de Inteligencia de Negocio para el Futuro
1. La Misión: De Datos a Decisiones
Imagina una empresa que crece a la velocidad de la luz, con información valiosa dispersa en archivos, bases de datos y APIs. Cada día, el equipo de liderazgo necesita tomar decisiones cruciales, pero la información es un laberinto.

Nuestro proyecto es la solución a ese desafío. Hemos construido un pipeline de datos robusto y automatizado que actúa como una autopista digital, llevando los datos desde sus orígenes dispares hasta un destino único y estructurado, listo para ser transformado en inteligencia de negocio.

Como prueba de concepto, hemos modelado un escenario real: analizamos el mercado de alquileres de Airbnb en Nueva York, enriqueciendo la data con la cotización del dólar para entender el valor real de cada propiedad. Esta es la base para una toma de decisiones más estratégica y efectiva.

2. La Arquitectura: Un Ecosistema de Servicios Gestionados
Para esta misión, hemos elegido a Google Cloud Platform (GCP) como nuestro aliado principal. Sus servicios gestionados nos permiten enfocarnos en la lógica del negocio sin preocuparnos por la infraestructura.

El Almacén de Origen (Data Lake): Google Cloud Storage (GCS)

Aquí es donde aterrizan nuestros datos crudos. Es como un gran almacén digital donde guardamos todo, tal como llega, sin procesar.

El Cerebro Analítico (Data Warehouse): Google BigQuery

Este es el corazón de nuestra solución. BigQuery es un Data Warehouse masivamente escalable que puede procesar petabytes de datos en segundos. Es donde transformamos los datos crudos en conocimiento estructurado.

El Cazador de Datos (Extracción): Python & Docker

Un script de Python, empaquetado en un contenedor de Docker, se encarga de ir a buscar datos frescos de APIs externas (como la cotización del dólar del BCRA). Es un agente portátil y eficiente que hace el trabajo pesado.

El Director de Orquesta (Automatización): Apache Airflow

Airflow es nuestro director de orquesta. Define la secuencia de tareas, desde la ingesta hasta la transformación, asegurando que todo se ejecute en el orden correcto y en el momento preciso. Es el motor que automatiza todo el proceso.

El Aseguramiento de Calidad (CI/CD): GitHub Actions

Nuestras "pruebas de control de calidad" están automatizadas con GitHub Actions. Cada vez que hacemos un cambio en el código, un robot lo revisa y se asegura de que no haya errores antes de implementarlo, garantizando la estabilidad del pipeline.

3. El Flujo de Trabajo: Cómo los Datos se Convierten en Conocimiento
1. 📥 Recolección (Extract & Load):

Nuestro cazador de datos (script Python) viaja a la API del BCRA, obtiene la cotización del dólar y la deposita en nuestro almacén digital (GCS).

Simultáneamente, los datos de Airbnb se cargan directamente en nuestro cerebro analítico (BigQuery), listo para ser procesado.

2. ✨ Transformación (Transform):

Aquí es donde ocurre la magia. Con una sola instrucción en SQL, le decimos a BigQuery que limpie, estandarice y combine la información. Los datos de Airbnb se enriquecen con la cotización del dólar, convirtiendo los precios de USD a ARS.

3. 🎵 Orquestación y Automatización:

Airflow se encarga de que todo este proceso se ejecute de forma diaria, garantizando que el equipo de negocio siempre tenga acceso a la información más reciente. Si algo falla, Airflow nos alerta para que podamos actuar rápidamente.

4. 📊 Análisis y Descubrimiento:

Finalmente, un notebook de Jupyter se conecta a la información ya procesada en BigQuery. Usando gráficos y tablas, respondemos preguntas clave de negocio: ¿Cuál es el precio promedio por barrio? ¿Qué tipo de alojamiento genera más ingresos?

4. Estructura del Proyecto
La organización de nuestros archivos está diseñada para la claridad y la colaboración.

PI_M3_Desarrollo de Pipeline de Datos/
├── .github/                  # Flujos de trabajo de automatización
├── airflow_project/                  # Directorio para la orquestación (Airflow DAGs)
├── documentos/                     # Documentación de diseño
├── imgagen_arquitectura_cloud                      # Diagramas visuales de la arquitectura
├── data_airflow/                      # Código fuente principal (scripts, notebooks)
└── README.md             
5. Conclusión: La Siguiente Fase del Viaje
Este proyecto es una prueba contundente de que con la estrategia adecuada y las herramientas correctas, podemos convertir un laberinto de datos en un mapa claro para la toma de decisiones. Es una solución robusta, escalable y automatizada, lista para ser adaptada a cualquier desafío de negocio.
