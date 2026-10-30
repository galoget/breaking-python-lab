# Breaking Python Lab

*Léelo en otros idiomas: [English](README.md).*

Laboratorio de la charla **Breaking Python: AppSec vs. OffSec — From Code to Exploit**.

Una aplicación Flask **intencionalmente vulnerable** para que pueda descargar el código, analizarlo, ejecutarlo en local y explotarlo. Cada vulnerabilidad tiene su versión corregida en la rama `fixed`.

> **Advertencia.** Este código es inseguro a propósito. Úselo solo en su propio equipo o en un entorno aislado. No lo despliegue en un servidor accesible desde Internet y no ejecute los exploits contra sistemas que no sean suyos.

## Cómo está organizado

| Rama | Contenido |
|------|-----------|
| `main` | Aplicación vulnerable |
| `fixed` | Misma aplicación, con cada falla corregida |

Para ver todas las correcciones a la vez: `git diff main fixed -- app/app.py`

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

## Inicio rápido

### Con Docker

```
git clone https://github.com/galoget/breaking-python-lab
cd breaking-python-lab
docker compose up --build
```

La aplicación queda en http://127.0.0.1:5000 (solo accesible desde su máquina).

#### Instalar Docker en Debian/Ubuntu

Si aún no tiene Docker, instale el motor y el plugin de Compose desde los paquetes de la distribución:

```
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"   # cierre y reabra la sesión para usar docker sin sudo
```

Verifique la instalación:

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

Todo lo de abajo (las PoC y las herramientas SAST) asume que este entorno virtual está activo (`source .venv/bin/activate`).

## Cómo practicar: del código al exploit

Siga el método de la charla en cada reto:

1. **Leer el código.** Abra `app/app.py`. Cada función marca con comentarios el `source` y el `sink`.
2. **Entender la falla.** ¿Por qué el dato llega al sink sin control?
3. **Explotar a mano.** Con `curl` o Burp Suite. Ejemplos inocuos:
   - SQLi: `curl "http://127.0.0.1:5000/login?user=x'%20OR%20name='admin'%20--"`
   - SSTI: `curl "http://127.0.0.1:5000/hello?name=%7B%7B7*7%7D%7D"` (debe responder 49)
   - LFI: `curl "http://127.0.0.1:5000/download?file=../.env"`
   - Explotación manual completa (un `curl` real por falla, estilo pentest): vea [`exploits/manual-exploits.md`](exploits/manual-exploits.md)
4. **Automatizar.** `exploits/poc.py` ejecuta una prueba por vulnerabilidad con cargas inocuas:
   ```
   python exploits/poc.py                  # todas
   python exploits/poc.py --only lfi sqli  # algunas
   ```
5. **Corregir.** Pase a `fixed` y compare: `git checkout fixed`
6. **Verificar y detectar.** Con la aplicación corregida en marcha, `poc.py` debe reportar `0/9` hallazgos y terminar con código de salida `0`. Úselo como prueba de regresión.

Pistas escalonadas para los retos tipo CTF: las banderas tienen el formato `FLAG{...}` y están en la base de datos, en `app/.env` y en el servicio interno simulado.

## Análisis estático (SAST)

Con el entorno virtual activo:

```
pip install bandit semgrep
bandit -r app/
semgrep --config auto app/
```

Compare qué detecta cada herramienta en `main` y en `fixed`. No todas las fallas aparecen: parte del ejercicio es identificar cuáles se escapan.

## Ejercicio avanzado (fuera de alcance): SSRF y DNS rebinding

> **Fuera de alcance.** La rama `fixed` aplica la mitigación estándar de SSRF (lista blanca explícita más bloqueo de IP internas). El endurecimiento que se describe aquí se deja a propósito como ejercicio y **no** está implementado en `fixed`.

La corrección de SSRF valida el host de destino y luego lo descarga, pero el nombre se resuelve **dos veces**: una en la comprobación (`_is_public`) y otra cuando el cliente HTTP se conecta. Eso es un hueco time-of-check / time-of-use (TOCTOU): un nombre cuyo DNS controla el atacante puede devolver una IP pública durante la comprobación y una IP interna (`127.0.0.1`, `169.254.169.254`, ...) durante la descarga. Esto es **DNS rebinding**.

Con la lista blanca por defecto (`example.com`) no es explotable, porque el atacante no controla el DNS de ese dominio. Solo importa si en la lista blanca hay un host cuyo DNS controla un atacante.

Cómo se cerraría (resolver una sola vez, validar y conectar a esa IP exacta — "fijar"/pin la IP):

- Resolver el nombre una vez, validar **todas** las IPs devueltas (rechazar rangos privados, loopback, link-local, CGNAT y reservados, además de IPv6 con IPv4 mapeada) y conectar solo a una IP validada manteniendo la cabecera `Host` original y el SNI de TLS. Un `HTTPAdapter` de `requests` / pool de `urllib3` personalizado es la forma limpia de hacerlo sin romper HTTPS.
- O validar la IP real del par **después** de conectar (`socket.getpeername()`) y abortar si no es pública.
- Revalidar cada salto si algún día se permiten redirecciones (la corrección mantiene `allow_redirects=False`).
- A nivel de infraestructura: un proxy de egress dedicado sin ruta a rangos internos, un network namespace restringido, o IMDSv2 en la nube con límite de saltos.

## Estructura

```
app/
  app.py               Aplicación Flask (vulnerable en main, corregida en fixed)
  internal_service.py  Servicio interno simulado para SSRF (solo 127.0.0.1)
  templates/           Plantillas
  uploads/             Archivos permitidos para descarga
  .env                 Valores FALSOS usados en el reto de LFI
exploits/poc.py              Pruebas de concepto inocuas y regresión
exploits/manual-exploits.md  Guía de explotación manual con curl (estilo pentest)
Dockerfile, docker-compose.yml, start.sh
```

## Licencia

MIT. Consulte `LICENSE`.

Autor: Galoget Latorre · Hackem Cybersecurity · https://hackem.org
