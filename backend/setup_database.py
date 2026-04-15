import asyncio
import os
from database import engine, Base, AsyncSessionLocal
from models.security import User, AuthorizedCert
from sqlalchemy import select

async def setup():
    print("⏳ Creating tables in Render...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("⏳ Seeding Sarah...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if sarah already exists
            stmt = select(User).where(User.username == 'sarah')
            res = await session.execute(stmt)
            existing_user = res.scalar_one_or_none()
            
            if not existing_user:
                u = User(username='sarah', email='sarah@gridco.local', full_name='Sarah Engineer')
                session.add(u)
                await session.flush()
                user_id = u.id
            else:
                user_id = existing_user.id
                print("  (User sarah already exists)")
            
            # Seed cert
            fingerprint = 'a1c13612ff348aa51e6410bfd791de93669c73efa90414199b1bd9bb399e9306'
            stmt_cert = select(AuthorizedCert).where(AuthorizedCert.fingerprint_sha256 == fingerprint)
            res_cert = await session.execute(stmt_cert)
            if not res_cert.scalar_one_or_none():
                cert = AuthorizedCert(
                    user_id=user_id, 
                    fingerprint_sha256=fingerprint, 
                    common_name='sarah@gridco.local'
                )
                session.add(cert)
                print("  (Cert seeded)")
            else:
                print("  (Cert already exists)")
                
            await session.commit()
            print("✅ Database is ready!")
        except Exception as e:
            print(f"❌ Setup error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(setup())
