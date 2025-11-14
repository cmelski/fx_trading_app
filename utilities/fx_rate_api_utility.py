import json
import os
import requests
from utilities.logging_utility import logging_format as logger


class FXRateAPIUtility:

    def __init__(self):
        self.base_url = 'https://v6.exchangerate-api.com/v6/6e63152bbe49578c46175711/latest/'

    def get(self, ccy_pairs=None):

        rates = dict()

        for ccy_pair in ccy_pairs:

            response = requests.get(url=self.base_url+ccy_pair[:3])
            response.raise_for_status()
            assert response.ok
            fx_rate = response.json()['conversion_rates'][ccy_pair[3:]]
            logger().info(fx_rate)
            rates[ccy_pair] = fx_rate

        return rates

