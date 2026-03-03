FROM pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime

WORKDIR /workspace

# Install git for cloning
RUN apt-get update && apt-get install -y git git-lfs && rm -rf /var/lib/apt/lists/*

# Install pinned dependencies.
# tokenizers and huggingface-hub are pinned explicitly because transformers==4.41.2
# requires older versions than what ships in the base Colab environment.
RUN pip install --no-cache-dir --break-system-packages \
    torch==2.10.0 \
    transformers==4.41.2 \
    tokenizers==0.19.1 \
    huggingface-hub==0.36.2 \
    tqdm==4.67.3 \
    xgboost==3.2.0 \
    pytorch-lightning==2.6.1 \
    fair-esm==2.0.0 \
    torchdiffeq==0.2.5 \
    Bio==1.8.1

# Clone moPPIt repository and pin to a specific commit
RUN git clone https://huggingface.co/ChatterjeeLab/moPPIt /workspace/moPPIt && \
    cd /workspace/moPPIt && \
    git checkout fe763faaf75b484c11120392ebe832b3e6dd8600

WORKDIR /workspace/moPPIt

# Prevent KeyError: 'getpwuid(): uid not found: 21155'
ENV TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor