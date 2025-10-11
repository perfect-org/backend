from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import Gender
from app.models import Product, Tag
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    async def create_product(
        self,
        prod_data: dict,
        tag_ids: List[int] | None = None,
    ) -> Product:

        product = Product(**prod_data)
        self.db.add(product)

        if tag_ids:
            tags = await self._get_related_objects(Tag, tag_ids)
            product.tags.extend(tags)

        try:
            await self.db.commit()
            await self.db.refresh(product, ["tags"])
            return product
        except Exception as e:
            await self.db.rollback()
            raise e

    async def deactivate_product(self, product: Product) -> None:
        try:
            product.is_active = False
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def activate_product(self, product: Product) -> None:
        try:
            product.is_active = True
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_all_products(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[Product]:
        query = select(self.model).offset(skip).limit(limit)

        if "name" in filters and filters["name"]:
            query = query.where(self.model.name.ilike(f"%{filters['name']}%"))

        if "min_price" in filters and filters["min_price"] is not None:
            query = query.where(self.model.price >= filters["min_price"])

        if "max_price" in filters and filters["max_price"] is not None:
            query = query.where(self.model.price <= filters["max_price"])

        if "min_age" in filters and filters["min_age"] is not None:
            query = query.where(self.model.min_age >= filters["min_age"])

        if "gender" in filters and filters["gender"]:
            if filters["gender"] != Gender.ANY:
                query = query.where(self.model.gender == filters["gender"])

        if "is_active" in filters and filters["is_active"] is not None:
            query = query.where(self.model.is_active == filters["is_active"])

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_ids(self, ids: List[int]) -> List[Product]:
        if not ids:
            return []

        result = await self.db.execute(
            select(Product).where(Product.id.in_(ids))
        )
        return list(result.scalars().all())
