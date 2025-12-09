import requests
from tests.conftest import logger


class FXAPIUtility:

    def __init__(self):
        self.base_url = 'http://127.0.0.1:5002/api/'

    def post(self, endpoint=None, data=None, params=None):
        response = requests.post(url=self.base_url + endpoint, json=data, params=params)
        logger.info(f'{self.base_url + endpoint}')
        response.raise_for_status()
        assert response.ok
        response_message = response.json()
        logger.info(f'Response from API: {response_message}')
        return response_message
