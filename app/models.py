from sqlalchemy import Column, String, Float, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SegmentCondition(Base):
    __tablename__ = "segment_conditions"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, index=True, nullable=False)
    inspection_id = Column(String, index=True, nullable=False)

    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    traversed_percent = Column(Float, nullable=False)
    visible_surface_percent = Column(Float, nullable=False)
    lighting_score = Column(Float, nullable=False)
    camera_stability_score = Column(Float, nullable=False)

    cleanliness_score = Column(Float, nullable=False)
    mechanical_score = Column(Float, nullable=False)
    obstruction_score = Column(Float, nullable=False)
    moisture_score = Column(Float, nullable=False)

    confidence_score = Column(Float, nullable=False)
    confidence_label = Column(String, nullable=False)

    overall_score = Column(Float, nullable=False)
    condition_label = Column(String, nullable=False)
    recommendation = Column(Text, nullable=False)
    urgent_flag = Column(Boolean, default=False, nullable=False)

    evidence_items = relationship(
        "InspectionEvidence",
        back_populates="segment_condition",
        cascade="all, delete-orphan",
    )

    findings = relationship(
        "InspectionFinding",
        back_populates="segment_condition",
        cascade="all, delete-orphan",
    )


class InspectionEvidence(Base):
    __tablename__ = "inspection_evidence"

    id = Column(Integer, primary_key=True, index=True)
    segment_condition_id = Column(Integer, ForeignKey("segment_conditions.id"), nullable=False, index=True)

    file_url = Column(Text, nullable=False)
    file_type = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    quality_score = Column(Float, nullable=False)

    segment_condition = relationship("SegmentCondition", back_populates="evidence_items")


class InspectionFinding(Base):
    __tablename__ = "inspection_findings"

    id = Column(Integer, primary_key=True, index=True)
    segment_condition_id = Column(Integer, ForeignKey("segment_conditions.id"), nullable=False, index=True)

    defect_type = Column(String, nullable=False)
    severity = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_index = Column(Integer, nullable=True)

    segment_condition = relationship("SegmentCondition", back_populates="findings")