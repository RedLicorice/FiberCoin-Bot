from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	chat_id = Column(Integer, nullable=False)
	code = Column(Integer, nullable=False, unique=True)
	name = Column(String(250), nullable=False)
	allow_mention = Column(Integer, default=1)
	coins = Column(Integer, default=0)
	privilege = Column(Integer, default=0)
	created_at = Column(DateTime, default=datetime.utcnow)
	last_dig = Column(DateTime, default=datetime.utcnow)


class Invitation(Base):
	__tablename__ = 'invites'
	id = Column(Integer, primary_key=True)
	signer_id = Column(Integer, ForeignKey('users.id'))
	signed_id = Column(Integer, ForeignKey('users.id'))
	signer = relationship(User, foreign_keys=signer_id)
	signed = relationship(User, foreign_keys=signed_id)
	created_at = Column(DateTime, default=datetime.utcnow)

class Tip(Base):
	__tablename__ = 'tips'
	chat_id =  Column(Integer, nullable=False, primary_key=True)
	message_id =  Column(Integer, nullable=False, primary_key=True)
	author_id = Column(Integer, ForeignKey('users.id'))
	last_tip_id = Column(Integer, ForeignKey('users.id'))
	total =  Column(Integer, default=0)

	created_at = Column(DateTime, default=datetime.utcnow)
	author = relationship(User, foreign_keys=author_id)
	last_tipper = relationship(User, foreign_keys=last_tip_id)

class Mine(Base):
	__tablename__ = 'mines'
	id = Column(Integer, primary_key=True)
	code = Column(Integer, unique=True, nullable=False)
	progress = Column(Integer, default=10)
	income = Column(Integer, default=0)
	wealth = Column(Integer, default=0)
	prime = Column(Integer, default=0)
	offset = Column(Integer, default=0)
	last_id = Column(Integer, ForeignKey('users.id'))
	owner_id = Column(Integer, ForeignKey('users.id'))
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow)

	last = relationship(User, foreign_keys=last_id)
	owner = relationship(User, foreign_keys=owner_id)

def migrate():
	if not os.path.exists(os.getenv("DB_FILE")):
		engine = create_engine('sqlite:///'+os.getenv("DB_FILE"))
		Base.metadata.create_all(engine)
		print("fibberbot.db created!")
		return True
	return False


if __name__ == '__main__':
	load_dotenv()
	if not migrate():
		print("fibberbot.db already exists.\nPlease delete it if you want to recreate it.")
