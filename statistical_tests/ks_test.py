import numpy as np
import surpyval as sp

from typing import Tuple, List, Optional


def calculate_ks_statistic(lifetime_samples: List[float], lifetime_sample_censoring: List[int], init_values: Optional[List[float]] = None) -> Tuple[float, float]:
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
    weibull_model = sp.Weibull.fit(lifetime_samples, lifetime_sample_censoring)
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
