import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from app.config import settings

async def fetch_and_push():
    # 1. Handle the 365-day limit automatically
    fetch_days = min(settings.DAYS_TO_FETCH, 365)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=fetch_days)
    
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())

    print(f"🚀 Fetching last {fetch_days} days for {settings.COIN_GECKO_ID}...")

    # 2. Setup CoinGecko Request
    gecko_url = f"https://api.coingecko.com/api/v3/coins/{settings.COIN_GECKO_ID}/market_chart/range"
    params = {"vs_currency": "usd", "from": start_ts, "to": end_ts}
    headers = {
        "x-cg-demo-api-key": settings.COINGECKO_API_KEY,
        "accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # A. Get Data from CoinGecko
        resp = await client.get(gecko_url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Gecko Error: {resp.status_code} - {resp.text}")
            return
        
        data = resp.json()
        prices = data.get("prices", [])
        print(f"✅ Received {len(prices)} price points.")

        # B. Find the Coin ID in your local Database (Dynamic Lookup)
        print(f"🔍 Looking up XRP in local database at {settings.API_CORE_URL}/coins/...")
        coin_list_resp = await client.get(f"{settings.API_CORE_URL}/coins/")
        
        # Check if the local API actually returned a 200 OK
        if coin_list_resp.status_code != 200:
            print(f"❌ Local API Error: {coin_list_resp.status_code}")
            print(f"📝 Response content: {coin_list_resp.text}")
            return

        coins = coin_list_resp.json()
        
        # Check if 'coins' is actually a list as expected
        if not isinstance(coins, list):
            print(f"❌ Expected a list of coins, but got: {type(coins)}")
            print(f"📝 Content: {coins}")
            return
        
        target = next((c for c in coins if c.get('symbol', '').upper() == settings.COIN_GECKO_ID.upper()), None)
        
        if not target:
            print("❌ Error: XRP not found in local DB. Create it via Swagger (Port 8000) first!")
            return
        
        coin_id = target['id']

        # C. Format for your API Core
        payload = [
            {
                "price": p[1], 
                "timestamp": datetime.fromtimestamp(p[0]/1000, tz=timezone.utc).isoformat(),
                "coin_id": coin_id
            } 
            for p in prices
        ]
        
        # D. Push to your local API
        print(f"📤 Pushing to local API (Coin ID: {coin_id})...")
        post_resp = await client.post(
            f"{settings.API_CORE_URL}/coins/{coin_id}/prices/bulk", 
            json=payload, 
            timeout=60.0
        )
        
        if post_resp.status_code == 200:
            print("🎉 Success! Your database is updated.")
        else:
            print(f"❌ API Core Error: {post_resp.status_code} - {post_resp.text}")

if __name__ == "__main__":
    asyncio.run(fetch_and_push())