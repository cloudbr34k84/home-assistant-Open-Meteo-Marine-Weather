DOMAIN = "open_meteo_marine_weather"
API_URL = "https://marine-api.open-meteo.com/v1/marine"
PLATFORMS = ["sensor"]

# API Health Check Configuration
API_HEALTH_CHECK_INTERVAL = 300  # 5 minutes
API_HEALTH_CHECK_TIMEOUT = 10    # 10 seconds
API_HEALTH_CHECK_ENDPOINT = "https://marine-api.open-meteo.com/v1/marine"
API_HEALTH_CONSECUTIVE_FAILURES_THRESHOLD = 3
API_HEALTH_RECOVERY_THRESHOLD = 2

# Health Status Constants
HEALTH_STATUS_HEALTHY = "healthy"
HEALTH_STATUS_DEGRADED = "degraded"
HEALTH_STATUS_UNHEALTHY = "unhealthy"
HEALTH_STATUS_UNKNOWN = "unknown"