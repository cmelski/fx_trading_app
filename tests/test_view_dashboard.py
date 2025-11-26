import asyncio
import pytest
from collections import Counter
from tests.conftest import logger


@pytest.mark.asyncio
@pytest.mark.dashboard
async def test_get_fx_dashboard(page):

    assert 'Dashboard' in await page.title()
    await asyncio.sleep(2)



@pytest.mark.asyncio
@pytest.mark.stats
async def test_dashboard_stats(page):

    #total trades
    trade_rows_blotter = page.locator("table tbody tr")
    trade_count_blotter = await trade_rows_blotter.count()  # FIX: await
    logger.info(f'Trade count blotter: {trade_count_blotter}')

    trade_count_stats = page.locator('#total-trades')
    trade_count_stats_text = int(await trade_count_stats.text_content())
    logger.info(f'Trade count stats: {trade_count_stats_text}')

    assert trade_count_stats_text == trade_count_blotter
    await asyncio.sleep(2)

    #last trade

    last_trade_row = trade_rows_blotter.nth(0)
    last_trade_cells = last_trade_row.locator('td')
    last_trade_ccy_pair = last_trade_cells.nth(3)
    last_trade_ccy_pair_text = await last_trade_ccy_pair.inner_text()
    logger.info(f'Last trade blotter: {last_trade_ccy_pair_text}')

    last_trade_ccy_pair_stats = page.locator('#last-trade')
    last_trade_ccy_pair_stats_text = await last_trade_ccy_pair_stats.text_content()
    logger.info(f'Last trade stats: {last_trade_ccy_pair_stats_text}')

    assert last_trade_ccy_pair_text == last_trade_ccy_pair_stats_text

    #most frequent ccy pair
    ccy_pairs = []
    blotter_rows = page.locator('#blotter-body tr')
    blotter_rows_count = await blotter_rows.count()

    headers = page.locator("table thead th")
    count = await headers.count()

    target_index = None
    target_text = "Pair"  # <-- the text you're looking for

    for i in range(count):
        text = await headers.nth(i).inner_text()
        if text.strip() == target_text:
            target_index = i
            break

    for i in range(blotter_rows_count):
        row = blotter_rows.nth(i)
        cells = row.locator('td')
        ccy_pair = cells.nth(target_index)
        ccy_pair_text = await ccy_pair.inner_text()
        ccy_pairs.append(ccy_pair_text)

    ccy_pair_counts = Counter(ccy_pairs)

    max_count = max(ccy_pair_counts.values())

    most_frequent = [f'{pair} ({count})' for pair, count in ccy_pair_counts.items() if count == max_count]

    logger.info(f'Most frequent pair blotter: {most_frequent}')


    most_frequent_stats_panel = page.locator('#most-frequent-pair')
    most_frequent_stats = await most_frequent_stats_panel.inner_text()
    most_frequent_stats_list = most_frequent_stats.split(',')
    most_frequent_stats_list_clean = [item.strip() for item in most_frequent_stats_list]
    logger.info(f'Most frequent pair stats: {most_frequent_stats_list_clean}')
    assert Counter(most_frequent_stats_list_clean) == Counter(most_frequent)

    #largest trade
    trade_amounts = []

    target_text = "Base Amount"  # <-- the text you're looking for

    for i in range(count):
        text = await headers.nth(i).inner_text()
        if text.strip() == target_text:
            target_index = i
            break

    for i in range(blotter_rows_count):
        row = blotter_rows.nth(i)
        cells = row.locator('td')
        amount = cells.nth(target_index)
        amount_text = await amount.inner_text()
        trade_amounts.append(float(amount_text.replace(',', '')))


    max_amount = max(trade_amounts)
    logger.info(f'Max amount: {max_amount}')

    largest_trade_panel = page.locator('#largest-trade')
    largest_trade_stats = await largest_trade_panel.inner_text()
    largest_trade_stats = largest_trade_stats.replace('$', '')
    largest_trade_stats = float(largest_trade_stats.replace(',', ''))
    logger.info(f'Largest trade stats panel: {largest_trade_stats}')

    assert max_amount == largest_trade_stats





    # for i in range(trade_count):
    #     trade_row = trade_rows.nth(i)
    #
    #     cells = trade_row.locator("td")
    #     cell_count = await cells.count()  # FIX: await
    #
    #     for j in range(cell_count):
    #         cell = cells.nth(j)
    #         text = await cell.inner_text()  # FIX: await
    #         logger.info(f"Cell[{i},{j}]: {text}")



