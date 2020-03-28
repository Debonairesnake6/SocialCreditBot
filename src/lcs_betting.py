"""
Handle all of the LCS betting logic for the Social Credit Bot
"""

import bs4
import sys
import os
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


class LCSBetting:
    """
    Handle all of the LCS betting logic
    """

    def __init__(self, league):
        self.driver = None
        self.soup = None
        self.matchups = None
        self.first_game = False
        self.team1 = []
        self.team2 = []

        # ToDo Headless switch
        headless = False
        options = webdriver.FirefoxOptions()
        binary = FirefoxBinary(r"D:\Documents\Python Projects\SocialCreditBot\driver\geckodriver.exe")
        if headless is True:
            os.environ['MOZ_HEADLESS'] = '1'
            options.add_argument('headless')

        # Load the web page
        with webdriver.Firefox(options=options) as self.driver:
            self.driver.get(f'https://watch.lolesports.com/schedule?leagues={league}')

            # Create a beautiful soup object
            self.create_soup()

            # grab the upcoming matches
            self.get_next_matches()

            # Todo skip matches if games in "Earlier Today" or "Yesterday"

            print()

    def create_soup(self):
        """
        Create a beautiful soup object
        """

        # Wait until the schedule loads
        try:
            WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'teams')))
        except TimeoutException as e:
            print(e, file=sys.stderr)

        # Create a beautiful soup object from the driver
        self.soup = bs4.BeautifulSoup(self.driver.page_source, 'html.parser')

    def get_next_matches(self):
        """
        Get the weekend upcoming matchups
        """

        # Grab all of the upcoming matchups on the page
        self.matchups = self.soup.find_all('div', {'class': 'versus'})

        # Only grab the next 10 matchups
        for match in self.matchups[:10]:
            self.get_team_abreveations(match)

    def get_team_abreveations(self, match):
        """
        Grab each team's abreveations
        """

        # Verify the next matchup is the first game of the week
        if match == self.matchups[0]:
            date = match.parent.parent.parent.previous_sibling.contents

            # Skip if the game is currently being played
            if match.parent.parent.attrs['class'] == ['single', 'link', 'live', 'event', 'lcs']:
                return

            elif len(date) == 0 or date[0].text.split('-')[0] != 'Saturday':
                self.first_game = False
        self.first_game = True

        # Grab the team abreveations
        self.team1.append(match.previous_sibling.contents[1].contents[0].contents[1].text)
        self.team2.append(match.next_sibling.contents[1].contents[0].contents[1].text)


if __name__ == '__main__':
    # Todo
    #   -   add date and time for each match in message
    lcs_betting = LCSBetting('lcs')
    print()
