import data_handler as DATA_HANDLER
from datetime import date
from 


class ImageHandler:

    def get_exponential_model_fit_image(self, failure_type_code: str, num_objects: int, end_observation_period: date = '2016-06-30'):
        lifetimes = DATA_HANDLER.calculate_lifetimes(
            failure_type_code, num_objects, end_observation_period)
        
        
    
    
