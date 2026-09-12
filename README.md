# Nova Flip — ElbowOS

Original full-colour **Python 3 + pygame** neon pinball. Not a clone of prior ElbowOS tide-hopper / light-cycle / grapple reels.

Featured account: [x.com/ElbowOS](https://x.com/ElbowOS)

## Play

```bash
pip install -r requirements.txt
python3 nova_flip.py --play
```

Controls: **Z / Left** left flipper, **X / Right / /** right flipper, **R** restart, **Esc** quit.

## Record a 9:16 reel

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 nova_flip.py
```

Writes a 15s 1080×1920 H.264 MP4 (30 fps).

## Reel

Google Drive (view): https://drive.google.com/file/d/1mY2Ca7pUE14BZuhi3byT2EnBP8nCaCcB/view?usp=drivesdk

## License

MIT
