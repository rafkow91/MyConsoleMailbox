"""All classes used in my app"""
from getpass import getpass
import imaplib
from json import load, dump

from email import message
from email.header import decode_header
from email import message_from_bytes
from re import match, search

from yaml import safe_load, safe_dump
from tabulate import tabulate


class Application:
    """Class repesented main app"""

    def __init__(self, config_file: str = 'config.yml') -> None:
        self.config_file = config_file
        self.mail_list = self._get_mails_list_from_yml()

    def _get_mails_list_from_yml(self):
        while True:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as config_file:
                    mail_list = safe_load(config_file)
                    break
            except FileNotFoundError:
                print('You don\'t have config file. Please insert your configuration.')
                login = input('Username (mail): ')
                password = getpass('Password: ')
                imap_server = input('IMAP server url: ')
                config = {'mails':
                          [{
                              'imap_server': imap_server,
                              'login': login,
                              'password': password
                          }]}

                with open(self.config_file, 'w', encoding='utf-8') as config_file:
                    safe_dump(config, config_file)
                continue
        return mail_list

    def run(self, keyword: str = None, search_range: int = 0, login: str = None):
        """Start the app"""
        regex = r'[a-z0-9.-_]+@[a-z0-9]+[.][a-z]{2,3}'
        for email in self.mail_list['mails']:
            if match(regex, email['login']) is not None:
                if login is None or email['login'].lower() == login.lower():
                    try:
                        mailbox = Mailbox(email['login'], email['password'], email['imap_server'])
                        mailbox.connect_to_mail()
                        mailbox.select_folder()
                        if keyword is None:
                            new_mails = mailbox.check_new_mails()
                        else:
                            new_mails = mailbox.search_in_mails(keyword, search_range)
                    except imaplib.IMAP4.error:
                        print(f'Authentication failed {email["login"]}')
                        return None
                    mails = []

                    for mail in new_mails:
                        mails.append(mailbox.get_header(mail))

                    if len(mails) != 0:
                        print(mailbox.login)
                        print(tabulate(mails, headers=["Title", "From"], tablefmt="github"))
                    elif keyword is None:
                        print(f'On mailbox {email["login"]} don\'t have new mails')
                    elif keyword is not None:
                        print(f'No matching emails were found in {email["login"]}')
            else:
                print(f'Your login {email["login"]} isn\'t correct mail address')


class Mailbox:
    """Class represented mailbox"""

    def __init__(self, login: str = None, password: str = None, imap_server: str = None) -> None:
        self.login = login if login is not None else input('imap_server: ')
        self.password = password if password is not None else input('login: ')
        self.imap_server = imap_server if imap_server is not None else getpass('password: ')
        self.mails_ids = []
        self.json_file = 'mails_ids.json'

    def connect_to_mail(self) -> None:
        """Create connection to mailbox server"""
        self.imap_server = imaplib.IMAP4_SSL(host=self.imap_server)
        self.imap_server.login(self.login, self.password)

    def select_folder(self, folder: str = 'Inbox') -> None:
        """Select folder to be searched"""
        self.imap_server.select(folder)

    def check_new_mails(self) -> list:
        """Check and returns ids of new mails"""
        self.mails_ids = self._get_mails_ids_from_json()
        new_ids = self._get_mails_ids_from_server()
        new_mails = set(new_ids).difference(set(self.mails_ids))
        if len(new_mails) != 0:
            self._save_mails_id_to_json()
        return list(new_mails)

    def _get_mails_ids_from_server(self) -> list:
        mails_ids = self.imap_server.search(None, 'ALL')[1][0].split()
        mails_ids = [int(mail_id) for mail_id in mails_ids]
        return mails_ids

    def _get_mails_ids_from_json(self) -> list:
        try:
            with open(self.json_file, 'r', encoding='utf-8') as input_file:
                content = load(input_file)
        except FileNotFoundError:
            content = {}
        try:
            return content[self.login]
        except KeyError:
            return []

    def _save_mails_id_to_json(self) -> None:
        try:
            with open(self.json_file, 'r', encoding='utf-8') as input_file:
                content = load(input_file)
        except FileNotFoundError:
            content = {}
        try:
            content[self.login] = self._get_mails_ids_from_server()
        except KeyError:
            pass
        with open(self.json_file, 'w', encoding='utf-8') as output_file:
            dump(content, output_file)

    def get_message(self, mail_id) -> message.Message:
        """Download message from mail server"""
        msg = self.imap_server.fetch(str(mail_id).encode('utf-8'), '(RFC822)')[1][0][1]
        mail = message_from_bytes(msg)
        return mail

    def get_header(self, mail_id) -> list:
        """Get header and sender from message object"""
        mail = self.get_message(mail_id)

        try:
            subject, message_encoding = decode_header(mail['Subject'])[0]
        except TypeError:
            subject, message_encoding = ['<without title>', None]
        if message_encoding is not None:
            subject = subject.decode('utf-8')

        sender, message_encoding = decode_header(mail['From'])[0]
        if message_encoding is not None:
            sender = sender.decode('utf-8')

        content = [subject, sender]
        return content

    def search_in_mails(self, keyword: str, seached_range: int = 0) -> list:
        """Search"""
        result = []
        mails_ids = self._get_mails_ids_from_server()[-seached_range:]
        for mail_id in mails_ids:
            mail = self.get_message(mail_id)
            in_content = False
            for part in mail.walk():
                if part.get_content_type() == 'text/plain':
                    if search(keyword, part.get_payload()) is not None:
                        in_content = True
                        break
            search_result = any([
                search(keyword, mail['Subject'] if mail['Subject'] is not None else ""),
                search(keyword, mail['From'] if mail['From'] is not None else ""),
                in_content
            ])

            if search_result:
                result.append(mail_id)
            else:
                continue

        return result
