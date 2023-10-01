# data_processing/lifetime_processor.py

class LifetimeProcessor:
    def __init__(self, data):
        self.data = data
        self.lifetime_array, self.censoring_array = self._extract_lifetime_and_censoring()

    def _extract_lifetime_and_censoring(self):
        lifetime_array = [entry["lifetime"] for entry in self.data]
        censoring_array = [entry["censoring"] for entry in self.data]
        return lifetime_array, censoring_array

    def process_interval_censoring(self, interval_lifetime_indicator='mid'):
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

        for i in range(len(self.lifetime_array)):
            lifetime = self.lifetime_array[i]
            censoring = self.censoring_array[i]

            if censoring == 2 and isinstance(lifetime, list):
                if interval_lifetime_indicator == 'start':
                    self.lifetime_array[i] = lifetime[0]
                elif interval_lifetime_indicator == 'mid':
                    self.lifetime_array[i] = sum(lifetime) / 2
                elif interval_lifetime_indicator == 'end':
                    self.lifetime_array[i] = lifetime[1]

                # updating censoring value for interval-censored data
                self.censoring_array[i] = 0

        return self.lifetime_array, self.censoring_array
