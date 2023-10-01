import numpy as np
from statistical_tests.ks_test import calculate_ks_statistic


def bootstrap_p_value(lifetime_array, censoring_array, number_of_samples=10):
    """
    Calculate the P-value using bootstrapping for Weibull and Exponential distributions.

    Parameters:
    - lifetime_array (list): List of lifetimes.
    - censoring_array (list): Censoring indicators for the lifetimes.
    - m (int, optional): Number of bootstrap samples.

    Returns:
    - tuple: P-values for Weibull and Exponential distributions.
    """

    weibull_D, exp_D = calculate_ks_statistic(lifetime_array, censoring_array)

    weibull_D_bootstraps = []
    exp_D_bootstraps = []

    # Perform bootstrapping
    for _ in range(number_of_samples):
        try:
            bootstrap_samples = np.random.choice(
                lifetime_array, len(lifetime_array), replace=True)
            bootstrap_sample_censoring = [
                censoring_array[lifetime_array.index(sample)] for sample in bootstrap_samples]

            weibull_D_bootstrap, exp_D_bootstrap = calculate_ks_statistic(
                bootstrap_samples, bootstrap_sample_censoring)
            weibull_D_bootstraps.append(weibull_D_bootstrap)
            exp_D_bootstraps.append(exp_D_bootstrap)

        except (RuntimeWarning, ValueError):
            continue

    # Number of samples generated
    number_of_samples = len(weibull_D_bootstraps)

    # Calculate P-values
    weibull_p_value = np.sum(
        np.array(weibull_D_bootstraps) >= weibull_D) / number_of_samples
    exp_p_value = np.sum(np.array(exp_D_bootstraps)
                         >= exp_D) / number_of_samples

    return weibull_p_value, exp_p_value, number_of_samples
