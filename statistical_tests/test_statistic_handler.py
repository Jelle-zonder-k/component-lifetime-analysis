from typing import Tuple
import surpyval as sp
import numpy as np


# Class that handles all the aspects of the statistical tests

class TestStatisticHandler:

    def __init__(self, lifetime_array: list, censoring_array: list, initial_guess=[]):
        """Initializes the pValueCalculator class.

        Args:
            lifetime_array (List): _description_
            censoring_array (List): _description_
            initial_guess (list, optional): _description_. Defaults to [].
        """
        self.lifetime_array = lifetime_array
        self.censoring_array = censoring_array
        self.initial_guess = initial_guess

    def generate_random_lifetime_dataset(self) -> Tuple[list[float], list[int]]:
        """Generates a random data set of lifetimes and corresponding censoring indicators. If all the lifetimes are identical, a new dataset is generated.

        Returns:
            tuple: A tuple containing the lifetime array and censoring array.
        """

        # Generate random lifetimes and censoring indicators, continue if not identical. The while loop should be capped at 1000 iterations.
        i = 0
        while i < 1000:
            random_lifetime_samples = np.random.choice(
                self.lifetime_array, len(self.lifetime_array), replace=True)
            random_lifetime_censoring = [
                self.censoring_array[self.lifetime_array.index(sample)] for sample in random_lifetime_samples]
            if len(set(random_lifetime_samples)) != 1:
                break
            i += 1
        return random_lifetime_samples, random_lifetime_censoring

    def bootstrap_p_value(self, number_of_samples=10):
        """
        Calculate the P-value using bootstrapping for Weibull and Exponential distributions.

        Parameters:
        - lifetime_array (list): List of lifetimes.
        - censoring_array (list): Censoring indicators for the lifetimes.
        - m (int, optional): Number of bootstrap samples.

        Returns:
        - tuple: P-values for Weibull and Exponential distributions.
        """

        weibull_D, exp_D = calculate_ks_statistic(
            self.lifetime_array, self.censoring_array, self.initial_guess)
        weibull_D_bootstrap_list = []
        exp_D_bootstrap_list = []

        # Perform bootstrapping
        for _ in range(number_of_samples):
            try:
                bootstrap_samples, bootstrap_sample_censoring = self.generate_random_lifetime_dataset()
                weibull_D_bootstrap, exp_D_bootstrap = calculate_ks_statistic(
                    bootstrap_samples, bootstrap_sample_censoring, self.initial_guess)
                weibull_D_bootstrap_list.append(weibull_D_bootstrap)
                exp_D_bootstrap_list.append(exp_D_bootstrap)

            except (RuntimeWarning, ValueError):
                continue

        # Number of samples generated
        number_of_samples = len(weibull_D_bootstrap_list)

        # Calculate P-values
        weibull_p_value = np.sum(
            np.array(weibull_D_bootstrap_list) >= weibull_D) / number_of_samples
        exp_p_value = np.sum(np.array(exp_D_bootstrap_list)
                             >= exp_D) / number_of_samples

        return weibull_p_value, exp_p_value, number_of_samples


def calculate_ks_statistic(lifetime_samples: list[float], lifetime_sample_censoring: list[int], initial_guess=None) -> Tuple[float, float]:
    """
    Calculate the Kolmogorov-Smirnov test statistic for Weibull and Exponential distributions.

    Parameters:
    - lifetime_samples (list): List of lifetime samples.
    - lifetime_sample_censoring (list): Censoring indicators for the lifetime samples.
    - init_values (list, optional): Initial values for Weibull fit.

    Returns:
    - tuple: Test statistic for Weibull (D) and Exponential (exp_D) distributions.
    """

    # Fit models
    weibull_model = sp.Weibull.fit(
        lifetime_samples, lifetime_sample_censoring, init=initial_guess)
    exponential_model = sp.Exponential.fit(
        lifetime_samples, lifetime_sample_censoring)
    nelson_aalen_estimate = sp.NelsonAalen.fit(
        lifetime_samples, lifetime_sample_censoring)

    unique_samples = np.unique(lifetime_samples)

    # Survival functions using lambda functions for brevity
    def weibull_sf(
        x): return np.exp(- (x / weibull_model.params[0]) ** weibull_model.params[1])

    def exponential_sf(x): return np.exp(-exponential_model.params[0] * x)

    # Calculate differences using list comprehensions
    weibull_diffs = [abs(est - weibull_sf(x))
                     for est, x in zip(nelson_aalen_estimate.R, unique_samples)]
    exp_diffs = [abs(est - exponential_sf(x))
                 for est, x in zip(nelson_aalen_estimate.R, unique_samples)]

    # Get maximum differences
    weibull_D = max(weibull_diffs)
    exp_D = max(exp_diffs)

    return weibull_D, exp_D
