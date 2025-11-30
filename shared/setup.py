"""
Setup script for nexus_lib shared library
"""
from setuptools import setup, find_packages

setup(
    name="nexus_lib",
    version="1.0.0",
    description="Shared library for Nexus Multi-Agent Release Automation System",
    author="Nexus Team",
    author_email="nexus@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # Core
        "pydantic>=2.0.0",
        "httpx>=0.25.0",
        "tenacity>=8.2.0",
        
        # FastAPI/Web
        "fastapi>=0.104.0",
        "starlette>=0.27.0",
        
        # Auth
        "PyJWT>=2.8.0",
        
        # Observability
        "prometheus-client>=0.18.0",
        "opentelemetry-api>=1.21.0",
        "opentelemetry-sdk>=1.21.0",
        "opentelemetry-exporter-otlp-proto-grpc>=1.21.0",
        "opentelemetry-instrumentation-fastapi>=0.42b0",
        "opentelemetry-instrumentation-httpx>=0.42b0",
        "opentelemetry-propagator-b3>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.6.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

