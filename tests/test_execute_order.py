import asyncio
import os

import pytest
from collections import Counter
from tests.conftest import logger
from utilities.db_common_functions import DB_Common
import pandas as pd
from pathlib import Path
from utilities import generic_utilities as gu


@pytest.fixture()
def get_orders_for_input():
    file_path = Path(__file__).parent.parent / "data" / "orders.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        orders = df.to_dict(orient="records")
        logger.info(f'Orders: {orders}')
        return orders
    else:
        return [{'CcyPair': 'EURUSD', 'Direction': 'Sell', 'Amount': 2000000, 'Level': '0.9245'}]


@pytest.mark.asyncio
@pytest.mark.order
async def test_order(page, get_orders_for_input):
    for order in get_orders_for_input:
        currency_pair_for_order = order['CcyPair']
        # get ccy_pair card
        card = page.locator(f'div.pair-card[data-pair="{currency_pair_for_order}"]')
        ccy_pair = await card.get_attribute("data-pair")
        logger.info(f'Ccy Pair: {ccy_pair}')

        # fill in order info
        direction_for_order = order['Direction']

        if direction_for_order == 'Sell':
            direction_dropdown = card.locator(f'select[name="direction"]')
            direction = await direction_dropdown.select_option(f'{direction_for_order} {ccy_pair[0:3]}')
            direction_for_order = direction[0]

        rate_for_order = card.locator('.spot-rate')
        rate_for_order_text = await rate_for_order.inner_text()

        await card.locator('.open-order-ticket').click()

        #fill in order ticket

        oe = page.locator('.order-entry')

        ccy_pair_oe = oe.locator('#oe-pair')
        ccy_pair_oe_text = await ccy_pair_oe.input_value()

        direction_oe = oe.locator('#oe-direction')
        direction_oe_text = await direction_oe.input_value()

        rate_oe = oe.locator('#oe-rate')
        rate_oe_text = await rate_oe.input_value()

        assert ccy_pair == ccy_pair_oe_text
        assert direction_for_order == direction_oe_text
        assert rate_for_order_text == rate_oe_text

        await oe.locator('#oe-level').fill(str(order['Level']))
        await oe.locator('#oe-amount').fill(str(order['Amount']))
        random_reference_string = gu.generate_random_string()
        await oe.locator('#oe-reference').fill(random_reference_string)

        await oe.locator('#oe-submit').click()

        #validate order details

        order_blotter_headers = page.locator('#order-blotter-table th')
        order_blotter_headers_count = await order_blotter_headers.count()
        order_row = page.locator('#order-blotter-table tbody tr:first-child')
        order_row_cells = order_row.locator('td')

        for i in range(order_blotter_headers_count):
            order_blotter_header = await order_blotter_headers.nth(i).inner_text()

            if order_blotter_header == 'Reference':
                reference_blotter_text = await order_row_cells.nth(i).inner_text()
                assert random_reference_string == reference_blotter_text

            if order_blotter_header == 'Ccy Pair':
                ccy_pair_blotter_text = await order_row_cells.nth(i).inner_text()
                assert ccy_pair == ccy_pair_blotter_text











        await asyncio.sleep(2)


