from email import message
from getpass import getpass
import imaplib
from json import load, dump
from email.header import decode_header
from email import message_from_bytes
from getpass import getpass
from yaml import safe_load, safe_dump
from tabulate import tabulate


class Application:
    def __init__(self, config_file: str = 'config.yml') -> None:
        self.config_file = config_file
        self.mail_list = self._get_mails_list_from_yml()

    def _get_mails_list_from_yml(self):
        while True:
            try:
                with open(self.config_file, 'r') as config_file:
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

                with open(self.config_file, 'w') as config_file:
                    safe_dump(config, config_file)
                continue
        return mail_list

    def run(self):
        for email in self.mail_list['mails']:
            mailbox = Mailbox(email['login'], email['password'], email['imap_server'])
            mailbox.connect_to_mail()
            mailbox.select_folder()
            new_mails = mailbox.check_new_mails()
            mails = []

            for mail in new_mails:
                mails.append(mailbox.get_header(mail))

            if len(mails) != 0:
                print(f'\t\t{mailbox.login}\n{tabulate(mails, headers=["Title", "From"], tablefmt="github")}\n')
            else:
                print(f'On mailbox {mailbox.login} don\'t have new mails')


class Mailbox:
    def __init__(self, login: str = None, password: str = None, imap_server: str = None) -> None:
        self.login = login if login != None else input('imap_server: ')
        self.password = password if password != None else input('login: ')
        self.imap_server = imap_server if imap_server != None else getpass('password: ')
        self.mails_ids = []
        self.json_file = 'mails_ids.json'

    def connect_to_mail(self):
        self.imap_server = imaplib.IMAP4_SSL(host=self.imap_server)
        self.imap_server.login(self.login, self.password)

    def select_folder(self, folder: str = 'Inbox'):
        self.imap_server.select(folder)

    def check_new_mails(self):
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
            with open(self.json_file, 'r') as input_file:
                content = load(input_file)
        except:
            content = {}
        try:
            return content[self.login]
        except KeyError:
            return []

    def _save_mails_id_to_json(self) -> None:
        try:
            with open(self.json_file, 'r') as input_file:
                content = load(input_file)
        except:
            content = {}
        try:
            content[self.login] = self._get_mails_ids_from_server()
        except KeyError:
            pass
        with open(self.json_file, 'w') as output_file:
            dump(content, output_file)

    def get_message(self, mail_id) -> message.Message:
        msg = self.imap_server.fetch(str(mail_id).encode('utf-8'), '(RFC822)')[1][0][1]
        message = message_from_bytes(msg)
        return message

    def get_header(self, mail_id):
        message = self.get_message(mail_id)

        if message is not None:
            try:
                subject, message_encoding = decode_header(message['Subject'])[0]
            except TypeError:
                subject, message_encoding = ['<without title>', None]
            if message_encoding is not None:
                subject = subject.decode('utf-8')

            reciver, message_encoding = decode_header(message['From'])[0]
            if message_encoding is not None:
                reciver = reciver.decode('utf-8')

            content = [subject, reciver]
            return content

    def search_in_mails():
        pass
