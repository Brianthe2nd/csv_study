import json
import random
import time

# Generate example trader data
trader_id = "example"
trades_data = {
    trader_id: {
        "active": {},
        "unknown": {},
        "rejected": {},
        "config": {
            "ignore": True,
            "ignore_pairs": ["EURUSD"],  # example ignored pair
            "only_pairs": ["GBPUSD", "USDJPY"],  # example whitelist
            "use_custom_risk": True,
            "custom_risk": 0.02  # 2% risk
        }
    }
}

# Optionally add a dummy active trade
pair_name = random.choice(["GBPUSD", "USDJPY"])
trades_data[trader_id]["active"][pair_name] = {
    "trade_type": random.choice(["buy", "sell"]),
    "open_time": time.time(),
    "sl": True,
    "tp": True,
    "status": "open"
}

# Save to JSON file
with open("trades_data.json", "w") as f:
    json.dump(trades_data, f, indent=4)

print(f"✅ Created trades_data.json with trader '{trader_id}'")
