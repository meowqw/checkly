"""API v1."""
from fastapi import APIRouter

from app.api.v1 import accounts, auth, categories, receipts, transactions

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(categories.router)
api_router.include_router(transactions.router)
api_router.include_router(receipts.router)
