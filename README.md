# YOLOv11 DeepStream for NVIDIA Jetson

This repository contains a Dockerfile for DeepStream-compatible Docker container for running YOLO models on NVIDIA Jetson devices.

## Features

- Pre-configured environment for running YOLO models with NVIDIA DeepStream
- Compatible with Jetson Jetpack 6
- Hardware-accelerated inference using NVIDIA GPU

## Quick Start

Pull the Docker image that you need:

```bash
docker pull arda78484/ultralytics-deepstream:latest-jetpack6
```
```bash
docker pull arda78484/ultralytics-deepstream:latest-480p-jetpack6
```

Run the container:

```bash
docker run -it --runtime=nvidia \
    --privileged \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v /dev:/dev \
    -v ~/Ultralytics-DeepStream-Jetson/engines:/ws \
    arda78484/ultralytics-deepstream:latest-jetpack6
```
Note: If you are running engine for the first time it can take long time don't worry
```bash
    cd ws 
    deepstream-app -c deepstream_app_config.txt
```

## Slower Start

Or you can build the dockerfile


```bash
docker build -t <<<NAME_YOUR_CONTAINER>>> .
```

## Requirements

- NVIDIA Jetson device
- JetPack 6
- Docker installed
- NVIDIA Container Runtime

## License

This project is open-source and available under the [MIT License](LICENSE).
