"""
Monitoring Metrics Module
"""

from prometheus_client import Counter, Gauge, Histogram

# API Metrics
API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status"],
)

API_REQUEST_SIZE = Histogram(
    "api_request_size_bytes",
    "API request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
)

API_RESPONSE_SIZE = Histogram(
    "api_response_size_bytes",
    "API response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
)

# System Metrics
SYSTEM_CPU = Gauge("system_cpu_percent", "System CPU usage percentage", ["type"])

SYSTEM_MEMORY = Gauge("system_memory_bytes", "System memory usage in bytes", ["type"])

# Task Metrics
TASK_COUNT = Counter("task_count_total", "Total number of tasks", ["status"])

TASK_DURATION = Histogram(
    "task_duration_seconds", "Task execution duration in seconds", ["type"]
)

TASK_QUEUE_SIZE = Gauge("task_queue_size", "Number of tasks in queue", ["queue"])

# Sync Metrics
SYNC_COUNT = Counter("sync_count_total", "Total number of synchronizations", ["status"])

SYNC_DURATION = Histogram(
    "sync_duration_seconds", "Synchronization duration in seconds", ["type"]
)

SYNC_DATA_SIZE = Histogram(
    "sync_data_size_bytes",
    "Synchronization data size in bytes",
    ["type"],
    buckets=[1000, 10000, 100000, 1000000, 10000000],
)

# Node Metrics
NODE_STATUS = Gauge("node_status", "Node status (1=up, 0=down)", ["node_id", "role"])

NODE_LATENCY = Histogram(
    "node_latency_seconds",
    "Node communication latency in seconds",
    ["node_id", "operation"],
)

# Security Metrics
AUTH_FAILURES = Counter(
    "auth_failures_total", "Total number of authentication failures", ["reason"]
)

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total", "Total number of rate limit hits", ["client_ip"]
)

# Database Metrics
DB_CONNECTION_POOL = Gauge(
    "db_connection_pool_size", "Database connection pool size", ["status"]
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds", "Database query duration in seconds", ["operation"]
)

DB_TRANSACTION_COUNT = Counter(
    "db_transaction_count_total", "Total number of database transactions", ["status"]
)

# Cache Metrics
CACHE_HIT_COUNT = Counter(
    "cache_hit_count_total", "Total number of cache hits", ["cache"]
)

CACHE_MISS_COUNT = Counter(
    "cache_miss_count_total", "Total number of cache misses", ["cache"]
)

CACHE_SIZE = Gauge("cache_size_bytes", "Cache size in bytes", ["cache"])
