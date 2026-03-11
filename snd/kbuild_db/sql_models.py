from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from sqlalchemy import String, Column, Integer, ForeignKey, Date


DB_FILE = r'W:/durant/programs/csp_scraper/kbuild.db'
engine = create_engine('sqlite:///' + DB_FILE, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Block(Base):
	__tablename__ = 'block'
	ID = Column(Integer, primary_key=True, index=True)

	block_engraving = Column(String(32))
	block_revision_fromfile = Column(Integer)
	block_revision_frompath = Column(Integer)
	block_revision = Column(Integer)
	block_serial = Column(String(16))

class Build(Base):
	__tablename__ = 'build'

	ID = Column(Integer, primary_key=True, index=True)

	build_name = Column(String(32))
	block_id = Column(Integer, ForeignKey('block.ID'))
	
	build_file_path = Column(String(128), unique=True)
	build_date = Column(Date)
	build_revision = Column(Integer)

class SimpleBuild(Base):
	__tablename__ = 'simplebuild'

	ID = Column(Integer, primary_key=True, index=True)
	build_name = Column(String(32))
	block_id = Column(Integer, ForeignKey('block.ID'))
	build_file_path = Column(String(128), unique=True)
	build_revision = Column(Integer)

	row1 = Column(String(128))
	row2 = Column(String(128))
	row3 = Column(String(128))
	row4 = Column(String(128))
	row5 = Column(String(128))
	row6 = Column(String(128))
	row7 = Column(String(128))
	row8 = Column(String(128))
	row9 = Column(String(128))
	row10 = Column(String(128))
	row11 = Column(String(128))
	row12 = Column(String(128))
	row13 = Column(String(128))
	row14 = Column(String(128))
	row15 = Column(String(128))
	row16 = Column(String(128))
	row17 = Column(String(128))
	row18 = Column(String(128))
	row19 = Column(String(128))
	row20 = Column(String(128))
	row21 = Column(String(128))
	row22 = Column(String(128))
	row23 = Column(String(128))
	row24 = Column(String(128))
	row25 = Column(String(128))
	row26 = Column(String(128))
	row27 = Column(String(128))
	row28 = Column(String(128))
	row29 = Column(String(128))
	row30 = Column(String(128))

metaobj = Base.metadata
metaobj.drop_all(engine)
metaobj.create_all(engine)