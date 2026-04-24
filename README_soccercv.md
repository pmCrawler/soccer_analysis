# Soccer CV — Tactical Video Analysis System

> A computer vision pipeline that turns raw soccer footage into tactical intelligence: player tracking, team identification, formation analysis, possession statistics, ball tracking, and AI-powered match reports — running entirely on a consumer laptop.

***

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Concepts Explained](#2-core-concepts-explained)
   * 2.1 [What is Computer Vision?](#21-what-is-computer-vision)
   * 2.2 [How Video is Represented](#22-how-video-is-represented)
   * 2.3 [Object Detection — YOLO](#23-object-detection--yolo)
   * 2.4 [Homography — Mapping Pixels to the Pitch](#24-homography--mapping-pixels-to-the-pitch)
   * 2.5 [K-Means Clustering — Team Identification](#25-k-means-clustering--team-identification)
   * 2.6 [The Kalman Filter — Ball Tracking Through Occlusion](#26-the-kalman-filter--ball-tracking-through-occlusion)
   * 2.7 [OpenVINO — CPU-Optimised Inference](#27-openvino--cpu-optimised-inference)
   * 2.8 [Tactical Soccer Concepts](#28-tactical-soccer-concepts)
3. [System Architecture](#3-system-architecture)
4. [Repository Structure](#4-repository-structure)
5. [Setup & Installation](#5-setup--installation)
   * 5.1 [Prerequisites by Platform](#51-prerequisites-by-platform)
   * 5.2 [Linux (Ubuntu / Mint)](#52-linux-ubuntu--mint)
   * 5.3 [macOS](#53-macos)
   * 5.4 [Windows](#54-windows)
   * 5.5 [Container Setup (Podman / Docker)](#55-container-setup-podman--docker)
   * 5.6 [API Keys](#56-api-keys)
6. [Ball Model Setup](#6-ball-model-setup)
   * 6.1 [Why a Dedicated Ball Model?](#61-why-a-dedicated-ball-model)
   * 6.2 [Download via Roboflow API Key (recommended)](#62-download-via-roboflow-api-key-recommended)
   * 6.3 [Download via Inference SDK (no account)](#63-download-via-inference-sdk-no-account)
   * 6.4 [Train Locally from Dataset](#64-train-locally-from-dataset)
   * 6.5 [How Ball Tracking Works](#65-how-ball-tracking-works)
7. [Configuration](#7-configuration)
8. [CLI Reference](#8-cli-reference)
   * 8.1 [soccercv info](#81-soccercv-info)
   * 8.2 [soccercv preprocess](#82-soccercv-preprocess)
   * 8.3 [soccercv calibrate](#83-soccercv-calibrate)
   * 8.4 [soccercv analyze](#84-soccercv-analyze)
   * 8.5 [soccercv run](#85-soccercv-run)
   * 8.6 [soccercv report](#86-soccercv-report)
   * 8.7 [soccercv download-ball-model](#87-soccercv-download-ball-model)
9. [The Processing Pipeline — Step by Step](#9-the-processing-pipeline--step-by-step)
10. [Module Reference](#10-module-reference)
11. [Output Files Reference](#11-output-files-reference)
12. [Homography Calibration Guide](#12-homography-calibration-guide)
13. [Performance Tuning](#13-performance-tuning)
14. [AI-Powered Reports](#14-ai-powered-reports)
15. [Game Plan Compliance](#15-game-plan-compliance)
16. [Troubleshooting](#16-troubleshooting)
17. [Next Steps & Roadmap](#17-next-steps--roadmap)
18. [Commercial Deployment](#18-commercial-deployment)

***

## 1. Introduction

Soccer CV converts a video clip of a soccer match into structured tactical data. It was built to answer questions coaches and analysts care about:

* Which team had possession, and when?
* Were players implementing the intended formation?
* Was the team pressing high or sitting deep?
* How compact was the defensive shape?
* Where was the ball, and how reliably can we track it?
* Given the final score, what could the losing team have done differently?

The system is designed to run on a **consumer laptop without a GPU** (tested on AMD Ryzen 4500U), making it accessible to clubs and analysts who don't have access to commercial broadcast analysis hardware.

### What It Does

```
Raw match video
      ↓  FFmpeg (preprocess)
Optimised clip at 10fps / 1280×720
      ↓  YOLOv8n + OpenVINO (detect)
Player bounding boxes per frame
      ↓  KMeans on jersey colour (team_cluster)
Each player labelled TEAM_A / TEAM_B / REF
      ↓  BallTracker: Roboflow model + Kalman filter (ball_tracker)
Ball position: DETECTED / PREDICTED / LOST per frame
      ↓  Homography matrix (homography)
Player + ball positions in real-world pitch metres
      ↓  Tactical functions (tactics)
Possession, formation, compactness, pressing
      ↓  cv2 rendering (overlay + tactical_video)
Annotated video + top-down tactical video
      ↓  Claude API (ai_analysis)
AI-generated match report (HTML)
```

### What It Does Not Do (Yet)

* Track individual players with persistent IDs across frames (needs ByteTrack)
* Analyse events (shots, passes, tackles)
* Process full 90-minute matches at speed (5–10 minute clips are the practical unit)

***

## 2. Core Concepts Explained

This section explains every technical concept used in the system, assuming no prior knowledge of computer vision, machine learning, or video processing.

### 2.1 What is Computer Vision?

Computer vision is the field of programming computers to understand images and video — the same way humans can glance at a photo and immediately know what they're looking at.

When a human watches a soccer match they instantly recognise players, the ball, the pitch lines, which team is which, and where everyone is. For a computer, an image is just a grid of numbers — each pixel has a red value, a green value, and a blue value (RGB), each between 0 and 255. A 1280×720 image is literally a matrix of 1,280 × 720 × 3 = 2,764,800 numbers.

Computer vision algorithms learn patterns in those numbers. "A player" might be characterised by an upright rectangular shape with a distinctive colour blob in the middle (the jersey). The field of machine learning has produced increasingly powerful models that can learn these patterns from millions of labelled examples.

### 2.2 How Video is Represented

A video file is a sequence of images (frames) played back at a speed measured in **frames per second (fps)**:

* Broadcast TV: 25 or 30 fps
* Sports cameras: 50 or 60 fps
* Our analysis clips: 10 fps (reduced deliberately for speed)

Each frame is a full image. A 5-minute clip at 10fps = 3,000 frames = 3,000 images to process.

**Why reduce to 10fps?** Player positions don't change meaningfully between frames 1/30th of a second apart. For tactical analysis 10fps gives more than enough temporal resolution while cutting the number of images to process by 3–6×.

**Key video properties:**

* **Resolution**: width × height in pixels (e.g. 1280×720 = "720p")
* **Codec**: the compression algorithm (H.264, H.265/HEVC). More efficient codecs = smaller files at same quality
* **Bitrate**: data per second — higher = better quality, bigger file
* **Pixel format**: how colour is encoded internally. `yuv420p` is the standard for compatibility with OpenCV

**FFmpeg** is the industry-standard tool for reading, writing, converting, and filtering video. It's used here to extract a clip from a longer match recording and apply visual enhancements (sharpening, noise reduction, contrast boosting) that make subsequent detection more reliable.

### 2.3 Object Detection — YOLO

**The problem:** Given a video frame (a grid of numbers), find every player in it and draw a box around each one.

This is called **object detection**. The output is a list of **bounding boxes** — each defined by its top-left corner `(x1, y1)` and bottom-right corner `(x2, y2)` — along with a **confidence score** (how certain the model is that something is there) and a **class** (what the object is).

**YOLO (You Only Look Once)** is the most widely used object detection architecture. The name comes from its key innovation: older approaches slid a window across the image and ran a classifier on each patch (slow). YOLO looks at the whole image exactly once and predicts all boxes simultaneously (fast).

**YOLOv8**, developed by Ultralytics, is the version used here. The model family has several sizes:

| Variant          | Parameters | Speed on CPU | Accuracy |
| ---------------- | ---------- | ------------ | -------- |
| YOLOv8n (nano)   | 3.2M       | \~7 fps      | Good     |
| YOLOv8s (small)  | 11.2M      | \~3 fps      | Better   |
| YOLOv8m (medium) | 25.9M      | \~1 fps      | Best     |

We use **nano** for speed — it's fast enough to run on a Ryzen laptop and accurate enough for player detection at 1280×720.

**Two YOLO models run in parallel:**

| Model                       | Purpose          | Training data                             |
| --------------------------- | ---------------- | ----------------------------------------- |
| `yolov8n.pt` (COCO)         | Player detection | 80 generic classes including `person`     |
| `soccer_ball.pt` (Roboflow) | Ball detection   | 887 soccer-specific images, mAP\@50 95.3% |

**COCO dataset:** The player model is pre-trained on COCO, which contains 80 common object categories including `person` (class index 0) and `sports ball` (class index 32). It can detect players immediately without any custom training. The COCO ball detection is weak at broadcast distance — which is why we add the dedicated Roboflow ball model.

**How a detection pipeline works:**

```
Frame (1280×720 pixels)
      ↓  resize to 320×320 (YOLO_IMGSZ)
      ↓  normalise pixel values 0–1
      ↓  pass through 168 neural network layers
      ↓  output: 8,400 candidate boxes
      ↓  filter by confidence (YOLO_CONF=0.4)
      ↓  Non-Maximum Suppression (remove overlapping boxes)
Final detections: [{bbox, class, confidence}, ...]
```

**Frame skipping:** Running YOLO on every frame would be too slow on CPU. Instead we run it on every Nth frame (`FRAME_SKIP=3` means 1 in 3). Skipped frames reuse the previous detection result. At 10fps with `FRAME_SKIP=3`, YOLO runs \~3.3 times per second — fast enough for smooth tactical analysis.

**OpenVINO export:** The player model is first run in PyTorch format, then exported to Intel's OpenVINO format. OpenVINO is specifically optimised for CPU inference and gives \~2–3× speedup. Critically, the OpenVINO model has its **input shape baked in at export time** — this is why the `YOLO_IMGSZ` value is encoded into the model directory name (`yolov8n_320_openvino_model`). If you change the image size, a fresh export is triggered automatically.

### 2.4 Homography — Mapping Pixels to the Pitch

**The problem:** A camera films the pitch from an angle. A player standing at the halfway line might appear at pixel (640, 400) in the frame. But what we really want to know is where they are on the pitch in **real-world metres** — which is needed for tactical analysis.

A **homography** is a mathematical transformation that maps one plane to another. In our case it maps the **image plane** (pixels) to the **pitch plane** (metres).

Mathematically, a homography is a 3×3 matrix H. Given a pixel point `(x, y)`, the pitch coordinate `(X, Y)` is computed as:

```
[X']   [h11 h12 h13]   [x]
[Y'] = [h21 h22 h23] × [y]
[W']   [h31 h32 h33]   [1]

X = X'/W',  Y = Y'/W'
```

**How do we find H?** By providing **4 or more corresponding point pairs** — pixels in the image and their known real-world coordinates on the pitch. The `calibrate` command handles this interactively:

1. Extract the first frame of the clip
2. Open the image, click on 4 visible field markings (penalty box corners, centre circle, etc.)
3. Read off the pixel coordinates from your image viewer
4. Enter those alongside the known pitch coordinates (in metres, from FIFA standard dimensions)
5. OpenCV's `findHomography()` computes the best-fit H matrix

**Why 4 points minimum?** A homography has 8 degrees of freedom. Each point pair provides 2 equations. 4 pairs → 8 equations → the system is determined.

**Pixel fallback:** When no calibration has been run, we fall back to a linear mapping. This is geometrically inaccurate but good enough to see which pitch zone the ball is in and generate rough heatmaps.

**Why calibration matters:** Without it, a player at pixel (640, 360) maps to exactly (52.5m, 34m) — the centre of the pitch — regardless of where the camera is pointing. With calibration, the same pixel correctly maps to wherever the camera is actually aimed. Possession statistics, pressing radii, and compactness measurements all become more meaningful with accurate pitch coordinates.

### 2.5 K-Means Clustering — Team Identification

**The problem:** How do we know which team each player belongs to? The most reliable signal is **jersey colour**.

**K-Means clustering** is an unsupervised machine learning algorithm that groups data points into K clusters by minimising the distance from each point to its cluster centre (centroid).

**How it's used here (two-stage approach):**

**Stage 1 — Calibration (first 10 frames):** For each detected player, we crop the torso region of their bounding box (middle 50% of height — avoids shorts and socks). We run K-Means with K=2 on the pixels of this crop to find the **dominant colour** of the jersey.

**Stage 2 — Fitting (once after calibration):** We collect all dominant colours from all players across the first 10 frames. We run K-Means with K=3 on these:

* Cluster 1 → Team A jerseys
* Cluster 2 → Team B jerseys
* Cluster 3 → Referee (identified by lowest HSV saturation — typically black or yellow)

**Stage 3 — Per-frame classification:** For each player in each frame, compute the mean colour of their torso crop and find the **nearest cluster centroid**. This is \~50× faster than re-running K-Means.

**Hue-based sorting:** Clusters are sorted by HSV hue so Team A assignment is deterministic. If the colours are inverted, set `SWAP_TEAMS=true` in `.env` or pass `--swap-teams` to `soccercv analyze`.

**Limitations:**

* Fails when teams wear similar colours (grey vs white, dark blue vs black)
* Affected by shadows, floodlights, and dirt on jerseys
* Goalkeeper (different kit) may be misclassified as referee

### 2.6 The Kalman Filter — Ball Tracking Through Occlusion

**The problem:** The ball disappears momentarily behind players, moves out of frame, or is missed by the detector in some frames. How do we maintain a smooth, continuous position estimate?

**This is now fully implemented** in `src/ball_tracker.py`.

A **Kalman filter** is a mathematical technique for estimating the state of a system (position, velocity) from noisy measurements. It works in two steps:

1. **Predict:** Based on current position and estimated velocity, predict where the ball will be in the next frame
2. **Update:** When a new detection arrives, combine the prediction with the measurement to get a refined estimate

The filter tracks 4 state variables: `[cx, cy, vx, vy]` — centre position and velocity in pixels per frame. Only position `[cx, cy]` is directly observed; velocity is inferred from position changes.

**Three tunable noise parameters** (all configurable via `.env`):

| Parameter           | Env var               | Default | Effect                                                            |
| ------------------- | --------------------- | ------- | ----------------------------------------------------------------- |
| Process noise       | `BALL_KALMAN_PROCESS` | 0.03    | How fast velocity can change. Higher = allows faster acceleration |
| Measurement noise   | `BALL_KALMAN_MEASURE` | 2.0     | How much we trust each detection. Higher = smoother but more lag  |
| Initial uncertainty | `BALL_KALMAN_INIT`    | 100.0   | Starting state uncertainty — high means "don't know yet"          |

**Ball state machine:**

| State             | Meaning                               | Bounding box colour |
| ----------------- | ------------------------------------- | ------------------- |
| `DETECTED`        | Found by Roboflow model this frame    | 🟢 Green            |
| `DETECTED` (COCO) | Found by COCO sports ball class       | 🟡 Cyan             |
| `PREDICTED`       | No detection — Kalman prediction used | 🟠 Orange           |
| `LOST`            | Missing > `BALL_MAX_MISSING` frames   | Not drawn           |

The `BALL_MAX_MISSING` window (default 15 frames = 1.5 seconds at 10fps) controls how long the filter keeps predicting before declaring the ball lost.

### 2.7 OpenVINO — CPU-Optimised Inference

**The problem:** Neural networks like YOLOv8 were designed to run on NVIDIA GPUs using CUDA. Without a GPU, they run on CPU — which is much slower.

**Intel OpenVINO** (Open Visual Inference and Neural Network Optimization) is a free toolkit that optimises neural network models specifically for CPU inference. It works by:

1. Analysing the network architecture
2. Fusing operations (e.g. batch normalisation + convolution → single operation)
3. Quantising weights (32-bit float → 8-bit integer, 4× smaller, \~2× faster)
4. Optimising memory layout for cache efficiency
5. Generating CPU-specific code using Intel's MKL-DNN library

**On AMD CPUs:** Despite being an Intel product, OpenVINO works on AMD CPUs too — it uses standard x86 SIMD instructions (AVX2, SSE4) that both manufacturers support. The Ryzen 4500U sees \~2–3× speedup vs raw PyTorch.

**Critical:** The input shape (`imgsz`) is fixed at export time. A model exported at 320×320 cannot run inference at 640×640. This is why we encode the imgsz into the directory name (`yolov8n_320_openvino_model`) and trigger a fresh export automatically if the user changes `--imgsz`.

**Note on PyTorch version compatibility:** PyTorch 2.6+ changed `torch.load` to default `weights_only=True`, which conflicts with older Ultralytics checkpoint formats. This project requires `ultralytics>=8.3.0`, which includes the fix internally. Do not downgrade to `ultralytics==8.2.x`.

### 2.8 Tactical Soccer Concepts

**Possession:** Which team controls the ball at any given moment. Measured by proximity — the team whose player is closest to the ball (within `POSSESSION_RADIUS`, default 3m) is deemed in possession.

**Formation (e.g. 4-3-3):** The positional arrangement of outfield players. Written as defenders-midfielders-attackers. We estimate this by binning players into pitch thirds.

**Formation stability:** How consistently a team holds its intended shape. A high stability % means players return to their designated positions.

**Compactness:** How tightly grouped a team is.

* **Depth** (metres): front-to-back distance between the most advanced and deepest player
* **Width** (metres): side-to-side distance between the widest players

**Pressing:** Applying pressure to the opponent when they have the ball. Measured as the number of a team's players within `PRESS_RADIUS` (default 12m) of the ball when defending.

* **High press**: pressing in the opponent's half
* **Mid-block**: pressing in the middle third
* **Low block**: sitting deep and compact in your own half

**Centroid:** The average position of all players — where the team's centre of gravity is.

**Territory:** Which part of the pitch the ball is in most frequently. `DEF_THIRD_A`, `MIDFIELD`, `ATT_THIRD_A`.

***

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  cli.py  ──  click commands  ──  rich console output        │
│  .env    ──  config defaults  ──  run_config.py (JSON)      │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌────────────────┐     ┌─────────────────────────────────────┐
│  preprocess    │     │           main.py                   │
│  (FFmpeg)      │     │  ┌──────────┐  ┌──────────────────┐ │
│                │     │  │ detect   │  │  team_cluster    │ │
│  hqdn3d noise  │     │  │ (YOLO +  │  │  (KMeans jersey  │ │
│  eq contrast   │     │  │ OpenVINO)│  │   colour)        │ │
│  scale/fps     │     │  └────┬─────┘  └────────┬─────────┘ │
└────────────────┘     │       │                 │           │
                       │       ▼                 │           │
                       │  ┌──────────────────┐   │           │
                       │  │  ball_tracker    │   │           │
                       │  │  Roboflow model  │   │           │
                       │  │  + Kalman filter │   │           │
                       │  └────┬─────────────┘   │           │
                       │       │                 ▼           │
                       │  ┌──────────────────────────────┐   │
                       │  │       homography.py          │   │
                       │  │  pixel (x,y) → pitch (m,m)   │   │
                       │  └──────────────┬───────────────┘   │
                       │                 │                   │
                       │                 ▼                   │
                       │  ┌──────────────────────────────┐   │
                       │  │         tactics.py           │   │
                       │  │  possession / formation /    │   │
                       │  │  compactness / pressing      │   │
                       │  └──────┬───────────────────────┘   │
                       │         │                           │
              ┌────────┴─────────┴──────────┐               │
              ▼                             ▼               │
   ┌─────────────────┐          ┌────────────────────┐      │
   │   overlay.py    │          │  tactical_video.py │      │
   │  minimap corner │          │  top-down pitch    │      │
   │  on main video  │          │  video             │      │
   └────────┬────────┘          └────────┬───────────┘      │
            │                            │                  │
            └──────────┬─────────────────┘                  │
                       ▼                                    │
              ┌────────────────┐                            │
              │   export.py    │                            │
              │  JSON / CSV /  │                            │
              │  heatmaps      │                            │
              └────────┬───────┘                            │
                       ▼                                    │
              ┌────────────────────────────────────────┐   │
              │           report.py                    │   │
              │  charts + HTML + (optional) Claude API │   │
              └────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

***

## 4. Repository Structure

```
soccercv/
├── .env                         # All tunable settings (see Section 7)
├── Containerfile                # Podman/Docker image definition
├── compose.yml                  # Podman Compose services
├── pyproject.toml               # Python package + uv dependency config
├── game_plan.example.json       # Template for game plan compliance
│
├── calibration/
│   └── calibrate.py             # Interactive homography calibration tool
│
├── scripts/
│   ├── preprocess.sh            # FFmpeg wrapper (used by container)
│   └── download_ball_model.py   # Soccer ball model downloader (Roboflow)
│
├── models/                      # All model files live here (auto-created)
│   ├── yolov8n.pt               # Player detection base weights
│   ├── yolov8n_320_openvino_model/  # OpenVINO export (auto-generated)
│   └── soccer_ball.pt           # Ball detection model (downloaded/trained)
│
├── videos/                      # Input video files
│   └── your_match.mp4
│
├── output/                      # All outputs organised by run
│   ├── .current_run             # Pointer to active run directory
│   └── game_04101623/           # Timestamped run directory
│       ├── game_clip.mp4             # Preprocessed analysis clip
│       ├── game_clip_annotated.mp4   # Bounding boxes + minimap overlay
│       ├── game_clip_tactical_view.mp4
│       ├── game_clip_calibration_frame.jpg
│       ├── homography.npy            # Calibration matrix
│       ├── tactical_report.json      # Per-frame tactical data (slim)
│       ├── tactical_data_raw.json    # Per-frame data with player arrays
│       ├── tactical_report.csv       # Flat CSV version
│       ├── heatmap_team_a.png
│       ├── heatmap_team_b.png
│       ├── match_report.html         # Generated HTML report
│       ├── run_config.json           # Settings used for this run
│       └── run.log                   # Full timestamped log
│
└── src/
    ├── ai_analysis.py       # Claude API integration for match reports
    ├── ball_tracker.py      # Kalman filter + dual-model ball tracking
    ├── cli.py               # Click CLI — all user-facing commands
    ├── console.py           # Rich console + logging setup
    ├── detect.py            # YOLO loading, OpenVINO export, per-frame detection
    ├── export.py            # JSON / CSV / heatmap export
    ├── homography.py        # Pixel → pitch coordinate projection
    ├── main.py              # Pipeline orchestrator
    ├── overlay.py           # cv2 minimap overlay on annotated video
    ├── report.py            # HTML report generation + AI integration
    ├── run_config.py        # Run directory management + JSON metadata
    ├── tactical_video.py    # Top-down pitch video renderer
    ├── tactics.py           # Possession / formation / compactness / pressing
    ├── team_cluster.py      # Jersey colour KMeans team classifier
    └── video_check.py       # Pre-run video sanity checks + runtime estimate
```

***

## 5. Setup & Installation

### 5.1 Prerequisites by Platform

All platforms require:

* **Python 3.11+** — the codebase uses `X | Y` union type syntax introduced in 3.10 and f-string improvements from 3.11
* **uv** — fast Python package/venv manager (replaces pip + venv)
* **FFmpeg** — video processing
* **Git** — to clone the repository

The sections below cover each platform. Read your section completely before starting.

***

### 5.2 Linux (Ubuntu / Mint)

**System dependencies:**

```Shell
sudo apt update
sudo apt install ffmpeg git python3.11 python3.11-dev
```

**Install uv:**

```Shell
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # or restart your terminal
```

**Clone and install:**

```Shell
git clone <repo-url> soccercv
cd soccercv
uv sync                  # creates .venv and installs all dependencies
uv pip install -e .      # registers the soccercv CLI command
```

**Verify:**

```Shell
soccercv --help
ffmpeg -version
```

**Container alternative (Podman):**

```Shell
sudo apt install podman
```

See [Section 5.5](#55-container-setup-podman--docker) for container usage.

***

### 5.3 macOS

**Install Homebrew** (if not already installed):

```Shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**System dependencies:**

```Shell
brew install ffmpeg git python@3.11
```

**Install uv:**

```Shell
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc   # or ~/.bashrc depending on your shell
```

**Clone and install:**

```Shell
git clone <repo-url> soccercv
cd soccercv
uv sync
uv pip install -e .
```

**Verify:**

```Shell
soccercv --help
ffmpeg -version
```

**Apple Silicon (M1/M2/M3) notes:**

* PyTorch runs on CPU via `torch.backends.mps` optionally, but OpenVINO is x86 only. On Apple Silicon, OpenVINO will fall back to PyTorch CPU mode automatically — analysis will still work but will be slower (\~2–3× vs x86 with OpenVINO).
* If you see `openvino` installation errors on Apple Silicon, add `openvino` to the `[tool.uv.excluded-packages]` section in `pyproject.toml` and the pipeline will use PyTorch CPU instead.

***

### 5.4 Windows

Windows requires a few extra steps because some dependencies behave differently.

**Install Python 3.11:**

1. Download from <https://www.python.org/downloads/> — choose **3.11.x** (not 3.12+)
2. During install, check **"Add Python to PATH"**
3. Verify: open Command Prompt and run `python --version`

**Install FFmpeg:**

1. Download the latest release from <https://ffmpeg.org/download.html> → Windows builds → gpl release
2. Extract the zip to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH:
   * Search "Environment Variables" in Start Menu
   * Edit the **Path** system variable
   * Add `C:\ffmpeg\bin`
4. Verify: open a new Command Prompt and run `ffmpeg -version`

**Install Git:**
Download and install from <https://git-scm.com/download/win>. During install, choose "Use Git from the Windows Command Line and also from 3rd-party software".

**Install uv:**
Open PowerShell as Administrator and run:

```PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell. Verify: `uv --version`

**Clone and install:**

```PowerShell
git clone <repo-url> soccercv
cd soccercv
uv sync
uv pip install -e .
```

**Verify:**

```PowerShell
soccercv --help
```

**Windows-specific notes:**

* Use **PowerShell** or **Windows Terminal** rather than the old Command Prompt — tab completion and colour output work correctly.
* Path separators: all commands in this README use forward slashes (`/`). PowerShell accepts both `/` and `\`, but if you see path errors try replacing `/` with `\`.
* The CLI uses `xdg-open` to open the HTML report on Linux/Mac. On Windows, replace with `start`:
  ```PowerShell
  start output\game_04101623\match_report.html
  ```
* Line continuation: Linux/Mac examples use `\` for multi-line commands. In PowerShell use backtick `` ` `` instead.
* **WSL2 alternative:** If you run into persistent issues on Windows native, installing WSL2 (Windows Subsystem for Linux) with Ubuntu 22.04 and following the Linux instructions is the most reliable path. FFmpeg and all dependencies work identically inside WSL2.

***

### 5.5 Container Setup (Podman / Docker)

Containers provide a completely reproducible environment that works identically across all platforms. Recommended if you're deploying to a server or want to avoid dependency conflicts.

**Generate the lockfile first (required once):**

```Shell
uv sync        # creates uv.lock
```

**Build and run with Podman:**

```Shell
podman build -t soccer-cv .

podman run --rm -it \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/.env:/app/.env \
  soccer-cv analyze videos/game.mp4 --frame-skip 3
```

**With Docker (same Containerfile works):**

```Shell
docker build -t soccer-cv .

docker run --rm -it \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/.env:/app/.env \
  soccer-cv analyze videos/game.mp4 --frame-skip 3
```

**Windows Docker Desktop (PowerShell):**

```PowerShell
docker run --rm -it `
  -v ${PWD}/videos:/app/videos `
  -v ${PWD}/output:/app/output `
  -v ${PWD}/models:/app/models `
  -v ${PWD}/.env:/app/.env `
  soccer-cv analyze videos/game.mp4 --frame-skip 3
```

**Keep container alive for multiple commands:**

```Shell
podman-compose up -d
podman-compose exec soccercv soccercv preprocess videos/game.mp4
podman-compose exec soccercv soccercv analyze videos/game.mp4
podman-compose down
```

***

### 5.6 API Keys

Two optional API keys unlock additional features. Add them to your `.env` file (see [Section 7](#7-configuration)).

**Anthropic API key** — required for `soccercv report --ai`:

1. Sign up at <https://console.anthropic.com>
2. Create an API key under API Keys
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-your-key-here`
4. Cost: \~\$0.01–0.02 per AI report (Claude Sonnet)

**Roboflow API key** — required for `soccercv download-ball-model` (without `--inference` or `--train`):

1. Sign up free at <https://app.roboflow.com> (no credit card required)
2. Go to Settings → Roboflow API → copy your key
3. Add to `.env`: `ROBOFLOW_API_KEY=rf_your-key-here`
4. Used only at download time — not needed for analysis after the model is saved

***

## 6. Ball Model Setup

### 6.1 Why a Dedicated Ball Model?

The generic COCO `sports ball` class (class index 32) achieves roughly 45–55% mAP on soccer footage — it was trained on hundreds of different ball types at various distances, not specifically soccer balls at broadcast camera distance. Detection is unreliable.

The dedicated model used here — `tomas-gear-mxzjq/soccer-ball-mfbf2 v1` from Roboflow Universe — was trained specifically on soccer broadcast footage:

| Metric          | COCO sports ball | Roboflow soccer ball       |
| --------------- | ---------------- | -------------------------- |
| mAP\@50         | \~50%            | **95.3%**                  |
| Precision       | \~55%            | **94.7%**                  |
| Recall          | \~45%            | **92.2%**                  |
| Training images | Mixed            | 887 soccer-specific        |
| Architecture    | YOLOv8n          | YOLOv8n (COCOn checkpoint) |

The Roboflow model is a drop-in replacement — same YOLOv8 format, loaded identically. The COCO model remains as a fallback when the dedicated model is not installed.

***

### 6.2 Download via Roboflow API Key (recommended)

This is the simplest path if you have a free Roboflow account (see [Section 5.6](#56-api-keys)).

Add your key to `.env`:

```Properties&#x20;files
ROBOFLOW_API_KEY=rf_your-key-here
```

Then run:

```Shell
soccercv download-ball-model
```

The script reads `ROBOFLOW_API_KEY` from `.env` automatically. It fetches version metadata from the Roboflow API, downloads the dataset, and if pre-exported weights aren't available (common for "Roboflow 3.0 Fast" models), trains a local copy from the dataset automatically.

**What gets downloaded to** **`models/soccer_ball.pt`** — a YOLOv8n model fine-tuned on 887 soccer ball images. Training takes approximately:

* CPU (Ryzen 4500U): 1–2 hours for 50 epochs
* GPU (NVIDIA T4 on Colab): \~15 minutes

If you want to train on Google Colab instead:

1. Download the dataset: `soccercv download-ball-model` (will download dataset then fail at training — that's fine, the dataset is saved to `training/soccer-ball-mfbf2/`)
2. Upload `training/soccer-ball-mfbf2/` to Google Drive
3. Train in Colab using `yolo train model=yolov8n.pt data=/path/to/data.yaml epochs=50 imgsz=640`
4. Download `runs/detect/soccer_ball/weights/best.pt` and save as `models/soccer_ball.pt`

***

### 6.3 Download via Inference SDK (no account)

No Roboflow account needed, but installs a large (\~200MB) inference package:

```Shell
soccercv download-ball-model --inference
```

This uses Roboflow's `inference` SDK which caches models locally on first use.

***

### 6.4 Train Locally from Dataset

No account needed. Downloads the public dataset and trains from scratch:

```Shell
soccercv download-ball-model --train
```

You will be prompted to confirm before training begins. The script downloads the dataset ZIP, extracts it, and runs `yolo train` with sensible defaults (50 epochs, imgsz=640, batch=8).

***

### 6.5 How Ball Tracking Works

Once `models/soccer_ball.pt` exists, it is loaded automatically at analysis time. The `BallTracker` class in `src/ball_tracker.py` runs every frame:

```
Frame N
  ↓
[Roboflow model] → ball detection (or None)
  ↓
[COCO model]     → sports ball detection (or None)   ← fallback only
  ↓
BallTracker.update(frame, coco_ball)
  ├── Roboflow found ball → update Kalman, return DETECTED (green)
  ├── Only COCO found ball → update Kalman, return DETECTED (cyan)
  ├── Neither found, frames_missing < MAX → Kalman predict, return PREDICTED (orange)
  └── frames_missing >= MAX → return None (LOST)
  ↓
pitch_coords = homography.pixel_to_pitch(cx, cy)
```

**Annotated video colour coding:**

* 🟢 **Green box** — ball detected by Roboflow model (highest confidence)
* 🟡 **Cyan box** — ball detected by COCO fallback
* 🟠 **Orange box** — Kalman prediction (ball not detected this frame)
* No box — ball is `LOST`

**Motion trail** — the last `BALL_TRAIL_LEN` (default 20) ball positions are drawn as a fading grey trail in both the annotated video and the tactical top-down video.

**Ball tracking stats** appear in the run summary after analysis completes:

```
Ball tracking   detected 67%  predicted 24%  lost 9%
```

These are also recorded in `run_config.json` under `analyze.ball_tracking`.

***

## 7. Configuration

All settings live in `.env` in the project root. **CLI arguments always take priority** over `.env` values, which take priority over built-in defaults.

Priority chain: `CLI arg > shell env > .env value > built-in default`

Copy `.env.example` to `.env` and edit as needed. Never commit `.env` to version control — it contains your API keys.

```Properties&#x20;files
# ── Directories ───────────────────────────────────────────────
VIDEOS_DIR=videos
OUTPUT_BASE_DIR=output
MODELS_DIR=models
HOMOGRAPHY_FILE=output/homography.npy

# ── API keys ──────────────────────────────────────────────────
ANTHROPIC_API_KEY=              # For: soccercv report --ai
ROBOFLOW_API_KEY=               # For: soccercv download-ball-model

# ── FFmpeg preprocess ─────────────────────────────────────────
CLIP_START=00:00:00
CLIP_DURATION=00:05:00
OUTPUT_FPS=10
OUTPUT_WIDTH=1280
OUTPUT_HEIGHT=720

# ── YOLO (player detection) ───────────────────────────────────
YOLO_MODEL=models/yolov8n.pt    # Moved to models/ after first export
YOLO_CONF=0.4
YOLO_IMGSZ=320
FRAME_SKIP=3

# ── Ball tracking ─────────────────────────────────────────────
BALL_MODEL=models/soccer_ball.pt   # Falls back to COCO if not found
BALL_CONF=0.25                     # Lower threshold — ball is small
BALL_IMGSZ=640                     # Higher than player model — ball needs detail
BALL_MAX_MISSING=15                # Frames before state becomes LOST (1.5s at 10fps)
BALL_TRAIL_LEN=20                  # Trail length in frames

# ── Kalman filter tuning ──────────────────────────────────────
BALL_KALMAN_PROCESS=0.03           # Velocity change per frame (higher = faster accel)
BALL_KALMAN_MEASURE=2.0            # Trust in each detection (higher = smoother/laggier)
BALL_KALMAN_INIT=100.0             # Initial uncertainty (high = unknown start)

# ── Roboflow model source (used by download-ball-model) ───────
BALL_RF_WORKSPACE=tomas-gear-mxzjq
BALL_RF_PROJECT=soccer-ball-mfbf2
BALL_RF_VERSION=1
BALL_INFERENCE_MODEL=soccer-ball-mfbf2/1
BALL_DATASET_URL=https://universe.roboflow.com/tomas-gear-mxzjq/soccer-ball-mfbf2/dataset/1/download/yolov8
BALL_RF_API_BASE=https://api.roboflow.com

# ── Team clustering ───────────────────────────────────────────
SWAP_TEAMS=false                   # true = flip Team A / Team B

# ── Tactical parameters ───────────────────────────────────────
POSSESSION_RADIUS=3.0              # Metres from ball = in possession
PRESS_RADIUS=12.0                  # Metres from ball = pressing
PITCH_WIDTH=105
PITCH_HEIGHT=68

# ── Video overlay ─────────────────────────────────────────────
OVERLAY_POSITION=bottom-right      # top-left/top-right/bottom-left/bottom-right
OVERLAY_SCALE=0.28
```

***

## 8. CLI Reference

All commands support `--help` for full option listings.

### 8.1 `soccercv info`

Show video metadata without processing.

```Shell
soccercv info videos/game.mp4
```

Output: file size, resolution, frame rate, total frames, duration, and active run directory (if any).

***

### 8.2 `soccercv preprocess`

Extract and optimise a clip from a source video using FFmpeg.

```Shell
soccercv preprocess videos/game.mp4 \
  --start 00:10:00 \
  --duration 00:05:00 \
  --fps 10 \
  --width 1280 \
  --height 720
```

**What FFmpeg does to the clip:**

1. `hqdn3d=1:1:3:3` — temporal noise reduction
2. `eq=contrast=1.3:brightness=0.05:saturation=2.0` — boost contrast and jersey colour saturation
3. `unsharp=3:3:0.5` — sharpen edges
4. `scale=1280:720` — resize to target resolution
5. `fps=10` — reduce frame rate
6. `-c:v libx264 -crf 20 -preset fast` — H.264 re-encode
7. `-pix_fmt yuv420p` — standard pixel format for OpenCV
8. `-an` — strip audio (not needed for analysis)

**Output:** `output/<run_dir>/<stem>_clip.mp4`

Creates a timestamped run directory and writes `output/.current_run` so subsequent commands use the same directory automatically.

***

### 8.3 `soccercv calibrate`

One-time homography calibration — run once per camera angle.

```Shell
soccercv calibrate output/game_04101623/game_clip.mp4
```

**What it does:**

1. Extracts the first frame → saves as `<run_dir>/game_clip_calibration_frame.jpg`
2. Prompts you to enter pixel coordinates of 4 field landmarks
3. Prompts for the real-world pitch coordinates of each landmark (metres)
4. Computes the homography matrix using `cv2.findHomography()`
5. Saves `<run_dir>/homography.npy`
6. Verifies accuracy by back-projecting each point (aim for < 0.5m error)

See [Section 12](#12-homography-calibration-guide) for a detailed walkthrough.

***

### 8.4 `soccercv analyze`

Run the full analysis pipeline on a preprocessed clip.

```Shell
soccercv analyze output/game_04101623/game_clip.mp4 \
  --frame-skip 3 \
  --imgsz 320 \
  --conf 0.4 \
  --model models/yolov8n.pt \
  --ball-model models/soccer_ball.pt \
  --swap-teams \
  --overlay-position bottom-right \
  --possession-radius 3.0 \
  --press-radius 12.0 \
  --log-level INFO
```

**Key options:**

| Option                | Default                 | Description                              |
| --------------------- | ----------------------- | ---------------------------------------- |
| `--frame-skip`        | 3                       | Run YOLO on every Nth frame              |
| `--imgsz`             | 320                     | YOLO input size (320=fast, 640=accurate) |
| `--ball-model`        | `models/soccer_ball.pt` | Path to dedicated ball model             |
| `--swap-teams`        | false                   | Flip Team A / Team B colour assignment   |
| `--possession-radius` | 3.0                     | Metres to ball = in possession           |
| `--press-radius`      | 12.0                    | Metres to ball = pressing                |

**Outputs in run directory:**

* `*_annotated.mp4` — original video with bounding boxes, ball trail, minimap
* `*_tactical_view.mp4` — top-down tactical video
* `tactical_report.json` — per-frame tactical data
* `tactical_report.csv` — flat CSV
* `heatmap_team_a.png` / `heatmap_team_b.png`
* `run_config.json` — all settings + ball tracking stats
* `run.log` — full timestamped log

Clears `output/.current_run` when complete so the next preprocess starts fresh.

***

### 8.5 `soccercv run`

Full pipeline in a single command: preprocess → calibrate → analyze.

```Shell
soccercv run videos/game.mp4 \
  --start 00:10:00 \
  --duration 00:05:00 \
  --frame-skip 3 \
  --imgsz 320 \
  --skip-calibrate
```

All three steps share a single run directory. Calibration is interactive unless `--skip-calibrate` is passed (uses pixel fallback).

***

### 8.6 `soccercv report`

Generate an HTML match report from a completed analysis run.

```Shell
# Basic report (rule-based analysis only)
soccercv report output/game_04101623 \
  --team-a "Rangers" \
  --team-b "United"

# With score (enables counterfactual section)
soccercv report output/game_04101623 \
  --team-a "Rangers" --team-b "United" \
  --score-a 2 --score-b 1

# With game plan compliance audit
soccercv report output/game_04101623 \
  --team-a "Rangers" --team-b "United" \
  --score-a 2 --score-b 1 \
  --game-plan game_plan.json

# Full AI-powered report (requires ANTHROPIC_API_KEY)
soccercv report output/game_04101623 \
  --team-a "Rangers" --team-b "United" \
  --score-a 2 --score-b 1 \
  --game-plan game_plan.json \
  --ai \
  --coach-notes "Rangers played without striker Jones (injured min 8). \
Wind against Rangers in first half. United sat in low block after min 3 goal."
```

Open the report:

```Shell
# Linux
xdg-open output/game_04101623/match_report.html

# macOS
open output/game_04101623/match_report.html

# Windows
start output\game_04101623\match_report.html
```

***

### 8.7 `soccercv download-ball-model`

Download a pre-trained soccer ball detection model.

```Shell
# Using Roboflow API key (reads ROBOFLOW_API_KEY from .env)
soccercv download-ball-model

# Explicit key
soccercv download-ball-model --api-key YOUR_KEY

# Using Roboflow inference SDK (no account, installs ~200MB package)
soccercv download-ball-model --inference

# Train locally from public dataset (no account, 1–2 hrs on CPU)
soccercv download-ball-model --train

# Custom output path
soccercv download-ball-model --output models/my_ball_model.pt

# Skip post-download verification
soccercv download-ball-model --no-verify
```

The downloaded model is saved to `models/soccer_ball.pt` (configurable via `BALL_MODEL` in `.env`) and picked up automatically by `soccercv analyze`.

***

## 9. The Processing Pipeline — Step by Step

### Step 1: Download ball model (one time)

```Shell
soccercv download-ball-model
```

This only needs to be done once. The model is saved to `models/soccer_ball.pt` permanently.

### Step 2: Preprocess

```Shell
soccercv preprocess videos/full_match.mp4 --start 00:10:00 --duration 00:05:00
```

Produces: `output/full_match_04101623/full_match_clip.mp4` and creates a run directory.

### Step 3: Calibrate (optional but recommended)

```Shell
soccercv calibrate output/full_match_04101623/full_match_clip.mp4
```

Open the saved calibration frame, identify 4 landmarks, enter coordinates. Saves `homography.npy`.

### Step 4: Analyze

```Shell
soccercv analyze output/full_match_04101623/full_match_clip.mp4
```

Runs detection, ball tracking, team clustering, homography projection, and tactical analysis. Produces all output files. When finished, the run pointer is cleared.

### Step 5: Report

```Shell
soccercv report output/full_match_04101623 \
  --team-a "Rangers" --team-b "United" \
  --score-a 2 --score-b 1 --ai
```

Generates `match_report.html` with charts, tactical analysis, and Claude-powered narrative.

***

## 10. Module Reference

### `src/ball_tracker.py`

The ball tracking engine. Two classes:

**`BallModel`** — lazy loader for the dedicated Roboflow soccer ball model. Loads on first use; returns `None` from `detect()` if the model file doesn't exist, so the pipeline degrades gracefully to COCO fallback.

**`BallTracker`** — main tracking class. `update(frame, coco_ball)` is called once per detection frame and returns a ball dict or `None`:

```Python
{
    "bbox":         [x1, y1, x2, y2],
    "conf":         float,        # 0.0 for Kalman predictions
    "source":       "roboflow" | "coco" | "kalman",
    "state":        "DETECTED" | "PREDICTED" | "LOST",
    "pitch_coords": [x_m, y_m],  # filled by main.py via homography
    "centre":       [cx, cy],
}
```

`BallTracker.trail` returns the last `BALL_TRAIL_LEN` centre positions as a list of `(x, y)` tuples for trail rendering.

### `src/detect.py`

YOLO-based player detection. Key functions:

* `load_model(imgsz)` — loads cached OpenVINO model or exports from PyTorch on first run. After export, moves `yolov8n.pt` from the project root into `models/` to keep the directory clean.
* `detect_frame(model, frame, imgsz)` — returns `{"players": [...], "ball": ...}` where `ball` is the COCO class-32 detection (low quality fallback — BallTracker uses its own Roboflow model as primary).

### `src/cli.py`

Entry point for all user interactions. Built with **Click** and **Rich**. Responsible for:

* Parsing all command-line arguments
* Loading `.env` into `os.environ` at startup
* Resolving the active run directory
* Setting env vars for downstream modules

Key design: CLI arguments are pushed into `os.environ` before calling pipeline modules, so the same modules work whether called from CLI or directly from Python scripts.

### `src/team_cluster.py`

Jersey colour classification using scikit-learn's `KMeans`. Two-phase approach: KMeans on individual torso pixel crops during calibration, then fast nearest-centroid lookup per frame. Referee identification via lowest HSV saturation cluster.

### `src/homography.py`

Wraps OpenCV's perspective transform. `HomographyProjector.pixel_to_pitch()` returns `[x_m, y_m]` always — falls back to linear normalisation if no calibration matrix exists.

### `src/tactics.py`

Pure tactical analysis functions (no OpenCV, no YOLO). Each operates on a list of player dicts with `pitch_coords` populated:

* `get_possession()` — nearest player to ball within radius
* `get_formation()` — bin players into thirds
* `get_compactness()` — bounding box stats of all player positions
* `get_pressing_intensity()` — count players within press radius of ball
* `get_ball_zone()` — which pitch third the ball is in
* `analyze_frame()` — computes all of the above for one frame

### `src/overlay.py`

Draws player bounding boxes (colour-coded by team) and the minimap overlay (top-down pitch view with players, ball, stats panel) onto each annotated video frame. Ball box is colour-coded by detection source (green/cyan/orange).

### `src/tactical_video.py`

Generates the full-resolution top-down tactical video (1050×680 + 160px stats panel). Features full pitch markings, zone shading, player circles with shadow, ball with motion trail, centroid markers, and possession bar.

### `src/export.py`

Three export functions: `save_tactical_json()`, `save_tactical_csv()`, `generate_heatmaps()`.

### `src/run_config.py`

Manages the "current run" pointer (`output/.current_run`) and per-run JSON metadata. Config is stored as `run_config.json` (not YAML) so it maps directly to PostgreSQL `jsonb` columns for cross-match querying.

### `src/report.py`

Self-contained HTML report generator. All charts are matplotlib figures serialised as base64-encoded PNG strings — no external files needed, the report opens in any browser. Two classes:

* `MatchReport` — rule-based analysis
* `MatchReportWithAI` — extends with Claude API narrative sections

### `src/ai_analysis.py`

Sends a compact pre-aggregated statistics summary to the Claude API. The raw `tactical_report.json` is never sent — only computed averages and percentages, keeping the payload under \~1,500 input tokens. Parses the structured response into named sections.

### `src/video_check.py`

Pre-analysis sanity checks: warns if FPS > 15, width > 1920, or duration > 10 minutes. Also estimates runtime based on empirical measurements on Ryzen 4500U.

### `src/console.py`

Shared Rich console and Python logging setup. All modules import `console` and `log` from here.

### `calibration/calibrate.py`

Interactive homography calibration tool. All paths come from environment variables — nothing hardcoded. Includes verification step showing pixel → pitch projection error for each landmark.

### `scripts/download_ball_model.py`

Standalone script for downloading the soccer ball detection model. Loads `.env` itself (same logic as `cli.py`) so `ROBOFLOW_API_KEY` is read automatically. Three download methods: Roboflow API, inference SDK, local training.

***

## 11. Output Files Reference

### `tactical_report.json`

Array of per-frame snapshots. Each frame:

```JSON
{
  "frame": 150,
  "timestamp_s": 15.0,
  "possession": "TEAM_A",
  "possession_pct": {"TEAM_A": 58, "TEAM_B": 42},
  "ball_zone": "MIDFIELD",
  "ball_pitch_coords": [52.4, 33.8],
  "ball_source": "roboflow",
  "ball_state": "DETECTED",
  "TEAM_A": {
    "player_count": 9,
    "formation": {"shape": "4-3-2", "def": 4, "mid": 3, "att": 2},
    "compactness": {
      "depth_m": 38.2,
      "width_m": 52.1,
      "centroid": [45.2, 34.1],
      "area_m2": 1989.4
    },
    "pressing": 2
  },
  "TEAM_B": { ... }
}
```

### `tactical_report.csv`

Flat CSV for pandas or spreadsheet analysis. One row per frame.

### `run_config.json`

Documents every setting used in the run, including ball tracking stats:

```JSON
{
  "run_directory": "/home/user/soccercv/output/game_04101623",
  "preprocess": {
    "timestamp": "2026-04-10 14:05:22",
    "elapsed": "2m 14s",
    "changed_from_defaults": {},
    "config": { "CLIP_START": "00:10:00", ... }
  },
  "analyze": {
    "timestamp": "2026-04-10 14:21:08",
    "elapsed": "16m 42s",
    "source_resolution": "1280x720",
    "total_frames": 3000,
    "ball_tracking": {
      "model": "models/soccer_ball.pt",
      "detected": 1680,
      "predicted": 900,
      "lost": 420
    }
  }
}
```

***

## 12. Homography Calibration Guide

Calibration is optional but significantly improves accuracy of all distance-based metrics.

### Finding Pixel Coordinates

Run calibration to extract the first frame:

```Shell
soccercv calibrate output/run_dir/clip.mp4
```

Open the saved calibration frame in an image viewer:

```Shell
# Linux
eog output/run_dir/clip_calibration_frame.jpg

# macOS
open output/run_dir/clip_calibration_frame.jpg

# Windows
start output\run_dir\clip_calibration_frame.jpg
```

Hover over a landmark — the status bar shows `x, y` pixel coordinates.

### Choosing Good Landmarks

**Good choices** (sharp visible intersections):

* Penalty box corners where two lines meet
* Corner flags at field corners
* Penalty spots (small dots inside penalty area)
* Centre circle top/bottom where it meets the halfway line

**Avoid:**

* Points close together (reduces accuracy)
* Curved lines (hard to pinpoint exactly)
* Points near the edge of frame (more lens distortion)

**Golden rule:** Spread your 4 points across the frame — one in each quadrant ideally.

### Standard Pitch Coordinates (metres)

Origin (0,0) is the **top-left corner** of the pitch.

| Landmark                            | Pitch x,y (metres) |
| ----------------------------------- | ------------------ |
| Top-left corner flag                | 0, 0               |
| Top-right corner flag               | 105, 0             |
| Bottom-right corner flag            | 105, 68            |
| Bottom-left corner flag             | 0, 68              |
| Left penalty box top-left           | 0, 13.84           |
| Left penalty box top-right          | 16.5, 13.84        |
| Left penalty box bottom-right       | 16.5, 54.16        |
| Left penalty box bottom-left        | 0, 54.16           |
| Right penalty box top-left          | 88.5, 13.84        |
| Right penalty box top-right         | 105, 13.84         |
| Penalty spot left                   | 11, 34             |
| Penalty spot right                  | 94, 34             |
| Centre circle top (halfway line)    | 52.5, 24.85        |
| Centre circle bottom (halfway line) | 52.5, 43.15        |

### Verifying Calibration

After entering 4 point pairs, the script shows projection errors:

```
✓  Landmark 1: pixel(312,580) → pitch(0.02,13.83)m  [expected (0,13.84)m  err=0.018m]
✓  Landmark 2: pixel(968,580) → pitch(16.49,13.84)m [expected (16.5,13.84)m  err=0.011m]
⚠  Landmark 3: pixel(968,298) → pitch(16.52,54.22)m [expected (16.5,54.16)m  err=0.063m]
```

Aim for all errors < 0.5m. If one is high, re-run with a more precise pixel reading for that landmark.

***

## 13. Performance Tuning

### Baseline (AMD Ryzen 4500U, no GPU)

| Settings                     | 5-min clip time |
| ---------------------------- | --------------- |
| `--frame-skip 3 --imgsz 320` | \~12–16 min     |
| `--frame-skip 4 --imgsz 320` | \~8–12 min      |
| `--frame-skip 4 --imgsz 256` | \~6–9 min       |
| `--frame-skip 2 --imgsz 640` | \~45–60 min     |

**Ball model adds minimal overhead** — it runs on the same frames as the player model and is the same nano architecture.

### Key Levers

**`--frame-skip N`** — Most impactful. `FRAME_SKIP=4` means YOLO runs on 1 in 4 frames. At 10fps that's 2.5 detections per second. The Kalman filter fills gaps between detections, so higher frame-skip values don't hurt ball tracking quality as much as they used to.

**`--imgsz N`** — YOLO input image size. Smaller = faster quadratically. Going from 640→320 halves linear dimension → 4× fewer pixels → \~2–3× speedup. `320` is the recommended default for CPU.

**`BALL_IMGSZ=640`** — The ball model always runs at 640 because the ball is small and needs the resolution. This is separate from `YOLO_IMGSZ` and doesn't affect player detection speed.

**`--model models/yolov8n.pt`** — Use nano. Upgrading to small (`yolov8s.pt`) doubles inference time for a modest accuracy gain.

**OpenVINO cache** — After the first run, subsequent runs load the pre-exported OpenVINO model instantly. Don't delete the `models/yolov8n_320_openvino_model/` directory.

***

## 14. AI-Powered Reports

When `--ai` is passed to `soccercv report`, the system:

1. Aggregates match statistics (possession %, formations, compactness, pressing, momentum windows, ball tracking quality)
2. Sends a compact structured prompt to Claude Sonnet via `https://api.anthropic.com/v1/messages`
3. Parses the structured response into named sections
4. Injects them into the HTML report with purple-accented styling

**What is sent to the API (not the raw JSON):**

```
Possession: Rangers 58%, United 42%
Formation: Rangers 4-3-3 (72% stability), United 4-4-2 (81%)
Compactness Rangers in possession: depth 38.2m width 52.1m
Ball tracking: detected 67%, predicted 24%, lost 9%
...
```

**Cost:** \~1,500 input tokens + 2,000 output tokens ≈ \$0.01–0.02 per report on Claude Sonnet.

**The** **`--coach-notes`** **flag** passes qualitative context the data can't capture — injuries, weather, deliberate tactical changes, referee decisions. This is essential for accurate counterfactual analysis:

```Shell
--coach-notes "Rangers played without striker Jones (injured min 8). \
  Wind heavily against Rangers in first half. \
  United sat in a low block after scoring in minute 3."
```

**Report sections generated by Claude:**

* Match Summary
* Team Tendencies
* Formation Analysis
* Pressing Analysis
* Momentum Analysis
* Counterfactual (if score provided — how could the losing team have won?)
* Game Plan Compliance (if game plan provided)
* Recommendations

***

## 15. Game Plan Compliance

Create a `game_plan.json` file describing the intended tactics. Use `game_plan.example.json` as a starting point:

```JSON
[
  {
    "instruction": "Press high in opponent half",
    "metric": "press_a_avg",
    "target": ">= 2.5"
  },
  {
    "instruction": "Maintain 4-3-3 shape",
    "metric": "stability_a",
    "target": ">= 75"
  },
  {
    "instruction": "Control possession",
    "metric": "poss_pct_a",
    "target": ">= 55"
  }
]
```

**Available metrics:**

| Metric key                              | Description                                |
| --------------------------------------- | ------------------------------------------ |
| `poss_pct_a` / `poss_pct_b`             | Possession %                               |
| `press_a_avg` / `press_b_avg`           | Average pressers near ball when defending  |
| `high_press_a` / `high_press_b`         | % of defending situations with ≥3 pressers |
| `stability_a` / `stability_b`           | % of frames holding primary formation      |
| `comp_a_depth_in` / `comp_b_depth_in`   | Avg depth (metres) in possession           |
| `comp_a_width_in` / `comp_b_width_in`   | Avg width (metres) in possession           |
| `comp_a_depth_out` / `comp_b_depth_out` | Avg depth (metres) out of possession       |

**Target format:** `>= 2.5`, `<= 40`, `== 58` etc.

The HTML report shows ✅/❌ per instruction. With `--ai`, Claude provides narrative assessment of each compliance item.

***

## 16. Troubleshooting

### OpenVINO shape mismatch

```
Can't set the input tensor with index: 0, because the model input (shape=[1,3,640,640])
and the tensor (shape=(1,3,320,320)) are incompatible
```

Delete the stale model directory and let it re-export:

```Shell
rm -rf models/yolov8n_320_openvino_model
# or on Windows:
rmdir /s /q models\yolov8n_320_openvino_model
```

### PyTorch 2.6 / Ultralytics compatibility error

```
_pickle.UnpicklingError: Weights only load failed.
GLOBAL ultralytics.nn.tasks.DetectionModel was not an allowed global
```

This means you have `ultralytics==8.2.x` installed with PyTorch 2.6+. The fix is to upgrade ultralytics:

```Shell
uv pip install "ultralytics>=8.3.0"
```

`pyproject.toml` already specifies `ultralytics>=8.3.0` — if you see this error you may have a stale venv. Run `uv sync` to resync.

### Ball model not found / falling back to COCO

```
[ball_tracker] No dedicated ball model found at models/soccer_ball.pt
```

This is a warning, not an error. Analysis continues with COCO fallback + Kalman filter, but ball detection quality will be lower. To fix:

```Shell
soccercv download-ball-model
```

### `yolov8n.pt` landing in project root

On first run, Ultralytics downloads `yolov8n.pt` to the working directory before `detect.py` can move it. This is normal — `detect.py` moves it to `models/yolov8n.pt` after the OpenVINO export completes. If you see it in the project root after a failed first run:

```Shell
mv yolov8n.pt models/
# Windows:
move yolov8n.pt models\
```

### Team colours inverted

Add `--swap-teams` to `soccercv analyze`, or set `SWAP_TEAMS=true` in `.env`.

### Ball tracking shows mostly PREDICTED/LOST

The ball model may not be detecting well on your footage. Try:

* Lower `BALL_CONF` from 0.25 to 0.15 in `.env`
* Increase `BALL_IMGSZ` to 1280 if your footage is high resolution
* Increase `BALL_MAX_MISSING` to 30 for smoother predictions through long gaps
* Retrain the model on your own footage (see [Section 6.4](#64-train-locally-from-dataset))

### Slow processing (> 20 min for 5-min clip)

* Increase `FRAME_SKIP` to 4 or 5
* Reduce `YOLO_IMGSZ` to 256
* Ensure OpenVINO model is being used (check log: `[detect] Loading OpenVINO model`)
* Verify the clip was preprocessed to 10fps

### `soccercv` command not found

The editable install may not be in your PATH. Try:

```Shell
uv pip install -e .
# or run directly with:
uv run soccercv --help
```

### Heatmaps empty / possession all `NO_BALL`

Homography calibration is missing or broken. Check:

1. `homography.npy` exists in your run directory
2. `HOMOGRAPHY_FILE` in `.env` points to the right path
3. If using pixel fallback, check `frame_w` and `frame_h` are non-zero in the logs

### Windows: `\` path errors in commands

Replace forward slashes with backslashes in paths, or wrap the path in quotes. Alternatively, use PowerShell which accepts both.

### macOS Apple Silicon: OpenVINO not available

OpenVINO is x86-only. On Apple Silicon, the system automatically falls back to PyTorch CPU inference. Analysis still works — it's just \~2–3× slower. No action needed.

***

## 17. Next Steps & Roadmap

### ✅ Completed

**Ball tracking (Kalman filter + pre-trained model)**

* `BallTracker` class with constant-velocity Kalman filter
* Dedicated Roboflow soccer ball model (tomas-gear-mxzjq/soccer-ball-mfbf2, mAP\@50 95.3%)
* Dual-model detection: Roboflow primary → COCO fallback → Kalman prediction
* State machine: DETECTED / PREDICTED / LOST with configurable timeout
* Motion trail rendering in both annotated and tactical videos
* Colour-coded bounding boxes by detection source
* Ball tracking stats in run summary and `run_config.json`
* `soccercv download-ball-model` CLI command with 3 download methods

**AI-powered match reports**

* `soccercv report --ai` sends compact stats to Claude Sonnet API
* 8 structured report sections including counterfactual and game plan compliance
* `--coach-notes` flag for qualitative context

**Game plan compliance**

* `game_plan.json` format with threshold-based ✅/❌ evaluation
* AI narrative assessment per instruction

**Run configuration as JSON**

* `run_config.json` replaces YAML for easy PostgreSQL `jsonb` import
* `changed_from_defaults` diff for quick review of non-default settings

### Near-term (Beta)

**P1 — ByteTrack player tracking**

* Assign persistent IDs to players across all frames
* Required for individual player analysis (distance covered, heatmaps per player)
* ByteTrack is MIT licensed and integrates with Ultralytics natively
* Estimated effort: 2–3 days

**P2 — Possession state machine**

* Replace per-frame proximity check with a dwell-time state machine
* A team must hold the closest-player condition for N consecutive frames
* Eliminates flickering in contested-possession moments
* Estimated effort: 1 day

**P3 — YOLOv8 fine-tuning on player data**

* Label 500–1,000 frames from your own footage using Roboflow (free tier)
* Fine-tune on Google Colab (free T4 GPU, \~2 hours)
* Improves detection of players in clusters, goalkeeper vs outfield distinction
* Estimated effort: 1 day setup + compute time

**P4 — Event detection**

* Shot detection, pass detection, tackle detection
* Requires ball tracking (now complete) and ByteTrack (P1)

### Medium-term (V1)

**Velocity and acceleration**

* Once ByteTrack provides persistent IDs, compute velocity (metres/second) per player
* Sprint detection, distance covered, high-intensity runs

**Pressing triggers**

* Identify the specific moment that triggers a team press, not just intensity

**Set piece detection**

* Corner kicks, free kicks, throw-ins have distinct spatial signatures

**Web dashboard**

* FastAPI backend serving `tactical_report.json`
* React frontend with interactive pitch view, timeline scrubber

**PostgreSQL integration**

* `run_config.json` is already structured for direct import
* Cross-match queries: "show possession % for all home games this season"

### Long-term (Commercial)

**Multi-camera support** — stitch views or select best camera per frame

**Live processing** — RTMP/HLS stream analysis (\~30s latency achievable on cloud GPU)

**Expected goals (xG) integration** — once shot events are detected

***

## 18. Commercial Deployment

### Market Opportunity

The soccer analytics market is dominated by expensive broadcast-only platforms (StatsBomb, Opta, Wyscout — $20,000–$100,000+/year per club). Youth clubs, semi-professional clubs, and national federations in lower-income countries have no access to this data.

Soccer CV targets the **grassroots and semi-professional segment** — clubs with budgets of $500–$5,000/year for analytical tools.

### Deployment Architecture

**Tier 1: Self-hosted (current)**

* Clubs with technical staff run it locally
* Cost: hardware + API credits
* Target: technically-capable clubs, university programs, coaching academies

**Tier 2: SaaS — Upload & Analyse**

* Club uploads 5-minute clip via web interface
* Processing runs on cloud GPU (Vast.ai \~$0.30/hr → ~$0.10 per 5-min analysis)
* Report delivered via email or in-browser
* Pricing: \$29–99/month per club (5–20 analyses/month)

**Tier 3: Enterprise — Full Integration**

* Camera at pitch connected to edge device (Raspberry Pi 5 + Hailo AI accelerator)
* Real-time processing, live dashboard on tablet
* API integration with club management software
* Pricing: \$500–2,000/month + hardware

### Cloud Infrastructure

| Provider             | Cost                | Best for                     |
| -------------------- | ------------------- | ---------------------------- |
| Vast.ai              | \$0.10–0.30/GPU hr  | Batch processing, cheapest   |
| RunPod               | \$0.30–0.50/GPU hr  | More reliable than Vast      |
| AWS g4dn.xlarge (T4) | \$0.53/hr on-demand | Production reliability       |
| Google Colab Pro     | \$10/month          | Development + model training |

**SaaS architecture:**

```
S3/GCS video upload → SQS/Pub-Sub queue → GPU worker (auto-scaling)
→ PostgreSQL + S3 results → Web dashboard / email delivery
```

### Key Differentiators vs Competitors

| Feature                  | Soccer CV              | StatsBomb | Wyscout   |
| ------------------------ | ---------------------- | --------- | --------- |
| Price                    | \$29–99/mo             | \$20K+/yr | \$10K+/yr |
| Requires broadcast feed  | No                     | Yes       | Yes       |
| Works with phone footage | Yes (with limitations) | No        | No        |
| Open source core         | Yes                    | No        | No        |
| Ball tracking (Kalman)   | Yes                    | Yes       | Yes       |
| AI report narrative      | Yes (Claude)           | No        | Basic     |
| Real-time (roadmap)      | Yes                    | No        | No        |

### Key Risks

**Accuracy at amateur level:** Camera shake, poor pitch markings, non-standard jersey colours. Homography calibration requirement is a UX friction point. **Mitigation:** Offer a premium "manual QA" tier.

**Ball tracking in adverse conditions:** Wet weather, dirty ball, heavy motion blur reduce Roboflow model confidence. **Mitigation:** Kalman filter maintains continuity through short gaps; tunable confidence threshold via `BALL_CONF`.

**GPU cost at scale:** Heavy upload volume increases compute cost. **Mitigation:** Batch jobs in off-peak hours (lower spot pricing), cap weekly volume per tier.

***

## Appendix: Dependency Summary

| Package                  | Version  | Purpose                                    |
| ------------------------ | -------- | ------------------------------------------ |
| `ultralytics`            | ≥8.3.0   | YOLOv8 model loading, training, export     |
| `opencv-python-headless` | 4.9.0.80 | Video I/O, image processing, Kalman filter |
| `torch` / `torchvision`  | ≥2.3.0   | PyTorch runtime for YOLO                   |
| `openvino`               | 2024.1.0 | CPU-optimised inference (x86 only)         |
| `scikit-learn`           | 1.4.2    | KMeans clustering for team ID              |
| `numpy`                  | 1.26.4   | Array operations throughout                |
| `matplotlib`             | 3.8.4    | Chart generation for reports               |
| `click`                  | 8.1.7    | CLI framework                              |
| `rich`                   | 13.7.1   | Terminal formatting + logging              |

**Important version notes:**

* `ultralytics>=8.3.0` is required — 8.2.x is incompatible with PyTorch 2.6+ due to a `torch.load` API change. Ultralytics 8.3+ includes the fix internally.
* `torch>=2.3.0` — any version 2.3 or later works provided ultralytics is also ≥8.3.0.
* `openvino` is x86-only. On Apple Silicon it is skipped and PyTorch CPU is used instead.

All Python dependencies are managed via `uv` / `pyproject.toml`. System dependencies (FFmpeg) are installed separately per platform.

***

*Soccer CV — built in conversation with Claude, April 2026*
