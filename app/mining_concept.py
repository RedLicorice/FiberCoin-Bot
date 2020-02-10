
MINE_LENGTH_RANGE = (10, 100)
FC_PER_MINE = 1
OWNER_FC_PER_MINE = 1
PRICE_PER_CHANCE = 1
SEARCH_PCT_PER_COIN = 10

#Get n-th number in fibonacci series
def fibonacci(n):
	a,b = 0,1
	for i in range(n):
		a,b = b,a+b
	return a

@app.on_message(Filters.command("mines") & Filters.private)
@with_user
def do_list_mines(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')

	mines = session.query(Mine).filter(Mine.owner == user).all()
	if mines:
		mines = [
			"ID:{} 💎{} ```{} {}```\n".format(m.code, m.progress, "👌" if m.last == user else "🔥", m.updated_at)
			for m in mines]
		message.reply("**Le tue miniere:**\n{}\n"
					  "\n Usa /mine ID_MINIERA per minare.\n"
					  "Usa /search per cercare nuove miniere!\n"
					  "Usa /search IMPORTO per aumentare le chances di successo\n"
					  " utilizzando 💸FC\n"
					  "ℹ Puoi cercare nuove miniere una volta ogni ora."\
					  .format('\n'.join(mines)))
	else:
		message.reply("**Al momento non possiedi miniere**\n"
					  "\nUsa /search per scavare e cercarne una.\n"
					  "Usa /search IMPORTO per aumentare le chances di successo\n"
					  " utilizzando 💸FC\n"
					  "ℹ Puoi cercare nuove miniere una volta ogni ora.")

@app.on_message(Filters.command("search") & Filters.private)
@with_user
def do_search(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')
	time_passed = datetime.utcnow() - user.last_dig
	time_needed = timedelta(minutes=15)
	if time_passed < time_needed:
		wait = time_needed  - time_passed
		message.reply("🚫 Devi attendere ancora 🕙[{}]\n".format(str(wait)))
		return
	# determine price
	percent = 10
	price = 0
	if len(message.command) > 1:
		price = min(try_parse_int(message.command[1], 0), 5)
		if price <= 0:
			message.reply("🚫 Importo non valido")
			return
		else:
			message.reply("🎩 Percentuale bonus: {}%".format(price*SEARCH_PCT_PER_COIN))
	if user.coins < price:
		message.reply("Non possiedi abbastanza 💸FC.\n- Borsellino: 💸{} FC\n- Necessari: 💸{} FC"\
					  .format(user.coins, price))
		return
	# pay price
	user.coins -= price
	user.last_dig = datetime.utcnow()
	# raffle
	if random.randint(1,100) <= (percent + price*SEARCH_PCT_PER_COIN):
		mine = Mine(
			code=random.randint(100000, 9999999),
			progress=random.randint(*MINE_LENGTH_RANGE),
			prime=random.randint(5,10),
			offset=random.randint(0, 6),
			last=user,
			owner=user
		)
		session.add(mine)
		message.reply("🥳 Hai trovato una nuova miniera ⛏ID:{} 💎{}!".format(mine.code, mine.progress))
	else:
		message.reply("😕 Non hai trovato nulla, ritenta!\n"
					  "Puoi aumentare le tue chances di successo usando 💸FC!\n"\
					  "ℹProva il comando /search IMPORTO\n"\
					  .format(user.coins, price))
	session.commit()

@app.on_message(Filters.command("mine") & Filters.private)
@with_user
def do_mine(client, message, *args, **kwargs):
	user = kwargs.get('user')
	session = kwargs.get('session')
	if len(message.command) < 2 or not message.command[1].isnumeric():
		message.reply("Uso: /mine ID_MINIERA")
		return
	mine = session.query(Mine).filter(Mine.code == message.command[1]).first()

	if not mine:
		message.reply("⚠ La miniera ID:{} non esiste!".format(message.command[1]))
		return

	if mine.progress <= 0:
		message.reply("🚫 Questa miniera è esaurita!\n")
		return

	if mine.last == user:
		message.reply("🚫 Non tocca ancora a te ✋\n Qualcun altro deve minare con il comando /mine {}\n".format(mine.code))
		return

	if len(message.command) > 2 and message.command[2].isnumeric():
		# If a solution is passed
		mine.last = user
		# "mine"
		input = int(message.command[2])
		exp = fibonacci(mine.prime + 1) + mine.offset
		if input != exp:
			message.reply("❌ Fibberato! Salta il turno. [{},{}]".format(input, exp))
			session.commit()
		else:
			# Input is the right number
			mine.prime += 1
			mine.offset = random.randint(0,10)
			mine.progress -= 1
			# Pay mining rewards
			user.coins += FC_PER_MINE
			if user != mine.owner:
				mine.wealth += FC_PER_MINE
				mine.income += OWNER_FC_PER_MINE
				mine.owner.coins += OWNER_FC_PER_MINE
			else:
				mine.income += FC_PER_MINE
			message.reply("🤑 Hai minato 💸{} FC!".format(FC_PER_MINE))
			# Check if mine is exhausted
			if mine.progress <= 0:
				# mine is exhausted
				app.send_message(chat_id=mine.owner.chat_id,
								 text="⛏ La miniera ID:{} si è esaurita!\n"
									  "Ti ha reso 💸{} FC\n"
									  "Sono stati minati 💸{} FC" \
								 .format(mine.code, mine.income, mine.wealth))
				mine.delete()
			session.commit()
	else:
		primes = ', '.join([str(fibonacci(n) + mine.offset) for n in range(mine.prime - 5, mine.prime)])
		message.reply("⛏ ID:{}\n{}, ?\n\nUsa il comando /mine {} SOLUZIONE!" \
										  .format(mine.code, primes, mine.code))