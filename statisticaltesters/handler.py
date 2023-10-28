from typing import Tuple
import surpyval as sp
import numpy as np
from image_handler import ImageHandler
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import time
# Class that handles all the aspects of the statistical tests
IMAGE_HANDLER = ImageHandler()


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

    def generate_random_lifetime_dataset(self) -> Tuple[list[float], list[int]]:
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

    def generate_lifetime_datasets_parallel(self, number_of_samples) -> list[Tuple]:
        datasets = []
        while len(datasets) < number_of_samples:
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(self.generate_random_lifetime_dataset) for _ in range(
                    number_of_samples - len(datasets))]
                for future in as_completed(futures):
                    samples, censoring = future.result()
                    if samples is not None:
                        datasets.append((samples, censoring))
        return datasets

    def fit_models_to_samples(self, datasets: list[Tuple[list, list]],
                              weibull_D_bootstrap_list: list[float],
                              exp_D_bootstrap_list: list[float]):
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(calculate_ks_statistic, samples, censoring, self.initial_guess)
                       for samples, censoring in datasets]
            for future in as_completed(futures):
                weibull_D_bootstrap, exp_D_bootstrap = future.result()
                if weibull_D_bootstrap is not None:
                    weibull_D_bootstrap_list.append(weibull_D_bootstrap)
                if exp_D_bootstrap is not None:
                    exp_D_bootstrap_list.append(exp_D_bootstrap)

    def generate_additional_samples_and_fit_models(self, weibull_D_bootstrap_list: list[float], exp_D_bootstrap_list: list[float]):
        additional_samples_needed = 1000 - len(weibull_D_bootstrap_list)
        if additional_samples_needed > 0:
            additional_datasets = self.generate_lifetime_datasets_parallel(
                additional_samples_needed)
            self.fit_models_to_samples(
                additional_datasets, weibull_D_bootstrap_list, exp_D_bootstrap_list)

    def bootstrap_test_statistic_values(self, number_of_samples: int = 1000) -> dict[str, dict[str, list[float]]]:
        weibull_D_bootstrap_list = []
        exp_D_bootstrap_list = []

        # Step 1: Generate datasets
        start = time()
        datasets = self.generate_lifetime_datasets_parallel(number_of_samples)
        end = time()
        print(f"Time to generate {len(datasets)} datasets: {end - start}s")

        # Step 2: Fit models
        self.fit_models_to_samples(
            datasets, weibull_D_bootstrap_list, exp_D_bootstrap_list)

        # Step 3: Ensure that we have at least 1000 bootstrap samples for Weibull
        self.generate_additional_samples_and_fit_models(
            weibull_D_bootstrap_list, exp_D_bootstrap_list)

        bootstrap_value_dict = {
            "Weibull": {"bootstrap_samples": weibull_D_bootstrap_list},
            "Exponential": {"bootstrap_samples": exp_D_bootstrap_list}
        }

        return bootstrap_value_dict


def calculate_p_value(bootstrap_values: list, original_value) -> float:
    """Calculates the p-value for a given original value and a list of bootstrap values."""
    return np.sum(np.array(bootstrap_values) >= original_value) / len(bootstrap_values)


def calculate_ks_statistic(lifetime_samples: list[float], lifetime_sample_censoring: list[int], initial_guess=None) -> Tuple[float, float]:
    weibull_model = sp.Weibull.fit(
        lifetime_samples, lifetime_sample_censoring, init=initial_guess)
    exponential_model = sp.Exponential.fit(
        lifetime_samples, lifetime_sample_censoring)
    nelson_aalen_estimate = sp.NelsonAalen.fit(
        lifetime_samples, lifetime_sample_censoring)

    unique_samples = np.unique(lifetime_samples)
    weibull_diffs = [abs(est - np.exp(- (x / weibull_model.params[0]) ** weibull_model.params[1]))
                     for est, x in zip(nelson_aalen_estimate.R, unique_samples)]
    exp_diffs = [abs(est - np.exp(-exponential_model.params[0] * x))
                 for est, x in zip(nelson_aalen_estimate.R, unique_samples)]

    return max(weibull_diffs), max(exp_diffs)
