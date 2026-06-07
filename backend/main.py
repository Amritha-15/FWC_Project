import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from backend.api.auth import router as auth_router
from backend.api.dashboard import router as dashboard_router
from backend.api.users import router as users_router
from backend.api.departments import router as dept_router
from backend.api.analytics import router as analytics_router
from backend.api.employee import router as employee_router
from backend.api.senior_manager import router as senior_manager_router
from backend.api.admin_management import router as admin_management_router
from backend.api.onboarding import router as onboarding_router
from backend.api.applications import router as applications_router
from backend.api.email_test import router as email_test_router
from backend.api.hr import router as hr_router

# Import WebSocket manager
from backend.websocket.manager import ws_manager
from backend.database import session as db_session



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="HRMS Admin Dashboard API",
    description="Python FastAPI backend serving analytics, monitoring, and admin control dashboards.",
    version="1.0.0"
)


# Initialize DB engine/session on startup and dispose on shutdown
@app.on_event("startup")
async def on_startup():
    try:
        db_session.init_db()
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    try:
        await db_session.close_db()
    except Exception as e:
        logger.error(f"Error closing DB: {e}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred. Please contact administrator."}
    )

# Register REST Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(dept_router)
app.include_router(analytics_router)
app.include_router(employee_router)
app.include_router(senior_manager_router)
app.include_router(admin_management_router)
app.include_router(onboarding_router)
app.include_router(applications_router)
app.include_router(email_test_router)
app.include_router(hr_router)
from backend.api.candidate import router as candidate_router
app.include_router(candidate_router)
from backend.api.ai import router as ai_router
app.include_router(ai_router)
print("✅ AI router registered") 

@app.get("/")
def read_root():
    return {"message": "HRMS Admin Dashboard API is active."}

# ==========================================
# WebSocket Endpoint: ws://localhost:8080/ws/admin
# ==========================================
@app.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; discard any text inputs from client as this is a push-only socket for admins
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("ADMIN_PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
