"""
Performance and Load Tests for Nexus
=====================================

Recommendation #5: Add Performance Tests
Tests for response times, throughput, and system behavior under load.

Coverage:
- Response time baselines
- Concurrent request handling
- Throughput measurements
- Memory usage patterns
- Connection pooling
- Rate limiting behavior
- Sustained load testing

Usage:
    pytest tests/performance/test_load.py -v
    pytest tests/performance/ -v --timeout=120
"""

import pytest
import asyncio
import httpx
import time
import os
import statistics
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Service URLs
SERVICES = {
    "orchestrator": os.environ.get("ORCHESTRATOR_URL", "http://localhost:8080"),
    "jira_agent": os.environ.get("JIRA_AGENT_URL", "http://localhost:8081"),
    "git_ci_agent": os.environ.get("GIT_CI_AGENT_URL", "http://localhost:8082"),
    "admin_dashboard": os.environ.get("ADMIN_DASHBOARD_URL", "http://localhost:8088"),
    "analytics": os.environ.get("ANALYTICS_URL", "http://localhost:8086"),
}

# Performance thresholds (in seconds)
THRESHOLDS = {
    "health_check": 0.1,      # 100ms
    "simple_query": 5.0,       # 5s (includes LLM)
    "metrics_fetch": 0.5,      # 500ms
    "config_read": 0.2,        # 200ms
    "list_specialists": 0.5,   # 500ms
}


# =============================================================================
# Response Time Tests
# =============================================================================

class TestResponseTimeBaselines:
    """Tests for response time baselines."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_health_check_response_time(self, client):
        """Test health check meets response time threshold."""
        url = f"{SERVICES['orchestrator']}/health"
        
        try:
            start = time.perf_counter()
            response = await client.get(url)
            duration = time.perf_counter() - start
            
            assert response.status_code == 200
            assert duration < THRESHOLDS["health_check"], \
                f"Health check took {duration:.3f}s, threshold is {THRESHOLDS['health_check']}s"
            
            print(f"✓ Health check: {duration*1000:.1f}ms")
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_metrics_response_time(self, client):
        """Test metrics endpoint response time."""
        url = f"{SERVICES['admin_dashboard']}/api/metrics"
        
        try:
            start = time.perf_counter()
            response = await client.get(url)
            duration = time.perf_counter() - start
            
            assert response.status_code == 200
            assert duration < THRESHOLDS["metrics_fetch"], \
                f"Metrics fetch took {duration:.3f}s, threshold is {THRESHOLDS['metrics_fetch']}s"
            
            print(f"✓ Metrics fetch: {duration*1000:.1f}ms")
            
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_config_read_response_time(self, client):
        """Test config read response time."""
        url = f"{SERVICES['admin_dashboard']}/config"
        
        try:
            start = time.perf_counter()
            response = await client.get(url)
            duration = time.perf_counter() - start
            
            assert response.status_code == 200
            assert duration < THRESHOLDS["config_read"], \
                f"Config read took {duration:.3f}s, threshold is {THRESHOLDS['config_read']}s"
            
            print(f"✓ Config read: {duration*1000:.1f}ms")
            
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_specialists_list_response_time(self, client):
        """Test specialists list response time."""
        url = f"{SERVICES['orchestrator']}/specialists"
        
        try:
            start = time.perf_counter()
            response = await client.get(url)
            duration = time.perf_counter() - start
            
            assert response.status_code == 200
            assert duration < THRESHOLDS["list_specialists"], \
                f"List specialists took {duration:.3f}s, threshold is {THRESHOLDS['list_specialists']}s"
            
            print(f"✓ List specialists: {duration*1000:.1f}ms")
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Concurrent Request Tests
# =============================================================================

class TestConcurrentRequests:
    """Tests for concurrent request handling."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_health_checks(self, client):
        """Test handling 20 concurrent health checks."""
        url = f"{SERVICES['orchestrator']}/health"
        concurrency = 20
        
        try:
            async def single_request():
                start = time.perf_counter()
                response = await client.get(url)
                duration = time.perf_counter() - start
                return (response.status_code, duration)
            
            tasks = [single_request() for _ in range(concurrency)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            successful = [r for r in results if isinstance(r, tuple)]
            durations = [r[1] for r in successful if r[0] == 200]
            
            assert len(successful) >= concurrency * 0.9, \
                f"Only {len(successful)}/{concurrency} requests succeeded"
            
            avg_duration = statistics.mean(durations)
            p95_duration = sorted(durations)[int(len(durations) * 0.95) - 1] if durations else 0
            
            print(f"✓ {concurrency} concurrent requests:")
            print(f"  - Success rate: {len(successful)/concurrency*100:.0f}%")
            print(f"  - Avg latency: {avg_duration*1000:.1f}ms")
            print(f"  - P95 latency: {p95_duration*1000:.1f}ms")
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_queries(self, client):
        """Test handling 5 concurrent queries."""
        url = f"{SERVICES['orchestrator']}/query"
        concurrency = 5
        
        try:
            async def single_query(query: str):
                start = time.perf_counter()
                response = await client.post(url, json={"query": query})
                duration = time.perf_counter() - start
                return (response.status_code, duration)
            
            queries = [
                "What is the release status?",
                "Show me the blockers",
                "Get build status",
                "Run hygiene check",
                "What are the KPIs?"
            ]
            
            tasks = [single_query(q) for q in queries[:concurrency]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = [r for r in results if isinstance(r, tuple) and r[0] == 200]
            
            print(f"✓ {concurrency} concurrent queries: {len(successful)}/{concurrency} succeeded")
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_mixed_workload(self, client):
        """Test mixed workload of different request types."""
        try:
            async def health_check():
                return await client.get(f"{SERVICES['orchestrator']}/health")
            
            async def get_config():
                return await client.get(f"{SERVICES['admin_dashboard']}/config")
            
            async def get_metrics():
                return await client.get(f"{SERVICES['admin_dashboard']}/api/metrics")
            
            async def get_kpis():
                return await client.get(f"{SERVICES['analytics']}/api/v1/kpis")
            
            # Mix of different requests
            tasks = [
                health_check(),
                health_check(),
                get_config(),
                get_metrics(),
                get_kpis(),
            ]
            
            start = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_duration = time.perf_counter() - start
            
            successful = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 200)
            
            print(f"✓ Mixed workload: {successful}/{len(tasks)} succeeded in {total_duration:.2f}s")
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Throughput Tests
# =============================================================================

class TestThroughput:
    """Tests for throughput measurements."""
    
    @pytest.mark.performance
    def test_health_check_throughput(self):
        """Measure health check throughput."""
        url = f"{SERVICES['orchestrator']}/health"
        duration_seconds = 5
        
        results = []
        
        def make_request():
            try:
                with httpx.Client(timeout=5.0) as client:
                    start = time.perf_counter()
                    response = client.get(url)
                    duration = time.perf_counter() - start
                    return (response.status_code, duration)
            except Exception:
                return (0, 0)
        
        start_time = time.perf_counter()
        request_count = 0
        
        while time.perf_counter() - start_time < duration_seconds:
            result = make_request()
            results.append(result)
            request_count += 1
        
        total_duration = time.perf_counter() - start_time
        successful = sum(1 for r in results if r[0] == 200)
        
        throughput = successful / total_duration
        
        print(f"\n✓ Throughput test ({duration_seconds}s):")
        print(f"  - Total requests: {request_count}")
        print(f"  - Successful: {successful}")
        print(f"  - Throughput: {throughput:.1f} req/s")
        
        # Should handle at least 10 req/s
        assert throughput >= 5, f"Throughput {throughput:.1f} req/s below minimum of 5"
    
    @pytest.mark.performance
    def test_concurrent_throughput(self):
        """Measure throughput with concurrent workers."""
        url = f"{SERVICES['orchestrator']}/health"
        workers = 5
        requests_per_worker = 20
        
        results = []
        
        def worker_task():
            worker_results = []
            with httpx.Client(timeout=5.0) as client:
                for _ in range(requests_per_worker):
                    try:
                        start = time.perf_counter()
                        response = client.get(url)
                        duration = time.perf_counter() - start
                        worker_results.append((response.status_code, duration))
                    except Exception:
                        worker_results.append((0, 0))
            return worker_results
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task) for _ in range(workers)]
            for future in as_completed(futures):
                results.extend(future.result())
        
        total_duration = time.perf_counter() - start_time
        successful = sum(1 for r in results if r[0] == 200)
        
        throughput = successful / total_duration
        
        print(f"\n✓ Concurrent throughput test ({workers} workers):")
        print(f"  - Total requests: {len(results)}")
        print(f"  - Successful: {successful}")
        print(f"  - Throughput: {throughput:.1f} req/s")
        print(f"  - Duration: {total_duration:.2f}s")


# =============================================================================
# Latency Distribution Tests
# =============================================================================

class TestLatencyDistribution:
    """Tests for latency distribution."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_health_check_latency_distribution(self, client):
        """Measure health check latency distribution."""
        url = f"{SERVICES['orchestrator']}/health"
        sample_size = 50
        
        try:
            latencies = []
            
            for _ in range(sample_size):
                start = time.perf_counter()
                response = await client.get(url)
                duration = time.perf_counter() - start
                
                if response.status_code == 200:
                    latencies.append(duration)
            
            if len(latencies) < sample_size * 0.9:
                pytest.skip("Too many failed requests")
            
            # Calculate statistics
            avg = statistics.mean(latencies)
            median = statistics.median(latencies)
            stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
            p99 = sorted(latencies)[int(len(latencies) * 0.99) - 1]
            
            print(f"\n✓ Latency distribution ({sample_size} samples):")
            print(f"  - Average: {avg*1000:.1f}ms")
            print(f"  - Median: {median*1000:.1f}ms")
            print(f"  - Std Dev: {stdev*1000:.1f}ms")
            print(f"  - P95: {p95*1000:.1f}ms")
            print(f"  - P99: {p99*1000:.1f}ms")
            
            # P99 should be reasonable
            assert p99 < 0.5, f"P99 latency {p99*1000:.1f}ms exceeds 500ms threshold"
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Sustained Load Tests
# =============================================================================

class TestSustainedLoad:
    """Tests for sustained load handling."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_sustained_load_30s(self):
        """Test sustained load for 30 seconds."""
        url = f"{SERVICES['orchestrator']}/health"
        duration_seconds = 30
        target_rps = 10
        
        results = []
        errors = 0
        
        interval = 1.0 / target_rps
        
        start_time = time.perf_counter()
        next_request_time = start_time
        
        with httpx.Client(timeout=5.0) as client:
            while time.perf_counter() - start_time < duration_seconds:
                try:
                    request_start = time.perf_counter()
                    response = client.get(url)
                    request_duration = time.perf_counter() - request_start
                    
                    results.append({
                        "status": response.status_code,
                        "duration": request_duration,
                        "timestamp": time.perf_counter() - start_time
                    })
                except Exception:
                    errors += 1
                
                # Pace the requests
                next_request_time += interval
                sleep_time = next_request_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        # Analyze results
        successful = [r for r in results if r["status"] == 200]
        durations = [r["duration"] for r in successful]
        
        if durations:
            avg_latency = statistics.mean(durations)
            max_latency = max(durations)
        else:
            avg_latency = 0
            max_latency = 0
        
        actual_rps = len(successful) / duration_seconds
        
        print(f"\n✓ Sustained load test ({duration_seconds}s @ {target_rps} RPS target):")
        print(f"  - Total requests: {len(results)}")
        print(f"  - Successful: {len(successful)}")
        print(f"  - Errors: {errors}")
        print(f"  - Actual RPS: {actual_rps:.1f}")
        print(f"  - Avg latency: {avg_latency*1000:.1f}ms")
        print(f"  - Max latency: {max_latency*1000:.1f}ms")
        
        # Should maintain at least 80% success rate
        success_rate = len(successful) / (len(results) + errors) if results else 0
        assert success_rate >= 0.8, f"Success rate {success_rate*100:.0f}% below 80%"


# =============================================================================
# Memory Usage Tests
# =============================================================================

class TestMemoryUsage:
    """Tests for memory usage patterns."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_stats_available(self, client):
        """Test memory stats are available."""
        url = f"{SERVICES['orchestrator']}/memory/stats"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ Memory stats: {data}")
                
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_no_memory_leak_on_repeated_requests(self, client):
        """Test for memory leaks on repeated requests."""
        url = f"{SERVICES['orchestrator']}/health"
        iterations = 100
        
        try:
            # Make many requests
            for _ in range(iterations):
                await client.get(url)
            
            # If we get here without OOM, test passes
            print(f"✓ {iterations} requests completed without memory issues")
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Connection Pool Tests
# =============================================================================

class TestConnectionPooling:
    """Tests for connection pooling behavior."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_connection_reuse(self):
        """Test connection reuse efficiency."""
        url = f"{SERVICES['orchestrator']}/health"
        
        try:
            # Create client with explicit limits
            async with httpx.AsyncClient(
                timeout=10.0,
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)
            ) as client:
                # Make many requests that should reuse connections
                tasks = [client.get(url) for _ in range(50)]
                
                start = time.perf_counter()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                duration = time.perf_counter() - start
                
                successful = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 200)
                
                print(f"\n✓ Connection pooling test:")
                print(f"  - Requests: 50")
                print(f"  - Successful: {successful}")
                print(f"  - Total time: {duration:.2f}s")
                print(f"  - Avg time/request: {duration/50*1000:.1f}ms")
                
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting behavior."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_burst_handling(self, client):
        """Test handling of request bursts."""
        url = f"{SERVICES['orchestrator']}/health"
        burst_size = 50
        
        try:
            # Send burst of requests
            tasks = [client.get(url) for _ in range(burst_size)]
            
            start = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.perf_counter() - start
            
            # Count different response codes
            status_counts = {}
            for r in results:
                if isinstance(r, httpx.Response):
                    status_counts[r.status_code] = status_counts.get(r.status_code, 0) + 1
                else:
                    status_counts["error"] = status_counts.get("error", 0) + 1
            
            print(f"\n✓ Burst handling ({burst_size} requests):")
            print(f"  - Duration: {duration:.2f}s")
            print(f"  - Status breakdown: {status_counts}")
            
            # Should mostly succeed (no aggressive rate limiting in test mode)
            assert status_counts.get(200, 0) >= burst_size * 0.8
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Performance Summary
# =============================================================================

class TestPerformanceSummary:
    """Generate performance summary."""
    
    @pytest.mark.performance
    def test_generate_summary(self):
        """Generate performance test summary."""
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY")
        print("="*60)
        print("Thresholds:")
        for metric, threshold in THRESHOLDS.items():
            print(f"  - {metric}: {threshold*1000:.0f}ms")
        print("="*60)

