import telebot
#import logging
import requests
import json
import os
import time
from PIL import Image, ImageFilter, ImageEnhance
from telebot import types

# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

TOKEN = os.environ['BLURBOT_TOKEN']
bot = telebot.TeleBot(TOKEN)

# dicts for user steps
langStep = {}
blurStep = {}
dimStep = {}

# convert dict for dim keyboard
dimdict = {
	'0%' : 1.0,
	'5%' : 0.95,
	'10%' : 0.9,
	'20%' : 0.8,
	'30%' : 0.7,
	'50%' : 0.5,
	'70%' : 0.3,
}
dimdict_inverted = dict(map(reversed, dimdict.items()))

# keyboard for blur power selection
blur_select = types.ReplyKeyboardMarkup(one_time_keyboard=True)
blur_select.add('1', '2', '3', '4', '5', '6')

# keyboard for dim power selection
dim_select = types.ReplyKeyboardMarkup(one_time_keyboard=True)
dim_select.add('0%', '5%', '10%', '20%', '30%', '50%', '70%')

# keyboard for language select
lang_select = types.ReplyKeyboardMarkup(one_time_keyboard=True)
lang_select.add("English 🇬🇧", "Русский 🇷🇺")

hide_board = types.ReplyKeyboardRemove() # hides keyboard fron screen


def get_step(uid, step_dict):
	"""returns current user step from corresponding dict"""
	if uid in step_dict:
		return step_dict[uid]
	else:
		pass

def json_get(cid, item):
	"""gets item from json file with user settings"""
	with open('data/%s.json' %cid) as f:
		user = json.load(f)
	return user[item]

def json_dump(cid, item, value):
	"""dumps setting to json file"""
	with open('data/%s.json' %cid) as f:
		user = json.load(f)
	user[item] = value
	with open('data/%s.json' %cid, 'w') as f:
		json.dump(user, f)

def photo_manipulation(photo, blur_pow, dim_pow, cid):
	"""actual photo processing"""
	try:
		img = Image.open(photo)
		blurred = dim(blur(img, blur_pow), dim_pow)
		blurred.save("data/%s.jpg" %cid)
		result = open("data/%s.jpg" %cid, 'rb')
		return result
	except IOError:
		return "IOError"

def cleanup(cid):
	"""delete user photo from disk"""
	# TODO: needs better solution 
	try:
		os.remove('data/%s.jpg' %cid)
	except:
		pass

# handle the "/start" command
@bot.message_handler(commands=['start'])
def command_start(m):
	"""handler for /start command"""
	cid = m.chat.id
	if os.path.isfile('data/%s.json' %cid): 		# user already pressed /start button and settings file exists
		lang = json_get(cid, 'lang')
		blur_pow = json_get(cid, 'blur_pow')
		dim_pow = json_get(cid, 'dim_pow')
		if lang == 'ru':
			bot.send_message(cid, "Добро пожаловать снова! Ваши настройки: *размытие*: %d, *затемнение*: %s" %(blur_pow, dimdict_inverted[dim_pow]), parse_mode='Markdown')
		elif lang == 'en':
			bot.send_message(cid, "Welcome again! Your settings: *blur power: %d*, *dim power: %s*" %(blur_pow, dimdict_inverted[dim_pow]), parse_mode='Markdown')
	else:									# or create new user with default settings
		newuser = {}
		newuser['blur_pow'] = 4
		newuser['dim_pow'] = 0.95
		with open('data/%s.json' %cid, 'w') as f:
			json.dump(newuser, f)

		# user selects language
		bot.send_message(cid, "Choose language", reply_markup=lang_select)
		langStep[cid] = 1


@bot.message_handler(func=lambda message:get_step(message.chat.id, langStep) == 1)
def save_lang(m):
	"""saves language flag to settings file"""
	cid = m.chat.id
	if m.text == "English 🇬🇧":
		json_dump(cid, 'lang', 'en')
	elif m.text == "Русский 🇷🇺":
		json_dump(cid, 'lang', 'ru')
	with open('data/start_%s.md' %(json_get(cid, 'lang'))) as text:
		bot.send_message(cid, text.read(), parse_mode='Markdown', reply_markup=hide_board)
	langStep[cid] = 0
    

@bot.message_handler(commands=['help'])
def command_help(m):
	"""shows help page with example"""
	cid = m.chat.id
	lang = json_get(cid, 'lang')
	with open('data/help_%s.md' %(json_get(cid, 'lang'))) as text:
		bot.send_message(cid, text.read(), parse_mode='Markdown')
	if lang == 'ru':
		bot.send_photo(cid, open('data/Screens/Screen_merged.jpg', 'rb'), caption="Пример применения😃")
	elif lang == 'en':
		bot.send_photo(cid, open('data/Screens/Screen_merged.jpg', 'rb'), caption="Usage example😃")

@bot.message_handler(commands=['blur'])
def blur_choose(m):
	"""user choose blur setting with custom keyboard"""
	cid = m.chat.id
	lang = json_get(cid, 'lang')
	if lang == 'ru':
		bot.send_message(cid, 'Выберите степень *размытия*', reply_markup=blur_select, parse_mode='Markdown')
	elif lang == 'en':
		bot.send_message(cid, 'Choose *blur* power', reply_markup=blur_select, parse_mode='Markdown')
	blurStep[cid] = 1	# sends to saving step

@bot.message_handler(func=lambda message:get_step(message.chat.id, blurStep) == 1)
def blur_choose_save(m):
	"""save blur settings to file"""
	cid = m.chat.id
	json_dump(cid, 'blur_pow', int(m.text))
	lang = json_get(cid, 'lang')
	if lang == 'ru':
		bot.send_message(cid, "Настройки сохранены", reply_markup=hide_board)
	elif lang == 'en':
		bot.send_message(cid, "Settings saved", reply_markup=hide_board)
	blurStep[cid] = 0

@bot.message_handler(commands=['dim'])
def dim_choose(m):
	"""user choose dim setting with custom keyboard"""
	cid = m.chat.id
	lang = json_get(cid, 'lang')
	if lang == 'ru':
		bot.send_message(cid, "Выберите степень *затемнения*", reply_markup=dim_select, parse_mode='Markdown')
	elif lang == 'en':
		bot.send_message(cid, "Choose *dim* power", reply_markup=dim_select, parse_mode='Markdown')
	dimStep[cid] = 1

@bot.message_handler(func=lambda message:get_step(message.chat.id, dimStep) == 1)
def dim_choose_save(m):
	"""save blur settings to file"""
	cid = m.chat.id
	lang = json_get(cid, 'lang')
	json_dump(cid, 'dim_pow', dimdict[m.text])
	if lang == 'ru':
		bot.send_message(cid, "Настройки сохранены", reply_markup=hide_board)
	elif lang == 'en':
		bot.send_message(cid, "Settings saved", reply_markup=hide_board)
	dimStep[cid] = 0

def blur(image, power):
	"""blurs image using pillow library"""
	radius = int((image.size[1] / 1000) * (power * 2))
	return image.filter(ImageFilter.GaussianBlur(radius))

def dim(image, power):
	"""dims image using pillow library"""
	enhancer = ImageEnhance.Brightness(image)
	return enhancer.enhance(power)

@bot.message_handler(content_types=['photo'])
def photo_handler(m):
	"""handles images sent as 'photo'"""
	cid = m.chat.id
	lang = json_get(cid, 'lang')
	bot.send_chat_action(cid, 'upload_photo')
	file_info = bot.get_file(m.photo[2].file_id)	# telegram saves images in different sizes, [2] has best quality
	json_dump(cid, 'last_file', file_info.file_path)	# save file_path for /last command
	time.sleep(3)	# a little sleep helps with multiple files
	resp = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path), stream=True).raw	# gets raw image data for processing

	if lang == 'ru':
		bot.send_message(cid, "Готово! Но изображение было пережато телеграмом, чтобы этого не происходило, отправляйте его как *файл*", parse_mode='Markdown')
	elif lang =='en':
		bot.send_message(cid, "Done! But image was compressed by telegram, send it as *file* if that is not desirable.", parse_mode='Markdown')

	bot.send_photo(cid, photo_manipulation(resp, json_get(cid, 'blur_pow'), json_get(cid, 'dim_pow'), cid))
	cleanup(cid)

@bot.message_handler(content_types=['document'])
def document_handler(m):
	"""handles images sent as documents/files"""
	cid = m.chat.id
	bot.send_chat_action(cid, 'upload_document')
	lang = json_get(cid, 'lang')

	# too big files will not get file_id
	try:
		file_info = bot.get_file(m.document.file_id)
	except:
		if lang == 'ru':
			bot.send_message(cid, "Файл слишком большой! Пожалуйста, не более *20 мегабайт*", parse_mode='Markdown')
		if lang == 'en':
			bot.send_message(cid, "File is too big! Files larger *20 mb* are not accepted", parse_mode='Markdown')
		return

	json_dump(cid, 'last_file', file_info.file_path)	# for /last command

	time.sleep(3)
	resp = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path), stream=True).raw

	result = photo_manipulation(resp, json_get(cid, 'blur_pow'), json_get(cid, 'dim_pow'), cid)

	# IOError means that file was not an image, or format was incompatible
	if result == "IOError":
		if lang == 'ru':
			bot.send_message(cid, "Похоже этот документ не является изображением, попробуйте другой формат")
		elif lang == 'en':
			bot.send_message(cid, "Looks like this file is not an image, try another format")
	else:
		bot.send_document(cid, result)
	cleanup(cid)

@bot.message_handler(commands=['last'])
def last_image(m):
	"""process image with previously saved file_id"""
	cid = m.chat.id
	lang = json_get(cid, 'lang')
	with open('data/%s.json' %cid) as f:
		user = json.load(f)
	try:
		resp = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, user['last_file']), stream=True).raw
		if user['last_file'][:1] == 'd': 
			bot.send_document(cid, photo_manipulation(resp, user['blur_pow'], user['dim_pow'], cid))
		else:
			bot.send_photo(cid, photo_manipulation(resp, user['blur_pow'], user['dim_pow'], cid))

	except KeyError:
		if lang == 'ru':
			bot.send_message(cid, "Вы пока не загружали фотографий!")
		elif lang == 'en':
			bot.send_message(cid, "You have not uploaded photos yet!")

	cleanup(cid)

@bot.message_handler(commands=['lang'])
def change_lang(m):
	"""handles language select command"""
	cid = m.chat.id
	bot.send_message(cid, "Choose language", reply_markup=lang_select)
	langStep[cid] = 1


bot.polling()