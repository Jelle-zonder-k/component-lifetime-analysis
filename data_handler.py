from dataclasses import dataclass
import data_model as data_model
from uuid import uuid4
from database.session_factory import SessionFactory
from typing import Dict, List, Union
from datetime import datetime
from sqlalchemy import func, text
from datetime import datetime
from fitters.surpyval_distribution_fitter import DistributionFitter
from statisticaltesters.handler import BootstrapHandler, calculate_ks_statistic
from dataprocessing.lifetime_processor import LifetimeProcessor
from image_handler import ImageHandler

IMAGE_HANDLER = ImageHandler()


@dataclass
class ComponentDataHandler:
    """
    Data handler class for managing various entities related to components.
    """

    def _parse_date(self, date_string: str) -> datetime.date:
        """Helper function to parse date in DD/MM/YYYY or DD-MM-YYYY format."""
        for fmt in ["%d/%m/%Y", "%d-%m-%Y"]:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                pass
        raise ValueError(
            f"Invalid date format. Expected DD/MM/YYYY or DD-MM-YYYY, got {date_string}")

    def upsert_objects(self, objects_list: List[Dict[str, str]]):
        """
        Upsert a list of object codes.

        For each object code in the provided list, if an existing record with the same code exists,
        only its description is updated. If no existing record is found, a new record is added.

        :param objects_list: List of dictionaries containing object attributes.
        """
        session = SessionFactory()
        for object_dict in objects_list:
            existing_object = session.query(data_model.ObjectCode).filter_by(
                Code=object_dict['Code'].upper()).first()

            if existing_object is not None:
                existing_object.Description = object_dict['Description']
            else:
                object_dict['ID'] = str(uuid4())  # Adding the UUID here
                new_object = data_model.ObjectCode(**object_dict)
                session.add(new_object)

        session.commit()

    def upsert_failure_type_codes(self, type_codes_list: List[Dict[str, str]]):
        """
        Upsert a list of failure type codes.

        For each failure type code in the provided list, if an existing record with the same code exists,
        only its description is updated. If no existing record is found, a new record is added.

        :param type_codes_list: List of dictionaries containing failure type code attributes.
        """
        session = SessionFactory()
        for type_code_dict in type_codes_list:
            existing_code = session.query(data_model.FailureTypeCode).filter_by(
                Code=type_code_dict['Code'].upper()).first()

            if existing_code is not None:
                existing_code.Description = type_code_dict['Description']
            else:
                type_code_dict['ID'] = str(uuid4())  # Adding the UUID here
                new_code = data_model.FailureTypeCode(**type_code_dict)
                session.add(new_code)

        session.commit()

    def upsert_maintenance_groups(self, groups_list: List[Dict[str, str]]):
        """
        Upsert a list of maintenance groups.

        For each maintenance group in the provided list, if an existing record with the same code exists,
        only its description is updated. If no existing record is found, a new record is added.

        :param groups_list: List of dictionaries containing maintenance group attributes.
        """
        session = SessionFactory()
        for group_dict in groups_list:
            existing_group = session.query(data_model.MaintenanceGroup).filter_by(
                Code=group_dict['Code'].upper()).first()

            if existing_group is not None:
                existing_group.Description = group_dict['Description']
            else:
                group_dict['ID'] = str(uuid4())  # Adding the UUID here
                new_group = data_model.MaintenanceGroup(**group_dict)
                session.add(new_group)

        session.commit()

    def upsert_malfunctions(self, malfunctions_list: List[Dict[str, str]]):
        """
        Upsert a list of malfunctions.
        ...
        """
        session = SessionFactory()
        for malfunction_dict in malfunctions_list:

            # Fetch related records and their IDs
            maintenance_group = session.query(data_model.MaintenanceGroup).filter(
                func.lower(data_model.MaintenanceGroup.Code) == malfunction_dict["MaintenanceGroup"].lower()).first()

            object_code = session.query(data_model.ObjectCode).filter(
                func.lower(data_model.ObjectCode.Code) == malfunction_dict["ObjectCode"].lower()).first()
            failure_type = session.query(data_model.FailureTypeCode).filter(
                func.lower(data_model.FailureTypeCode.Code) == malfunction_dict["FailureTypeCode"].lower()).first() if malfunction_dict.get("FailureTypeCode") else None

            if not (maintenance_group and object_code and (failure_type or not malfunction_dict.get("FailureTypeCode"))):
                continue  # Skip the record if foreign key values are invalid

            malfunction_dict["MaintenanceGroupID"] = maintenance_group.ID
            malfunction_dict["ObjectCodeID"] = object_code.ID
            malfunction_dict["FailureTypeCodeID"] = failure_type.ID if failure_type else None
            malfunction_dict.pop("MaintenanceGroup", None)
            malfunction_dict.pop("ObjectCode", None)
            malfunction_dict.pop("FailureTypeCode", None)

            existing_malfunction = session.query(data_model.MalfunctionRecord).filter_by(
                MalfunctionNumber=malfunction_dict["MalfunctionNumber"]).first()
            if existing_malfunction:
                existing_malfunction.Description = malfunction_dict["Description"]
                existing_malfunction.LastTestDate = malfunction_dict["LastTestDate"]
                existing_malfunction.EventDate = malfunction_dict["EventDate"]
                existing_malfunction.Observable = malfunction_dict["Observable"]
                existing_malfunction.FailureTypeCodeID = malfunction_dict["FailureTypeCodeID"]
                # Add/update other fields as needed
            else:
                malfunction_dict["ID"] = str(uuid4())  # Adding the UUID here
                new_malfunction = data_model.MalfunctionRecord(
                    **malfunction_dict)
                session.add(new_malfunction)

        session.commit()

        # Update the lifetimes
        function_query = text("SELECT update_object_lifetimes()")
        session.execute(function_query)

        session.commit()

    @staticmethod
    def calculate_lifetimes(failure_type_code: str, num_objects: int, end_observation_period: datetime) -> List[Union[float, List[float]]]:
        """
        Calculate lifetimes based on the provided failure type code, number of objects, and observation period.
        Returns a list of lifetimes (in hours) for each object.
        """
        session = SessionFactory()

        # Convert the failure type code to lowercase for case insensitivity
        failure_type_code = failure_type_code.lower()

        # Fetch FailureTypeCode ID
        failure_type = session.query(data_model.FailureTypeCode).filter(
            func.lower(data_model.FailureTypeCode.Code) == failure_type_code).first()

        if not failure_type:
            session.close()
            raise ValueError("FailureTypeCode not found")

        # Fetch Malfunctions with the given FailureTypeCode ID
        malfunctions = session.query(data_model.MalfunctionRecord).filter_by(
            FailureTypeCodeID=failure_type.ID).all()

        failure_type_ids = [m.FailureTypeCodeID for m in malfunctions]
        object_ids = [m.ObjectCodeID for m in malfunctions]

        # Get the corresponding ObjectLifetime records
        object_lifetimes = session.query(data_model.ObjectLifetime).filter(
            data_model.ObjectLifetime.FailureTypeCodeID.in_(failure_type_ids)).all()
        earliest_lifetime_start = session.query(
            func.min(data_model.ObjectLifetime.StartDate)).first()[0]

        lifetime_list = []

        # Check for Observable Malfunctions
        # This assumes Observable is a boolean column in the MalfunctionRecord model
        if any([m.Observable for m in malfunctions]):

            # Loop through each object lifetime
            for ol in object_lifetimes:

                # If the object has an end date, it's a complete failure
                if ol.EndDate:
                    # Calculate the lifetime in hours
                    lifetime = (
                        ol.EndDate - ol.StartDate).total_seconds() / 3600.0
                    # Append the lifetime and its censoring type (0 for complete) to the list
                    lifetime_list.append(
                        {"lifetime": lifetime, "censoring": 0})

                # If the object doesn't have an end date, it's right-censored
                else:
                    # Calculate the right-censored lifetime in hours
                    lifetime = (end_observation_period -
                                ol.StartDate).total_seconds() / 3600.0
                    # Append the right-censored lifetime and its censoring type (1 for right-censored) to the list
                    lifetime_list.append(
                        {"lifetime": lifetime, "censoring": 1})

            # Calculate the number of unobserved objects
            unobserved_objects_count = num_objects - len(set(object_ids))
            # Calculate the lifetime for unobserved objects in hours
            unobserved_lifetime = (
                end_observation_period - earliest_lifetime_start).total_seconds() / 3600.0
            # Extend the list with the lifetimes of unobserved objects, which are all right-censored
            lifetime_list.extend(
                [{"lifetime": unobserved_lifetime, "censoring": 1}] * unobserved_objects_count)

        # If the malfunctions are Non-Observable
        else:

            # Loop through each object lifetime
            for ol in object_lifetimes:

                # If the object has an end date, it's interval-censored
                if ol.EndDate:
                    # Calculate the start and end lifetimes for the interval in hours
                    start_lifetime = (ol.IntervalStart -
                                      ol.StartDate).total_seconds() / 3600.0
                    end_lifetime = (ol.IntervalEnd -
                                    ol.StartDate).total_seconds() / 3600.0
                    # Append the interval-censored lifetimes and its censoring type (2 for interval-censored) to the list
                    lifetime_list.append(
                        {"lifetime": [start_lifetime, end_lifetime], "censoring": 2})

                # If the object doesn't have an end date, it's right-censored
                else:
                    # Calculate the right-censored lifetime in hours
                    lifetime = (end_observation_period -
                                ol.StartDate).total_seconds() / 3600.0
                    # Append the right-censored lifetime and its censoring type (1 for right-censored) to the list
                    lifetime_list.append(
                        {"lifetime": lifetime, "censoring": 1})

            # Calculate the number of unobserved objects
            unobserved_objects_count = num_objects - len(set(object_ids))
            # Calculate the lifetime for unobserved objects in hours
            unobserved_lifetime = (
                end_observation_period - earliest_lifetime_start).total_seconds() / 3600.0
            # Extend the list with the lifetimes of unobserved objects, which are all right-censored
            lifetime_list.extend(
                [{"lifetime": unobserved_lifetime, "censoring": 1}] * unobserved_objects_count)

        # Close the database session
        session.close()
        # Return the list of lifetimes with their respective censoring types
        return lifetime_list

    def get_fit_lifetime_distributions(self, lifetimes) -> dict:
        # Fit distributions
        ModelFitter = DistributionFitter()
        Processor = LifetimeProcessor(lifetimes)
        lifetime_array, censoring_array = Processor.get_lifetime_arrays()
        fits = ModelFitter.fit_parametric_distributions_to_data(
            lifetime_array, censoring_array)

        # Convert fits to the desired dictionary format
        results = {
            "weibull": {
                "alpha": fits["weibull"].params[0],
                "beta": fits["weibull"].params[1],
                "aic": fits["weibull"].aic()
            },
            "exponential": {
                "lambda_": fits["exponential"].params[0],
                "aic": fits["exponential"].aic()
            }
        }
        return results

    def get_fit_weibull_lifetime_distributions_with_initial_guess(self, lifetimes, initial_guess: list = []) -> dict:
        # Fit distributions
        ModelFitter = DistributionFitter()
        Processor = LifetimeProcessor(lifetimes)
        lifetime_array, censoring_array = Processor.get_lifetime_arrays()
        weibull_fit = ModelFitter.fit_weibull_with_initial_guess(
            lifetime_array, censoring_array, initial_guess
        )

        # Convert fits to the desired dictionary format
        return weibull_fit

    def get_fit_exponential_lifetime_distributions(self, lifetimes: list) -> dict:
        # Fit distributions
        ModelFitter = DistributionFitter()
        Processor = LifetimeProcessor(lifetimes)
        lifetime_array, censoring_array = Processor.get_lifetime_arrays()
        exponential_fit = ModelFitter.fit_exponential(
            lifetime_array, censoring_array)

        # Convert fits to the desired dictionary format
        return exponential_fit

    def get_test_statistics_dict(self, lifetimes: list, number_of_samples=1000, initial_guess: list = []) -> dict:
        # get bootstrapped test statistics
        bootstrap_dict = self.get_bootstrap_test_statistics(
            lifetimes, number_of_samples, initial_guess)

        # get original test statistics
        weibull_test_statistic, exponential_test_statistic = self.get_test_statistics(
            lifetimes, initial_guess)

        # Create test statistics dictionary
        test_statistics = {
            "Weibull": {
                "bootstrap_samples": bootstrap_dict["Weibull"]["bootstrap_samples"],
                "original_test_statistic": weibull_test_statistic
            },
            "Exponential": {
                "bootstrap_samples": bootstrap_dict["Exponential"]["bootstrap_samples"],
                "original_test_statistic": exponential_test_statistic
            }
        }
        return test_statistics

    def get_bootstrap_test_statistics(self, lifetimes: list, number_of_samples=None, initial_guess: list = []) -> dict:
        # Extract lifetimes and censoring arrays
        processor = LifetimeProcessor(lifetimes)
        simplified_lifetime_array, simplified_censoring_array = processor.get_simplified_lifetime_arrays()
        # Initialise the statistical test handler
        test_handler = BootstrapHandler(
            simplified_lifetime_array, simplified_censoring_array, initial_guess)
        # Generate statistical test bootstrap dict
        test_statistic_bootstrap_dict = test_handler.bootstrap_test_statistic_values(
            number_of_samples)
        return test_statistic_bootstrap_dict

    def get_bootstrap_model_parameters(self, lifetimes: list, number_of_samples=None, initial_guess: list = []) -> dict:
        # Extract lifetimes and censoring arrays
        processor = LifetimeProcessor(lifetimes)
        simplified_lifetime_array, simplified_censoring_array = processor.get_simplified_lifetime_arrays()
        # Initialise the statistical test handler
        test_handler = BootstrapHandler(
            simplified_lifetime_array, simplified_censoring_array, initial_guess)
        # Generate statistical test bootstrap dict
        model_parameter_bootstrap_dict = test_handler.bootstrap_model_parameters(
            number_of_samples)
        return model_parameter_bootstrap_dict

    def get_test_statistics(self, lifetimes: list, initial_guess: list = []):
        # Extract lifetimes and censoring arrays
        processor = LifetimeProcessor(lifetimes)
        simplified_lifetime_array, simplified_censoring_array = processor.get_simplified_lifetime_arrays()
        # Calculate Original Test Statistic
        weibull_test_statistic, exponential_test_statistic = calculate_ks_statistic(
            simplified_lifetime_array, simplified_censoring_array, initial_guess)
        return weibull_test_statistic, exponential_test_statistic
