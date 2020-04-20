"""
This is the brain of the bot which parses input and manages the discord server
"""

import os
import json
import urllib
import time
import sys
import lcs_stock_market

from discord import File
from discord import Activity
from discord import ActivityType
from discord.errors import HTTPException
from discord.ext import commands
from dotenv import load_dotenv
from text_to_image import CreateImage

# Load environment variables
load_dotenv()


class DiscordBot:
    """
    Social Credit Discord bot
    """

    def __init__(self):
        """
        Social Credit Discord bot
        """
        self.credits = {}
        self.user = None
        self.display_name = None
        self.message = None
        self.stock_market_bot_commands = None
        self.post_credits = False
        self.bot = commands.Bot(command_prefix='!')

        # Grab the initial values
        self.setup()

        # Start listening to chat
        self.start_bot()

    def setup(self):
        """
        Setup the bot with the stored values
        """

        # If the credit_data.json file does not exist, create it
        if not os.path.isfile('../extra_files/credit_data.json'):
            with open('../extra_files/credit_data.json', 'w', encoding='utf-8') as credit_data_file:
                credit_data_file.write('{\n}')

        # If the file does exist, read it and save it's values
        else:
            try:
                with open('../extra_files/credit_data.json', 'r', encoding='utf-8') as credit_data_file:
                    self.credits = json.load(credit_data_file)

            # If the file is empty, create it an as empty dictionary
            except json.decoder.JSONDecodeError:
                with open('../extra_files/credit_data.json', 'w', encoding='utf-8') as credit_data_file:
                    credit_data_file.write('{\n}')

    def save_credits(self):
        """
        Save the current credits to the credit_data.json file
        """

        # Save the credits to the credit_data.json file
        with open('../extra_files/credit_data.json', 'w', encoding='utf-8') as credit_data_file:
            json.dump(self.credits, credit_data_file, indent=4)

    async def add_credits(self, amount: str):
        """
        Add credits to the given user's account

        :param amount: Amount of credits to add
        """
        amount = int(amount)

        # Add if the value is positive
        if amount >= 0:

            # Processes for the author of the message if no mentions were included
            if len(self.message.mentions) == 0 and len(self.message.role_mentions) == 0:
                self.credits[self.user]['credits'] += amount
                self.save_credits()
                self.post_credits = True

            # Do the action for everyone mentioned
            else:

                # Process each mention
                for member in self.message.mentions:
                    self.credits[member.name]['credits'] += amount
                    self.save_credits()
                    self.post_credits = False
                    await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                    f'{self.credits[member.name]["credits"]} social credits')

                # Process each role mention
                for role in self.message.role_mentions:
                    for member in role.members:
                        self.credits[member.name]['credits'] += amount
                        self.save_credits()
                        self.post_credits = False
                        await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                        f'{self.credits[member.name]["credits"]} social credits')

        # Don't add if negative
        else:
            self.post_credits = False
            await self.message.channel.send(f'Only user positive numbers, cheater.')

    async def remove_credits(self, amount: str):
        """
        Remove credits from the given user's account

        :param amount: Amount of credits to remove
        """
        amount = int(amount)

        # Add if the value is positive
        if amount >= 0:

            # Processes for the author of the message if no mentions were included
            if len(self.message.mentions) == 0 and len(self.message.role_mentions) == 0:
                self.credits[self.user]['credits'] -= amount
                self.save_credits()
                self.post_credits = True

            # Do the action for everyone mentioned
            else:

                # Process each mention
                for member in self.message.mentions:
                    self.credits[member.name]['credits'] -= amount
                    self.save_credits()
                    self.post_credits = False
                    await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                    f'{self.credits[member.name]["credits"]} social credits')

                # Process each role mention
                for role in self.message.role_mentions:
                    for member in role.members:
                        self.credits[member.name]['credits'] -= amount
                        self.save_credits()
                        self.post_credits = False
                        await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                        f'{self.credits[member.name]["credits"]} social credits')

        # Don't add if negative
        else:
            self.post_credits = False
            await self.message.channel.send(f'Only user positive numbers, cheater.')

    async def set_credits(self, amount: int):
        """
        Set the user's credits

        :param amount: Amount of credits to set
        """
        amount = int(amount)

        # Processes for the author of the message if no mentions were included
        if len(self.message.mentions) == 0 and len(self.message.role_mentions) == 0:
            self.credits[self.user]['credits'] = amount
            self.save_credits()
            self.post_credits = True

        # Do the action for everyone mentioned
        else:

            # Process each mention
            for member in self.message.mentions:
                self.credits[member.name]['credits'] = amount
                self.save_credits()
                self.post_credits = False
                await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                f'{self.credits[member.name]["credits"]} social credits')

            # Process each role mention
            for role in self.message.role_mentions:
                for member in role.members:
                    self.credits[member.name]['credits'] = amount
                    self.save_credits()
                    self.post_credits = False
                    await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                    f'{self.credits[member.name]["credits"]} social credits')

    async def post_user_credits(self):
        """
        Post the user's credits to discord
        """

        # Display the users current credits
        try:
            await self.message.channel.send(f'{self.display_name} now has '
                                            f'{self.credits[self.user]["credits"]} social credits.')

        # If the user has over the max discord character limit
        except HTTPException:

            # If they have positive credits
            if self.credits[self.user]['credits'] > 0:
                await self.message.channel.send(f'{self.display_name} is a social credit.')

            # If they have negative credits
            elif self.credits[self.user]['credits'] < 0:
                await self.message.channel.send(f'{self.display_name} couldn\'t dream of being worth enough to '
                                                f'obtain a single social credit.')

    async def leader_board(self):
        """
        Post the leader board to discord
        """

        try:
            # Get the user's scores in order
            score_order = sorted([self.credits[user]['credits'] for user in self.credits], reverse=True)

            # Create a array for each row
            rows = []
            for amount in score_order:
                for name in self.credits:
                    if amount == self.credits[name]['credits'] \
                            and self.credits[name]['display name'] not in [user[0] for user in rows]:
                        rows.append([self.credits[name]['display name'], amount])
                        break

            # Set the value to a message if it is too big/small
            for user_cnt, user in enumerate(rows):
                if user[1] > 1000000000000000:
                    rows[user_cnt][1] = 'Literally a social credit'
                elif user[1] < -1000000000000000:
                    rows[user_cnt][1] = 'Is mot worth your time reading their name'

            # Create the image and send it to discord
            CreateImage(['Citizen', 'Social Credits'], rows, '../extra_files/credit_leader_board.png')
            await self.message.channel.send(file=File('../extra_files/credit_leader_board.png',
                                                      filename='credit_leader_board.png'))
            os.remove('../extra_files/credit_leader_board.png')
        except ValueError:
            await self.message.channel.send(f'Leader board too big to display')

    def get_all_member_credit_information(self):
        """
        Add all of the members of the server to the credits list if they do not already exist
        """

        # Loop through each member
        for member in self.message.guild.members:
            if member.name not in self.credits:

                # Extract all of the information needed
                self.credits[member.name] = {'credits': 0,
                                             'id': member.id,
                                             'mention': member.mention,
                                             'display name': member.display_name}

            # Updated display names
            else:
                self.credits[member.name]['display name'] = member.display_name

        # Save the dictionary
        self.save_credits()

    async def help_message(self):
        """
        Display the help message for the bot
        """
        await self.message.channel.send('Social Credit commands:```'
                                        'Whenever I have multiple commands like ussr/USSR that means any of the listed '
                                        'ones work. Anything in square brackets [] is optional, curly braces {} are '
                                        'required but have an obvious substitute for the word. All commands start '
                                        'with !'
                                        ''
                                        '\n\n!ussr/USSR'
                                        '\n\t-\tBasic commands to use the bot. This will display your current balance.'
                                        '\n\t-\tAll of the following commands work with all of these options, but I '
                                        'will just show using USSR as it is redundant to list all of them.'
                                        ''
                                        '\n\n!USSR add {amount} [@Citizen]'
                                        '\n\t-\tAdd social credits to your account. Replace {amount} with the value you'
                                        ' want to add.'
                                        '\n\t-\tIf you ping a user or group at the end of the message it will '
                                        'add credits to their account instead.'
                                        '\n\t-\te.g. !USSR add 12345'
                                        '\n\t-\te.g. !USSR add 54321 @Debonairesnake6'
                                        '\n\t-\te.g. !USSR add 123 @TheSquad'
                                        ''
                                        '\n\n!USSR remove {amount} [@Citizen]'
                                        '\n\t-\tRemove social credits from your account. Replace {amount} with the '
                                        'value you want to remove.'
                                        '\n\t-\tIf you ping a user or group at the end of the '
                                        'message it will remove credits from their account instead.'
                                        '\n\t-\te.g. !USSR remove 12345'
                                        '\n\t-\te.g. !USSR remove 54321 @Debonairesnake6'
                                        '\n\t-\te.g. !USSR remove 123 @TheSquad'
                                        ''
                                        '\n\n!USSR set {amount} [@Citizen]'
                                        '\n\t-\tSet the amount of social credits in your account. Replace {amount} '
                                        'with the value you want to set it to.'
                                        '\n\t-\tIf you ping a user or group at the end '
                                        'of the message it will set their credits to that amount instead.'
                                        '\n\t-\te.g. !USSR set 12345'
                                        '\n\t-\te.g. !USSR set 54321 @Debonairesnake6'
                                        '\n\t-\te.g. !USSR set 123 @TheSquad'
                                        ''
                                        '\n\n!USSR leaderboard'
                                        '\n\t-\tDisplay the leaderboard for each citizen\'s bank account.'
                                        '\n\t-\te.g. !USSR leaderboard'
                                        ''
                                        '\n\n!USSR help'
                                        '\n\t-\tShow this help message.```')

    async def unknown_command(self):
        """
        Tell the user the given command is unknown
        """
        await self.message.channel.send(f'Unknown command: {self.message.content.split()[1]}. Use the following command'
                                        f' for help.\n!ussr help')

    async def handle_ussr_message(self):
        """
        Process the incoming USSR discord message
        """
        # Check if any arguments were given
        valid = ['!USSR', '!ussr']
        if self.message.content not in valid:

            # Process the command based on the arguments
            command = self.message.content.split(' ')[1]
            command_list = {
                'add': self.add_credits,
                'remove': self.remove_credits,
                'set': self.set_credits,
                'leaderboard': self.leader_board,
                'help': self.help_message
            }
            if len(self.message.content.split(' ')) == 2:
                await command_list.get(command, self.unknown_command)()
            else:
                # noinspection PyArgumentList
                await command_list.get(command, self.unknown_command)(self.message.content.split(' ')[2])

            # Toggle if the user's credits should be posted
            if self.post_credits is True:
                await self.post_user_credits()

        # If no arguments were given
        else:
            await self.post_user_credits()

    async def handle_stock_market_message(self):
        """
        Handle the incoming stock marker message
        """
        self.stock_market_bot_commands = lcs_stock_market.StockMarketBotCommands(self)
        self.stock_market_bot_commands.setup()
        self.stock_market_bot_commands.parse_discord_message()

        # Post any given status messages
        if self.stock_market_bot_commands.status_message:
            await self.message.channel.send(self.stock_market_bot_commands.status_message)

        # Post and remove any created images
        images = ['stock_market_line_graph.png', 'stock_market_leaderboard.png', 'stock_market_player_status.png',
                  'stock_market_table.png']
        for image_file in images:
            image_file = f'../extra_files/{image_file}'
            if os.path.isfile(image_file):
                await self.message.channel.send(self.stock_market_bot_commands.image_description,
                                                file=File(image_file, filename=image_file))
                os.remove(image_file)

        # Post if any teams were not found
        not_found = ''
        for team in self.stock_market_bot_commands.stock_market.not_found_teams:
            not_found += f'{team}, '
        if not_found != '':
            await self.message.channel.send(f'Could not find the teams: {not_found[:-2]}')

    async def handle_happy_birthday_message(self):
        """
        Handle the incoming happy birthday message
        """

        birthday_message = 'Happy Birthday'
        for letter in birthday_message:
            await self.message.channel.send(f'{letter} {self.message.content.split()[1]}')
            time.sleep(1)

    @staticmethod
    async def message_user(user: object, message: str):
        """
        Send a private message to the user. For the message variable you can use message.author.send()

        :param user: User to send the message to
        :param message: Message contents to send to the user
        """
        await user.send(message)

    def start_bot(self):
        """
        Start the bot
        """
        valid_commands = {
            'USSR': self.handle_ussr_message,
            'ussr': self.handle_ussr_message,
            'stock': self.handle_stock_market_message,
            'stocks': self.handle_stock_market_message,
            'stonk': self.handle_stock_market_message,
            'stonks': self.handle_stock_market_message,
            'birthday': self.handle_happy_birthday_message
        }

        @self.bot.event
        async def on_message(message: object):
            """
            Receive any message

            :param message: Context of the message
            """
            if message.content != '' \
                    and message.content.split()[0][1:] in valid_commands \
                    and message.content[0] == '!':
                self.user = message.author.name
                self.display_name = message.author.display_name
                self.message = message
                self.get_all_member_credit_information()
                await valid_commands[message.content.split()[0][1:]]()

        @self.bot.event
        async def on_ready():
            """
            Set the bot status on discord
            """
            if os.name == 'nt':
                print('Ready')

            await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name='!ussr help | '
                                                                                             '!stocks help'))

        # Run the bot
        self.bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':

    while True:

        # Wait until retrying if the service is down
        try:

            # ToDo list:
            #   -   class roles based on credits
            #   -   insult based on class
            #   -   periodically insult members of the lowest rank
            #   -   gain/lose permissions based on rank
            #   -   delete messages from a user from x minutes ago
            #   -   remove permissions for period of time
            #   -   Announce birthdays/other events/holidays
            #   -   Users forced to distribute wealth to new citizens
            #   -   tax system
            #   -   Leader board colouring
            #   -   Gain credits over time
            #   -   Bank
            #   -   LCS betting
            #   -   Buy abilities to mute others

            DiscordBot()
            break

        # Catch if service is down
        except urllib.error.HTTPError as e:
            error_msg = "Service Temporarily Down"
            print(error_msg)
            print(e)
            # post_message(error_msg)
            time.sleep(60)

        # Catch random OS error
        except OSError as e:
            print(e, file=sys.stderr)
            time.sleep(60)
