# Política de seguridad

*Léelo en otros idiomas: [English](SECURITY.md).*

## Este repositorio es intencionalmente vulnerable

`breaking-python-lab` es un lab didáctico para la charla y taller práctico
**Breaking Python: AppSec vs. OffSec**. La rama `main` contiene
**vulnerabilidades de seguridad deliberadas y documentadas** para que las
personas aprendan a encontrarlas y corregirlas. Son una característica, no un
error.

**Por favor, no reportes las vulnerabilidades intencionales.** Cada falla en
`main` está listada en el [README](README.es.md) y mitigada en la rama `fixed`;
no hay nada que divulgar. Los escáneres y bots de seguridad deben tratar este
repositorio como una muestra conocidamente vulnerable.

## Qué *sí* vale la pena reportar

Abre un issue normal de GitHub si encuentras un problema con el lab en sí, como:

- un reto que ya no funciona, o `exploits/poc.py` que no corre;
- un fix en `fixed` que todavía se puede evadir (una brecha real en el código
  *parchado*);
- errores en la documentación, los comandos o las traducciones;
- un problema de build o de dependencias.

## Uso seguro

- Córrelo **solo** en tu propia máquina o en un entorno aislado.
- **No** lo despliegues en un servidor accesible desde Internet. Por defecto la
  app escucha en loopback y Docker publica el puerto solo en `127.0.0.1`.
- **No** ejecutes los exploits contra sistemas que no sean tuyos.

El código se provee con fines educativos bajo los términos de [`LICENSE`](LICENSE).
