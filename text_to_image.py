"""
This file will create an image from the input as a table
"""

import prettytable
from PIL import Image, ImageDraw, ImageFont


class CreateImage:
    """
    Create an image from the given input
    """
    def __init__(self, titles: list, rows: list, file_name: str):
        """
        Create an image from the given input

        :param titles: List of names to use for the titles of each column
        :param rows: List of rows to add to the table
        :param file_name: Name to save the file as
        """
        self.titles = titles
        self.rows = rows
        self.table = None
        self.table_to_image = None
        self.file_name = file_name

        # Setup and add rows to the table
        self.setup()
        self.add_rows()

        # Create the image from the table
        self.turn_into_image()
        self.save_image()

    def setup(self):
        """
        Create the table object and add the titles\
        """
        self.table = prettytable.PrettyTable()
        self.table.field_names = self.titles

    def add_rows(self):
        """
        Add each row to the table
        """
        for row in self.rows:
            self.table.add_row(row)

    def turn_into_image(self):
        """
        Turn the table into an image
        """
        self.table_to_image = TableToImage(self.table.get_string())

    def save_image(self):
        """
        Save the image as the given file name
        """
        self.table_to_image.img.save(self.file_name)


class TableToImage:
    """
    Create an image from the text table given to it
    """

    def __init__(self, table):
        self.img = None
        self.font = None
        self.draw = None
        self.table = table

        self.setup_image()

    def setup_image(self):
        """
        Basic setup for the image to set the size, font, background colour, and all of the text in black
        """
        # Create the correct size image for the table
        rows = self.table.count('\n')
        columns = self.table.split('\n')[0].count('-') + self.table.split('\n')[0].count('+')
        self.img = Image.new('RGB', ((columns * 12), rows * 21 + 21), color=(54, 57, 63))

        # Initialize font and drawing object
        self.font = ImageFont.truetype('cour.ttf', 20)
        self.draw = ImageDraw.Draw(self.img)

        # Draw the table without markings
        self.draw.text((0, 0), self.table, font=self.font, fill=(255, 255, 255))
