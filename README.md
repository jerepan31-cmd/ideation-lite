# Ideation Lite

Skill ligera para Codex: entender la tarea, presentar un plan, esperar aprobacion, ejecutar los pasos en orden y comprobar el resultado.

Inspirada en [Ideation](https://ideation.engineering/); adaptacion independiente de cuatro etapas, no el plugin oficial.

## Requisitos

Windows, Python 3.9+ y PowerShell. Sin paquetes adicionales, interfaz web ni procesos residentes.

## Instalacion

Clona este repositorio dentro de tu carpeta personal `.agents/skills/ideation-lite`. Si Codex no la muestra, reinicialo.

## Uso

En Codex:

```text
$ideation-lite Organiza y ejecuta esta tarea: [objetivo, limites y resultado esperado]
```

Revisa el plan y responde con tu aprobacion para comenzar. La skill se detiene ante errores y conserva el estado para continuar.

Ayuda CLI desde la raiz del repositorio:

```powershell
python -B scripts/orchestrator.py --help
```

Flujo CLI: `init` → `plan --file plan.json` → `approve --sha SHA --approval-text TEXTO` → `run` → `review` → `finish --review-text EVIDENCIA`. Cada comando requiere `--state C:\ruta\de\trabajo\state.json` antes del subcomando. El estado debe guardarse fuera de la instalacion.

Consulta `SKILL.md` para el formato del plan y las instrucciones completas. La aprobacion queda vinculada al contenido del plan; modificarlo impide su ejecucion. Los registros pueden crecer con el trabajo. La seleccion automatica depende de Codex; el ejecutor es una barrera cooperativa, no un aislamiento de seguridad.
