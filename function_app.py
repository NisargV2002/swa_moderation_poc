"""
function_app.py  —  Azure Functions Entry Point

Purpose:
- Register the FastAPI app (app/main.py) as an Azure Functions ASGI app.
- This single file is all the Azure Functions runtime needs to discover
  and serve every FastAPI route (/projects, /moderate/{id}, etc.).

How it works:
- Azure Functions Python v2 programming model supports ASGI apps natively
  via func.AsgiFunctionApp().
- Every HTTP route defined in app/main.py is automatically exposed as an
  Azure Function HTTP trigger — no per-route function files needed.
- local.settings.json injects environment variables exactly like .env does,
  so config/settings.py and os.getenv() continue to work with zero changes.

Routes available after func start:
  GET  http://localhost:7071/api/
  GET  http://localhost:7071/api/projects
  GET  http://localhost:7071/api/projects/{project_id}
  POST http://localhost:7071/api/moderate/{project_id}
  POST http://localhost:7071/api/moderate/{project_id}?policy_code=REG-01

Note on /api prefix:
  Azure Functions adds /api/ in front of all routes by default when running
  locally. In production (Azure portal) this can be removed via the Function
  App's routePrefix setting in host.json if needed.
"""

import azure.functions as func
from app.main import app as fastapi_app

# Wrap the FastAPI app as an Azure Functions ASGI app.
# AuthLevel.ANONYMOUS means no function key is required to call the API —
# which is correct for a POC behind your own network/UI.
app = func.AsgiFunctionApp(
    app=fastapi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS
)
