from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class LoginInfos(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class FuConstituantProduct(BaseModel):
    name: str
    quantity: Optional[float] = None
    unit: str
    unitId: int
    constituantType: Optional[int]


class HealthData(BaseModel):
    airRating: Optional[str]
    eCovFormaldehyde: Optional[str]
    eRadioactive: Optional[str]
    otherHealthInfo: Optional[str]
    isContactDrinkingWater: Optional[bool]
    isContactNotDrinkingWater: Optional[bool]
    healthNumber: Optional[str]
    infosDrinkingWater: Optional[str]
    infosNotDrinkingWater: Optional[str]


class ComfortData(BaseModel):
    comfortHygrothermal: Optional[str]
    comfortAcoustic: Optional[str]
    comfortVisual: Optional[str]
    comfortOlfactory: Optional[str]
    otherComfortInfo: Optional[str]


class ResponsibleOrganism(BaseModel):
    name: Optional[str]
    acronym: Optional[str]
    country: Optional[str]
    address: Optional[str]
    website: Optional[str]


class ResponsibleContact(BaseModel):
    lastName: Optional[str]
    firstName: Optional[str]
    phone: Optional[str]
    fax: Optional[str]
    email: Optional[str]


class IndicatorQuantity(BaseModel):
    indicatorId: int
    indicatorName: Optional[str] = None
    indicatorUnit: Optional[str] = None
    phaseId: int
    phaseName: Optional[str] = None
    quantity: Optional[float] = None

    def populate_indicator_fields(self, indicators: List[dict]):
        for indicator in indicators:
            if indicator["id"] == self.indicatorId:
                self.indicatorName = indicator["nameFr"]
                self.indicatorUnit = indicator["unitName"]
                return

    def populate_phase_name(self, phases: List[dict]):
        for phase in phases:
            if phase["id"] == self.phaseId:
                self.phaseName = phase["nameFr"]
                return


class IndicatorSet(BaseModel):
    id: int
    name: Optional[str] = None
    indicatorQuantities: List[IndicatorQuantity]

    def populate_name(self, mapping: dict):
        self.name = mapping.get(self.id, "Autre norme")

    def populate_indicators(self, indicators: List[dict], phases: List[dict]):
        for i in range(len(self.indicatorQuantities)):
            self.indicatorQuantities[i].populate_indicator_fields(indicators)
            self.indicatorQuantities[i].populate_phase_name(phases)


class EpdShort(BaseModel):
    id: int
    serialIdentifier: str
    name: Optional[str]
    classificationIds: List[int]
    lastUpdate: Optional[datetime]
    isArchived: Optional[bool]


class Epd(BaseModel):
    id: int
    serialIdentifier: str
    name: str
    version: Optional[str]
    issueDate: Optional[datetime]
    declarationType: Optional[int]
    declarationTypeName: Optional[str]
    responsibleOrganism: ResponsibleOrganism
    commercialReferences: Optional[str]
    dvt: Optional[int]
    ufQuantity: Optional[float]
    ufUnit: Optional[str]
    ufDescription: Optional[str]
    carbonBiogenicStorage: Optional[float]
    packagingCarbonBiogenicStorage: Optional[float]
    distanceTransportA4Km: Optional[float]
    productionPlace: Optional[str]
    productionRegionFr: List[str]
    fuConstituantProducts: List[FuConstituantProduct]
    indicatorSet: IndicatorSet


class EpdFull(Epd):
    statut: Optional[int]
    statutName: Optional[str]
    onlineDate: Optional[datetime]
    lastUpdateDate: Optional[datetime]
    expirationDate: Optional[datetime]
    isPep: Optional[bool]
    classificationId: Optional[int]
    classificationId2: Optional[int]
    classificationId3: Optional[int]
    isVerified: Optional[bool]
    verificationDate: Optional[datetime]
    commercialBrands: Optional[str]
    commercialReferencesNumber: Optional[int]
    usageAbility: Optional[str]
    ufUnitId: Optional[int]
    implementationFallRate: Optional[float]
    maintenanceFrequency: Optional[float]
    contentDeclaration: Optional[str]
    characteristicsNotInUf: Optional[str]
    healthData: HealthData
    comfortData: ComfortData
    responsibleContact: ResponsibleContact
    isBtoB: Optional[bool]
    performanceUf: Optional[str]
    performanceUfQuantity: Optional[float]
    performanceUfUnit: Optional[str]
    performanceUfUnitId: Optional[int]
    distanceTransportC2DechetsRecyclesKm: Optional[float]
    distanceTransportC2DechetsValorisesKm: Optional[float]
    distanceTransportC2DechetsEliminesKm: Optional[float]
    registrationDate: Optional[datetime]
