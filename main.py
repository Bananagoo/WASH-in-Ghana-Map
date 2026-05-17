import asyncio
import sys
import os

# Ensure imports resolve relative to this file's directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from src.game import Game


async def main():
    pygame.init()
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
