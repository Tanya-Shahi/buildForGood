import os
import uvicorn

if __name__ == "__main__":
    # 1. Dynamically read the port assigned by Railway, defaulting to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    
    # 2. Automatically detect if running inside Railway to safely toggle reload
    is_production = os.environ.get("RAILWAY_ENVIRONMENT_NAME") is not None
    reload_setting = False if is_production else True

    print(f"📡 Booting server on port {port} (Production Mode: {is_production})")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_setting,
        workers=1
    )