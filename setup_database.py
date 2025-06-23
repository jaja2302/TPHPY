#!/usr/bin/env python3
"""
Database Setup Script for TPH Route Optimizer API
This script helps set up and test the database connection.
"""

import asyncio
import os
from db import test_connection, setup_env_example

def create_env_file():
    """Create .env file with database configuration"""
    env_content = """# Database Configuration for TPH Route Optimizer
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=tph_database

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("📝 Please edit .env file with your database credentials")
    else:
        print("⚠️ .env file already exists")

def print_sql_schema():
    """Print SQL schema for TPH table"""
    print("\n📋 SQL Schema for TPH Table:")
    print("=" * 50)
    
    schema = """
CREATE DATABASE IF NOT EXISTS tph_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tph_database;

CREATE TABLE IF NOT EXISTS tph (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nomor INT NOT NULL,
    dept_abbr VARCHAR(10) NOT NULL,
    divisi_abbr VARCHAR(10) NOT NULL,
    blok_kode VARCHAR(15) NOT NULL,
    lat DECIMAL(10,8) NOT NULL,
    lon DECIMAL(11,8) NOT NULL,
    kode_tph VARCHAR(50),
    status TINYINT DEFAULT 1,
    display_order INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_dept_divisi_blok (dept_abbr, divisi_abbr, blok_kode),
    INDEX idx_status (status),
    INDEX idx_coordinates (lat, lon)
);

-- Sample data (optional)
INSERT INTO tph (nomor, dept_abbr, divisi_abbr, blok_kode, lat, lon, kode_tph) VALUES
(1, 'PKS', 'DIV1', 'BLK001', -2.123456, 110.654321, 'TPH001'),
(2, 'PKS', 'DIV1', 'BLK001', -2.124456, 110.655321, 'TPH002'),
(3, 'PKS', 'DIV1', 'BLK001', -2.125456, 110.656321, 'TPH003'),
(4, 'PKS', 'DIV2', 'BLK002', -2.126456, 110.657321, 'TPH004'),
(5, 'PKS', 'DIV2', 'BLK002', -2.127456, 110.658321, 'TPH005');
"""
    
    print(schema)
    print("=" * 50)

async def main():
    """Main setup function"""
    print("🚀 TPH Route Optimizer - Database Setup")
    print("=" * 50)
    
    # Create .env file
    create_env_file()
    
    # Show environment variables example
    print("\n📝 Environment Variables Configuration:")
    setup_env_example()
    
    # Print SQL schema
    print_sql_schema()
    
    # Test database connection
    print("🔗 Testing database connection...")
    if await test_connection():
        print("\n✅ Database setup completed successfully!")
        print("🚀 You can now run the API with: python api.py")
    else:
        print("\n❌ Database connection failed!")
        print("📝 Please check your database configuration in .env file")
        print("🔧 Make sure MySQL/MariaDB is running and accessible")

if __name__ == "__main__":
    asyncio.run(main()) 