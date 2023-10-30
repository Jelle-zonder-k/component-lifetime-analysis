# models/distribution_fitter.py

import surpyval as sp


class DistributionFitter:

    def __init__(self):
        pass

    def fit_parametric_distributions_to_data(self, lifetime_array, censoring_array, initial_guess: list = None) -> dict:
        """_summary_

        Args:
            lifetime_array (_type_): _description_
            censoring_array (_type_): _description_
            initial_guess (list, optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """

        # Fit Exponentil and Weibull, if initial guess is provided, fit Weibull with initial guess
        if initial_guess is not None:
            weibull_fit = sp.Weibull.fit(
                lifetime_array, censoring_array, init=initial_guess)
        else:
            weibull_fit = sp.Weibull.fit(lifetime_array, censoring_array)

        exponential_fit = sp.Exponential.fit(lifetime_array, censoring_array)

        return {
            "weibull": weibull_fit,
            "exponential": exponential_fit,
        }

    def fit_non_parametric_distributions_to_data(self, lifetime_array, censoring_array) -> dict:

        # Fit Nelson-Aalen and Kaplan-Meier distributions
        nelson_aalen_fit = sp.NelsonAalen.fit(lifetime_array, censoring_array)
        kaplan_meier_fit = sp.KaplanMeier.fit(lifetime_array, censoring_array)

        return {
            "nelson_aalen": nelson_aalen_fit,
            "kaplan_meier": kaplan_meier_fit
        }

    def get_model_parameters(self, lifetime_array, censoring_array, initial_guess: list = None) -> dict:
        # Fits the models and returns the parameters as variables
        model_parameters = self.fit_parametric_distributions_to_data(
            lifetime_array, censoring_array, initial_guess)
        return {
            "weibull": {
                "alpha": model_parameters["weibull"].params[0],
                "beta": model_parameters["weibull"].params[1],
            },
            "exponential": {
                "lambda": model_parameters["exponential"].params[0],
            }
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
            "AIC": weibull_fit.aic(),
        }

    def fit_exponential(self, lifetime_array, censoring_array) -> dict:
        """Fits an Exponential distribution to the data.
        Args:
            data (list): _description_

        Returns:
            dict: _description_
        """

        # Fit Weibull and Exponential distributions
        exponential_fit = sp.Exponential.fit(lifetime_array, censoring_array)

        return {
            "lambda": exponential_fit.params[0],
            "AIC": exponential_fit.aic()
        }
