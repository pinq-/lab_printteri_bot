import extra_info
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import bambulabs_api as bl
import time
import datetime
import json
import urllib3
import requests
from PIL import Image


def get_bambulabs_stats():
	printer = bl.Printer(extra_info.bambu_ip, extra_info.acces_code, extra_info.bambu_serial)
	printer.connect()
	time.sleep(5)
	bambu_stats = {}
	# Get the printer status
	bambu_stats['status'] = printer.get_state()
	bambu_stats['percentage'] = printer.get_percentage()
	bambu_stats['layer_num'] = printer.current_layer_num()
	bambu_stats['total_layer_num'] = printer.total_layer_num()
	bambu_stats['bed_temperature'] = printer.get_bed_temperature()
	bambu_stats['nozzle_temperature'] = round(printer.get_nozzle_temperature())
	bambu_stats['remaining_time'] = printer.get_time()
	if bambu_stats['remaining_time'] is not None:
		finish_time = datetime.datetime.now() + datetime.timedelta(minutes=int(bambu_stats['remaining_time']))
		bambu_stats['finish_time_format'] = finish_time.strftime("%Y-%m-%d %H:%M:%S")
	else:
		bambu_stats['finish_time_format'] = "NA"
	try:
		image = printer.get_camera_image()
		image.save('bambu_status.png')
	except Exception as e:
		print(e)
	printer.disconnect()
	return bambu_stats

def get_octo_status():
	octo_ip = '192.168.10.158'
	url = 'http://' + octo_ip + '/api/job'
	http = urllib3.PoolManager()
	r = http.request('GET',url, headers={'Content-Type': 'application/json', 'X-Api-Key': extra_info.octo_api})
	
	#camera 1
	url = 'http://octopi.local/webcam/?action=snapshot'
	#camera 2
	url2 = 'http://octopi.local/webcam2/?action=snapshot'

	octo_image_1 = requests.get(url).content
	octo_image_2 = requests.get(url2).content

	with open("octo_img_1.jpg", 'wb') as file: file.write(octo_image_1)
	with open("octo_img_2.jpg", 'wb') as file: file.write(octo_image_2)
	return r.json()


async def bambu_status(update, context):
    await update.message.reply_text("Haetaan bambun tietoja")
    bambu_stats = get_bambulabs_stats()
    if bambu_stats['percentage'] is None:
    	await update.message.reply_text("Tietoja ei saatavissa")
    	return 0
    try:
    	remainig_time = str(datetime.timedelta(minutes=bambu_stats['remaining_time']))
    except:
    	remainig_time = "---"
    await update.message.reply_text(
    	'Printter status: ' + str(bambu_stats['status']) + "\n"
    	'Layers: ' + str(bambu_stats['layer_num']) + "/" + str(bambu_stats['total_layer_num']) + "\n"
    	'Percentage: ' + str(bambu_stats['percentage']) + " %" + "\n"
    	'Bed tempereture: ' + str(bambu_stats['bed_temperature']) + " C" + "\n"
    	'Nozzle tempereture: ' + str(bambu_stats['nozzle_temperature']) + " C" + "\n"
    	'Remaining time: ' + remainig_time  + "\n"
    	'Finish time: ' + str(bambu_stats['finish_time_format'])  + "\n"
    	)
    with open('bambu_status.png', 'rb') as img:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)

async def octo_status(update, context):
    stats = get_octo_status()
    #print(stats)
    await update.message.reply_text("Haetaan octon tietoja")
    await update.message.reply_text(
		'Printter status: ' + str(stats['state']) + "\n")
    if stats['state'] != 'Operational':
    	await update.message.reply_text(
			#'Layers: ' + str(stats['layer_num']) + "/" + str(stats['total_layer_num']) + "\n"
			#'Percentage: ' + str(stats['percentage']) + " %" + "\n"
			#'Bed tempereture: ' + str(stats['bed_temperature']) + " C" + "\n"
			#'Nozzle tempereture: ' + str(stats['nozzle_temperature']) + " C" + "\n"
			'Remaining time: ' + str(datetime.timedelta(seconds=stats['progress']['printTimeLeft']))  + "\n"
			'Whole time: ' + str(datetime.timedelta(seconds=int(stats['job']['estimatedPrintTime'])))  + "\n"
			#'Finish time: ' + str(stats['finish_time_format'])  + "\n"
			)
    img = Image.open('octo_img_1.jpg').transpose(Image.ROTATE_180).save('octo_img_1.jpg')

    with open('octo_img_1.jpg', 'rb') as img_1:
    	await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_1)
    with open('octo_img_2.jpg', 'rb') as img_2:
    	await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_2)
    #await context.bot.send_photo(chat_id=update.effective_chat.id, photo = img)

async def bot_status(update, context):
	await update.message.reply_text("Botti on toiminnassa")

def main():
    """
    Handles the initial launch of the program (entry point).
    """
    token = extra_info.telegram_bot_api
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()
    #application.add_handler(MessageHandler(filters.TEXT, reply))
    application.add_handler(CommandHandler("bambu", bambu_status)) # Bambulab status
    application.add_handler(CommandHandler("octo", octo_status)) # Octoprint status
    application.add_handler(CommandHandler("status", bot_status)) # bot status
    print("Telegram Bot started!", flush=True)
    application.run_polling()

if __name__ == '__main__':
    main()