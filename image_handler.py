
import surpyval as sp
import matplotlib.pyplot as plt
from enum_handler import PlotTypes
from dataprocessing.lifetime_processor import LifetimeProcessor


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
            failure_type_code, PlotTypes.CDF)
        exponential_fit.plot()
        plt.title(f"{failure_type_code} Exponential Model")
        plt.show()
        plt.savefig(image_path)
        plt.close
        return image_path

    def get_weibull_model_CDF_plot(self, lifetimes: list, failure_type_code: str):
        """ Returns the image of the weibull model fit for the given failure type code and number of objects.

        Args:
            failure_type_code (str): _description_
            num_objects (int): _description_
            end_observation_period (date, optional): _description_. Defaults to '2016-06-30'.
        """

        Processor = LifetimeProcessor(lifetimes)
        lifetime_array, censoring_array = Processor.get_lifetime_arrays()
        weibull_fit = sp.Weibull.fit(lifetime_array, censoring_array)
        image_path = self.get_image_path_for_type_code_plot_types(
            failure_type_code, PlotTypes.CDF)
        weibull_fit.plot()
        plt.title(f"{failure_type_code} Weibull Model")
        plt.show()
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
