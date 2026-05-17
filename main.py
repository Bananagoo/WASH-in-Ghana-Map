import asyncio
import sys
import os

# Ensure imports resolve relative to this file's directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from src.game import Game


async def main():
    # Pre-init mixer before pygame.init() — larger buffer prevents WASM audio underruns/static
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=4096)
    pygame.init()
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
