import time
import asyncio
import aiohttp
import random
import string
import json
import logging
import requests
from bs4 import BeautifulSoup
from logging.handlers import RotatingFileHandler
from tempmail import TempMail 

def fetch_proxies_from_github(urls):
    proxies = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  
            proxies += response.text.split('\n')
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch proxies from {url}. Error: {e}")
            continue
    return proxies

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
log_file = 'errors.log'

my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.ERROR)

app_log = logging.getLogger('root')
app_log.setLevel(logging.ERROR)

app_log.addHandler(my_handler)

with open('config.json') as f:
    config = json.load(f)

async def main():
    with open('config.json') as f:
        config = json.load(f)

    proxy_source = input("Choose proxy source (1 - local files, 2 - GitHub repo, 3 - both): ")
    proxies = []
    if proxy_source in ['1', '3']:
        for filename in ['/home/pogoweb/PoGo/PTC/proxy-scraper-checker/proxies/http.txt', '/home/pogoweb/PoGo/PTC/proxy-scraper-checker/proxies/socks4.txt', '/home/pogoweb/PoGo/PTC/proxy-scraper-checker/proxies/socks5.txt']:
            with open(filename) as f:
                proxies += [line.strip() for line in f.readlines()]
    if proxy_source in ['2', '3']:
        if 'github_urls' in config:
            github_urls = config['github_urls']
            proxies += fetch_proxies_from_github(github_urls)

    accounts = []
    async with aiohttp.ClientSession() as session:
        for proxy in proxies:
            proxy_error_count = 0
            username = generate_random_string(config['username_length'])
            password = generate_random_string(config['password_length'])
            for i in range(config['num_accounts_per_proxy']):
                if proxy_error_count >= 2:
                    print(f"Skipping proxy {proxy} due to too many errors.")
                    break

                temp = TempMail()  
                email = temp.mail  
                temp.delete_mail()  

                try:
                    success = await asyncio.wait_for(register_and_activate_account(session, temp, proxy, email, username, password), timeout=config['timeout'])
                    if success:
                        accounts.append([username, password])
                    proxy_error_count = 0
                except asyncio.TimeoutError:
                    print(f"Timeout while creating account with proxy {proxy}. Moving to the next one...")
                    continue
                except Exception as e:
                    app_log.error(f"Error while using proxy {proxy}: {e}")
                    proxy_error_count += 1


async def request_with_retry(session, url, method="GET", retries=3, **kwargs):
    for i in range(retries):
        try:
            if method == "GET":
                async with session.get(url, **kwargs) as response:
                    return response
            elif method == "POST":
                async with session.post(url, **kwargs) as response:
                    return response
        except Exception as e:
            if i == retries - 1: 
                raise e 
            await asyncio.sleep(1) 

def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

async def register_and_activate_account(session, temp, proxy, email, username, password):
    # Register account
    url = "https://club.pokemon.com/us/pokemon-trainer-club/sign-up/"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Content-Type": "application/json"
    }
    data = {
    "email": email,
    "password": password,
    "confirm_password": password,
    "username": username,
    "dob": "2000-01-01",
    "locale": "en_US",
    "country": "US",
    "isChild": "false",
    "cboxTOS": "true",
    }
    try:
        async with session.post(url, headers=headers, json=data, proxy=proxy, timeout=10) as response:
            if response.status == 200:
                print(f"Account created successfully! Email: {email}, Username: {username}, Password: {password}")

                messages = []
                while not messages:  
                    await asyncio.sleep(10)  
                    messages = await temp.check_mails()  

                message_content = next((m['mail_text'] for m in messages if m['mail_subject'] == 'Activate Your Pokémon Trainer Club Account'), None)
                soup = BeautifulSoup(message_content, 'html.parser')
                activation_code_element = soup.select_one('a[href^="https://club.pokemon.com/us/pokemon-trainer-club/activated/"]')
                activation_code = activation_code_element['href'].split('/')[-1] if activation_code_element else None

                if activation_code:
                    await asyncio.sleep(10)  
                    activation_url = f"https://club.pokemon.com/us/pokemon-trainer-club/activated/{activation_code}"
                    async with session.get(activation_url, proxy=proxy) as response:
                        response.raise_for_status()  
                    return True  
                else:
                    print(f"Failed to extract activation code from email with proxy {proxy}. Skipping activation...")
            else:
                raise Exception(f"Failed to create account with status code {response.status}")
    except Exception as e:
        status_code = response.status if 'response' in locals() else 'No response'
        print(f"Error while creating account. Status code: {status_code}. Error: {e}")
        raise e

temp = TempMail()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())