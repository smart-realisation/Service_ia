"""Schemas pour les mesures de capteurs"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TypeMesureEnum(str, Enum):
    TEMPERATURE = "TEMPERATURE"
    HUMIDITE = "HUMIDITE"
    GAZ = "GAZ"


class UniteMesureEnum(str, Enum):
    CELSIUS = "CELSIUS"
    POURCENT = "POURCENT"
    PPM = "PPM"


class TypeMesure(BaseModel):
    id: int
    code: TypeMesureEnum
    unite: UniteMesureEnum
    description: Optional[str] = None


class MesureBase(BaseModel):
    type_mesure_id: int = Field(..., description="ID du type de mesure (1=TEMPERATURE, 2=HUMIDITE, 3=GAZ)")
    valeur: float = Field(..., description="Valeur de la mesure")


class MesureCreate(MesureBase):
    pass


class MesureResponse(MesureBase):
    id: int
    mesure_at: datetime
    
    class Config:
        from_attributes = True


class MesureWithType(BaseModel):
    id: int
    valeur: float
    mesure_at: datetime
    type_code: TypeMesureEnum
    unite: UniteMesureEnum
    description: Optional[str] = None


class MesuresListResponse(BaseModel):
    success: bool
    total: int
    mesures: List[MesureWithType]


class MesureStats(BaseModel):
    type_code: TypeMesureEnum
    unite: UniteMesureEnum
    count: int
    min_value: float
    max_value: float
    avg_value: float
    last_value: float
    last_mesure_at: datetime


class StatsResponse(BaseModel):
    success: bool
    period: str
    stats: List[MesureStats]
