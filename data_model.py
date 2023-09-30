from datetime import date
from sqlalchemy import ForeignKey, Integer, String, Float, Date, Time, Boolean, Column
from sqlalchemy.orm import (DeclarativeBase, Mapped, class_mapper,
                            mapped_column, relationship)
import uuid
from sqlalchemy.ext.hybrid import HybridExtensionType


class Base(DeclarativeBase):
    def to_dict(self):
        """Converts the class instance into a dictionary with all the columns and hybrid_properties as keys."""
        return {c: getattr(self, c) for c in get_columns(self.__class__)}


def get_columns(model):
    """Returns all the columns of the model class."""
    columns = [c.key for c in class_mapper(model).columns]
    hybrid_columns = [
        c.__name__
        for c in class_mapper(model).all_orm_descriptors
        if c.extension_type == HybridExtensionType.HYBRID_PROPERTY
    ]

    return columns + hybrid_columns


class FailureTypeCode(Base):
    __tablename__ = 'FailureTypeCode'
    ID: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4)
    Code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    Description: Mapped[str] = mapped_column(String)


class FailureTypeCodeChangeHistory(Base):
    __tablename__ = 'FailureTypeCodeChangeHistory'
    ID: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4)
    FailureTypeCodeID: Mapped[str] = mapped_column(
        String(36), ForeignKey('FailureTypeCode.ID'))
    FailureFrequency: Mapped[float] = mapped_column(Float)
    NumberOfComponents: Mapped[int] = mapped_column(Integer)
    StartDate: Mapped[date] = mapped_column(Date, nullable=False)
    EndDate: Mapped[date] = mapped_column(Date, nullable=True)


class MaintenanceGroup(Base):
    __tablename__ = 'MaintenanceGroup'
    ID: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4)
    Code: Mapped[str] = mapped_column(
        String, nullable=False, unique=True)
    Description: Mapped[str] = mapped_column(String)


class ObjectCode(Base):
    __tablename__ = 'ObjectCode'
    ID: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4)
    # renamed to avoid conflict with class name
    Code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    Description: Mapped[str] = mapped_column(String)


class MalfunctionRecord(Base):
    __tablename__ = 'MalfunctionRecord'
    ID: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4)
    MaintenanceGroupID: Mapped[str] = mapped_column(
        String(36), ForeignKey('MaintenanceGroup.ID'))
    MalfunctionNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    ObjectCodeID: Mapped[str] = mapped_column(
        String(36), ForeignKey('ObjectCode.ID'))
    Description: Mapped[str] = mapped_column(String)
    EventDate: Mapped[date] = mapped_column(Date, nullable=False)
    LastTestDate: Mapped[date] = mapped_column(Date, nullable=True)
    EventTime: Mapped[Time] = mapped_column(Time, nullable=True)
    Observable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    FailureTypeCodeID: Mapped[str] = mapped_column(
        String(36), ForeignKey('FailureTypeCode.ID'))


class ObjectLifetime(Base):
    __tablename__ = 'ObjectLifetime'
    ID: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=str(uuid.uuid4()))
    ObjectCodeID: Mapped[str] = mapped_column(
        String(36), ForeignKey('ObjectCode.ID'))
    StartDate: Mapped[date] = mapped_column(Date, nullable=False)
    StartTime: Mapped[Time] = mapped_column(Time, nullable=True)
    EndDate: Mapped[date] = mapped_column(Date, nullable=True)
    EndTime: Mapped[Time] = mapped_column(Time, nullable=True)
    IntervalStart: Mapped[date] = mapped_column(
        Date, nullable=True)  # Interval Start Date
    IntervalStartTime: Mapped[Time] = mapped_column(
        Time, nullable=True)  # Interval Start Time
    IntervalEnd: Mapped[date] = mapped_column(
        Date, nullable=True)  # Interval End Date
    IntervalEndTime: Mapped[Time] = mapped_column(
        Time, nullable=True)  # Interval End Time
