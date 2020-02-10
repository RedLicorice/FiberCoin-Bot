from pyrogram import Client, Filters, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, User, Invitation, Mine, Tip
import random
import threading
import os
import wrapt
import humanize
from datetime import datetime, timedelta
import math
from dotenv import load_dotenv
load_dotenv()

FC_PER_FIBBERATION = 10
DAILY_AMOUNT_RANGE = (1,3)
FC_PER_GROUP_TIP = 1
# os.getenv("EMAIL")
BASE_LINK = "https://t.me/"+os.getenv("BOT_NAME")+"?start={}"
MENTION = "[{}](tg://user?id={})"  # User mention markup
# Initialize Telegram client
app = Client(os.getenv("SESSION_FILE"), bot_token=os.getenv("BOT_TOKEN"), api_id=os.getenv("API_ID"), api_hash=os.getenv("API_HASH"))
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

@wrapt.decorator
def with_user(wrapped, instance, args, kwargs):
	def _execute(*args, **kwargs):
		client, message = args[0], args[1]
		session = DBSession()
		if not session:
			message.reply("Impossibile creare sessione!")
			return
		user = session.query(User).filter(User.chat_id == message.from_user.id).first()
		res = None
		if user:
			#user = session.query(User).filter(User.chat_id == message.chat.id).first()
			kwargs.update({'session':session,'user':user})
			res = wrapped(*args, **kwargs)
		else:
			message.reply("Non sei stato ancora fibberato.")
		DBSession.remove()
		return res
	return _execute(*args, **kwargs)

@wrapt.decorator
def with_session(wrapped, instance, args, kwargs):
	def _execute(*args, **kwargs):
		client, message = args[0], args[1]
		session = DBSession()
		res = None
		if session:
			#user = session.query(User).filter(User.chat_id == message.chat.id).first()
			kwargs.update({'session':session})
			res = wrapped(*args, **kwargs)
		else:
			message.reply("Impossibile creare sessione!")
			return
		DBSession.remove()
		return res
	return _execute(*args, **kwargs)

@app.on_message(Filters.command("start") & Filters.private)
@with_session
def do_start_user(client, message, *args, **kwargs):
	session = kwargs.get('session')
	user = session.query(User).filter(User.chat_id == message.chat.id).first()
	if user: # Utente era già fibberato
		fibberations = session.query(Invitation).filter(Invitation.signer == user).all()
		reply = "👋 **Bentornato {}**\n" \
				"☣ Hai fibberato **{}** Persone!\n" \
				"💰 Possiedi 💸**{} FiberCoin**\n\n" \
				"🔗 Fibbera la gente con questo link:\n{}" \
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

				new_user = User(
					chat_id=message.chat.id,
					name=name,
					code=(random.randint(10000,9999999)^message.chat.id),
					coins=math.floor(FC_PER_FIBBERATION/2)
				)
				session.add(new_user)
				#session.commit()

				# Insert fiberation in the fibberations table
				new_fibberation = Invitation(signer=inviter, signed=new_user)
				session.add(new_fibberation)
				#session.commit()

				inviter.coins += FC_PER_FIBBERATION
				session.commit()
				# Prepare reply

				app.send_message(chat_id=inviter.chat_id,
								 text="Hai ricevuto 💸**{} FiberCoin** per aver fibberato {}\n"
									  "💰 Borsellino: 💸**{} FiberCoin**"\
									.format(FC_PER_FIBBERATION, MENTION.format(new_user.name, new_user.chat_id), inviter.coins)
								)
				message.reply("**SEI STATO FIBBERATO!**⬆\n\n"
							  "🔗 Puoi fibberare la gente con questo link:\n"
							  "{}\n\n"\
							  "Scopri di più utilizzando il comando /about\n"\
					.format(BASE_LINK.format(new_user.code)))
			else:
				message.reply("FibberCode non valido!")
	elif not len(session.query(User).all()):
		# Fibbera un nuovo utente senza invito (SOLO SE NESSUN ALTRO è STATO FIBBERATO)
		name = message.from_user.username
		if not name:
			name = "{} {}".format(message.from_user.first_name, message.from_user.last_name)

		new_user = User(
			chat_id=message.chat.id,
			name=name,
			code=(random.randint(10000,9999999)^message.chat.id),
			coins=math.floor(FC_PER_FIBBERATION / 2),
			privilege=1
		)
		session.add(new_user)
		session.commit()

		reply = "SEI STATO FIBBERATO!\n\n\n Sei il primo fibberatore della catena.\nPuoi fibberare laggente con questo link:\n{}" \
			.format(BASE_LINK.format(new_user.code))
		message.reply(reply)

@app.on_message(Filters.command("list") & Filters.private)
@with_user
def do_list_user(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')
	invites = session.query(Invitation).filter(Invitation.signer == user).all()
	reply = "Hai fibberato **{}** Persone!\n".format(len(invites))
	for inv in invites:
		reply += "{} — 💸**{}**\n".format(MENTION.format(inv.signed.name, inv.signed.chat_id), inv.signed.coin)
	message.reply(reply)

@app.on_message(Filters.command("tag") & Filters.private)
@with_user
def do_tag_user(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')
	user.allow_mention = not user.allow_mention
	if user.allow_mention:
		message.reply("🐵 Tag abilitati")
	else:
		message.reply("🙈 Tag disabilitati")
	session.commit()

@app.on_message(Filters.command("bonus") & Filters.private)
@with_user
def do_bonus_user(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')
	time_passed = datetime.utcnow() - user.last_dig
	time_needed = timedelta(days=1)
	if time_passed < time_needed:
		wait = time_needed - time_passed
		_t = humanize.i18n.activate("it")
		message.reply("🚫 Devi attendere ancora {}!\n".format(humanize.naturaldelta(time_needed)))
		humanize.i18n.deactivate()
		return
	amount = random.randint(*DAILY_AMOUNT_RANGE)
	user.coins += amount
	user.last_dig = datetime.utcnow()
	message.reply("Hai ricevuto 💸**{} FiberCoin**\n"
				  "💰 Borsellino: 💸**{} FiberCoin**\n\n"
				  "ℹ Puoi richiedere il bonus una volta al giorno." \
					.format(amount, user.coins)
				)
	session.commit()

@app.on_message(Filters.command("about") & Filters.private)
def do_about_user(client, message):
	message.reply("**●Sei stato Fibberato!●**\n\n"
				  "Fibbera i tuoi amici ed usa i FiberCoin per premiare un messaggio o il miglior meme nei gruppi supportati!\n"
				  "Accedi quotidianamente al bot per avere nuovi FiberCoin gratuiti da utilizzare e "
				  "punta in alto nella classifica Fiberatori!")

##
# Both Chat and Group functions
##
@app.on_message(Filters.regex("/help"))
def do_help_user(client, message):
	m = app.send_message(chat_id=message.chat.id,
		text="**Comandi Chat**\n"
		"/start - Visualizza lo stato\n"
		"/list - Elenca gli utenti che hai fibberato\n"
		"/bonus - Ottieni il tuo bonus giornaliero\n"
		"/tag - Attiva/Disattiva i tag nelle chat pubbliche\n"
		"/about - Scopri di più su FiberCoin\n"
		"/help - Mostra questo messaggio\n"
		"\n**Comandi Gruppo**\n"
		"/check - Scopri chi è stato Fibberato nel gruppo\n"
		"/rank - Classifica dei Fibberatori nel gruppo\n"
		"/tip - Tippa un messaggio\n"
	)
	if message.chat.id < 0: # if it's a group
		app.delete_messages(message.chat.id, message.message_id)
		threading.Timer(10.0, delete_message_cb, kwargs={'chat_id': message.chat.id, 'message_id': m.message_id}).start()


##
# Group Functionality
##
@app.on_message(Filters.command("tip") & Filters.group)
@with_user
def do_tip_group(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')
	if not message.reply_to_message:
		m = app.send_message(chat_id=message.chat.id, text="⛔ {}: Devi rispondere al messaggio da tippare" \
							 .format(MENTION.format(user.name, user.chat_id)))
		# Queue a job for deleting the message
		threading.Timer(10.0, delete_message_cb,
						kwargs={'chat_id': message.chat.id, 'message_id': m.message_id}).start()
		# Delete messages which are not replies to other messages
		app.delete_messages(message.chat.id, message.message_id)
		return
	to = session.query(User).filter(User.chat_id == message.reply_to_message.from_user.id).first()
	if not to:
		m = app.send_message(chat_id=message.chat.id, text="😢 {}: L'utente non è stato fibberato!"\
							 .format(MENTION.format(user.name, user.chat_id)))
		# Queue a job for deleting the message
		threading.Timer(10.0, delete_message_cb, kwargs={'chat_id': message.chat.id, 'message_id': m.message_id}).start()
	elif to == user:
		m = app.send_message(chat_id=message.chat.id, text="⛔ {}: Non puoi tipparti da solo!"\
							 .format(MENTION.format(user.name, user.chat_id)))
		threading.Timer(10.0, delete_message_cb, kwargs={'chat_id': message.chat.id, 'message_id': m.message_id}).start()
	else:
		# Get Tip Record for that message
		tip = session.query(Tip).filter((Tip.author_id == message.reply_to_message.from_user.id) & \
										(Tip.chat_id == message.reply_to_message.chat.id) & \
										(Tip.message_id == message.reply_to_message.message_id)
										).first()
		if not tip: # Or create a new one
			tip = Tip(chat_id=message.reply_to_message.chat.id,
					  message_id=message.reply_to_message.message_id,
					  author_id=message.reply_to_message.from_user.id,
					  total=0,
					  last_tipper=user
				)
			session.add(tip)
		elif tip.last_tipper == user:
			m = app.send_message(chat_id=message.chat.id,
								 text="⛔ {}: Non puoi tippare lo stesso messaggio più volte di seguito."\
								 .format(MENTION.format(user.name, user.chat_id)))
			threading.Timer(10.0, delete_message_cb, kwargs={'chat_id': message.chat.id, 'message_id': m.message_id}).start()
			app.delete_messages(message.chat.id, message.message_id)
			return
		else:
			tip.last_tipper = user
		user.coins -= FC_PER_GROUP_TIP
		to.coins += FC_PER_GROUP_TIP
		tip.total += 1
		session.commit()
		app.send_message(chat_id=to.chat_id,
						 text="Hai ricevuto 💸**{} FiberCoin** da {}\n"
				  				"💰 Borsellino: 💸**{} FiberCoin**"\
						.format(FC_PER_GROUP_TIP, MENTION.format(user.name, user.chat_id), to.coins)
						)
		app.send_message(chat_id=user.chat_id,
						 text="Hai inviato 💸**{} FiberCoin** a {}\n"
				  				"💰 Borsellino: 💸**{} FiberCoin**"\
						.format(FC_PER_GROUP_TIP, MENTION.format(to.name, to.chat_id), user.coins)
						)

		message.reply_to_message.reply("● **{} FiberCoin**{} ●\n{} ha tippato".format(
			tip.total,
			" 👌 " if tip.total == 69 or tip.total == 420 else "",
			MENTION.format(user.name, user.chat_id)
		))
	#Delete tip request message
	app.delete_messages(message.chat.id, message.message_id)

@app.on_message(Filters.command("rank") & Filters.group)
@with_session
def do_rank_group(client, message, *args, **kwargs):
	session = kwargs.get('session')
	# Get Chat Members
	members = [m.user.id for m in app.iter_chat_members(message.chat.id)]
	# Get fibbered UID's
	ranks = session.query(User).filter(User.chat_id.in_(members)).order_by(User.coins.desc()).limit(10)
	medals = ["🥇", "🥈", "🥉"] + ["({})".format(i) for i in range(4,11)]
	ranks = ["{} {} 💸**{} FiberCoin**".format(m, u.name, u.coins) for m, u in zip(medals, ranks)]

	m = app.send_message(chat_id=message.chat.id, text="**Classifica FiberCoin:**\n"+"\n".join(ranks))
	# Queue a job for deleting the message
	threading.Timer(30.0, delete_message_cb, kwargs={'chat_id':message.chat.id,'message_id':m.message_id}).start()
	# Delete tip request message
	app.delete_messages(message.chat.id, message.message_id)

@app.on_message(Filters.command("check") & Filters.group)
@with_session
def do_check_group(client, message, *args, **kwargs):
	session = kwargs.get('session')
	# Get Chat Members
	members = [m.user.id for m in app.iter_chat_members(message.chat.id)]
	# Get fibbered UID's
	uids = []
	for mid in members:
		u = session.query(User).filter(User.chat_id == mid).first()
		if(u):
			uids.append(u.id)
	# Get Invitations
	fiberations = session.query(Invitation).filter(Invitation.signed_id.in_(uids)).all()
	fibered = []
	fiberer_id = []
	fibered_id = []
	for fib in fiberations:
		fiberer_id.append(fib.signer.id)
		fibered_id.append(fib.signed.id)
		fibered.append("{} (💸**{} FiberCoin**) ```fibberato da {} (💸{} FiberCoin)```".format(
			MENTION.format(fib.signed.name, fib.signed.chat_id) if fib.signed.allow_mention else fib.signed.name, fib.signed.coins,
			fib.signer.name, fib.signer.coins #MENTION.format(fib.signer.name, fib.signer.chat_id) if fib.signer.allow_mention else
		))
	m = app.send_message(chat_id=message.chat.id, text="**Utenti fiberati:**\n"+"\n".join(fibered))
	# Queue a job for deleting the message
	threading.Timer(30.0, delete_message_cb, kwargs={'chat_id':message.chat.id,'message_id':m.message_id}).start()
	# Delete check request message
	app.delete_messages(message.chat.id, message.message_id)

if __name__ == '__main__':
	app.run()  # Automatically start() and idle()