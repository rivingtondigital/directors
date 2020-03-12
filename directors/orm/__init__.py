import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from contextlib import contextmanager

CON_STRING = 'mysql+pymysql://{username}:{password}@{host}/{dbname}'.format(
    username='root',
    password='',
    host='db',
    dbname='public_listings')

engine = sql.create_engine(CON_STRING, echo=False, pool_size=100, pool_recycle=3600)
_session_factory = sessionmaker(bind=engine)
Session = scoped_session(_session_factory)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.expunge_all()
        session.close()
