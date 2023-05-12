import asyncio
import requests
import random
import string
import csv
import aiohttp
from bs4 import BeautifulSoup


async def main():
    with open('working_proxy.txt') as f:
        proxies = [line.strip() for line in f.readlines()]

    accounts = []
    for proxy in proxies:
        for i in range(50):
            email = generate_temp_email()
            username = generate_random_string(8)
            password = generate_random_string(12)
            try:
                success = await asyncio.wait_for(register_account(proxy, email, username, password), timeout=10)
                if success:
                    accounts.append([username, password])
                    await activate_account(email)  # fix: properly await coroutine
                else:
                    print(f"Failed to create account with proxy {proxy}. Moving to the next one...")
            except asyncio.TimeoutError:
                print(f"Timeout while checking {proxy}. Moving to the next one...")
                break
            except Exception as e:
                print(f"Error while using proxy {proxy}: {e}")
                continue
            
    save_accounts_to_csv(accounts)



def generate_temp_email():
    url = "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1"
    response = requests.get(url)
    email = response.json()[0].replace("@", "+") + "@1secmail.com"
    return email


async def register_account(proxy, email, username, password):
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
    proxies = {"http": proxy, "https": proxy}
    try:
        response = requests.post(url, headers=headers, json=data, proxies=proxies, timeout=5)
        if response.status_code == 200:
            print(f"Account created successfully! Email: {email}, Username: {username}, Password: {password}")
            messages = await get_email_messages(email)
            while not messages:
                await asyncio.sleep(1)
                messages = await get_email_messages(email)
            message_id = messages[0]['id']
            message = await read_email_message(email, message_id)
            activation_link = message['body'].split('\n')[-2].split()[-1]
            async with aiohttp.ClientSession() as session:
                async with session.get(activation_link) as response:
                    response.raise_for_status()
            print(f"Account activated successfully! Email: {email}")
            return True
        else:
            print(f"Failed to create account with error code {response.status_code}")
    except (requests.exceptions.ProxyError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"Error while using proxy {proxy}: {e}")
    return False


async def activate_account(email):
    try:
        messages = await get_email_messages(email)
        if not messages:
            raise ValueError(f"No messages found for email {email}")
        message_id = messages[0]['id']
        message = await read_email_message(email, message_id)
        activation_link = message['body'].split('\n')[-2].split()[-1]
        async with aiohttp.ClientSession() as session:
            async with session.get(activation_link) as response:
                response.raise_for_status()
        print(f"Account activated successfully! Email: {email}")
    except Exception as e:
        print(f"Error while activating account {email}: {e}")


async def read_email_message(email, message_id):
    url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={email.split('@')[0]}&domain=1secmail.com&id={message_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    message = {
        'from': soup.find('div', class_='col-md-8').find_all('div')[0].text.strip(),
        'subject': soup.find('div', class_='col-md-8').find_all('div')[1].text.strip(),
        'date': soup.find('div', class_='col-md-8').find_all('div')[2].text.strip(),
        'body': str(soup.find('div', class_='col-md-8').find_all('div')[3]),
    }
    return message

async def get_email_messages(email):
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={email.split('@')[0]}&domain=1secmail.com"
    response = requests.get(url)
    messages = response.json()
    return messages

def save_accounts_to_csv(accounts):
    with open('pokemon_accounts.csv', mode='w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Username', 'Password'])
        writer.writerows(accounts)

def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

if __name__ == "__main__":
    asyncio.run(main())
