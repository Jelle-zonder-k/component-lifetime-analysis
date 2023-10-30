from typing import Tuple, Dict, List
import surpyval as sp
import numpy as np
from image_handler import ImageHandler
from concurrent.futures import ProcessPoolExecutor, as_completed
from fitters.surpyval_distribution_fitter import DistributionFitter
from time import time
from scipy.stats import norm
# Class that handles all the aspects of the statistical tests
IMAGE_HANDLER = ImageHandler()
DISTRIBUTION_FITTER = DistributionFitter()


def bootstrap_worker(instance, _):
    try:
        bootstrap_samples, bootstrap_sample_censoring = instance.generate_random_lifetime_dataset()
        weibull_D_bootstrap, exp_D_bootstrap = calculate_ks_statistic(
            bootstrap_samples, bootstrap_sample_censoring, instance.initial_guess)
        return weibull_D_bootstrap, exp_D_bootstrap
    except (RuntimeWarning, ValueError):
        return None, None


class BootstrapHandler:

    def __init__(self, lifetime_array: list, censoring_array: list, initial_guess=[]):
        """Initializes the pValueCalculator class.

        Args:
            lifetime_array (list): _description_
            censoring_array (list): _description_
            initial_guess (list, optional): _description_. Defaults to [].
        """
        self.lifetime_array = lifetime_array
        self.censoring_array = censoring_array
        self.initial_guess = initial_guess

    def _generate_random_lifetime_dataset(self) -> Tuple[list[float], list[int]]:
        i = 0
        while i < 1000:
            random_lifetime_samples = np.random.choice(
                self.lifetime_array, len(self.lifetime_array), replace=True)
            random_lifetime_censoring = [self.censoring_array[self.lifetime_array.index(
                sample)] for sample in random_lifetime_samples]

            if len(set(random_lifetime_samples)) != 1 and 0 in random_lifetime_censoring:
                return random_lifetime_samples, random_lifetime_censoring

            i += 1
        return None, None

    def _generate_lifetime_datasets_parallel(self, number_of_samples) -> list[Tuple]:
        """
            Generate lifetime datasets in parallel.

            Parameters:
                number_of_samples (int): The number of samples to generate.

            Returns:
                list: List of datasets.
            """
        datasets = []
        while len(datasets) < number_of_samples:
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(self._generate_random_lifetime_dataset) for _ in range(
                    number_of_samples - len(datasets))]
                for future in as_completed(futures):
                    samples, censoring = future.result()
                    if samples is not None:
                        datasets.append((samples, censoring))
        return datasets

    def _get_fit_statistics(self, datasets: list[Tuple[list, list]],
                            weibull_list: list[float],
                            exp_list: list[float]):
        """ Get fit statistics for Weibull and Exponential models.

            Parameters:
                datasets (list): List of datasets.
                weibull_list (list): List to store Weibull statistics.
                exp_list (list): List to store Exponential statistics.
        """
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(calculate_ks_statistic, samples, censoring, self.initial_guess)
                       for samples, censoring in datasets]
            for future in as_completed(futures):
                weibull_D_bootstrap, exp_D_bootstrap = future.result()
                if weibull_D_bootstrap is not None:
                    weibull_list.append(weibull_D_bootstrap)
                if exp_D_bootstrap is not None:
                    exp_list.append(exp_D_bootstrap)

    def _get_fit_parameters(self, datasets: list[Tuple[list, list]], weibull_list: list[list[float, float]], exp_list: list[float]):
        """ get the parameters of the fitted weibull model, e.g. [[1,1],[1.1,1.1],...]], and the fitted exponential model, e.g. [1,1.1,...]

        Args:
            datasets (list[Tuple[list, list]]): _description_
            weibuill_list (list[]): _description_
            exp_list (list[float]): _description_
        """
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(DISTRIBUTION_FITTER.get_model_parameters, samples, censoring, self.initial_guess)
                       for samples, censoring in datasets]
            for future in as_completed(futures):

                params = future.result()
                if params is not None:
                    weibull_list.append(params["weibull"])
                    exp_list.append(params["exponential"])

    def bootstrap_model_parameters(self, number_of_samples: int = 1000) -> Dict[str, Dict[str, List[float]]]:
        """Bootstrap model parameters for Weibull and Exponential distributions.

        Args:
            number_of_samples (int): The number of bootstrap samples to generate.

        Returns:
            Dict[str, Dict[str, List[float]]]: Dictionary containing the bootstrapped parameters for each model.
        """
        datasets = self._generate_and_time_datasets(number_of_samples)
        weibull_params_list = []
        exp_params_list = []

        # Get initial bootstrap parameters
        self._get_fit_parameters(
            datasets, weibull_params_list, exp_params_list)

        # Ensure sufficient samples
        self._ensure_sufficient_parameters(
            weibull_params_list, exp_params_list, number_of_samples)
        return {
            "weibull": {"bootstrap_parameters": weibull_params_list},
            "exponential": {"bootstrap_parameters": exp_params_list}
        }

    def _ensure_sufficient_parameters(self, weibull_list: List[List[float]], exp_list: List[float], num_required_samples: int):
        """Ensures that there are sufficient bootstrap samples for parameter estimates.

        Args:
            weibull_list (List[List[float]]): List of Weibull model parameters.
            exp_list (List[float]): List of Exponential model parameters.
            num_required_samples (int): The number of bootstrap samples required.
        """
        is_insufficient, samples_needed = self._check_sufficient_samples(
            [weibull_list, exp_list], num_required_samples)

        if is_insufficient:
            additional_datasets = self._generate_lifetime_datasets_parallel(
                samples_needed)
            self._get_fit_parameters(
                additional_datasets, weibull_list, exp_list)

    def bootstrap_test_statistic_values(self, number_of_samples: int = 1000) -> dict[str, dict[str, list[float]]]:
        """Calculates the p-values for the given failure type code and number of objects."""
        datasets = self._generate_and_time_datasets(number_of_samples)
        weibull_D_bootstrap_list, exp_D_bootstrap_list = self._fit_models_to_datasets(
            datasets)
        self._ensure_sufficient_samples(
            weibull_D_bootstrap_list, exp_D_bootstrap_list, number_of_samples)
        return self._prepare_result_dict(weibull_D_bootstrap_list, exp_D_bootstrap_list)

    def _generate_and_time_datasets(self, number_of_samples: int):
        start = time()
        datasets = self._generate_lifetime_datasets_parallel(number_of_samples)
        end = time()
        print(f"Time to generate {len(datasets)} datasets: {end - start}s")
        return datasets

    def _fit_models_to_datasets(self, datasets: list[tuple[list[float], list[int]]]) -> tuple[list[float], list[float]]:
        weibull_D_bootstrap_list = []
        exp_D_bootstrap_list = []
        self._get_fit_statistics(
            datasets, weibull_D_bootstrap_list, exp_D_bootstrap_list)
        return weibull_D_bootstrap_list, exp_D_bootstrap_list

    def _ensure_sufficient_samples(self, weibull_list: list[float], exp_list: list[float], num_required_samples: int):
        is_insufficient, samples_needed = self._check_sufficient_samples(
            [weibull_list, exp_list], num_required_samples)
        if is_insufficient:
            additional_datasets = self._generate_lifetime_datasets_parallel(
                samples_needed)
            self._get_fit_statistics(
                additional_datasets, weibull_list, exp_list)

    def _check_sufficient_samples(self, statistic_lists: list[list[float]], num_required_samples: int) -> tuple[bool, int]:
        insufficient_samples = num_required_samples - len(statistic_lists[1])
        return insufficient_samples > 0, insufficient_samples

    def _prepare_result_dict(self, weibull_list: list[float], exp_list: list[float]) -> dict[str, dict[str, list[float]]]:
        return {
            "Weibull": {"bootstrap_samples": weibull_list},
            "Exponential": {"bootstrap_samples": exp_list}
        }


def calculate_p_value(bootstrap_values: list, original_value) -> float:
    """Calculates the p-value for a given original value and a list of bootstrap values."""
    return np.sum(np.array(bootstrap_values) >= original_value) / len(bootstrap_values)


def calculate_p_value_z_score(bootstrap_values: list, original_value) -> float:
    """Calculates the p-value using Z-score."""
    mean_val = np.mean(bootstrap_values)
    std_dev = np.std(bootstrap_values)
    print(mean_val)
    print(std_dev)
    z_score = (original_value - mean_val) / std_dev
    # Two-tailed p-value
    return 2 * (1 - norm.cdf(abs(z_score)))


def confidence_interval_approach(bootstrap_samples, original_value, alpha=0.05):
    mean_val = np.mean(bootstrap_samples)
    std_dev = np.std(bootstrap_samples)
    n = len(bootstrap_samples)
    z_value = norm.ppf(1 - alpha/2)
    lower_bound = mean_val - z_value * (std_dev/np.sqrt(n))
    upper_bound = mean_val + z_value * (std_dev/np.sqrt(n))
    return {
        "lower_bound": lower_bound,
        "original_value": original_value,
        "upper_bound": upper_bound,
    }


def calculate_ks_statistic(lifetime_samples: list[float], lifetime_sample_censoring: list[int], initial_guess=None) -> Tuple[float, float]:

    # Get distribution model fits
    parametric_distribution_models = DISTRIBUTION_FITTER.fit_parametric_distributions_to_data(
        lifetime_samples, lifetime_sample_censoring, initial_guess)
    non_parametric_distribution_models = DISTRIBUTION_FITTER.fit_non_parametric_distributions_to_data(
        lifetime_samples, lifetime_sample_censoring)

    weibull_model = parametric_distribution_models["weibull"]
    exponential_model = parametric_distribution_models["exponential"]
    nelson_aalen_estimate = non_parametric_distribution_models["nelson_aalen"]

    unique_samples = np.unique(lifetime_samples)
    weibull_diffs = [abs(est - np.exp(- (x / weibull_model.params[0]) ** weibull_model.params[1]))
                     for est, x in zip(nelson_aalen_estimate.R, unique_samples)]
    exp_diffs = [abs(est - np.exp(-exponential_model.params[0] * x))
                 for est, x in zip(nelson_aalen_estimate.R, unique_samples)]

    return max(weibull_diffs), max(exp_diffs)
