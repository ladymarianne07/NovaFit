from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProgressPeriod(str, Enum):
    SEMANA = "semana"
    MES = "mes"
    ANIO = "anio"


class ProgressEvaluationRequest(BaseModel):
    """Request payload for progress evaluation endpoint."""

    periodo: ProgressPeriod = Field(default=ProgressPeriod.MES)


class ProgressMetrics(BaseModel):
    """Delta metrics returned by progress evaluator."""

    deltaPeso: float
    deltaGrasa: Optional[float] = None
    deltaMagra: Optional[float] = None


class ProgressEvaluationResponse(BaseModel):
    """Response payload for physical progress evaluation."""

    periodo: str
    score: float = Field(..., ge=-100, le=100)
    estado: str
    resumen: str
    metricas: ProgressMetrics
    advertencias: list[str]


class TimelinePoint(BaseModel):
    fecha: str
    valor: float


class DailyCaloriesPoint(BaseModel):
    fecha: str
    consumidas: float
    meta: float


class DailyMacroPercentagePoint(BaseModel):
    fecha: str
    carbs: float
    protein: float
    fat: float


class ProgressTimelineSeries(BaseModel):
    peso: list[TimelinePoint]
    porcentaje_grasa: list[TimelinePoint]
    porcentaje_masa_magra: list[TimelinePoint]
    calorias_diarias: list[DailyCaloriesPoint]
    macros_porcentaje: list[DailyMacroPercentagePoint]


class ProgressTimelineSummary(BaseModel):
    calorias_semana_real: float
    calorias_semana_meta: float


class ProgressTimelineResponse(BaseModel):
    periodo: str
    rango_inicio: str
    rango_fin: str
    series: ProgressTimelineSeries
    resumen: ProgressTimelineSummary
    advertencias: list[str]
