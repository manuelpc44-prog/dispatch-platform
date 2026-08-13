from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin (ejemplo RBAC)"])


@router.get("/ping")
def admin_ping(current_user: User = Depends(require_role("ADMINISTRADOR"))) -> dict:
    """Endpoint de prueba: solo ADMINISTRADOR puede acceder. Se reemplaza por los
    endpoints reales de gestión de usuarios en fases posteriores."""
    return {"message": f"Hola {current_user.full_name}, tienes acceso de administrador"}
