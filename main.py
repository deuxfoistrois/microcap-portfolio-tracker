# same main.py code as before omitted here for brevity
from datetime import datetime
import os

# Crear carpeta data si no existe
os.makedirs("data", exist_ok=True)

# Guardar la hora de ejecución en un archivo
with open("data/last_run.txt", "w") as f:
    f.write(f"Run completed at {datetime.utcnow()} UTC\n")
