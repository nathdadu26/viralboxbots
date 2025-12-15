#!/bin/sh

echo "🚀 Starting all Telegram bots..."

python uploader.py &
python converter.py &
python fileserver.py &

wait
