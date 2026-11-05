# Notas de SAST: qué detectan (y qué no) las herramientas

*Léelo en otros idiomas: [English](sast-notes.md).*

El análisis estático (SAST) escanea el código fuente en busca de patrones riesgosos sin ejecutarlo. Este lab es un buen lugar para ver **qué hace bien el SAST y dónde falla** — un punto central de la charla: las herramientas encuentran *patrones*, las personas encuentran *lógica*.

Los resultados de abajo son **reales**, producidos corriendo las herramientas sobre este repo. Son una foto del momento: los paquetes de reglas cambian con el tiempo, así que vuelve a correrlos tú.

## Entorno y comandos exactos

```
Python   3.14.7
bandit   1.9.4
semgrep  1.183.0
```

Con el entorno virtual activo (`pip install -r requirements-dev.txt`), corre en cada rama:

```
# en main (vulnerable), luego: git checkout fixed, y corre de nuevo
bandit -r app/
semgrep --config auto app/
```

> `semgrep --config auto` descarga un paquete de reglas del registro de Semgrep (requiere red) y habilita métricas anónimas. Sin red, fija un paquete local/registro, p. ej. `semgrep --config p/python app/`.

## Resultados por reto en `main` (vulnerable)

| # | Vulnerabilidad | bandit | semgrep | Detectada por |
|---|----------------|--------|---------|---------------|
| 1 | SQL Injection | `B608` (Media, confianza Baja) | `tainted-sql-string`, `formatted-sql-query`, `sql-injection-db-cursor-execute` | ambas |
| 2 | Command Injection | `B605` start_process_with_a_shell (**Alta**) | `dangerous-system-call` | ambas |
| 3 | Path Traversal / LFI | — | — | **ninguna** |
| 4 | XXE | — | — | **ninguna** |
| 5 | XSS reflejado | `B704` markupsafe_markup_xss (Media) | `explicit-unescape-with-markup` | ambas |
| 6 | SSTI | — | `dangerous-template-string`, `render-template-string` | solo semgrep |
| 7 | Deserialización (pickle) | `B301`/`B403` (Media/Baja) | `insecure-deserialization`, `avoid-pickle` | ambas |
| 8 | Deserialización (yaml) | `B506` yaml_load (Media) | `avoid-pyyaml-load` | ambas |
| 9 | SSRF | — | `ssrf-requests`, `ssrf-injection-requests` | solo semgrep |
| 10 | Control de acceso roto / IDOR | — | — | **ninguna** |

**Cobertura:** bandit marcó 5 de 10, semgrep 7 de 10. **Incluso combinadas, 3 de 10 se escapan por completo: Path Traversal / LFI, XXE e IDOR** — incluyendo Control de acceso roto, la categoría #1 de OWASP.

Conteos crudos (hay solapamiento — varias reglas pueden caer en una línea): bandit reportó **7 issues** en `main` (1 Alta, 4 Medias, 2 Bajas); semgrep reportó **25 findings** en 15 reglas.

## Antes vs después (`main` → `fixed`)

| Herramienta | `main` | `fixed` |
|-------------|--------|---------|
| bandit | 7 issues (incl. 1 Alta, 4 Medias) | 3 issues (todos **Bajos**) |
| semgrep | 25 findings / 15 reglas | 8 findings / 3 reglas |

Los findings *peligrosos* desaparecen en `fixed` — pero lo que queda son **todos falsos positivos**, lo cual es en sí una lección:

- **bandit en `fixed`:** `B404` (import de subprocess), `B607` (ruta parcial `ping`), `B603` (subprocess "revisar entrada no confiable"). Todos **Bajos** y benignos: el fix corre `ping` con una lista de argumentos (sin shell) *y* valida la entrada como IP. El escáner no puede ver que la entrada ya es segura.
- **semgrep en `fixed`:** `render-template-string` (×6) y `ssrf-requests` (×2). Todos falsos positivos: las plantillas son constantes con variables autoescapadas, y la petición pasa por una allowlist + bloqueo de IP internas. El escáner marca la *llamada a la función*, no la *seguridad a su alrededor*.

## Por qué el SAST se pierde cosas (y sobre-reporta)

1. **No razona sobre autorización ni lógica de negocio.** El IDOR es invisible para ambas herramientas en ambas ramas: decidir *quién puede leer qué nota* es una política que el escáner no modela. Los fallos de control de acceso son la categoría #1 de OWASP y los más difíciles para SAST.
2. **El contexto derrota al pattern matching.** El XXE aquí arma un objeto parser con `resolve_entities=True` y lo usa en otro lado; el LFI concatena una ruta. Ninguno coincidió con una regla, porque la propiedad peligrosa está repartida entre sentencias en vez de en un único sink reconocible.
3. **Los falsos positivos son la norma en código seguro.** Cada finding en `fixed` es un falso positivo. Alguien debe triar cada uno — "¿esto es *realmente* explotable?" — trabajo manual y con mentalidad ofensiva. La fatiga de alertas hace que se descarten bugs reales.
4. **La severidad y la confianza son aproximadas.** bandit calificó una inyección SQL funcional como `Media / confianza Baja`, y levantó el secreto desechable del lab (`B105`) y un simple `import pickle` (`B403`) como issues — ruido que compite con el finding Alto real.
5. **Las herramientas no concuerdan.** semgrep detectó SSTI y SSRF; bandit no. bandit detectó el string hardcodeado; semgrep no lo trató igual. Usa más de una — y aun así no asumas cobertura total.

## Conclusión

El SAST es una primera pasada rápida que detecta de forma fiable los sinks conocidos de inyección y deserialización, pero **no** reemplaza la revisión manual ni el testing ofensivo. En este lab, dos herramientas de la industria juntas dejaron **30%** de las vulnerabilidades sin detectar — justo las que necesitan una persona que entienda la aplicación: lógica, contexto y autorización. Esa brecha es todo el punto de combinar AppSec con OffSec.

## Reprodúcelo

```
git checkout main  && bandit -r app/ ; semgrep --config auto app/
git checkout fixed && bandit -r app/ ; semgrep --config auto app/
```

Compara la salida contra `exploits/poc.py` (que prueba lo que *realmente* es explotable) y la [guía manual](../exploits/manual-exploits.es.md).
