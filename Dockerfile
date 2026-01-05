# RunPod Serverless Blender Renderer
# GPU-accelerated B-roll generation

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics

# Install dependencies and Blender from official repos
RUN apt-get update && apt-get install -y \
    blender \
    python3 \
    python3-pip \
    ffmpeg \
    wget \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install RunPod SDK
RUN pip3 install --no-cache-dir runpod requests

# Create workspace
WORKDIR /workspace

# Copy handler and templates
COPY handler.py /workspace/handler.py
COPY templates/ /workspace/templates/

# Verify Blender installation
RUN blender --version

# Set entrypoint
CMD ["python3", "-u", "/workspace/handler.py"]
