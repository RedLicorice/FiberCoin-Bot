from pyrogram import Client, Filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, User, Fiberation
import random
import threading
import os
from dotenv import load_dotenv
load_dotenv()

FC_PER_FIBBERATION = 1
# os.getenv("EMAIL")
BASE_LINK = "https://t.me/the_fibber_bot?start={}"
MENTION = "[{}](tg://user?id={})"  # User mention markup
# Initialize Telegram client
app = Client("/db/the_fibber_bot", bot_token=os.getenv("BOT_TOKEN"), api_id=os.getenv("API_ID"), api_hash=os.getenv("API_HASH"))
# Initialize SQLAlchemy
engine = create_engine('sqlite:///'+ os.getenv("DB_FILE"))
Base.metadata.bind = engine
session_factory = sessionmaker(bind=engine)
DBSession = scoped_session(session_factory)

#Try parsing an int, default on failure
def try_parse_int(m, default = None):
	try:
		return int(m)
	except:
		return default

#Delete a message after N Seconds
def delete_message_cb(**kwargs):
	app.delete_messages(
		chat_id=kwargs.get('chat_id'),
		message_ids=kwargs.get('message_id')
	)

@app.on_message(Filters.command("start") & Filters.private)
def start_bot(client, message):
	session = DBSession()
	user = session.query(User).filter(User.chat_id == message.chat.id).first()
	if user: # Utente era già fibberato
		fibberations = session.query(Fiberation).filter(Fiberation.signer == user).all()
		reply = "👋 Bentornato {}.\n☣ Hai fibberato {} Persone!\n📈 Possiedi 💸{} FC (FibberCoins)\n🔗 Fibbera laggente con questo link:\n{}" \
			.format(user.name, len(fibberations), user.coins, BASE_LINK.format(user.code))
		message.reply(reply)
	elif len(message.command) > 1:
		# fibbera un nuovo utente con invito
		invite_code = try_parse_int(message.command[1], None)
		if invite_code:
			inviter = session.query(User).filter(User.code == invite_code).first()
			if inviter:
				# Insert a User in the user table
				name = message.from_user.username
				if not name:
					name = "{} {}".format(message.from_user.first_name, message.from_user.last_name)

				new_user = User(chat_id=message.chat.id, name=name, code=(random.randint(100000,9999999)^message.chat.id))
				session.add(new_user)
				#session.commit()

				# Insert fiberation in the fibberations table
				new_fibberation = Fiberation(signer=inviter, signed=new_user)
				session.add(new_fibberation)
				#session.commit()

				inviter.coins += FC_PER_FIBBERATION
				session.commit()
				# Prepare reply
				reply = "SEI STATO FIBBERATO!⬆\n\n🔗 Puoi fibberare laggente con questo link:\n{}"\
					.format(BASE_LINK.format(new_user.code))

				app.send_message(chat_id=inviter.chat_id, text="Hai ricevuto 💸{} FC per aver fibberato {}.\n- Borsellino: 💸{} FC"\
								 .format(FC_PER_FIBBERATION, new_user.name, inviter.coins))
				message.reply(reply)
			else:
				message.reply("FiberCode non valido!")
		elif not len(session.query(User).all()):
			# Fibbera un nuovo utente senza invito (SOLO SE NESSUN ALTRO è STATO FIBBERATO)
			name = message.from_user.username
			if not name:
				name = "{} {}".format(message.from_user.first_name, message.from_user.last_name)

			new_user = User(chat_id=message.chat.id, name=name, code=(random.randint(100000,9999999)^message.chat.id))
			session.add(new_user)
			session.commit()

			reply = "SEI STATO FIBBERATO!\n\n\n Sei il primo fibberatore della catena.\nPuoi fibberare laggente con questo link:\n{}" \
				.format(BASE_LINK.format(new_user.code))
			message.reply(reply)
		else:
			message.reply("Non sei stato ancora fibberato.")
		DBSession.remove()

@app.on_message(Filters.command("list") & Filters.private)
def list_fibberations(client, message):
	session = DBSession()
	user = session.query(User).filter(User.chat_id == message.chat.id).first()
	if user: # Utente era già fibberato
		fibberations = session.query(Fiberation).filter(Fiberation.signer == user).all()
		reply = "Hai fibberato {} Persone!\n".format(len(fibberations))
		for f in fibberations:
			reply += "{}\n".format(MENTION.format(f.signed.name, f.signed.chat_id))
		message.reply(reply)
	else:
		message.reply("Non sei stato ancora fibberato.")
	DBSession.remove()

@app.on_message(Filters.command("tag") & Filters.private)
def user_mention(client, message):
	session = DBSession()
	user = session.query(User).filter(User.chat_id == message.chat.id).first()
	if user: # Utente era già fibberato
		user.allow_mention = not user.allow_mention
		if user.allow_mention:
			message.reply("🐵 Tag abilitati")
		else:
			message.reply("🙈 Tag disabilitati")
		session.commit()
	else:
		message.reply("Non sei stato ancora fibberato.")
	DBSession.remove()

@app.on_message(Filters.command("tip") & Filters.private)
def user_tip(client, message):
	session = DBSession()
	user = session.query(User).filter(User.chat_id == message.chat.id).first()
	if user: # Utente era già fibberato
		to_name = message.command[1]
		amount = try_parse_int(message.command[2], 1)
		to = session.query(User).filter(User.name == to_name).first()
		if not to:
			message.reply("😢 L'utente {} non è stato fibberato!".format(to_name))
		elif amount > user.coins:
			message.reply("Non possiedi abbastanza 💸FC.\n- Borsellino: 💸{} FC\n- Necessari: 💸{} FC".format(user.coins, amount))
		else:
			user.coins -= amount
			to.coins += amount
			session.commit()
			app.send_message(chat_id=to.chat_id, text="Hai ricevuto 💸{} FC da {}.\n- Borsellino: 💸{} FC".format(amount, user.name, to.coins))
			message.reply("Hai inviato 💸{} FC a {}.\n- Borsellino: 💸{} FC".format(amount, to.name, user.coins))
	else:
		message.reply("Non sei stato ancora fibberato.")
	DBSession.remove()

@app.on_message(Filters.command("about") & Filters.private)
def about_fibberations(client, message):
	message.reply("Scopri di più qui: [Attacco Fibbering](https://rentry.co/nkr7i)")

@app.on_message(Filters.regex("/check") & Filters.group)
def check_fibberations(client, message):
	session = DBSession()
	# Get Chat Members
	members = [m.user.id for m in app.iter_chat_members(message.chat.id)]
	# Get fibbered UID's
	uids = []
	for mid in members:
		u = session.query(User).filter(User.chat_id == mid).first()
		if(u):
			uids.append(u.id)
	# Get Fiberations
	fiberations = session.query(Fiberation).filter(Fiberation.signed_id.in_(uids)).all()
	fibered = []
	fiberer_id = []
	fibered_id = []
	for fib in fiberations:
		fiberer_id.append(fib.signer.id)
		fibered_id.append(fib.signed.id)
		fibered.append("{} (💸{} FC) ```fibered by {} (💸{} FC)```".format(
			MENTION.format(fib.signed.name, fib.signed.chat_id) if fib.signed.allow_mention else fib.signed.name, fib.signed.coins,
			fib.signer.name, fib.signer.coins #MENTION.format(fib.signer.name, fib.signer.chat_id) if fib.signer.allow_mention else
		))
	m = app.send_message(chat_id=message.chat.id, text="**Utenti fiberati:**\n\n"+"\n".join(fibered))
	# Queue a job for deleting the message
	threading.Timer(30.0, delete_message_cb, kwargs={'chat_id':message.chat.id,'message_id':m.message_id}).start()
	DBSession.remove()

if __name__ == '__main__':
	app.run()  # Automatically start() and idle()