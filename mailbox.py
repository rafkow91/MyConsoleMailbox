"""Main application"""
import click

from controllers import Application


@click.command()
@click.option('--searched-phrase', '-s', 'keyword',
              help='Phrase to search in mails', default=None)
@click.option('--range', '-r', 'search_range',
              help='Searched phrase in x last mails', default=0, type=int)
@click.option('--login', '-l', 'login',
              help='Mail where you want to seach', default=None)
def main(keyword, search_range, login):
    """Start main app"""
    app = Application()
    app.run(keyword, search_range, login)


if __name__ == "__main__":
    main()
