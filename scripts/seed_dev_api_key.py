import asyncio
import hashlib
from api.db import db_client
from api.db.models import OrganizationModel, UserModel, APIKeyModel

async def seed():
    # Force DB init
    
    raw_key = "sk_dograh_local_dev_key"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    
    async with db_client.async_session() as session:
        # Create a dummy internal user if none exists
        from sqlalchemy.future import select
        res = await session.execute(select(UserModel).where(UserModel.id == 1))
        user = res.scalars().first()
        if not user:
            user = UserModel(id=1, provider_id="internal-system", is_superuser=True, email="internal@dograh.local")
            session.add(user)
            await session.commit()
            
        # Create a dummy org
        res = await session.execute(select(OrganizationModel).where(OrganizationModel.id == 1))
        org = res.scalars().first()
        if not org:
            org = OrganizationModel(id=1, provider_id="internal-org")
            session.add(org)
            await session.commit()
            
        # Insert the API key if not exists
        res = await session.execute(select(APIKeyModel).where(APIKeyModel.key_hash == key_hash))
        api_key = res.scalars().first()
        if not api_key:
            api_key = APIKeyModel(
                organization_id=1,
                name="Internal Dev Key",
                key_hash=key_hash,
                key_prefix=key_prefix,
                created_by=1,
                is_active=True
            )
            session.add(api_key)
            await session.commit()
            print("Successfully seeded sk_dograh_local_dev_key into database!")
        else:
            print("API Key already exists in database.")
            
if __name__ == "__main__":
    asyncio.run(seed())
