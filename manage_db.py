import click
from alembic.config import Config
from alembic import command
from models import init_db, Base
import psycopg2
from sqlalchemy import create_engine, text

def get_db_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost"
    )

def terminate_db_connections(cur):
    cur.execute("""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'blockchain'
        AND pid <> pg_backend_pid();
    """)

@click.group()
def cli():
    pass

@cli.command()
def init():
    """Initialize the database"""
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()
        
        # Drop the database if it exists and recreate it
        terminate_db_connections(cur)
        cur.execute("DROP DATABASE IF EXISTS blockchain")
        cur.execute("CREATE DATABASE blockchain")
        print("Database 'blockchain' created.")
        
        cur.close()
        conn.close()

        # Initialize the database schema
        db = init_db()
        print("Database initialized successfully!")
        
        # Run initial migration
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Initial migration completed successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")

@cli.command()
def migrate():
    """Run database migrations"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {e}")
        if "DuplicateTable" in str(e):
            print("Tables already exist. Try running 'reset' command first.")

@cli.command()
def rollback():
    """Rollback the last migration"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, "-1")
        print("Rollback completed successfully!")
    except Exception as e:
        print(f"Error rolling back migration: {e}")

@cli.command()
def reset():
    """Reset the database"""
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()
        
        # Close all connections and drop database
        terminate_db_connections(cur)
        cur.execute("DROP DATABASE IF EXISTS blockchain")
        cur.execute("CREATE DATABASE blockchain")
        
        cur.close()
        conn.close()

        # Create a new connection to the blockchain database
        engine = create_engine("postgresql://postgres:postgres@localhost:5432/blockchain")
        
        # Create all tables
        Base.metadata.create_all(engine)
        print("Database tables created successfully!")

        # Initialize Alembic
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        print("Database reset completed successfully!")
        
    except Exception as e:
        print(f"Error resetting database: {e}")

@cli.command()
def status():
    """Show current database status"""
    try:
        engine = create_engine("postgresql://postgres:postgres@localhost:5432/blockchain")
        with engine.connect() as conn:
            # Check database version
            result = conn.execute(text("SELECT version()"))
            db_version = result.scalar()
            print(f"\nDatabase Version: {db_version}")

            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name)))
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC
            """))
            print("\nTable Statistics:")
            print("-" * 50)
            print(f"{'Table Name':<20} {'Row Count':<10} {'Size':<10}")
            print("-" * 50)
            
            for table_name, table_size in result:
                # Get row count for each table
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar()
                print(f"{table_name:<20} {row_count:<10} {table_size:<10}")

            # Get blockchain statistics
            blocks_result = conn.execute(text("SELECT COUNT(*), MAX(index) FROM blocks"))
            block_count, last_block_index = blocks_result.one()
            
            tx_result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
            tx_count = tx_result.scalar()
            
            print("\nBlockchain Statistics:")
            print("-" * 50)
            print(f"Total Blocks: {block_count}")
            print(f"Latest Block Index: {last_block_index or 0}")
            print(f"Total Transactions: {tx_count}")

            # Get migration status
            version_result = conn.execute(text(
                "SELECT version_num FROM alembic_version"
            ))
            current_version = version_result.scalar()
            print(f"\nCurrent Migration Version: {current_version}")
                
    except Exception as e:
        print(f"Error getting database status: {e}")

@cli.command()
def verify():
    """Verify blockchain integrity"""
    try:
        engine = create_engine("postgresql://postgres:postgres@localhost:5432/blockchain")
        with engine.connect() as conn:
            # Check block sequence
            result = conn.execute(text("""
                SELECT index, previous_hash 
                FROM blocks 
                ORDER BY index
            """))
            blocks = result.fetchall()
            
            print("\nVerifying Blockchain Integrity:")
            print("-" * 50)
            
            if not blocks:
                print("No blocks found in the chain.")
                return
                
            for i, (index, prev_hash) in enumerate(blocks):
                if i == 0:  # Genesis block
                    if prev_hash != "0":
                        print(f"❌ Invalid genesis block: previous_hash should be '0', got {prev_hash}")
                    else:
                        print("✅ Genesis block is valid")
                else:
                    # Get previous block's hash
                    prev_block_result = conn.execute(text(
                        "SELECT id FROM blocks WHERE index = :idx"
                    ), {"idx": index - 1})
                    if not prev_block_result.scalar():
                        print(f"❌ Missing block at index {index - 1}")
                    
            print("\nVerifying Transactions:")
            # Check for invalid transactions (e.g., spending more than available)
            result = conn.execute(text("""
                SELECT sender, SUM(amount) as total_sent
                FROM transactions
                GROUP BY sender
                HAVING sender != '0'
            """))
            for sender, total_sent in result:
                received_result = conn.execute(text("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM transactions
                    WHERE recipient = :sender
                """), {"sender": sender})
                total_received = received_result.scalar()
                
                if total_sent > total_received:
                    print(f"❌ Invalid balance for {sender}: sent {total_sent} but only received {total_received}")
                else:
                    print(f"✅ Valid balance for {sender}: {total_received - total_sent}")
                
    except Exception as e:
        print(f"Error verifying blockchain: {e}")

if __name__ == '__main__':
    cli() 