from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    BackgroundTasks,
)
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.schemas import OrderOut, UserOut
from app.services import OrderService, NotificationService
from app.api.dependencies import (
    get_order_service,
    get_current_user,
    get_notification_service,
)
from app.exceptions.service_errors import EntityNotFound, ServiceError

router = APIRouter()


@router.get(
    "/cart",
    response_model=OrderOut,
    summary="Получить содержимое корзины пользователя",
    status_code=status.HTTP_200_OK,
)
async def get_cart(
    current_user: UserOut = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.get_active_cart(current_user.id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get(
    "/",
    response_model=List[OrderOut],
    summary="Получить все заказы",
    responses={
        404: {"description": "Список заказов пуст"},
        200: {"description": "Успешное получение списка заказов"},
    },
)
async def get_all_orders(
    current_user: UserOut = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> List[OrderOut]:
    try:
        return await service.get_confirmed_cart(current_user.id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post(
    "/cart/items/{product_id}",
    response_model=OrderOut,
    summary="Управление товарами в корзине",
    responses={
        200: {"description": "Товар успешно обновлен/удален"},
        201: {"description": "Товар успешно добавлен"},
        400: {"description": "Неверный запрос"},
        404: {"description": "Товар не найден"},
    },
)
async def modify_cart(
    product_id: int,
    action: str = Query(
        default="add", description="Действие: add, remove или set"
    ),
    quantity: int = Query(
        default=1, description="Количество (требуется для add/set)"
    ),
    current_user: UserOut = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        result = await service.modify_cart_item(
            user_id=current_user.id,
            product_id=product_id,
            action=action,
            quantity=quantity,
        )

        status_code = (
            status.HTTP_201_CREATED if action == "add" else status.HTTP_200_OK
        )
        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=status_code,
        )

    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except (ServiceError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/cart/apply-promo",
    response_model=OrderOut,
    summary="Применить промокод к корзине",
    status_code=status.HTTP_200_OK,
)
async def apply_promo_to_cart(
    promo: str = Query(..., description="Промокод"),
    current_user: UserOut = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.apply_promo_to_order(current_user.id, promo)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post(
    "/cart/confirm",
    response_model=OrderOut,
    summary="Оформить заказ (подтвердить корзину)",
    status_code=status.HTTP_200_OK,
)
async def confirm_order(
    background_tasks: BackgroundTasks,
    current_user: UserOut = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
    notification_service: NotificationService = Depends(
        get_notification_service
    ),
):
    try:
        order = await service.confirm_order(current_user.id)

        background_tasks.add_task(
            notification_service.send_order_email, current_user.email, order
        )

        return order
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete(
    "/clear",
    response_model=OrderOut,
    summary="Очистить корзину",
    responses={
        200: {"description": "Корзина успешно очищена"},
        404: {"description": "Корзина не найдена"},
    },
)
async def clear_cart(
    current_user: UserOut = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.clear_cart(current_user.id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
