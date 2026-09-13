"""Vercel serverless entry point — wraps FastAPI with Mangum for AWS Lambda."""

from mangum import Mangum
from app.main import app

handler = Mangum(app)
