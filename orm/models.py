from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UniqueConstraint
from orm import engine


Base = declarative_base()


class Company(Base):
    __tablename__ = 'company'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    symbol = Column(String(8))
    market = Column(String(20))

    UniqueConstraint(symbol)

    def __repr__(self):
        return "<Company: {}>".format(self.symbol)

Base.metadata.create_all(engine)

