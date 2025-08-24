from fastapi import APIRouter

from .auth import router as auth_router
from .user_form import router as user_form_router
from .product import router as product_router
from .order import router as order_router
from .admin.user import router as admin_user_router
from .admin.product import router as admin_product_router
from .admin.promo import router as admin_promo_router


main_router = APIRouter()

main_router.include_router(
    auth_router, prefix=f"/auth", tags=["Аутентификация"]
)
main_router.include_router(
    user_form_router, prefix=f"/user_form", tags=["Анкета"]
)
main_router.include_router(
    product_router, prefix=f"/product", tags=["Продукт"]
)
main_router.include_router(order_router, prefix=f"/order", tags=["Заказ"])
main_router.include_router(
    admin_user_router,
    prefix=f"/admin/user",
    tags=["Админка: Пользователь"],
)
main_router.include_router(
    admin_product_router,
    prefix=f"/admin/product",
    tags=["Админка: Продукт"],
)
main_router.include_router(
    admin_promo_router,
    prefix=f"/admin/promo",
    tags=["Админка: Промокод"],
)
