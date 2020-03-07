import os
import json
import requests
import urllib
import time
import sys
import prettytable
import lcs_stock_market

from discord import File
from discord import User
from discord.errors import HTTPException
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from text_to_image import CreateImage

# Load environment variables
load_dotenv()


class DiscordBot:
    """
    Social Credit Discord bot
    """

    def __init__(self):

        # Placeholder variables
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
        if not os.path.isfile('credit_data.json'):
            with open('credit_data.json', 'w', encoding='utf-8') as credit_data_file:
                credit_data_file.write('{\n}')

        # If the file does exist, read it and save it's values
        else:
            try:
                with open('credit_data.json', 'r', encoding='utf-8') as credit_data_file:
                    self.credits = json.load(credit_data_file)

            # If the file is empty, create it an as empty dictionary
            except json.decoder.JSONDecodeError:
                with open('credit_data.json', 'w', encoding='utf-8') as credit_data_file:
                    credit_data_file.write('{\n}')

    def save_credits(self):
        """
        Save the current credits to the credit_data.json file
        """

        # Save the credits to the credit_data.json file
        with open('credit_data.json', 'w', encoding='utf-8') as credit_data_file:
            credit_data_file.write(str(self.credits).replace('{\'', '{\n\t\'').replace(': {\n\t', ': {\n\t\t')
                                   .replace('}, ', '},\n\t').replace(', ', ',\n\t\t').replace('}}', '}\n}')
                                   .replace('"', '\\"').replace('\'', '"'))

    async def add_credits(self, amount):
        """
        Add credits to the given user's account
        :param amount: Amount of credits to add
        """

        # Add if the value is positive
        if amount >= 0:

            # Processes for the author of the message if no mentions were included
            if len(self.message.message.mentions) == 0 and len(self.message.message.role_mentions) == 0:
                self.credits[self.user]['credits'] += amount
                self.save_credits()
                self.post_credits = True

            # Do the action for everyone mentioned
            else:

                # Process each mention
                for member in self.message.message.mentions:
                    self.credits[member.name]['credits'] += amount
                    self.save_credits()
                    self.post_credits = False
                    await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                    f'{self.credits[member.name]["credits"]} social credits')

                # Process each role mention
                for role in self.message.message.role_mentions:
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

    async def remove_credits(self, amount):
        """
        Remove credits from the given user's account
        :param amount: Amount of credits to remove
        """

        # Add if the value is positive
        if amount >= 0:

            # Processes for the author of the message if no mentions were included
            if len(self.message.message.mentions) == 0 and len(self.message.message.role_mentions) == 0:
                self.credits[self.user]['credits'] -= amount
                self.save_credits()
                self.post_credits = True

            # Do the action for everyone mentioned
            else:

                # Process each mention
                for member in self.message.message.mentions:
                    self.credits[member.name]['credits'] -= amount
                    self.save_credits()
                    self.post_credits = False
                    await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                    f'{self.credits[member.name]["credits"]} social credits')

                # Process each role mention
                for role in self.message.message.role_mentions:
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

    async def set_credits(self, amount):
        """
        Set the user's credits
        :param amount: Amount of credits to set
        """

        # Processes for the author of the message if no mentions were included
        if len(self.message.message.mentions) == 0 and len(self.message.message.role_mentions) == 0:
            self.credits[self.user]['credits'] = amount
            self.save_credits()
            self.post_credits = True

        # Do the action for everyone mentioned
        else:

            # Process each mention
            for member in self.message.message.mentions:
                self.credits[member.name]['credits'] = amount
                self.save_credits()
                self.post_credits = False
                await self.message.channel.send(f'{self.credits[member.name]["display name"]} now has '
                                                f'{self.credits[member.name]["credits"]} social credits')

            # Process each role mention
            for role in self.message.message.role_mentions:
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
        CreateImage(['Citizen', 'Social Credits'], rows, 'credit_leader_board.png')
        await self.message.channel.send(file=File('credit_leader_board.png', filename='credit_leader_board.png'))

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

    async def handle_ussr_message(self):
        """
        Process the incoming USSR discord message
        """

        # Check if any arguments were given
        valid = ['!USSR', '!ussr']
        if self.message.content not in valid:

            # Process the command based on the arguments
            command = self.message.content.split(' ')[1]

            # Add credits for the user and post them to discord
            if command == 'add':
                try:
                    await self.add_credits(int(self.message.content.split(' ')[2]))
                except (ValueError, TypeError):
                    await self.message.channel.send(f'{self.message.content.split(" ")[2]} '
                                                    f'is not a valid number to add.')

            # Remove credits from the user and post them to discord
            elif command == 'remove':
                try:
                    await self.remove_credits(int(self.message.content.split(' ')[2]))
                except (ValueError, TypeError):
                    await self.message.channel.send(f'{self.message.content.split(" ")[2]} '
                                                    f'is not a valid number to add.')

            # Set the credits for the user and post them to discord
            elif command == 'set':
                try:
                    await self.set_credits(int(self.message.content.split(' ')[2]))
                except ValueError:
                    await self.message.channel.send(f'{self.message.content.split(" ")[2]} '
                                                    f'is not a valid number to add.')

            # Display the credit leader board
            elif command == 'legend':
                try:
                    await self.leader_board()
                except ValueError:
                    await self.message.channel.send(f'Leader board too big to display')

            # Toggle if the user's credits should be posted
            if self.post_credits is True:
                await self.post_user_credits()

        # If no arguments were given
        else:

            # Post the user's credits to discord
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
        images = ['stock_market_line_graph.png', 'stock_market_leaderboard.png', 'stock_market_player_status.png']
        for image_file in images:
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

    @staticmethod
    async def message_user(user, message):
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
            'stonks': self.handle_stock_market_message
        }

        @self.bot.event
        async def on_message(message):
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

        # Run the bot
        if os.name == 'nt':
            print('Ready')
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
