import asyncio
import pytest
from collections import Counter
from tests.conftest import logger
from utilities.db_common_functions import DB_Common


@pytest.mark.asyncio
@pytest.mark.dashboard
async def test_get_fx_dashboard(page):
    assert 'Dashboard' in await page.title()
    await asyncio.sleep(2)


@pytest.mark.asyncio
@pytest.mark.stats
async def test_dashboard_stats(page):
    # total trades
    trade_rows_blotter = page.locator("#spot-blotter table tbody tr")
    trade_count_blotter = await trade_rows_blotter.count()  # FIX: await
    logger.info(f'Trade count blotter: {trade_count_blotter}')

    trade_count_stats = page.locator('#total-trades')
    trade_count_stats_text = int(await trade_count_stats.text_content())
    logger.info(f'Trade count stats: {trade_count_stats_text}')

    assert trade_count_stats_text == trade_count_blotter
    await asyncio.sleep(2)

    # last trade

    last_trade_row = trade_rows_blotter.nth(0)
    last_trade_cells = last_trade_row.locator('td')
    last_trade_ccy_pair = last_trade_cells.nth(3)
    last_trade_ccy_pair_text = await last_trade_ccy_pair.inner_text()
    logger.info(f'Last trade blotter: {last_trade_ccy_pair_text}')

    last_trade_ccy_pair_stats = page.locator('#last-trade')
    last_trade_ccy_pair_stats_text = await last_trade_ccy_pair_stats.text_content()
    logger.info(f'Last trade stats: {last_trade_ccy_pair_stats_text}')

    assert last_trade_ccy_pair_text == last_trade_ccy_pair_stats_text

    # most frequent ccy pair
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

    # largest trade
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

    # GUI vs API trades
    trade_source = []
    trade_source_panel = page.locator('#trade-source')
    target_text = 'Source'
    target_index = None

    for i in range(count):
        text = await headers.nth(i).inner_text()
        if text.strip() == target_text:
            target_index = i
            break

    for i in range(blotter_rows_count):
        row = blotter_rows.nth(i)
        cells = row.locator('td')
        source = cells.nth(target_index)
        source_text = await source.inner_text()
        trade_source.append(source_text)

    source_counts = Counter(trade_source) #turns into a dictionary
    sorted_source_counts = dict(sorted(source_counts.items()))
    source_counts_string = ''
    for key, value in sorted_source_counts.items():
        source_counts_string+= f'{key} ({value}), '

    logger.info(f'source counts: {source_counts_string}')

    trade_source_panel_text = await trade_source_panel.inner_text()
    logger.info(f'source counts panel: {trade_source_panel_text}')

    assert source_counts_string.replace(',','').strip() == trade_source_panel_text.replace(',','').strip()

    #total orders

    total_orders_panel = page.locator('#total-orders')
    total_orders_panel_text = await total_orders_panel.inner_text()

    logger.info(f'total orders stats panel: {total_orders_panel_text}')

    total_orders_blotter_tab = page.locator('.blotter-tab[data-target="order-blotter"]')
    total_orders_blotter_tab_text = await total_orders_blotter_tab.inner_text()
    total_orders_blotter_tab_text_stripped = total_orders_blotter_tab_text.split('(')[1].replace(')', '')

    logger.info(f'total orders blotter tab: {total_orders_blotter_tab_text_stripped}')

    assert total_orders_panel_text == total_orders_blotter_tab_text_stripped

    order_blotter_rows = page.locator('#order-blotter-body tr')
    order_blotter_rows_count = await order_blotter_rows.count()

    assert int(total_orders_panel_text) == order_blotter_rows_count



@pytest.mark.asyncio
@pytest.mark.cards
async def test_dashboard_cards(page):
    # verify number of ccy pair cards

    # GUI
    cards = page.locator('div .pair-card')
    cards_count = await cards.count()
    logger.info(f'GUI card count: {cards_count}')

    # DB

    ccy_pair_info_db = DB_Common().retrieve_ccy_pairs()
    logger.info(f'DB ccy pair count: {len(ccy_pair_info_db)}')

    assert cards_count == len(ccy_pair_info_db)

    # verify max position and current position per ccy pair

    ccy_pair_card_gui = dict()

    for i in range(cards_count):
        ccy_pair = await cards.nth(i).get_attribute("data-pair")
        max_balance = await cards.nth(i).get_attribute("data-maxbalance")
        max_balance = str("{:.2f}".format(float(max_balance)))
        current_position = await cards.nth(i).get_attribute("data-currentposition")
        current_position = str("{:.2f}".format(float(current_position)))
        ccy_pair_card_gui[ccy_pair] = (max_balance, current_position)

    logger.info(f'card info gui: {ccy_pair_card_gui}')

    ccy_pair_card_db = dict()

    for i in range(len(ccy_pair_info_db)):
        ccy_pair = ccy_pair_info_db[i][1]
        max_balance = str(ccy_pair_info_db[i][2])
        current_position = str(ccy_pair_info_db[i][4])
        ccy_pair_card_db[ccy_pair] = (max_balance, current_position)

    logger.info(f'card info db: {ccy_pair_card_db}')

    assert ccy_pair_card_db == ccy_pair_card_gui
