from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EvidenceIn(BaseModel):
    file_url: str
    file_type: str
    timestamp: datetime
    quality_score: float = Field(ge=0, le=100)


class FindingIn(BaseModel):
    defect_type: str
    severity: int = Field(ge=0, le=3)
    confidence: float = Field(ge=0, le=100)
    evidence_index: Optional[int] = None


class SegmentInspectionIn(BaseModel):
    segment_id: str
    inspection_id: str
    evidence: List[EvidenceIn]
    findings: List[FindingIn]
    traversed_percent: float = Field(ge=0, le=100)
    visible_surface_percent: float = Field(ge=0, le=100)
    lighting_score: float = Field(ge=0, le=100)
    camera_stability_score: float = Field(ge=0, le=100)


class SegmentConditionOut(BaseModel):
    segment_id: str

    traversed_percent: float
    visible_surface_percent: float
    lighting_score: float
    camera_stability_score: float

    cleanliness_score: float
    mechanical_score: float
    obstruction_score: float
    moisture_score: float

    confidence_score: float
    confidence_label: str

    overall_score: float
    condition_label: str
    recommendation: str
    urgent_flag: bool


class EvidenceDBOut(BaseModel):
    id: int
    file_url: str
    file_type: str
    timestamp: datetime
    quality_score: float

    class Config:
        from_attributes = True


class FindingDBOut(BaseModel):
    id: int
    defect_type: str
    severity: int
    confidence: float
    evidence_index: Optional[int] = None

    class Config:
        from_attributes = True


class SegmentConditionDBOut(BaseModel):
    id: int
    segment_id: str
    inspection_id: str
    version: int
    created_at: datetime

    traversed_percent: float
    visible_surface_percent: float
    lighting_score: float
    camera_stability_score: float

    cleanliness_score: float
    mechanical_score: float
    obstruction_score: float
    moisture_score: float

    confidence_score: float
    confidence_label: str

    overall_score: float
    condition_label: str
    recommendation: str
    urgent_flag: bool

    class Config:
        from_attributes = True


class SegmentConditionDetailOut(BaseModel):
    id: int
    segment_id: str
    inspection_id: str
    version: int
    created_at: datetime

    traversed_percent: float
    visible_surface_percent: float
    lighting_score: float
    camera_stability_score: float

    cleanliness_score: float
    mechanical_score: float
    obstruction_score: float
    moisture_score: float

    confidence_score: float
    confidence_label: str

    overall_score: float
    condition_label: str
    recommendation: str
    urgent_flag: bool

    evidence_items: List[EvidenceDBOut]
    findings: List[FindingDBOut]

    class Config:
        from_attributes = True


class InspectionResultsOut(BaseModel):
    inspection_id: str
    results: List[SegmentConditionDBOut]

    class Config:
        from_attributes = True


class InspectionSummaryOut(BaseModel):
    inspection_id: str
    total_results: int
    unique_segments: int
    average_overall_score: float
    urgent_count: int
    good_count: int
    fair_count: int
    poor_count: int
    critical_count: int


class SegmentComparisonOut(BaseModel):
    segment_id: str
    inspection_id_a: str
    version_a: int
    score_a: float
    label_a: str
    created_at_a: datetime

    inspection_id_b: str
    version_b: int
    score_b: float
    label_b: str
    created_at_b: datetime

    score_delta: float
    trend: str

class ReportFindingOut(BaseModel):
    defect_type: str
    severity: int
    confidence: float
    evidence_index: Optional[int] = None


class ReportEvidenceOut(BaseModel):
    file_url: str
    file_type: str
    timestamp: datetime
    quality_score: float


class ReportSegmentOut(BaseModel):
    segment_id: str
    version: int
    created_at: datetime

    traversed_percent: float
    visible_surface_percent: float
    lighting_score: float
    camera_stability_score: float

    cleanliness_score: float
    mechanical_score: float
    obstruction_score: float
    moisture_score: float

    confidence_score: float
    confidence_label: str
    overall_score: float
    condition_label: str
    recommendation: str
    urgent_flag: bool

    findings: List[ReportFindingOut]
    evidence_items: List[ReportEvidenceOut]


class ReportSummaryOut(BaseModel):
    inspection_id: str
    total_segments: int
    average_overall_score: float
    urgent_count: int
    good_count: int
    fair_count: int
    poor_count: int
    critical_count: int


class InspectionReportOut(BaseModel):
    inspection_id: str
    generated_at: datetime
    summary: ReportSummaryOut
    urgent_segments: List[ReportSegmentOut]
    segments: List[ReportSegmentOut]