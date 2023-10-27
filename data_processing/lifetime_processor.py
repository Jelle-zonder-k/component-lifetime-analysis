# data_processing/lifetime_processor.py

class LifetimeProcessor:
    def __init__(self, data):
        self.data = data

    def get_lifetime_arrays(self):
        lifetime_array = [entry["lifetime"] for entry in self.data]
        censoring_array = [entry["censoring"] for entry in self.data]
        return lifetime_array, censoring_array

    def get_simplified_lifetime_arrays(self, interval_lifetime_indicator='mid'):
        """
        This function modifies lifetime and censoring arrays based on the interval_lifetime_indicator.

        Parameters:
        interval_lifetime_indicator (str): A string that is either 'start', 'mid' or 'end', 
                                        which is used to select the lifetime within an interval.

        Returns:
        list, list: The modified lifetime_array and censoring_array.
        """
        # Check validity of interval_lifetime_indicator
        assert interval_lifetime_indicator in ['start', 'mid', 'end'], \
            "interval_lifetime_indicator should be one of ['start', 'mid', 'end']"
        lifetime_array, censoring_array = self.get_lifetime_arrays()

        for i in range(len(lifetime_array)):
            lifetime = lifetime_array[i]
            censoring = censoring_array[i]

            if censoring == 2 and isinstance(lifetime, list):
                if interval_lifetime_indicator == 'start':
                    lifetime_array[i] = lifetime[0]
                elif interval_lifetime_indicator == 'mid':
                    lifetime_array[i] = sum(lifetime) / 2
                elif interval_lifetime_indicator == 'end':
                    lifetime_array[i] = lifetime[1]

                # updating censoring value for interval-censored data
                censoring_array[i] = 0

        return lifetime_array, censoring_array
