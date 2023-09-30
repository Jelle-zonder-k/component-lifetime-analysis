from fastapi import FastAPI
from typing import List
from datetime import date
from data_handler import ComponentDataHandler
from pydantic_model import ObjectCode, FailureTypeCode, MaintenanceGroup, MalfunctionRecord, LifetimeInput

app = FastAPI()

DATA_HANDLER = ComponentDataHandler()


@app.post("/object/upsert/")
async def upsert_objects(objects: List[ObjectCode]):
    DATA_HANDLER.upsert_objects([obj.dict() for obj in objects])
    return {"message": f"{len(objects)} object(s) processed."}


@app.post("/failure_type_code/upsert/")
async def upsert_failure_type_codes(type_codes: List[FailureTypeCode]):
    DATA_HANDLER.upsert_failure_type_codes(
        [type_code.dict() for type_code in type_codes])
    return {"message": f"{len(type_codes)} type code(s) processed."}


@app.post("/maintenance_group/upsert/")
async def upsert_maintenance_groups(groups: List[MaintenanceGroup]):
    DATA_HANDLER.upsert_maintenance_groups([group.dict() for group in groups])
    return {"message": f"{len(groups)} group(s) processed."}


@app.post("/malfunction/upsert/")
async def upsert_malfunctions(malfunctions: List[MalfunctionRecord]):
    DATA_HANDLER.upsert_malfunctions(
        [malfunction.dict() for malfunction in malfunctions])
    return {"message": f"{len(malfunctions)} malfunction(s) processed."}


@app.get("/calculate_lifetimes/")
async def calculate_lifetimes(failure_type_code: str, num_objects: int, end_observation_period: date):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return {"lifetimes": lifetimes}
