import asyncio
import pytest
from tests.conftest import logger

@pytest.mark.asyncio
@pytest.mark.trade_validations
async def test_trade_validations(page):
    card = page.locator(f'div.pair-card').nth(1)

    #max position breached buying base ccy

    max_position = await card.get_attribute("data-maxbalance")
    current_position = await card.get_attribute("data-currentposition")
    if '-' in current_position:
        max_position = float(max_position) + abs(float(current_position))
        avail_amt = float(max_position)
    else:
        avail_amt = float(max_position) - float(current_position)

    input_amt = avail_amt + 1
    logger.info(f'Max position: {max_position}')
    logger.info(f'Current position: {current_position}')
    logger.info(f'Available Amt: {avail_amt}')
    logger.info(f'Input amt: {input_amt}')

    base_amount_input = card.locator('.base-amount')
    await base_amount_input.fill(f'{str(input_amt)}')

    alert_text = None

    # Attach dialog handler before click
    def handle_dialog(dialog):
        nonlocal alert_text
        alert_text = dialog.message
        asyncio.create_task(dialog.accept())  # accept asynchronously

    page.once("dialog", handle_dialog)

    # Trigger the alert
    await card.locator(".submit-trade").click()

    # Give event loop a tiny moment to process dialog
    await asyncio.sleep(0.1)

    # Assert the alert text
    logger.info(f'Alert text: {alert_text}')
    assert alert_text == "Trade amount breaches limit."

    #validate position bar tooltip

    tooltip = card.locator('.tooltiptext')
    tooltip_text = await tooltip.text_content()
    assert tooltip_text == current_position

    #empty trade amount

    await base_amount_input.fill('')

    page.once("dialog", handle_dialog)

    await card.locator(".submit-trade").click()

    # Give event loop a tiny moment to process dialog
    await asyncio.sleep(0.1)

    # Assert the alert text
    logger.info(f'Alert text: {alert_text}')
    assert alert_text == "Enter a base amount before continuing."







