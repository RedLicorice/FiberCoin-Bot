from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	# Here we define columns for the table person
	# Notice that each column is also a normal Python instance attribute.
	id = Column(Integer, primary_key=True)
	chat_id = Column(Integer, nullable=False)
	code = Column(Integer, nullable=False, unique=True)
	name = Column(String(250), nullable=False)
	allow_mention = Column(Integer, default=1)
	coins = Column(Integer, default=0)
	created_at = Column(DateTime, default=datetime.utcnow)


class Fiberation(Base):
	__tablename__ = 'signatures'
	# Here we define columns for the table address.
	# Notice that each column is also a normal Python instance attribute.
	id = Column(Integer, primary_key=True)
	signer_id = Column(Integer, ForeignKey('user.id'))
	signed_id = Column(Integer, ForeignKey('user.id'))
	signer = relationship(User, foreign_keys=signer_id)
	signed = relationship(User, foreign_keys=signed_id)
	created_at = Column(DateTime, default=datetime.utcnow)

if __name__ == '__main__':
	load_dotenv()
	if not os.path.exists(os.getenv("DB_FILE")):
		engine = create_engine('sqlite:///'+os.getenv("DB_FILE"))
		Base.metadata.create_all(engine)
		print("fibberbot.db created!")
	else:
		print("fibberbot.db already exists.\nPlease delete it if you want to recreate it.")