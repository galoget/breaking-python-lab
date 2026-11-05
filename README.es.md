# Breaking Python Lab

*Léelo en otros idiomas: [English](README.md).*

Laboratorio de la charla y taller práctico (hands-on) **Breaking Python: AppSec vs. OffSec — From Code to Exploit**.

Una aplicación Flask **intencionalmente vulnerable** para que pueda descargar el código, analizarlo, ejecutarlo en local y explotarlo. Cada vulnerabilidad tiene su versión corregida en la rama `fixed`.

> **Advertencia.** Este código es inseguro a propósito. Úselo solo en su propio equipo o en un entorno aislado. No lo despliegue en un servidor accesible desde Internet y no ejecute los exploits contra sistemas que no sean suyos.

> **Alcance y diseño.** Este lab reduce a propósito cada reto a la vulnerabilidad en sí: sin frontend, sin estilos, sin convenciones REST/API — solo la ruta, el `source` (dónde entra la entrada del atacante) y el `sink` (dónde causa daño), marcados con comentarios. Así el foco queda en *por qué* existe la falla y cómo la cierra el fix, sin ruido de UI o framework. Es una herramienta didáctica, no una aplicación pulida.

> **No es un problema de Python.** Estas fallas nacen de *patrones de código* inseguros — confiar en la entrada, mezclar código y datos, elegir un default inseguro — no de Python en sí. Las mismas clases de vulnerabilidad (inyección SQL, inyección de comandos, XXE, SSRF, IDOR, ...) aparecen en Java, PHP, Node.js, C#, Go y cualquier otro ecosistema; solo cambia la sintaxis del sink. Python es solo el vehículo de la charla, y las lecciones se transfieren directamente a cualquier lenguaje que uses.

## Cómo está organizado

| Rama | Contenido |
|------|-----------|
| `main` | Aplicación vulnerable |
| `fixed` | Misma aplicación, con cada falla corregida |

Para ver todas las correcciones a la vez: `git diff main fixed -- app/app.py`

## Releases

Cada rama se publica como un release:

| Release | Rama | Úselo para |
|---------|------|------------|
| [`v1.0.0`](https://github.com/galoget/breaking-python-lab/releases/tag/v1.0.0) | `main` | Atacar el lab — todas las vulnerabilidades están activas |
| [`v1.0.1`](https://github.com/galoget/breaking-python-lab/releases/tag/v1.0.1) | `fixed` | Estudiar las mitigaciones — todo está parchado |

GitHub muestra **`v1.0.1` (fixed) como el release "Latest"**, solo porque tiene el número de versión más alto. Es lo esperado y **no** es por donde se empieza: la etiqueta más nueva es el código *parchado*. Comience en la rama por defecto `main` (`v1.0.0`, vulnerable), explote cada falla y luego pase a `fixed` (`v1.0.1`) para ver cómo se cerró cada una:

```
git checkout main    # vulnerable (v1.0.0) -> explote esto primero
git checkout fixed   # parchado   (v1.0.1) -> compare las correcciones
```

## Vulnerabilidades

| # | Falla | CWE | Endpoint | Corrección en `fixed` |
|---|-------|-----|----------|------------------------|
| 1 | SQL Injection | CWE-89 | `/login?user=` | Consulta parametrizada |
| 2 | Command Injection | CWE-78 | `/ping?host=` | `subprocess` sin shell + validación con `ipaddress` |
| 3 | Path Traversal / LFI | CWE-22 | `/download?file=` | `send_from_directory` |
| 4 | XXE | CWE-611 | `POST /import` | `defusedxml` |
| 5 | XSS reflejado | CWE-79 | `/search?q=` | Plantilla con autoescape |
| 6 | SSTI (Jinja2) | CWE-1336 | `/hello?name=` | Entrada como variable, plantilla fija |
| 7 | Deserialización (`pickle`) | CWE-502 | `/session` (cookie `s`) | Cookie firmada con `itsdangerous` |
| 8 | Deserialización (`yaml.load`) | CWE-502 | `POST /config` | `yaml.safe_load` |
| 9 | SSRF | CWE-918 | `/preview?url=` | Lista de destinos permitidos y bloqueo de IP internas |
| 10 | Control de acceso roto / IDOR | CWE-639 | `/note?id=` | Propiedad verificada desde la sesión firmada |

**Por qué funciona cada fix** (defensa en profundidad, fail-closed, codificación de salida, validación de entrada, allowlisting): ver [`fixes-explained.es.md`](docs/fixes-explained.es.md).

## Inicio rápido

### Con Docker

```
git clone https://github.com/galoget/breaking-python-lab
cd breaking-python-lab
docker compose up --build
```

La aplicación queda en http://127.0.0.1:5000 (solo accesible desde su máquina).

#### Instalar Docker en Debian/Ubuntu

Si aún no tiene Docker, instale el motor y Compose v2 desde los paquetes de la distribución. El nombre del paquete de Compose cambia según la distribución:

```
# Debian / Kali
sudo apt update
sudo apt install -y docker.io docker-compose

# Ubuntu
sudo apt update
sudo apt install -y docker.io docker-compose-v2
```

Luego habilite el servicio y (opcional) permita a su usuario usar Docker sin sudo:

```
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"   # agrega tu usuario al grupo 'docker'; cierra y
                                  # vuelve a iniciar sesión, o ejecuta `newgrp docker`,
                                  # para que el nuevo grupo tenga efecto en tu shell
```

Verifique (ambos paquetes proveen Compose v2, es decir el subcomando `docker compose`):

```
docker --version
docker compose version
```

### Sin Docker

Requiere Python 3.10 o superior y `ping` instalado.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd app
python internal_service.py &     # servicio interno simulado para el reto SSRF
python app.py
```

Una sola instalación con `pip` cubre ambas ramas, así que no necesita reinstalar tras `git checkout fixed`. Todo lo de abajo (las PoC y las herramientas SAST) asume que este entorno virtual está activo (`source .venv/bin/activate`).

### Opcional: atajos con `make`

Un `Makefile` envuelve los comandos usados a lo largo de este README para no tener que reescribirlos. Es **totalmente opcional** — cada target solo ejecuta el mismo comando documentado en otra parte. Ejecute `make help` para listarlos:

| Target | Qué hace |
|--------|----------|
| `make install` | Instala las dependencias de runtime (ambas ramas) |
| `make install-dev` | Instala las herramientas SAST (bandit + semgrep) |
| `make run` | Levanta el lab + el servicio interno simulado (SSRF) |
| `make poc` | Ejecuta todas las pruebas de concepto contra un lab en marcha |
| `make lint` | Revisa el estilo del código (flake8, 79 columnas) |
| `make sast` | Corre análisis estático sobre `app/` (bandit + semgrep) |
| `make docker-up` / `make docker-down` | Levanta / detiene el lab con Docker |
| `make clean` | Elimina la base de datos local y las cachés de Python |

## Cómo practicar: del código al exploit

Siga el método de la charla en cada reto:

1. **Leer el código.** Abra `app/app.py`. Cada función marca con comentarios el `source` y el `sink`.
2. **Entender la falla.** ¿Por qué el dato llega al sink sin control?
3. **Explotar a mano.** Con `curl` o Burp Suite. Ejemplos inocuos:
   - SQLi: `curl "http://127.0.0.1:5000/login?user=x'%20OR%20name='admin'%20--"`
   - SSTI: `curl "http://127.0.0.1:5000/hello?name=%7B%7B7*7%7D%7D"` (debe responder 49)
   - LFI: `curl "http://127.0.0.1:5000/download?file=../.env"`
   - Explotación manual completa (un `curl` real por falla, estilo pentest): vea [`exploits/manual-exploits.es.md`](exploits/manual-exploits.es.md)
4. **Automatizar.** `exploits/poc.py` ejecuta una prueba por vulnerabilidad con cargas inocuas:
   ```
   python exploits/poc.py                  # todas
   python exploits/poc.py --only lfi sqli  # algunas
   ```
5. **Corregir.** Pase a `fixed` y compare: `git checkout fixed`
6. **Verificar y detectar.** Con la aplicación corregida en marcha, `poc.py` debe reportar `0/10` hallazgos y terminar con código de salida `0`. Úselo como prueba de regresión.

## Flags

**No todos los retos tienen flag — es a propósito, por la naturaleza de cada vulnerabilidad.** Solo cuatro fallas exponen un secreto almacenado, así que solo esas esconden un `FLAG{...}` literal para capturar (SQLi, LFI, SSRF, IDOR). Las otras seis (command injection, XXE, XSS, SSTI, pickle, yaml) dan ejecución de código o fuga en el momento, por lo que no hay un string de flag — la explotación exitosa *es* la prueba. Las cuatro flags reales van censuradas abajo a propósito: el prefijo y la ubicación son la pista, no la respuesta.

| # | Reto | Flag (censurada) | Dónde encontrarla |
|---|------|------------------|-------------------|
| 1 | SQL Injection | `FLAG{sqli_****}` | BD, tabla `users` (fila admin) — vía `/login` |
| 2 | Command Injection | *(prueba)* salida de tu comando, ej. `id` → `uid=...` | se ejecuta en el servidor |
| 3 | Path Traversal / LFI | `FLAG{lfi_****}` | `app/.env` — vía `/download` |
| 4 | XXE | *(prueba)* contenido de un archivo local, ej. `/etc/passwd` | lo lee el parser XML |
| 5 | XSS reflejado | *(prueba)* tu `<script>` se ejecuta | en el navegador (lado cliente) |
| 6 | SSTI | *(prueba)* el template evalúa (`{{7*7}}`→`49`) → RCE | en el servidor |
| 7 | Deserialización (pickle) | *(prueba)* tu código corre al cargar `/session` | en el servidor |
| 8 | Deserialización (yaml) | *(prueba)* tu código corre en `POST /config` | en el servidor |
| 9 | SSRF | `FLAG{ssrf_****}` | servicio interno simulado (JSON) — vía `/preview` |
| 10 | Control de acceso roto / IDOR | `FLAG{idor_****}` | BD, tabla `notes` (nota del admin) — vía `/note` |

Una vez que logras ejecución de código (SSTI, pickle, yaml, command injection) o lectura arbitraria de archivos (LFI, XXE), puedes leer cualquier flag almacenada — ese solapamiento es realista.

## Análisis estático (SAST)

Con el entorno virtual activo:

```
pip install -r requirements-dev.txt   # bandit + semgrep (no son deps de runtime)
bandit -r app/
semgrep --config auto app/
```

Compare qué detecta cada herramienta en `main` y en `fixed`. No todas las fallas aparecen: parte del ejercicio es identificar cuáles se escapan. Los resultados reales (versiones exactas, lo que detecta y lo que se le escapa) y las limitaciones del SAST están en [`docs/sast-notes.es.md`](docs/sast-notes.es.md).

## Ejercicio avanzado (fuera de alcance): SSRF y DNS rebinding

> **Fuera de alcance.** La rama `fixed` aplica la mitigación estándar de SSRF (lista blanca explícita más bloqueo de IP internas). El endurecimiento que se describe aquí se deja a propósito como ejercicio y **no** está implementado en `fixed`.

La corrección de SSRF valida el host de destino y luego lo descarga, pero el nombre se resuelve **dos veces**: una en la comprobación (`_is_public`) y otra cuando el cliente HTTP se conecta. Eso es un hueco time-of-check / time-of-use (TOCTOU): un nombre cuyo DNS controla el atacante puede devolver una IP pública durante la comprobación y una IP interna (`127.0.0.1`, `169.254.169.254`, ...) durante la descarga. Esto es **DNS rebinding**.

Se vuelve explotable cuando un atacante controla el DNS de un host que pasa tus comprobaciones — lo más común, una app que descarga una **URL suministrada por el usuario** (webhook, "importar desde URL", preview de enlace) defendida solo con "resolver y comprobar que la IP es pública", o una allowlist que contiene un host cuyo DNS el atacante puede influir. Este lab **no** es explotable: la allowlist es `example.com`, cuyo DNS el atacante no controla, así que la comprobación y la descarga siempre ven la misma IP pública.

Los escenarios concretos y la corrección correcta — resolver una vez, validar todas las IPs devueltas y **fijar (pin)** la IP para la conexión — se explican en [`fixes-explained.es.md`](docs/fixes-explained.es.md#a-fondo-ssrf-y-dns-rebinding).

## Estructura

```
app/
  app.py               Aplicación Flask (vulnerable en main, corregida en fixed)
  internal_service.py  Servicio interno simulado para SSRF (solo 127.0.0.1)
  templates/           Plantillas (search.html, usada por la rama fixed)
  uploads/             Archivos permitidos para descarga
  .env                 Valores FALSOS usados en el reto de LFI
exploits/poc.py                 Pruebas de concepto inocuas y regresión
exploits/manual-exploits.md     Guía de explotación manual con curl (inglés)
exploits/manual-exploits.es.md  Guía de explotación manual con curl (español)
docs/fixes-explained.md         Por qué funciona cada fix (inglés)
docs/fixes-explained.es.md      Por qué funciona cada fix (español)
docs/sast-notes.md              Qué detecta y qué omite el SAST (inglés)
docs/sast-notes.es.md           Qué detecta y qué omite el SAST (español)
SECURITY.md, SECURITY.es.md     Política de seguridad (aviso: vulnerable a propósito)
Dockerfile, docker-compose.yml, start.sh
Makefile                        Atajos de comandos (ejecute `make help`)
.dockerignore, .flake8, .editorconfig
requirements.txt, requirements-dev.txt   Deps de runtime / herramientas dev (SAST)
```

## Licencia

Este proyecto — **código y documentación** — está licenciado bajo [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.es). Consulte [`LICENSE`](LICENSE).

Puede usarlo, compartirlo y adaptarlo con fines **no comerciales**, siempre que **dé crédito** a "Galoget Latorre / Hackem Cybersecurity", enlace a la licencia, indique si hizo cambios, y publique cualquier obra derivada (fork o variante) bajo la **misma** licencia.

Autor: Galoget Latorre · Hackem Cybersecurity · https://hackem.org
