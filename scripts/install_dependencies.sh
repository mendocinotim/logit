#!/bin/bash

# Navigate to project root
cd /Volumes/AI_ETS_2TB/EverythingSwing || exit

# Create virtual environment if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install with MPS fallback
export PYTORCH_ENABLE_MPS_FALLBACK=1
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt \
  --no-cache-dir \
  --no-build-isolation \
  --extra-index-url https://pypi.nvidia.com

# Post-install verification
python3 -c "from nemo.collections.asr.models import EncDecCTCModel; print('NeMo ASR installed successfully')"
