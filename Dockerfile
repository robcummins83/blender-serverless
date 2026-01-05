# RunPod Serverless Blender Renderer
# GPU-accelerated B-roll generation with CUDA support

FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libxrender1 \
    libxxf86vm1 \
    libxfixes3 \
    libxi6 \
    libxkbcommon0 \
    libsm6 \
    libgl1 \
    libgomp1 \
    python3 \
    python3-pip \
    ffmpeg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Download and install Blender 4.2 LTS with CUDA support
RUN wget -q https://download.blender.org/release/Blender4.2/blender-4.2.0-linux-x64.tar.xz \
    && tar -xf blender-4.2.0-linux-x64.tar.xz \
    && mv blender-4.2.0-linux-x64 /opt/blender \
    && ln -s /opt/blender/blender /usr/local/bin/blender \
    && rm blender-4.2.0-linux-x64.tar.xz

# Install RunPod SDK
RUN pip3 install --no-cache-dir runpod requests

# Verify Blender installation
RUN blender --version

# Create workspace
WORKDIR /workspace

# Copy handler and templates
COPY handler.py /workspace/handler.py
COPY templates/ /workspace/templates/

# Set entrypoint
CMD ["python3", "-u", "/workspace/handler.py"]
