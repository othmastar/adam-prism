"""API Server — re-export from adam package"""
import os
# Full server (91 routes) in production, minimal (9 routes) in dev
if os.environ.get("ADAM_PRODUCTION", "0") == "1":
    from adam.api.server import create_app  # noqa
else:
    from adam.api.server_minimal import create_app  # noqa
