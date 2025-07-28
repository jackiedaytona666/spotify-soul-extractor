# Production Deployment Commands

## Start Gunicorn Server
python3 server.py

## Start Ngrok Tunnel (Fixed Syntax)
# The correct ngrok command should be:
ngrok http 8889 --domain=saint1.soulsyphonacadamy.art

# NOT: ngrok https 8889 --https://saint1.soulsyphonacadamy.art/callback