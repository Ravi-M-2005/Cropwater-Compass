"""
History API Routes
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional

from backend.app.schemas.schemas import HistoryStatsResponse
from backend.app.services.history import (
    get_history,
    get_history_by_id,
    delete_prediction,
    clear_history,
    get_history_stats
)

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("", response_model=List[Dict[str, Any]])
def list_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    crop_type: Optional[str] = Query(None),
    soil_type: Optional[str] = Query(None)
):
    """Retrieves paginated historical irrigation prediction runs."""
    # Ensure types if function is invoked directly in Python
    l_val = limit.default if hasattr(limit, "default") else limit
    o_val = offset.default if hasattr(offset, "default") else offset
    c_val = crop_type.default if hasattr(crop_type, "default") else crop_type
    s_val = soil_type.default if hasattr(soil_type, "default") else soil_type
    if c_val is not None and hasattr(c_val, "default"):
        c_val = None
    if s_val is not None and hasattr(s_val, "default"):
        s_val = None

    return get_history(limit=int(l_val), offset=int(o_val), crop_type=c_val, soil_type=s_val)


@router.get("/stats", response_model=HistoryStatsResponse)
def get_stats():
    """Returns analytics aggregations on historical predictions for dashboard charts."""
    return get_history_stats()


@router.get("/{pred_id}")
def get_single_prediction(pred_id: str):
    """Retrieves a single prediction run by unique ID."""
    record = get_history_by_id(pred_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
    return record


@router.delete("/{pred_id}")
def delete_single_prediction(pred_id: str):
    """Deletes a specific prediction entry from history."""
    success = delete_prediction(pred_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
    return {"message": f"Prediction {pred_id} deleted successfully."}


@router.delete("")
def clear_all_history():
    """Clears all historical prediction logs."""
    count = clear_history()
    return {"message": f"Successfully cleared {count} prediction records."}
