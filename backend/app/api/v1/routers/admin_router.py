from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.controllers import admin_controller
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_admin)])


@router.get("/dashboard", response_model=ApiResponse)
def dashboard(db: Session = Depends(get_db_session)):
    return ApiResponse(data=admin_controller.dashboard_stats(db))


@router.get("/users", response_model=ApiResponse)
def list_users(page: int = 1, per_page: int = 20, role: str | None = None, query: str | None = None, db: Session = Depends(get_db_session)):
    return ApiResponse(data=admin_controller.list_users(db, page, per_page, role, query))


@router.patch("/users/{user_id}/status", response_model=ApiResponse)
def update_user_status(user_id: int, is_active: bool, db: Session = Depends(get_db_session)):
    return ApiResponse(data=admin_controller.update_user_status(db, user_id, is_active))


@router.delete("/users/{user_id}", response_model=ApiResponse)
def delete_user(user_id: int, db: Session = Depends(get_db_session)):
    return ApiResponse(data=admin_controller.delete_user(db, user_id))


@router.post("/ml/retrain", response_model=ApiResponse)
def retrain(data_path: str | None = None, db: Session = Depends(get_db_session)):
    return ApiResponse(data=admin_controller.retrain_model(db, data_path))


@router.get("/export/csv", response_model=None)
def export_csv(db: Session = Depends(get_db_session)):
    content = admin_controller.export_csv(db)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=destinations.csv"},
    )


@router.post("/import/csv", response_model=ApiResponse)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    content = (await file.read()).decode("utf-8-sig")
    return ApiResponse(data=admin_controller.import_csv(db, content))
