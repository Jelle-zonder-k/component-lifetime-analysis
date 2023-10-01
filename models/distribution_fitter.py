# models/distribution_fitter.py

import surpyval as sp
from data_processing.lifetime_processor import LifetimeProcessor


def fit_distributions_to_data(data: list) -> dict:
    processor = LifetimeProcessor(data)
    lifetime_array, censoring_array = processor.process_interval_censoring()

    # Fit Weibull and Exponential distributions
    weibull_fit = sp.Weibull.fit(lifetime_array, censoring_array)
    exponential_fit = sp.Exponential.fit(lifetime_array, censoring_array)

    return {
        "weibull": weibull_fit,
        "exponential": exponential_fit
    }
