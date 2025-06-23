#!/usr/bin/env python3
"""
Simple Database Test for TPH
Just test connection and run basic query
"""

import asyncio
from db import init_db, close_db, execute_query

async def test_simple():
    """Simple database test"""
    print("🔗 Testing database connection...")
    
    try:
        # Initialize database
        success = await init_db()
        if not success:
            print("❌ Failed to connect to database")
            return
            
        print("✅ Database connected successfully")
        
        # Run the simple query user requested
        print("\n📋 Running query: SELECT * FROM tph ORDER BY id DESC LIMIT 100")
        
        results = await execute_query("""
            SELECT * FROM tph 
            ORDER BY id DESC 
            LIMIT 100
        """)
        
        print(f"✅ Query returned {len(results)} records")
        
        if results:
            print("\n📊 Results:")
            print("-" * 80)
            
            # Show first few records
            for i, row in enumerate(results[:10]):  # Show max 10 records
                print(f"ID: {row.get('id', 'N/A')} | "
                      f"Nomor: {row.get('nomor', 'N/A')} | "
                      f"Dept: {row.get('dept_abbr', 'N/A')} | "
                      f"Divisi: {row.get('divisi_abbr', 'N/A')} | "
                      f"Blok: {row.get('blok_kode', 'N/A')} | "
                      f"Lat: {row.get('lat', 'N/A')} | "
                      f"Lon: {row.get('lon', 'N/A')} | "
                      f"Update Date: {row.get('update_date', 'N/A')} | "
                      f"TPH: {row.get('kode_tph', 'N/A')}")
                
            
            if len(results) > 10:
                print(f"... and {len(results) - 10} more records")
        else:
            print("⚠️ No data found in TPH table")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    finally:
        await close_db()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_simple())
