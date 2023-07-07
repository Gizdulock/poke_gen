from random import choice
from time import sleep
from re import search
import sys, os, string
import requests
import aiohttp
from bs4 import BeautifulSoup

class TempMail:
    API = 'https://www.1secmail.com/api/v1/'
    DELETE_API = 'https://www.1secmail.com/mailbox'
    DOMAIN_LIST = ['1secmail.com', '1secmail.net', '1secmail.org']
    NAME_LENGHT = 10

    def __init__(self, name=None, verbose=0):
        if name == None:
            self.name = self.generate_user_name()
        else:
            self.name = name
        self.verbose = verbose
        self.create_mail(self.name, choice(self.DOMAIN_LIST))
        if self.verbose:
            print(f"[+] {self.mail} Created")
        self.recived_mails = 0

    @staticmethod
    def generate_user_name():
        name = string.ascii_lowercase + string.digits
        username = ''.join(choice(name) for char in range(TempMail.NAME_LENGHT))
        return username

    @staticmethod
    def mkdir(folder):
        cwd = os.getcwd()
        new_dir = os.path.join(cwd, folder)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        return new_dir

    @staticmethod
    def print_statusline(msg):
        last_msg_len = len(print_statusline.last_msg) if hasattr(print_statusline, 'last_msg') else 0
        print(' ' * last_msg_len, end='\r')
        print(msg, end='\r')
        sys.stdout.flush()
        print_statusline.last_msg = msg

    def create_mail(self, name, domain):
        self.login = name
        self.domain = domain
        new_mail = f"{self.API}?login={self.name}&domain={self.domain}"
        request_mail = requests.get(new_mail)
        self.mail = f"{self.login}@{self.domain}"

    def delete_mail(self):
        data = {
            'action': 'deleteMailbox',
            'login': f'{self.login}',
            'domain': f'{self.domain}'
        }
        req = requests.post(self.DELETE_API, data=data)

    def read_mail(self, mail_id):
        msg_read = f'{self.API}?action=readMessage&login={self.login}&domain={self.domain}&id={mail_id}'
        req = requests.get(msg_read).json()
        soup = BeautifulSoup(req['body'], 'html.parser')
        content = dict(req.items())
        content['body'] = soup.get_text()
        content['id'] = mail_id
        return content

    def write_mail(self, content):
        mail_id = content.get('id')
        mail_file_path = os.path.join(self.mail_dir, f'{mail_id}.txt')
        with open(mail_file_path,'w') as file:
            file.write(f"To: {self.mail}\n\n")
            for key, text in content.items():
                file.write(f"{key}: {text}\n")

    async def check_mails(self):
        request_link = f'{self.API}?action=getMessages&login={self.name}&domain={self.domain}'
        async with aiohttp.ClientSession() as session:
            response = await session.get(request_link)
            req = await response.json()

        self.recived_mails = len(req)
        if self.recived_mails == 0:
            if self.verbose:
                self.print_statusline("[-] Your mailbox is empty")
            return []

        self.mail_ids = []
        for response in req:
            for key, mail_id in response.items():
                if key == 'id':
                    self.mail_ids.append(mail_id)

        if self.verbose:
            print(f"[+] You received {self.recived_mails}", 'mails' if self.recived_mails > 1 else 'mail')
        return req

    def run_server(self):
        try:
            while True:
                self.check_mails()
                self.mail_dir = self.mkdir('Mails')
                for mail_id in self.mail_ids:
                    content = self.read_mail(mail_id)
                    self.write_mail(content)
                sleep(5)
        except KeyboardInterrupt:
            self.delete_mail()
            if self.verbose:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f'[+] {self.mail} Deleted')