from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_current_user
from ..db.database import get_database_session
from ..db.models import User
from ..schemas.food import FoodParseCalculateResponse, FoodParseLogResponse, FoodParseRequest
from ..services.food_service import FoodService, FoodServiceError
from ..services.food_aggregator_service import FoodAggregatorService
from ..schemas.food_normalized import FoodNormalized


router = APIRouter(prefix="/food", tags=["food"])


@router.post("/parse-and-calculate", response_model=FoodParseCalculateResponse)
async def parse_and_calculate_food(
    payload: FoodParseRequest,
    db: Session = Depends(get_database_session),
):
    """Parse food text, resolve USDA calories, store entry, and return total calories."""
    try:
        result = await run_in_threadpool(FoodService.parse_and_calculate, db, payload.text)
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

        if error_code == "gemini_quota_exceeded":
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": error_code},
            )

        if error_code in {"missing_gemini_api_key", "gemini_request_failed", "gemini_model_not_found"}:
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


@router.get("/search-multi")
async def search_multi_source_food(
    query: str,
    db: Session = Depends(get_database_session),
) -> list[FoodNormalized]:
    """
    Search for food across multiple sources (USDA, OpenFoodFacts, FatSecret).
    
    Returns ranked results (top 5) with confidence scores.
    Prioritizes barcodes → OpenFoodFacts, generic foods → USDA.
    """
    aggregator = FoodAggregatorService()
    results = await aggregator.search_food(query=query, db=db)
    return results


@router.post("/parse-and-log", response_model=FoodParseLogResponse)
async def parse_and_log_food(
    payload: FoodParseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session),
):
    """Parse free-text meals, split by meal types, log nutrition, and return itemized totals."""
    try:
        user_id: int = current_user.id  # type: ignore
        result = await run_in_threadpool(FoodService.parse_and_log_meals, db, user_id, payload.text)
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

        if error_code == "gemini_quota_exceeded":
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": error_code},
            )

        if error_code in {"missing_gemini_api_key", "gemini_request_failed", "gemini_model_not_found"}:
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
