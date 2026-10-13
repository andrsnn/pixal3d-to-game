Make a 3D model of `statue.png` for my game with Pixal3D.

1. If Pixal3D isn't installed, install it from https://github.com/TencentARC/Pixal3D on Linux or WSL and download the weights. It needs an NVIDIA GPU and about 46 GB of disk space. Tell me before you start the download.
2. Clean the picture first: the object alone, centred, on a plain dark background.
3. Run `python inference.py --image <picture> --output model.glb --low_vram`. Run one job at a time on the GPU.
4. Run `python glb_to_game_model.py model.glb game.glb --triangles 120000 --views views.jpg` from https://github.com/andrsnn/pixal3d-to-game. Go lower only if a close screenshot still shows the small details.
5. Look at `views.jpg` and show it to me. Tell me if the model leans, if thin parts are missing, or if the back looks wrong.
6. Put `game.glb` in the game at the right size and facing the way the player arrives.
7. Take screenshots of it in the game, one of them close up, and tell me what looks wrong before you call it done.
