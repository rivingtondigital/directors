from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UniqueConstraint
from directors.orm import engine, session_scope


Base = declarative_base()


class Company(Base):
    __tablename__ = 'company'
    __table_args__ = (
        UniqueConstraint('symbol', 'market'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    symbol = Column(String(8))
    market = Column(String(20))

    def __repr__(self):
        return "<Company: {}>".format(self.symbol)

    @classmethod
    def batch_update(cls, batch, market=None):
        batch = set(batch)
        with session_scope() as sess:
            table_data = set(sess.query(Company).filter(Company.market == market)
                             .values('name', 'symbol', 'market'))

        new_listings = batch - table_data
        deleted_listings = table_data - batch
        unchanged = batch & table_data

        with session_scope() as sess:
            inserts = [Company(**x._asdict()) for x in new_listings]
            sess.add_all(inserts)

        with session_scope() as sess:
            for listing in deleted_listings:
                sess.query(Company).filter_by(**listing._asdict()).delete()


        return {
            'new': new_listings,
            'deleted': deleted_listings,
            'unchanged': unchanged
        }

Base.metadata.create_all(engine)
