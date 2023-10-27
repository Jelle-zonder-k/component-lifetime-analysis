# models/distribution_fitter.py

import surpyval as sp


class DistributionFitter:

    def __init__(self):
        pass

    def fit_distributions_to_data(self, lifetime_array, censoring_array, ) -> dict:

        # Fit Weibull and Exponential distributions
        weibull_fit = sp.Weibull.fit(lifetime_array, censoring_array)
        exponential_fit = sp.Exponential.fit(lifetime_array, censoring_array)

        return {
            "weibull": weibull_fit,
            "exponential": exponential_fit
        }

    def fit_weibull_with_initial_guess(self, lifetime_array, censoring_array, initial_guess: list = []) -> dict:
        """Fits a Weibull distribution to the data using an initial guess.
        Args:
            data (list): _description_
            initial_guess (list): _description_

        Returns:
            dict: _description_
        """

        # Fit Weibull and Exponential distributions
        weibull_fit = sp.Weibull.fit(
            lifetime_array, censoring_array, init=initial_guess)

        return {
            "alpha": weibull_fit.params[0],
            "beta": weibull_fit.params[1],
            "AIC": weibull_fit.aic()
        }

    def fit_exponential_with_initial_guess(self, lifetime_array, censoring_array, initial_guess: list = []) -> dict:
        """Fits an Exponential distribution to the data using an initial guess.

        Args:
            lifetime_array (_type_): _description_
            censoring_array (_type_): _description_
            initial_guess (list, optional): _description_. Defaults to [].

        Returns:
            dict: _description_
        """
        exponential_fit = sp.Exponential.fit(
            lifetime_array, censoring_array, init=initial_guess)

        return {
            "lambda": exponential_fit.params[0],
            "AIC": exponential_fit.aic()
        }
