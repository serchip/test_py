from fastapi import APIRouter, Depends

from .balance import router as segments_router
from .auth import router as auth_router

router = APIRouter()

router.include_router(segments_router,
                      prefix="/balances",
                      tags=["balances"],
                      )
router.include_router(auth_router,
                      prefix="/auth",
                      tags=["auth"],
                      )
