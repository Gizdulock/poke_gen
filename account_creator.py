# account_creator.py

import requests
import json

def register_and_activate_account():
    config = json.load(open('config.json')) # load configuration file
    proxies = config['proxies'] # get list of proxies
    
    for proxy in proxies:
        try:
            # make a request to create account using current proxy
            response = requests.post('https://example.com/api/account', proxies={'https': proxy})
            account_info = response.json()
            # activate account using the retrieved info
            activation_response = requests.post('https://example.com/api/account/activate', data=account_info)
            print(f"Account created successfully! Email: {account_info['email']}, Username: {account_info['username']}, Password: {account_info['password']}")
            return
        except requests.exceptions.Timeout:
            print(f"Timeout while creating account with proxy {proxy}. Moving to the next one...")
            continue

    print("Failed to create account with all available proxies.")

def retry_on_timeout_error():
    try:
        register_and_activate_account()
    except requests.exceptions.Timeout:
        print("Timeout while creating account. Retrying with next available proxy...")
        retry_on_timeout_error() # recursively call function to retry with next available proxy

retry_on_timeout_error() # start account creation process with retry on timeout error