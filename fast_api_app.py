from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from datetime import date
from data_handler import ComponentDataHandler
from pydantic_model import ObjectCode, FailureTypeCode, MaintenanceGroup, MalfunctionRecord, GoodnessOfFitResponse, DistributionModelResponse
from image_handler import ImageHandler
from statisticaltesters.handler import calculate_ks_statistic, calculate_p_value
app = FastAPI()

DATA_HANDLER = ComponentDataHandler()
IMAGE_HANDLER = ImageHandler()


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
async def calculate_lifetimes(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return {"lifetimes": lifetimes}


@app.get("/distribution_model/fit_parameters/", response_model=DistributionModelResponse)
async def get_fitted_distributions(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_fit_lifetime_distributions(lifetimes)


@app.post("/distribution_model/fit/weibull/initial_guess")
async def get_fitted_weibull_distributions_using_initial_guess(failure_type_code: str, num_objects: int, initial_guess: list[float, float] = [1, 1],  end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_fit_weibull_lifetime_distributions_with_initial_guess(lifetimes, initial_guess)


@app.get("/distribution_model/fit/exponential")
async def get_fitted_exponential_distribution(failure_type_code: str, num_objects: int,  end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_fit_exponential_lifetime_distributions(lifetimes)


@app.get("/calculate_lifetimes/count/")
async def calculate_lifetimes_count(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return {"count": len(lifetimes)}


@app.post("/distribution_model/goodness-of-fit/", response_model=GoodnessOfFitResponse)
async def get_fit_statistics(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30', number_of_bootstrap_samples: int = 100, initial_guess: list[float, float] = [1, 1]):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)

    test_statistics_dict = DATA_HANDLER.get_test_statistics_dict(
        lifetimes, number_of_bootstrap_samples, initial_guess)

    exponential_p_value = calculate_p_value(
        test_statistics_dict["Exponential"]["bootstrap_samples"], test_statistics_dict["Exponential"]["original_test_statistic"])
    weibull_p_value = calculate_p_value(
        test_statistics_dict["Weibull"]["bootstrap_samples"], test_statistics_dict["Weibull"]["original_test_statistic"])

    IMAGE_HANDLER.plot_bootstrap_histograms(
        failure_type_code, test_statistics_dict)

    return {
        "exponential": {
            "KS_test_statistic": test_statistics_dict["Exponential"]["original_test_statistic"],
            "p_value": exponential_p_value
        },
        "weibull": {
            "KS_test_statistic": test_statistics_dict["Weibull"]["original_test_statistic"],
            "p_value": weibull_p_value
        },
        "general_information": {
            "number_of_samples": number_of_bootstrap_samples
        }
    }


@app.post("/distribution-model/test-statistics/censored-data")
async def get_test_statistics_censored_data(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30', initial_guess: list[float, float] = [1, 1]):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_test_statistics(lifetimes, initial_guess)


@app.get("/distribution_model/exponential/plot/")
async def get_exponential_model_CDF_plot(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return FileResponse(IMAGE_HANDLER.get_exponential_model_CDF_plot(lifetimes, failure_type_code))
