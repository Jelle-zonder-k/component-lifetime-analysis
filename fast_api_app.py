from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from datetime import date
from data_handler import ComponentDataHandler
from pydantic_model import ObjectCode, FailureTypeCode, MaintenanceGroup, MalfunctionRecord, GoodnessOfFitResponse, DistributionModelResponse
from image_handler import ImageHandler
from statisticaltesters.handler import calculate_ks_statistic, calculate_p_value, calculate_p_value_z_score, confidence_interval_approach
app = FastAPI()

DATA_HANDLER = ComponentDataHandler()
IMAGE_HANDLER = ImageHandler()


@app.get("/distribution-model/fit/parameters/exponential")
async def get_fitted_exponential_distribution(failure_type_code: str, num_objects: int,  end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_fit_exponential_lifetime_distributions(lifetimes)


@app.get("/calculate-lifetimes/count/")
async def calculate_lifetimes_count(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return {"count": len(lifetimes)}


@app.get("/calculate-lifetimes/")
async def calculate_lifetimes(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return {"lifetimes": lifetimes}


@app.get("/distribution-model/exponential/plot/")
async def get_exponential_model_CDF_plot(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return FileResponse(IMAGE_HANDLER.get_exponential_model_CDF_plot(lifetimes, failure_type_code))


@app.get("/distribution-model/fit/parameters/", response_model=DistributionModelResponse)
async def get_fitted_distributions(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_fit_lifetime_distributions(lifetimes)


@app.post("/distribution-model/fit/parameters/weibull/initial-guess")
async def get_fitted_weibull_distributions_using_initial_guess(failure_type_code: str, num_objects: int, initial_guess: list[float, float] = [1, 1],  end_observation_period: date = '2016-06-30'):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return DATA_HANDLER.get_fit_weibull_lifetime_distributions_with_initial_guess(lifetimes, initial_guess)


@app.post("/distribution-model/goodness-of-fit/test", response_model=GoodnessOfFitResponse)
async def get_fit_statistics(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30', number_of_bootstrap_samples: int = 1000, initial_guess: list[float, float] = [1, 1]):
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


@app.post("/distribution-model/fit/parameters/test")
async def get_fit_parameters(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30', number_of_bootstrap_samples: int = 1000, initial_guess: list[float, float] = [1, 1]):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)

    # get original model parameters
    original_model_parameters = DATA_HANDLER.get_fit_lifetime_distributions(
        lifetimes)

    # bootstrap model parameters
    bootstrap_model_parameters = DATA_HANDLER.get_bootstrap_model_parameters(
        lifetimes, number_of_bootstrap_samples, initial_guess)
    lambda_values = [d['lambda']
                     for d in bootstrap_model_parameters["exponential"]["bootstrap_parameters"]]
    exponential_p_value = calculate_p_value_z_score(
        lambda_values, original_model_parameters["exponential"]["lambda_"])
    scale_values = [d['alpha']
                    for d in bootstrap_model_parameters["weibull"]["bootstrap_parameters"]]
    shape_values = [d['beta']
                    for d in bootstrap_model_parameters["weibull"]["bootstrap_parameters"]]
    weibull_p_value_scale = confidence_interval_approach(
        scale_values, original_model_parameters["weibull"]["alpha"])
    weibull_p_value_shape = calculate_p_value_z_score(
        shape_values, original_model_parameters["weibull"]["beta"])
    print(original_model_parameters["weibull"]["alpha"])
    return {
        "exponential": {
            "p_value": exponential_p_value
        },
        "weibull": {
            "p_value_scale": weibull_p_value_scale,
            "p_value_shape": weibull_p_value_shape
        },
        "general_information": {
            "number_of_samples": number_of_bootstrap_samples
        }
    }


@app.post("/distribution-model/weibull/plot/")
async def get_weibull_model_CDF_plot(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30', initial_guess: list[float, float] = [1, 1]):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return FileResponse(IMAGE_HANDLER.get_weibull_model_CDF_plot(lifetimes, failure_type_code, initial_guess))


@app.post("/distribution-model/plot/hazard-function/")
async def get_hazard_function_plot(failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30', initial_guess: list[float, float] = [1, 1]):
    lifetimes = DATA_HANDLER.calculate_lifetimes(
        failure_type_code, num_objects, end_observation_period)
    return FileResponse(IMAGE_HANDLER.get_hazard_function_plot(failure_type_code, lifetimes, initial_guess))


@app.post("/object/upsert/")
async def upsert_objects(objects: List[ObjectCode]):
    DATA_HANDLER.upsert_objects([obj.dict() for obj in objects])
    return {"message": f"{len(objects)} object(s) processed."}


@app.post("/failure-type-code/upsert/")
async def upsert_failure_type_codes(type_codes: List[FailureTypeCode]):
    DATA_HANDLER.upsert_failure_type_codes(
        [type_code.dict() for type_code in type_codes])
    return {"message": f"{len(type_codes)} type code(s) processed."}


@app.post("/maintenance-group/upsert/")
async def upsert_maintenance_groups(groups: List[MaintenanceGroup]):
    DATA_HANDLER.upsert_maintenance_groups([group.dict() for group in groups])
    return {"message": f"{len(groups)} group(s) processed."}


@app.post("/malfunction/upsert/")
async def upsert_malfunctions(malfunctions: List[MalfunctionRecord]):
    DATA_HANDLER.upsert_malfunctions(
        [malfunction.dict() for malfunction in malfunctions])
    return {"message": f"{len(malfunctions)} malfunction(s) processed."}
