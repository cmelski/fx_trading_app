import json
import os
import shutil
import logging
import time
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright, TimeoutError
import psycopg
import pytest
import pytest_asyncio

# load prod.env file variables
from dotenv import load_dotenv

# set up logging
# Configure once (e.g., in conftest.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# define test run parameters
# in terminal you can run for e.g. 'pytest test_web_framework_api.py --browser_name firefox'
def pytest_addoption(parser):
    parser.addoption(
        "--browser_name", action="store", default="chrome", help="browser selection"
    )

    parser.addoption(
        "--url_start", action="store", default="test", help="starting url"
    )

    parser.addoption(
        "--env", action="store", default="test", help="Environment to run tests against")


@pytest.fixture(scope="session")
def env(request):
    env_name = request.config.getoption("--env")
    # Load the corresponding .env file
    load_dotenv(f"{env_name}.env")
    return env_name


@pytest.fixture(scope="session")
def url_start(env):  # env fixture ensures .env is loaded first
    return os.environ.get("BASE_URL")


@pytest.fixture(scope="session")
def db_connection(env):
    if env == 'test':
        conn = psycopg.connect(
            dbname=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT')
        )
    else:
        conn = psycopg.connect(os.environ.get('DB_HOST'))

    yield conn
    conn.close()


load_dotenv(f"{env}.env")

#with async playwright, conftest fixture to yield page must be scope=function
@pytest_asyncio.fixture(scope='function')
async def page(request, url_start, env):
    async with async_playwright() as p:
        browser_name = request.config.getoption('browser_name')
        url_start = url_start
        if browser_name == 'chrome':
            browser = await p.chromium.launch(headless=False)
        elif browser_name == 'firefox':
            browser = await p.firefox.launch(headless=False)

        context = await browser.new_context()

        page = await context.new_page()
        await page.goto(url_start)

        try:

            yield page
        finally:
            await context.close()
            await browser.close()

