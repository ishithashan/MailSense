import os
from middleware.server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render gives PORT

    app.run(
        host="0.0.0.0",   # IMPORTANT
        port=port,
        debug=False
    )