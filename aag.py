#!/usr/bin/env python
import logging
import json
import sys
import configargparse
import os

from enum import Enum
from PIL import Image
from pathlib import Path

parser = configargparse.get_argument_parser(description='ASCII Art Generator.',
                                            formatter_class=configargparse.ArgumentDefaultsRawHelpFormatter)

parser.add_argument('-l', '--log-level', type=str, required=False,
                    default='INFO', help='The application log level.')

parser.add_argument('-i', '--image-path', type=str, required=True, help='Path to target image.')
parser.add_argument('-p', '--output-path', type=str, required=False,
                    default='output', help='Path for output ascii image (DIRECTORY ONLY).')

parser.add_argument('-o', '--output-file-name', type=str, required=False,
                    default='ascii_image.txt', help='Path for output ascii image - .txt suffix recommended.')

cfg = parser.parse_known_args()[0]


logging.basicConfig(
    datefmt='%y-%m-%d %H:%M:%S',
    format='%(process)d - %(asctime)s - %(funcName)s - %(levelname)s: %(message)s',
    level=logging.getLevelName(cfg.log_level)
)

log = logging.getLogger()


class Chars(Enum):
    ASCII_CHARS = ["@", "#", "$", "%", "?", "*", "+", ";", ":", ",", "."]


class AsciiArtConverter:
    def __init__(self, path_to_image: str, target_width: int = 100):
        self._is_context_manager = False

        self.path_to_image = path_to_image
        self.image = None
        self.target_width = target_width

        self.load_image()

    def __str__(self):
        return self.__dict__

    def __enter__(self):
        self._is_context_manager = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.image:
                log.info(f'Closing image object(s).')
                self.image.close()

        except Exception as e:
            log.error(f'Closing image object failed:\n{e}', exc_info=True)

    def convert(self):
        log.info(f'Converting {cfg.image_path} to ASCII.')

        target_image = self.resize_image()
        greyscale_image = self.convert_to_greyscale(target_image)
        ascii_str = self.convert_pixel_to_ascii(greyscale_image)

        ascii_img = ''

        # Split the string based on width of the image
        for i in range(0, len(ascii_str), greyscale_image.width):
            ascii_img += ascii_str[i: i + greyscale_image.width] + "\n"

        return ascii_img

    @staticmethod
    def write_ascii_to_file(ascii_image: str, file_name: str = 'ascii_image.txt') -> None:
        try:
            log.info(f'New ASCII image available at {cfg.output_path}/{file_name}')

            with open(os.path.join(cfg.output_path, file_name), 'w') as f:
                f.write(ascii_image)

        except IOError as e:
            log.error(f'Unable to write file:\n{e}', exc_info=True)

    @staticmethod
    def convert_pixel_to_ascii(resized_greyscale_image: Image):

        try:
            pixels = resized_greyscale_image.getdata()
            ascii_str = ''

            for pixel in pixels:
                ascii_str += Chars.ASCII_CHARS.value[(pixel // 25)]

            log.debug(f'Pixels: {pixels}')
            log.debug(f'ASCII: {ascii_str}')

            return ascii_str

        except Exception as e:
            log.error(f'ASCII conversion failed:\n{e}', exc_info=True)

    @staticmethod
    def convert_to_greyscale(resized_image: Image):
        try:
            return resized_image.convert('L')

        except Exception as e:
            log.error(f'Greyscale conversion failed:\n{e}.', exc_info=True)

    def resize_image(self):
        try:
            current_image_width, current_image_height = self.image.size
            log.debug(f'OG width: {current_image_width} | OG height: {current_image_height}')

            target_height = self.target_width * int(current_image_height) / int(current_image_width)

            # decrease target height by 30% or image seems stretched
            target_height = target_height - (int(target_height * .3))

            log.debug(f'Target width: {self.target_width} | Target height: {int(target_height)}')

            return self.image.resize((self.target_width, int(target_height)))

        except Exception as e:
            log.error(f'Resize failed:\n{e}', exc_info=True)

    def load_image(self):
        try:
            log.info(f'Loading image {self.path_to_image}.')
            self.image = Image.open(self.path_to_image)

        except FileNotFoundError as e:
            log.error(f'Unable to open {self.path_to_image}.\n{e}', exc_info=True)
            sys.exit(1)


def create_output_directory():
    try:
        output_folder = '/'.join(cfg.output_path.split('/')[:-1]) if '.' in cfg.output_path else cfg.output_path

        if not os.path.exists(output_folder):
            log.debug(f'Output folder {output_folder} does not exist- creating it.')
            Path(output_folder).mkdir(parents=True, exist_ok=True)

    except Exception as e:
        log.error(f'Unable to create output folder:\n{e}', exc_info=True)


if __name__ == '__main__':
    log.debug(json.dumps(vars(cfg), indent=4))

    create_output_directory()

    with AsciiArtConverter(cfg.image_path, target_width=120) as aac:
        ascii_string = aac.convert()
        aac.write_ascii_to_file(ascii_string, cfg.output_file_name)
