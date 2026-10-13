# pixal3d-to-game

How I get a model from one picture into my game with [Pixal3D](https://github.com/TencentARC/Pixal3D), an open-source model that turns one picture into a textured 3D model.

The example is the Statue of Liberty in my game Salt Blade. It started as one public-domain photo. Pixal3D made a model with 972,738 triangles in about 5 minutes on a laptop with an RTX 5080. My agent's script cut it to 13,623 triangles for the game, and the script here is a cleaned-up version of it.

## What you need

- An NVIDIA GPU. I run it on an RTX 4090 and on an RTX 5080 laptop with 16 GB.
- About 46 GB of disk space for the downloads.

## Three ways to run Pixal3D

### 1. The Python script

This is the official way. It runs on Linux. On Windows I use WSL, which is Linux inside Windows.

1. Follow the install steps in the [Pixal3D README](https://github.com/TencentARC/Pixal3D#-getting-started).
2. Make a model:

```bash
python inference.py --image statue.png --output statue.glb --low_vram
```

`--low_vram` loads each part of the model only when it's needed. On my 4090 a run peaks at about 11 GB of GPU memory.

### 2. ComfyUI

Pixal3D has been built into ComfyUI since August 2026 ([pull request 14718](https://github.com/Comfy-Org/ComfyUI/pull/14718)), so you don't need a custom node.

1. Update ComfyUI.
2. Download the model files from [Comfy-Org/Pixal3D](https://huggingface.co/Comfy-Org/Pixal3D) into `models/diffusion_models`, `models/clip_vision` and `models/vae`. They come to about 36 GB.
3. Load the example workflow from the same page, `pixal3d_test_jester.json`, and swap in your picture.

I use the Python script, so I haven't run this one myself.

### 3. A coding agent like Claude

Paste [claude-prompt.md](claude-prompt.md) into Claude Code and change the first line to your picture. It asks the agent to install Pixal3D if it's missing, run it, check the model from four sides, make the game version with the script below, and put it in your game.

## From the Pixal3D model to a game model

A Pixal3D model has about a million triangles and a 4K texture, which is too much for one prop in most games.

```bash
pip install trimesh numpy scipy pillow
python glb_to_game_model.py statue.glb statue-game.glb --triangles 14000 --views views.jpg
```

The script:

1. Copies the texture's colour onto every corner point, so the game needs no texture file.
2. Draws the model from four sides into `views.jpg`, so you can check it before you use it. ([example](example/views.jpg))
3. Merges nearby points until the model is under the triangle count you asked for.
4. Turns every face to point outward.

On the statue it prints:

```
source: 972,738 triangles, 714,698 points
game model: 13,994 triangles, 4,484 points, 3,489 faces turned outward
```

The merge is a simple grid, so the result looks blocky up close. It suits a prop the camera stays away from. For a close-up model, use Blender's Decimate modifier and keep the texture.

## What to check

Pixal3D sees one side of the object, so it guesses the back. These are the problems I've had:

- The model can lean. My statue leaned back about 15 degrees and needed standing upright.
- Thin parts come out soft or fused. My agent rebuilt the statue's crown rays in code.
- The first size in the game is usually wrong. Take screenshots and look at them, or have a second agent review them.

## The input picture

One object, alone and centred, on a plain dark background. Cut it out of its background first.
