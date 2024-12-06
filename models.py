from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
import datetime
import os

Base = declarative_base()

class Block(Base):
    __tablename__ = 'blocks'
    
    id = Column(Integer, primary_key=True)
    index = Column(Integer, unique=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    proof = Column(Integer)
    previous_hash = Column(String)
    transactions = relationship("Transaction", back_populates="block")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    sender = Column(String)
    recipient = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    block_id = Column(Integer, ForeignKey('blocks.id'))
    block = relationship("Block", back_populates="transactions")

class Node(Base):
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True)
    
    def __repr__(self):
        return f"<Node {self.address}>"

class Wallet(Base):
    __tablename__ = 'wallets'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True)
    public_key = Column(String)
    private_key = Column(String)

# Database connection
def init_db(db_url=None):
    if db_url is None:
        db_url = "postgresql://postgres:postgres@localhost:5432/blockchain"
        
    try:
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  
            pool_pre_ping=True  
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise