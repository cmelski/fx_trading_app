import asyncio
import os

import pytest
from collections import Counter
from tests.conftest import logger
from utilities.db_common_functions import DB_Common
import pandas as pd
from pathlib import Path

from utilities.fx_api_utility import FXAPIUtility


@pytest.fixture()
def get_trades_for_input():
    file_path = Path(__file__).parent.parent / "data" / "trades.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        trades = df.to_dict(orient="records")
        logger.info(f'Trades: {trades}')
        return trades
    else:
        return [{'CcyPair': 'CADSGD', 'Direction': 'Sell', 'Amount': 2000000, 'Markup': 50}]


@pytest.mark.asyncio
@pytest.mark.deal
async def test_deal(page, get_trades_for_input):
    for trade in get_trades_for_input:
        currency_pair = trade['CcyPair']
        # clear position
        DB_Common().clear_position(currency_pair)

    for trade in get_trades_for_input:

        ccy_pair_for_trade = trade['CcyPair']
        # get ccy_pair card
        card = page.locator(f'div.pair-card[data-pair="{ccy_pair_for_trade}"]')
        ccy_pair = await card.get_attribute("data-pair")
        logger.info(f'Ccy Pair: {ccy_pair}')

        # fill in trade info
        direction_for_trade = trade['Direction']

        direction_dropdown = card.locator(f'select[name="direction"]')
        direction = await direction_dropdown.select_option(f'{direction_for_trade} {ccy_pair[0:3]}')
        logger.info(f'Direction: {direction[0]}')

        base_amount_for_trade = trade['Amount']

        base_amount_input = card.locator('.base-amount')
        await base_amount_input.fill(f'{base_amount_for_trade}')
        base_amount_value = await base_amount_input.input_value()
        logger.info(f'Base amount: {base_amount_value}')

        counter_amount = card.locator('.counter-amount')
        counter_amount_value = await counter_amount.input_value()
        logger.info(f'Counter amount: {counter_amount_value}')

        # markup

        markup_for_trade = int(trade['Markup'])

        slider = card.locator('input[type="range"]')

        await slider.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('input')); el.dispatchEvent(new Event('change')); }",
            markup_for_trade)

        markup_value = await card.locator('.markup-value-pips').inner_text()
        logger.info(f'Markup: {markup_value}')

        # deal

        rate = await card.get_attribute("data-rate")
        logger.info(f'Rate: {rate}')

        # validate spot rate on trade matches latest spot rate in DB

        # spot_rate_db = DB_Common().get_spot_rate(ccy_pair)
        # logger.info(f'Spot Rate DB: {spot_rate_db}')
        # assert "{:,.4f}".format(float(spot_rate_db)) == "{:,.4f}".format(float(rate))

        await card.locator('.submit-trade').click()

        await asyncio.sleep(2)

        # get trade from blotter
        #await page.locator('button[data-target="spot-blotter"]').click()
        trade_rows_blotter = page.locator("div #spot-blotter #blotter-body tr")
        trade_count_blotter = await trade_rows_blotter.count()
        logger.info(f'trade count blotter: {trade_count_blotter}')
        last_trade_row = trade_rows_blotter.nth(0)
        last_trade_cells = last_trade_row.locator('td')

        # get column headings

        trade_blotter_headers = page.locator('div #spot-blotter table th')
        trade_blotter_headers_count = await trade_blotter_headers.count()
        logger.info(f'blotter header count: {trade_blotter_headers_count}')

        dealt_counter_amount = 0.00
        blotter_counter_amount = 0.00

        for i in range(trade_blotter_headers_count):
            header = await trade_blotter_headers.nth(i).inner_text()
            if header == 'Pair':
                index = i
                blotter_ccy_pair = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter Ccy Pair: {blotter_ccy_pair}')
                assert blotter_ccy_pair == ccy_pair
            if header == 'Direction':
                index = i
                blotter_direction = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter direction: {blotter_direction}')
                assert blotter_direction == direction[0]
            if header == 'Base Amount':
                index = i
                blotter_base_amount = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter Base Amount: {blotter_base_amount}')
                assert blotter_base_amount == base_amount_value
            if header == 'Spot Rate':
                index = i
                blotter_spot_rate = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter Spot Rate: {blotter_spot_rate}')
                assert "{:,.4f}".format(float(blotter_spot_rate)) == "{:,.4f}".format(float(rate))
            if header == 'Dealt Rate':
                index = i
                blotter_dealt_rate = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter Dealt Rate: {blotter_dealt_rate}')
                if direction[0] == 'Buy':
                    calc_rate = "{:,.4f}".format(float(rate) + (float(markup_value) / 10000))
                    logger.info(f'Calc Rate: {calc_rate}')
                    dealt_counter_amount = float(base_amount_value.replace(',', '')) * float(calc_rate)
                    logger.info(f'Dealt Counter Amount: {dealt_counter_amount}')
                    assert "{:,.4f}".format(float(blotter_dealt_rate)) == calc_rate


                else:
                    calc_rate = "{:,.4f}".format(float(rate) - (float(markup_value) / 10000))
                    logger.info(f'Calc Rate: {calc_rate}')
                    dealt_counter_amount = float(base_amount_value.replace(',', '')) * float(calc_rate)
                    logger.info(f'Dealt Counter Amount: {dealt_counter_amount}')
                    assert "{:,.4f}".format(float(blotter_dealt_rate)) == calc_rate

            if header == 'Counter Amount':
                index = i
                blotter_counter_amount = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter Counter Amount: {blotter_counter_amount}')

            if header == 'Markup (pips)':
                index = i
                blotter_markup = await last_trade_cells.nth(index).inner_text()
                logger.info(f'Blotter Markup: {blotter_markup}')
                assert float(blotter_markup) * 10000 == float(markup_value)

        # validate counter amount
        logger.info('reached here')
        assert float(blotter_counter_amount.replace(',', '')) == dealt_counter_amount

        await asyncio.sleep(2)


@pytest.mark.asyncio
@pytest.mark.deal_api
async def test_deal_api(page):
    trade_data = {
        "ccy_pair": "CADSGD",
        "direction": "Buy",
        "base_ccy": "CAD",
        "base_amt": "1234.56",
        "counter_ccy": "SGD",
        "markup": "48"

    }

    end_point = 'submit_trade'

    result = FXAPIUtility().post(end_point, trade_data)
    logger.info(result)

    #assert spot rate matches DB:

    spot_rate_api_response = result['trade']['spot_rate']
    spot_rate_db = DB_Common().get_spot_rate(result['trade']['ccy_pair'])

    assert spot_rate_db == spot_rate_api_response




