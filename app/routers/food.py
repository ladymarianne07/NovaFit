from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db.database import get_database_session
from ..schemas.food import FoodParseCalculateResponse, FoodParseRequest
from ..services.food_service import FoodService, FoodServiceError


router = APIRouter(prefix="/food", tags=["food"])


@router.post("/parse-and-calculate", response_model=FoodParseCalculateResponse)
async def parse_and_calculate_food(
    payload: FoodParseRequest,
    db: Session = Depends(get_database_session),
):
    """Parse food text, resolve USDA calories, store entry, and return total calories."""
    try:
        result = FoodService.parse_and_calculate(db=db, text=payload.text)
        return result
    except FoodServiceError as exc:
        error_code = str(exc)

        if error_code == "invalid_domain":
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"error": "invalid_domain"},
            )

        if error_code in {"insufficient_data", "malformed_parser_response"}:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"error": "insufficient_data"},
            )

        if error_code in {"invalid_json_response", "malformed_ai_response", "empty_ai_response"}:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": "invalid_parser_response"},
            )

        if error_code in {"missing_gemini_api_key", "gemini_request_failed"}:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": error_code},
            )

        if error_code == "missing_usda_api_key":
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "USDA API key is not configured"},
            )

        if error_code in {"food_not_found", "no_calorie_data", "usda_request_failed", "unsupported_unit", "low_similarity_match"}:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": error_code},
            )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "food_processing_failed"},
        )
