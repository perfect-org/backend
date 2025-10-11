from dataclasses import dataclass
from decimal import Decimal
from typing import List

from app.exceptions.service_errors import (
    EntityNotFound,
    ServiceError,
    OrderAtWorkError,
    EntityAlreadyExistsError,
)

from app.repositories import (
    OrderRepository,
    ProductRepository,
    OrderItemRepository,
    PromoRepository,
)
from app.schemas import (
    OrderOut,
    OrderStatus,
    OrderItemCreate,
    PromoCreate,
    PromoOut,
)


@dataclass(kw_only=True, frozen=True, slots=True)
class OrderService:
    order_repository: OrderRepository
    order_item_repository: OrderItemRepository
    promo_repository: PromoRepository
    product_repository: ProductRepository

    async def get_active_cart(self, user_id: int) -> OrderOut:
        order = await self.order_repository.get_pending_order(user_id)
        if not order:
            order_data = {
                "user_id": user_id,
                "status": OrderStatus.PENDING,
                "total_amount": 0,
            }
            order = await self.order_repository.create(order_data)
        return OrderOut.model_validate(order)

    async def get_confirmed_cart(self, user_id: int) -> List[OrderOut]:
        list_orders = await self.order_repository.get_confirmed_orders(user_id)
        if not list_orders:
            raise EntityNotFound("Подтвержденных заказов не найдено")
        return [OrderOut.model_validate(order) for order in list_orders]

    async def modify_cart_item(
        self,
        user_id: int,
        product_id: int,
        action: str = "add",  # "add" | "remove" | "remove_all" | "set"
        quantity: int = 1,
    ) -> OrderOut:
        order = await self.get_active_cart(user_id)

        if order.status != OrderStatus.PENDING:
            raise OrderAtWorkError(
                f"Заказ {order.id} имеет статус {order.status}"
            )

        if action not in ("remove", "remove_all"):
            product = await self.product_repository.get_by_id(product_id)
            if not product:
                raise EntityNotFound("Продукт не найден")

        if action in ("remove", "remove_all"):
            if not any(item.product_id == product_id for item in order.items):
                raise EntityNotFound(
                    f"Товар {product_id} отсутствует в корзине"
                )

        updated_items = []
        item_found = False

        for item in order.items:
            if item.product_id == product_id:
                item_found = True
                new_quantity = item.quantity

                if action == "add":
                    new_quantity += quantity
                elif action == "remove":
                    new_quantity = max(0, item.quantity - quantity)
                elif action == "remove_all":
                    new_quantity = 0
                elif action == "set":
                    new_quantity = max(0, quantity)
                else:
                    raise ValueError(f"Неизвестное действие: {action}")

                if new_quantity > 0:
                    updated_items.append(
                        {
                            "id": item.id,
                            "product_id": item.product_id,
                            "quantity": new_quantity,
                        }
                    )
            else:
                updated_items.append(
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                    }
                )

        if not item_found and action == "add":
            updated_items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            )

        product_ids = {item["product_id"] for item in updated_items}
        products = await self.product_repository.get_by_ids(list(product_ids))
        products_map = {p.id: p for p in products}

        missing_ids = product_ids - products_map.keys()
        if missing_ids:
            raise EntityNotFound(f"Товары с id {missing_ids} не найдены")

        total_amount = sum(
            item["quantity"] * products_map[item["product_id"]].price
            for item in updated_items
        )

        updated_order = await self.order_repository.update_cart(
            order_id=order.id,
            items=updated_items,
            total_amount=total_amount,
        )

        return OrderOut.model_validate(updated_order)

    async def apply_promo_to_order(
        self, user_id: int, promo_code: str
    ) -> OrderOut:
        order = await self.order_repository.get_pending_order(user_id)

        if not order or not order.items:
            raise EntityNotFound("Корзина пуста или не найдена")

        if order.status != OrderStatus.PENDING:
            raise OrderAtWorkError(
                f"Нельзя применить промокод. Заказ {order.id} имеет статус {order.status}"
            )

        promo = await self.promo_repository.get_by_code(promo_code)

        if not promo or not promo.is_available:
            raise EntityNotFound(
                f"Промокод '{promo_code}' не существует или недоступен"
            )

        discount_percent = Decimal(promo.discount_percent) / Decimal(100)
        discounted_total = order.total_amount * (Decimal(1) - discount_percent)

        update_data = {
            "total_amount": discounted_total,
            "promo_id": promo.id,
        }

        updated_order = await self.order_repository.update(order, update_data)
        await self.promo_repository.update(promo, {"is_available": False})

        return OrderOut.model_validate(updated_order)

    async def confirm_order(self, user_id: int) -> OrderOut:
        order = await self.order_repository.get_pending_order(user_id)

        if not order or not order.items:
            raise EntityNotFound("Корзина пуста или не найдена")

        if order.status != OrderStatus.PENDING:
            raise OrderAtWorkError(
                f"Вы не можете подтвердить заказ. Заказ {order.id} имеет статус {order.status}"
            )

        updated_order = await self.order_repository.update(
            order, {"status": OrderStatus.CONFIRMED}
        )
        return OrderOut.model_validate(updated_order)

    async def clear_cart(self, user_id: int) -> OrderOut:

        try:
            order = await self.order_repository.get_pending_order(user_id)
            if not order:
                raise EntityNotFound("Корзина не найдена")

            if order.status != OrderStatus.PENDING:
                raise OrderAtWorkError(
                    f"Заказ {order.id} имеет статус {order.status}"
                )

            await self.order_item_repository.delete_by_order_id(order.id)

            updated_order = await self.order_repository.update(
                order, {"total_amount": 0, "promo_id": None}
            )
            await self.order_repository.db.refresh(updated_order)

            return OrderOut.model_validate(updated_order)

        except Exception as e:
            raise ServiceError("Ошибка очистки корзины", e)

    async def promo_create(self, promo_data: PromoCreate) -> PromoOut:
        if await self.promo_repository.get_by_code(promo_data.code):
            raise EntityAlreadyExistsError("Такой Промокод уже существует")
        res = await self.promo_repository.create(promo_data.model_dump())
        return PromoOut.model_validate(res)

    async def promo_delete(self, promo_id: int) -> None:
        promo = await self.promo_repository.get_by_id(promo_id)

        if not promo:
            raise EntityNotFound(f"Промокод с id {promo_id} не найден")

        await self.promo_repository.delete(promo_id)

    async def get_all_promos(self) -> List[PromoOut]:
        list_promos = await self.promo_repository.get_all()
        if not list_promos:
            raise EntityNotFound("Список промокодов пуст")
        return [PromoOut.model_validate(promo) for promo in list_promos]
