import asyncio
import aiomysql
import os
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'db': os.getenv('DB_NAME', 'tph_database'),
    'autocommit': True,
    'charset': 'utf8mb4'
}

# Global connection pool
pool = None

async def init_db():
    """Initialize database connection pool"""
    global pool
    try:
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            autocommit=DB_CONFIG['autocommit'],
            charset=DB_CONFIG['charset'],
            minsize=1,
            maxsize=10
        )
        print(f"✅ Database connection pool initialized")
        print(f"🔗 Connected to: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db']}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {str(e)}")
        print("📝 Database configuration:")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Port: {DB_CONFIG['port']}")
        print(f"   User: {DB_CONFIG['user']}")
        print(f"   Database: {DB_CONFIG['db']}")
        return False

async def close_db():
    """Close database connection pool"""
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        print("✅ Database connection pool closed")

@asynccontextmanager
async def get_db_connection():
    """Get database connection from pool"""
    if not pool:
        raise Exception("Database pool not initialized. Call init_db() first.")
    
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

async def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute SELECT query and return results as list of dictionaries"""
    try:
        async with get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                
                result = await cursor.fetchall()
                return result if result else []
                
    except Exception as e:
        print(f"❌ Database query error: {str(e)}")
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        raise Exception(f"Database query failed: {str(e)}")

async def execute_single_query(query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """Execute SELECT query and return single result as dictionary"""
    try:
        async with get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                
                result = await cursor.fetchone()
                return result
                
    except Exception as e:
        print(f"❌ Database query error: {str(e)}")
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        raise Exception(f"Database query failed: {str(e)}")

async def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """Execute INSERT/UPDATE/DELETE query and return affected rows"""
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                if params:
                    result = await cursor.execute(query, params)
                else:
                    result = await cursor.execute(query)
                
                return result
                
    except Exception as e:
        print(f"❌ Database update error: {str(e)}")
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        raise Exception(f"Database update failed: {str(e)}")

async def test_connection():
    """Test database connection"""
    try:
        await init_db()
        
        # Test query
        result = await execute_query("SELECT 1 as test")
        print(f"✅ Database connection test successful: {result}")
        
        # Check if TPH table exists
        table_check = await execute_query("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'tph'
        """, (DB_CONFIG['db'],))
        
        if table_check[0]['count'] > 0:
            print("✅ TPH table exists")
            
            # Check TPH table structure
            columns = await execute_query("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = 'tph'
                ORDER BY ordinal_position
            """, (DB_CONFIG['db'],))
            
            print("📋 TPH table columns:")
            for col in columns:
                print(f"   - {col['column_name']} ({col['data_type']})")
                
            # Sample data count
            count_result = await execute_query("SELECT COUNT(*) as total FROM tph WHERE status = 1")
            print(f"📊 Active TPH records: {count_result[0]['total']}")
            
        else:
            print("⚠️ TPH table does not exist. Please create the table first.")
            print("📝 Expected table structure:")
            print("""
            CREATE TABLE tph (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nomor INT,
                dept_abbr VARCHAR(10),
                divisi_abbr VARCHAR(10),
                blok_kode VARCHAR(15),
                lat DECIMAL(10,8),
                lon DECIMAL(11,8),
                kode_tph VARCHAR(50),
                status TINYINT DEFAULT 1,
                display_order INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
            """)
        
        await close_db()
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")
        return False

# Environment variables helper
def setup_env_example():
    """Print example environment variables"""
    print("📝 Environment Variables Example:")
    print("Create a .env file or set these environment variables:")
    print("")
    print("DB_HOST=localhost")
    print("DB_PORT=3306")
    print("DB_USER=your_username")
    print("DB_PASSWORD=your_password")
    print("DB_NAME=tph_database")
    print("")

if __name__ == "__main__":
    # Run database test
    asyncio.run(test_connection()) 