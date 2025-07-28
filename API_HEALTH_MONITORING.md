# API Health Monitoring

The Marine Weather integration now includes comprehensive API health monitoring to ensure reliable operation and provide visibility into API performance.

## Features

### Real-time Health Monitoring
- **Continuous Monitoring**: The integration performs health checks every 5 minutes (configurable)
- **Health Status Tracking**: Reports health status as Healthy, Degraded, Unhealthy, or Unknown
- **Performance Metrics**: Tracks response times, success rates, and error counts

### Health Status Definitions
- **Healthy**: API responding normally with good performance
- **Degraded**: API responding but with slow response times or occasional failures  
- **Unhealthy**: API experiencing consistent failures or timeouts
- **Unknown**: Health status not yet determined

### Health Sensor
A dedicated sensor (`sensor.open_meteo_marine_weather_api_health`) provides:
- Current health status in the sensor state
- Detailed metrics in sensor attributes:
  - Success rate percentage
  - Average response time
  - Last successful/failed check times
  - Consecutive failure/success counts
  - Total checks performed

### Smart Request Handling
- **Intelligent Throttling**: Skips API requests when the API is unhealthy to reduce load
- **Graceful Degradation**: Maintains last known good sensor values during API issues
- **Automatic Recovery**: Resumes normal operation when API health improves

## Services

### Health Check Service
Manual health check can be triggered via the service:
```yaml
service: open_meteo_marine_weather.health_check
```

This performs an immediate health check and fires an event with results.

### Cleanup Service  
```yaml
service: open_meteo_marine_weather.cleanup
```
Manually cleanup resources and HTTP sessions.

### Reload Service
```yaml
service: open_meteo_marine_weather.reload  
```
Reload the entire integration.

## Events

The integration fires the following events:

### API Health Status Changed
Fired when the API health status changes:
```yaml
event_type: open_meteo_marine_weather_api_health_status_changed
event_data:
  old_status: "healthy"
  new_status: "degraded"
  metrics:
    status: "degraded"
    success_rate: 95.5
    average_response_time: 2.34
    # ... other metrics
```

### Manual Health Check Completed
Fired after a manual health check:
```yaml
event_type: open_meteo_marine_weather_manual_health_check_completed  
event_data:
  is_healthy: true
  metrics:
    status: "healthy"
    # ... metrics
```

## Configuration

Health monitoring is automatically enabled and uses these default settings:

- **Check Interval**: 300 seconds (5 minutes)
- **Request Timeout**: 10 seconds  
- **Failure Threshold**: 3 consecutive failures trigger "unhealthy" status
- **Recovery Threshold**: 2 consecutive successes restore "healthy" status

## Diagnostics Integration

Health monitoring data is included in the integration's diagnostic information, accessible through Home Assistant's diagnostics download feature. This includes:

- Current API health status and metrics
- Sensor states and availability
- Resource usage statistics
- Historical performance data

## Troubleshooting

### View Current Health Status
Check the `sensor.open_meteo_marine_weather_api_health` entity for current status.

### Manual Health Check
Use the `open_meteo_marine_weather.health_check` service to perform immediate checks.

### Check Logs
Enable debug logging to see detailed health check information:
```yaml
logger:
  logs:
    custom_components.open_meteo_marine_weather: debug
```

The health monitoring system helps ensure the integration operates reliably and provides early warning of API issues.
