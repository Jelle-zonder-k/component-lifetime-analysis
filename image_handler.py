
import surpyval as sp
import matplotlib.pyplot as plt
from enum_handler import PlotTypes
from dataprocessing.lifetime_processor import LifetimeProcessor
from fitters.surpyval_distribution_fitter import DistributionFitter

DISTRIBUTION_FITTER = DistributionFitter()


class ImageHandler:

    def get_image_path_for_type_code_plot_types(self, failure_type_code: str, plot_type: PlotTypes):
        """ Returns the image path for the given failure type code and plot type.

        Args:
            failure_type_code (str): _description_
            plot_type (PlotTypes): _description_
        """
        file_name = f"images/{failure_type_code}_{plot_type.name}.png"
        return file_name

    def get_exponential_model_CDF_plot(self, lifetimes: list, failure_type_code: str):
        """ Returns the image of the exponential model fit for the given failure type code and number of objects.

        Args:
            failure_type_code (str): _description_
            num_objects (int): _description_
            end_observation_period (date, optional): _description_. Defaults to '2016-06-30'.
        """

        Processor = LifetimeProcessor(lifetimes)
        lifetime_array, censoring_array = Processor.get_lifetime_arrays()
        exponential_fit = sp.Exponential.fit(lifetime_array, censoring_array)
        image_path = self.get_image_path_for_type_code_plot_types(
            f"{failure_type_code}_EXP", PlotTypes.CDF)
        plt.figure()
        plt.xlabel("Lifetime in Hours")
        exponential_fit.plot()
        plt.title(f"{failure_type_code} Exponential Model")
        plt.show()
        plt.savefig(image_path)
        plt.close
        return image_path

    def get_weibull_model_CDF_plot(self, lifetimes: list, failure_type_code: str, initial_guess: list = None):
        """ Returns the image of the weibull model fit for the given failure type code and number of objects.

        Args:
            failure_type_code (str): _description_
            num_objects (int): _description_
            end_observation_period (date, optional): _description_. Defaults to '2016-06-30'.
        """

        Processor = LifetimeProcessor(lifetimes)
        lifetime_array, censoring_array = Processor.get_lifetime_arrays()
        weibull_fit = sp.Weibull.fit(
            lifetime_array, censoring_array, init=initial_guess)
        image_path = self.get_image_path_for_type_code_plot_types(
            f"{failure_type_code}_WEIBULL", PlotTypes.CDF)
        plt.figure()
        weibull_fit.plot()
        plt.title(f"{failure_type_code} Weibull Model")
        plt.xlabel('Lifetime in Hours')
        plt.savefig(image_path)
        plt.close
        return image_path

    def plot_bootstrap_histograms(self, failure_type_code: str, bootstrap_information: dict):
        """Creates content of bootstrap information dictionary.
        example dict:
                    {Weibull:{
                         bootstrap_samples: [1,2,3,4,5,6,7,8,9,10],
                        original_test_statistic: 1.0

                     },
                     Exponential:{
                            bootstrap_samples: [1,2,3,4,5,6,7,8,9,10],
                            original_test_statistic: 1.0}
                     }
        """
        image_path = self.get_image_path_for_type_code_plot_types(
            failure_type_code, PlotTypes.HISTOGRAM)

        # Set the number of bins, if there are large jumps in the data, so one bin is 500, the bin next to it is 100, and the next is 400 again, then the histogram will look weird. This is a way to fix that.

        plt.figure()
        plt.figure()
        for key in bootstrap_information:
            plt.hist(
                bootstrap_information[key]["bootstrap_samples"], label=f"{key}", bins=30, alpha=0.5)

        plt.axvline(bootstrap_information["Weibull"]["original_test_statistic"],
                    color='r', linestyle='--', linewidth=1, label="Weibull Orig.")
        plt.axvline(bootstrap_information["Exponential"]["original_test_statistic"],
                    color='b', linestyle='--', linewidth=1, label="Exp. Orig.")

        plt.legend(loc='upper right')
        plt.xlabel('Test Statistic Value')
        plt.ylabel('Frequency')
        # Create a title that indicates the number of bootstrap samples and the number of bins
        plt.title(
            f"{failure_type_code} Test Stats: {len(bootstrap_information['Weibull']['bootstrap_samples'])} Samples")

        plt.savefig(image_path)
        plt.close()
        return image_path

    def get_hazard_function_plot(self, failure_type_code: str, lifetimes: list, initial_guess: list = None):
        """Plots the hazard functions for the given failure type code and lifetimes.

        Args:
            failure_type_code (str): _description_
            lifetimes (list): _description_
        """
        # set image path
        image_path = self.get_image_path_for_type_code_plot_types(
            failure_type_code, PlotTypes.HAZARD_FUNCTION)
        Processor = LifetimeProcessor(lifetimes)
        simplified_lifetime_array, simplified_cenosring_array = Processor.get_simplified_lifetime_arrays()

        # Fit non parametric model
        nelson_aalen_fit = DISTRIBUTION_FITTER.fit_non_parametric_distributions_to_data(
            simplified_lifetime_array, simplified_cenosring_array)["nelson_aalen"]
        # Fit parametric models
        parametric_model_fits = DISTRIBUTION_FITTER.fit_parametric_distributions_to_data(
            simplified_lifetime_array, simplified_cenosring_array, initial_guess)

        weibull_fit = parametric_model_fits["weibull"]
        exponential_fit = parametric_model_fits["exponential"]

        # Sort simplified lifetime array from smallest to largest
        simplified_lifetime_array.sort()
        plt.figure()

        plt.plot(simplified_lifetime_array, weibull_fit.Hf(
            simplified_lifetime_array), label="Weibull")
        plt.plot(simplified_lifetime_array, exponential_fit.Hf(
            simplified_lifetime_array), label="Exponential")
        plt.step(simplified_lifetime_array, nelson_aalen_fit.Hf(
            simplified_lifetime_array), label="Nelson-Aalen")
        # add legend to upper left
        plt.legend(loc='upper left')

        # Set title
        plt.title(f"{failure_type_code} Hazard Function")
        # Set clear labels
        plt.xlabel('Time in Hours')
        plt.ylabel('Hazard Function')
        plt.savefig(image_path)
        plt.close
        return image_path
