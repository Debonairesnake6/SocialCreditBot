"""
Interact with the stock market spreadsheet to play along with the LCS stock market game
"""

import os
import requests
import json
import sys
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from text_to_image import CreateImage

load_dotenv()


class StockMarket:
    """
    Stock Market Object
    """
    def __init__(self):
        """
        Create the stock market object
        """
        self.stock_market_values = None
        self.api_key = f'?key={os.getenv("SHEETS_API_KEY")}'
        self.api_base_url = 'https://sheets.googleapis.com'
        self.sheet_values_query = '/v4/spreadsheets/1y3rMtxTl8h-KtJJdI1x2Yy3TY02lGvdB4bBGteIh5Ao/values/Prices'
        self.not_found_teams = []

    def get_stock_market_information(self):
        """
        Setup the stock information
        """
        self.query_stock_information_sheet()
        self.format_stock_market_values()

    def query_stock_information_sheet(self):
        """
        Query the sheet to grab the information
        """
        sheet_info = requests.get(f'{self.api_base_url}{self.sheet_values_query}{self.api_key}').text
        self.stock_market_values = json.loads(sheet_info)['values'][1:]

    def format_stock_market_values(self):
        """
        Format the values from the sheet into a proper dictionary
        """
        stock_market_values_copy = self.stock_market_values[:]
        self.stock_market_values = {}
        for team_value_per_day in stock_market_values_copy:
            team = team_value_per_day[0]
            current = team_value_per_day[2]

            if team not in self.stock_market_values:
                self.stock_market_values[team] = [int(current)]
            elif int(current) != self.stock_market_values[team][-1]:
                self.stock_market_values[team].append(int(current))

    def create_stock_value_graph_for_league(self):
        """
        Create a stock value graph for the entire league
        """
        for team in self.stock_market_values:
            self.create_team_stock_value_graph(team)

    def create_team_stock_value_graph(self, team: str):
        """
        Create a line chart for the given team

        :param team: Team abbreviation
        """
        if self.verify_team_exists(team):
            self.plot_values_on_graph(team)
        else:
            self.not_found_teams.append(team)

    def verify_team_exists(self, team: str) -> bool:
        """
        Verify the given team exists before attempting to create a graph

        :param team: Team abbreviation to check
        :return: Boolean indicating if the team exists
        """
        if team in self.stock_market_values:
            return True
        else:
            return False

    def plot_values_on_graph(self, team: str):
        """
        Plot the stock values of the team on the graph

        :param team: Team abbreviation to plot on the graph
        """
        x = [day_cnt for day_cnt in range(len(self.stock_market_values[team]))]
        y = self.stock_market_values[team]
        plt.plot(x, y, label=team)

    def display_stock_market_graph(self, debug=False):
        """
        Add the legend to the graph and display it

        :param debug: If debug is on it will show the graph
        """
        plt.xticks([day_cnt for day_cnt in range(len(self.stock_market_values['TL']))])
        plt.title('LCS Stock Market Values')
        plt.xlabel('Game')
        plt.ylabel('Value')
        plt.legend(loc='upper left', ncol=2)
        plt.savefig('stock_market_line_graph.png')
        plt.clf()
        if debug:
            plt.show()


class StockMarketBotCommands:
    """
    Handle the discord commands for the stock market
    """
    # Todo
    #   -   Create table showing gains/losses in green/red
    #   -   Better status message
    def __init__(self, social_credit_bot: object):
        self.social_credit_bot = social_credit_bot
        self.message = social_credit_bot.message
        self.credits = social_credit_bot.credits
        self.stock_market = StockMarket()
        self.command = None
        self.user_stock_market_credits = None
        self.team = None
        self.amount = None
        self.status_message = False
        self.total_worth = None
        self.team_stocks = None
        self.command_options = {
            'teams': self.process_individual_team_graphs,
            'team': self.process_individual_team_graphs,
            'league': self.process_league_graph,
            'lcs': self.process_league_graph,
            'buy': self.buy_or_sell_stock,
            'purchase': self.buy_or_sell_stock,
            'sell': self.buy_or_sell_stock,
            'status': self.player_status,
            'help': self.help_message,
            'leaderboard': self.leader_board
        }

    def setup(self):
        """
        Setup the stock market object to run the given commands on
        """
        self.stock_market.get_stock_market_information()
        if 'stock_market' not in self.credits[self.message.author.name]:
            self.credits[self.message.author.name]['stock_market'] = {'money': 5000}
            for team in self.stock_market.stock_market_values.keys():
                self.credits[self.message.author.name]['stock_market'][team] = 0
            self.social_credit_bot.save_credits()
        self.user_stock_market_credits = self.credits[self.message.author.name]['stock_market']

    def parse_discord_message(self):
        """
        Parse the discord message to determine what the user wants to do
        """
        if len(self.message.content.split()) > 1:
            self.command = self.message.content.split()[1]
            if self.command_options.get(self.command, False):
                self.command_options[self.command]()
            else:
                self.status_message = f'Unknown command: {self.command}'
        else:
            self.command = self.message.content
            self.process_league_graph()

    def process_individual_team_graphs(self):
        """
        Create graphs for every team in the message
        """
        for team in self.message.content.split()[1:]:
            self.stock_market.create_team_stock_value_graph(team.replace(',', '').strip().upper())
        self.stock_market.display_stock_market_graph()

    def process_league_graph(self):
        """
        Create a graph for the entire league
        """
        self.stock_market.create_stock_value_graph_for_league()
        self.stock_market.display_stock_market_graph()

    def buy_or_sell_stock(self):
        """
        Setup for the user to buy or sell stocks
        """
        try:
            self.team = self.message.content.split()[2].upper()
            self.amount = int(self.message.content.split()[3])
        except IndexError:
            self.status_message = 'Not enough commands, see !stocks help for guidance.'
        except ValueError:
            self.status_message = 'Invalid number of stocks, see !stocks help for guidance.'

        else:
            if self.team not in self.stock_market.stock_market_values.keys():
                self.stock_market.not_found_teams.append(self.team)
            elif self.message.content.split()[1] == 'buy' or self.message.content.split()[1] == 'purchase':
                self.buy_stocks()
            elif self.message.content.split()[1] == 'sell':
                self.sell_stocks()
        self.social_credit_bot.save_credits()

    def buy_stocks(self):
        """
        Have the user purchase stocks
        """
        stock_requested_value = self.stock_market.stock_market_values[self.team][-1] * self.amount
        if stock_requested_value < self.user_stock_market_credits['money']:
            self.user_stock_market_credits['money'] -= stock_requested_value
            self.user_stock_market_credits[self.team] += self.amount
            self.status_message = f'Successfully purchased {self.amount} stocks of {self.team} for ' \
                                  f'{stock_requested_value}.\nYou have {self.user_stock_market_credits["money"]} ' \
                                  f'remaining.'
        else:
            max_can_buy = int(self.user_stock_market_credits["money"] /
                              self.stock_market.stock_market_values[self.team][-1])
            left = self.user_stock_market_credits["money"] % self.stock_market.stock_market_values[self.team][-1]
            cost = self.user_stock_market_credits["money"] - left
            self.status_message = f'Not enough money to buy the requested stocks. \n' \
                                  f'{self.amount} {self.team} stocks are worth {stock_requested_value} but you only ' \
                                  f'have {self.user_stock_market_credits["money"]}.\n' \
                                  f'You can buy a maximum of {max_can_buy} {self.team} stock(s) for {cost} which ' \
                                  f'would leave you with {left}.'

    def sell_stocks(self):
        """
        Have the user sell stocks
        """
        if self.user_stock_market_credits[self.team] >= self.amount:
            sell_value = self.stock_market.stock_market_values[self.team][-1] * self.amount
            self.user_stock_market_credits['money'] += sell_value
            self.user_stock_market_credits[self.team] -= self.amount
            self.status_message = f'Successfully sold {self.amount} stocks of {self.team} for {sell_value}.\n' \
                                  f'You now have {self.user_stock_market_credits["money"]} remaining.'
        else:
            self.status_message = f'You do not have {self.amount} stocks to sell. You only have ' \
                                  f'{self.user_stock_market_credits[self.team]}.'

    def player_status(self):
        """
        Set the status message as the player's overall worth
        """
        self.get_player_worth(self.user_stock_market_credits)
        self.status_message = f'{self.social_credit_bot.user}\'s total worth is: {self.total_worth}{self.team_stocks}'

    def get_player_worth(self, player_stock_market: dict):
        """
        Get the player's overall worth

        :param player_stock_market: Stock market dictionary for a player
        """
        self.total_worth = player_stock_market['money']
        self.team_stocks = f'\nBank: {player_stock_market["money"]}'
        for team in player_stock_market:
            if team == 'money':
                continue
            team_worth = self.stock_market.stock_market_values[team][-1] * player_stock_market[team]
            if team_worth > 0:
                self.total_worth += team_worth
                self.team_stocks += f'\n\t{team}:\t{player_stock_market[team]} * ' \
                                    f'{self.stock_market.stock_market_values[team][-1]}'

    def help_message(self):
        """
        Display the help message for how to use the bot
        """
        self.status_message = '```Stocks commands:' \
                              'Whenever I have multiple commands like stocks/stock that means any of the listed ones ' \
                              'work. All commands start with !' \
                              '' \
                              '\n\n!stocks/stock/stonks/stonk' \
                              '\n\t-\tBasic commands to use the bot. The base command is the same as using the ' \
                              'league/lcs option.' \
                              '\n\t-\tAll of the following commands work with all of these options, but I will just ' \
                              'show using stocks as it is redundant to list all of them.' \
                              '' \
                              '\n\n!stocks team/teams [team 1 abbreviation] [team 2 abbreviation]' \
                              '\n\t-\tDisplay the line graph for the listed team or teams. Once again using team/' \
                              'teams does not matter, what matters is how many teams you list afterwards' \
                              '\n\t-\te.g. !stocks team tl c9 tsm' \
                              '\n\t-\te.g. !stocks team tl' \
                              '' \
                              '\n\n!stocks league/lcs' \
                              '\n\t-\tDisplay a line graph of the stock market values for every team over the season.' \
                              '' \
                              '\n\n!stocks buy/purchase [team abbreviation] [amount]' \
                              '\n\t-\tPurchase the specified amount of stocks for the requested team.' \
                              '\n\t-\te.g. !stocks buy tl 5' \
                              '' \
                              '\n\n!stocks sell [team abbreviation] [amount]' \
                              '\n\t-\tSell the specified amount of stocks for the requested team.' \
                              '\n\t-\te.g. !stocks sell tl 5' \
                              '' \
                              '\n\n!stocks status' \
                              '\n\t-\tShow your account value including all of your stocks```'

    def leader_board(self):
        """
        Display a leader board of the current users playing in the stock market
        """
        titles = ['Player', 'Worth']
        rows = self.get_every_players_worth()
        file_name = 'stock_market_leaderboard.png'
        CreateImage(titles, rows, file_name)

    def get_every_players_worth(self) -> list:
        """
        Return a dual array of each player's worth

        :return: Dual array [[name, worth], [name, worth]...]
        """
        all_rows = []
        for user in self.social_credit_bot.credits:
            if 'stock_market' in self.social_credit_bot.credits[user]:
                self.get_player_worth(self.social_credit_bot.credits[user]['stock_market'])
                all_rows.append([self.social_credit_bot.credits[user]['display name'].strip(), self.total_worth])
        return all_rows


if __name__ == '__main__':
    stock_market = StockMarket()
    stock_market.get_stock_market_information()
    stock_market.create_team_stock_value_graph('C9')
    stock_market.create_team_stock_value_graph('CLG')
    # stock_market.create_stock_value_graph_for_league()
    stock_market.display_stock_market_graph(debug=True)
    print()
