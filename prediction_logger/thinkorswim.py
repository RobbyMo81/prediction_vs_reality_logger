import asyncio
import json
import websockets
import logging
from .config import load_config
from pathlib import Path


async def _connect():
    cfg = load_config()
    host = cfg['thinkorswim']['host']
    port = cfg['thinkorswim']['port']
    use_ssl = cfg['thinkorswim']['use_ssl']
    scheme = 'wss' if use_ssl else 'ws'
    uri = f"{scheme}://{host}:{port}"
    try:
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"action": "subscribe", "symbols": ["NQ"]}))
            async for msg in ws:
                data = json.loads(msg)
                logging.debug(f"Received market data: {data}")
    except Exception as e:
        logging.error(f"Thinkorswim socket error: {e}")


def run_socket():
    try:
        asyncio.run(_connect())
    except Exception as e:
        logging.critical(f"Socket run failed: {e}")