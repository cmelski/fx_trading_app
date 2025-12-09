import random
import string


def generate_random_string():
    random_string = ''.join(random.choices(string.ascii_letters, k=10))
    return random_string


def generate_random_rates(ccy_pair_info):
    for ccy_pair, rate in ccy_pair_info.items():
        source = rate[3]
        if source == 'streaming':
            rate_constant = str(rate[0]).split('.')[0] + '.' + str(rate[0]).split('.')[1][0]
            random_rate = ''
            for i in range(1, 4):
                random_rate += str(random.randint(0, 9))

            ccy_pair_info[ccy_pair] = (rate_constant + random_rate, float(rate[1]), float(rate[2]), source)

    return ccy_pair_info
