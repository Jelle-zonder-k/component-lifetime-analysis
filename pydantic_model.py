from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, validator, ValidationError

# Failure Type Code


class FailureTypeCode(BaseModel):
    Code: str
    Description: Optional[str]

# Failure Type Code Change History


class FailureTypeCodeChangeHistory(BaseModel):
    FailureTypeCodeID: str
    FailureFrequency: Optional[float]
    NumberOfComponents: Optional[int]
    StartDate: date
    EndDate: Optional[date]

# Maintenance Group


class MaintenanceGroup(BaseModel):
    Code: str
    Description: Optional[str]

# Object Code


class ObjectCode(BaseModel):
    Code: str
    Description: Optional[str]

# Malfunction Record


class MalfunctionRecord(BaseModel):
    MaintenanceGroup: str
    MalfunctionNumber: int
    ObjectCode: str
    Description: Optional[str]
    EventDate: date
    LastTestDate: Optional[date]
    EventTime: Optional[str]
    Observable: bool
    FailureTypeCode: Optional[str]

    @validator('EventDate', 'LastTestDate', pre=True)
    def parse_date_formats(cls, date_value):
        if isinstance(date_value, date):
            return date_value

        for date_format in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_value, date_format).date()
            except ValueError:
                pass
        raise ValueError(f"Invalid date format for {date_value}")


# Object Lifetime


class ObjectLifetime(BaseModel):
    ObjectCodeID: str
    StartDate: date
    StartTime: Optional[str]
    EndDate: Optional[date]
    EndTime: Optional[str]
    IntervalStart: Optional[date]  # Interval Start Date
    IntervalStartTime: Optional[str]  # Interval Start Time
    IntervalEnd: Optional[date]  # Interval End Date
    IntervalEndTime: Optional[str]  # Interval End Time


class LifetimeInput(BaseModel):
    FailureTypeCode: str
    NumberOfObjects: int
    ObservationEndTime: date


class DistributionFitWeibull(BaseModel):
    alpha: float
    beta: float
    aic: float


class DistributionFitExponential(BaseModel):
    lambda_: float
    aic: float


class GoodnessOfFit(BaseModel):
    KS_test_statistic: float
    p_value: float


class GeneralInformation(BaseModel):
    number_of_samples: int


class DistributionModelResponse(BaseModel):
    weibull: DistributionFitWeibull
    exponential: DistributionFitExponential


class GoodnessOfFitResponse(BaseModel):
    exponential: GoodnessOfFit
    weibull: GoodnessOfFit
    general_information: GeneralInformation
