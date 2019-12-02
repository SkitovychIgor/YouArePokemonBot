import telebot        # для роботи з  API Телеграму (pyTelegramBotAPI 3.6.6)
import cv2            # комп'ютерний зір OpenCV для пошуку облич (opencv-python 4.1.2.30)
import os             # для видалення фото з диску після надсилання
from PIL import Image # для об'єднання зображеннь (Pillow 5.4.1)
import random         # для випадкового вибору
import psutil         # для моніторингу процесів і систем (psutil 5.6.7)
import time           # для роботи таймера сну


# Зберігаємо ТОКЕН в змінну TOKEN та user_id адміністратора в змінну admin_id
TOKEN = "975011749:AAEbBs_ijmHJphZwpiRQxe9rcuexoFr__k8" # <--- YOUR TOKEN
admin_id = 303694396  # <--- YOUR USER ID
bot = telebot.TeleBot(TOKEN, threaded=False)
# getMe
user = bot.get_me()
file_name_by_id = ''


# Легенда бота на запит /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    UserPhotoID = message.chat.id
    bot.reply_to(message, "Давним давно, в далекій галактиці стоп..не те..ааа..ось..колись давно покемони навчилися вселятися в людей, що в принципі й обумовлює психотипи, а не те що думають психологи..розуміння того, характер якого покемона впливає на людину, нам би сало у нагоді. Цей Бот є сканером, який дозволяє зрозуміти який cаме покемон зараз живе в людині, а інколи навіть фіксує тих покемонів, які ще перебувають у пошуку...знайди їх усіх!")
    bot.reply_to(message, "Надішли ботові фотогафію для поке-сканування")


#  Отримуємо зображення від користувача
@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    file_info = bot.get_file(message.photo[len(message.photo)-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    # Прописуємо шлях збереження отриманих зображень '/шлях/'
    src = '/home/pi/mybot/in/received/photos/' + str(message.chat.id) + file_info.file_path[-4:]
    file_name_by_id = str(message.chat.id) + file_info.file_path[-4:]             #src[34:]
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.reply_to(message, "Шукаю покемонів...")
    pokemons_qty = search_faces(src, file_name_by_id)
    pk_qty = str(pokemons_qty)
    bot.reply_to(message, "Я знайшов " + pk_qty + "!")
    # Якщо на фото є обличя:
    if pk_qty != '0':
        photo_out = open('/home/pi/mybot/out/' + file_name_by_id, 'rb') # best way use join for path
        # Відправляємо фінальне зображення
        bot.send_photo(chat_id=message.chat.id, photo=photo_out)
        # Видаляємо зображення з серверу
        os.remove('/home/pi/mybot/out/' + file_name_by_id)
    # Якщо на фото немає облич:
    else:
        bot.reply_to(message, "Цього разу чисто, але вони точно десь поруч!")


# Шукаємо обличя каскадами
def search_faces(image_path, file_name):
    image_path = (r"%s" % image_path)
    face_cascade = cv2.CascadeClassifier(r"/home/pi/opencv/opencv-4.1.2/data/haarcascades_cuda/haarcascade_frontalface_default.xml")
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,   # <-- scale ratio for new face finding cicle
        minNeighbors=9,    # <-- accuracy 
        minSize=(10, 10)   # <-- Min size of face in pixels
    )
    faces_detected = str(format(len(faces)))
    # Зберігаємо шлях до фото в змінну
    background = Image.open('/home/pi/mybot/in/received/photos/' + file_name) # <-- background image
    foreground = Image.open('/home/pi/mybot/out/pokemons/1.png')              # <-- foreground image
    # Визнчаємо для кожного обличчя випадкову картинку зі списку
    for (x, y, w, h) in faces:
        foreground = Image.open(random.choice(['/home/pi/mybot/out/pokemons/1.png',
                                               '/home/pi/mybot/out/pokemons/2.png',
                                               '/home/pi/mybot/out/pokemons/3.png',
                                               '/home/pi/mybot/out/pokemons/4.png',
                                               '/home/pi/mybot/out/pokemons/7.png',
                                               '/home/pi/mybot/out/pokemons/9.png',]))
        # Покемони з вухами чи чубом мають більший зазор альфа-канала по боках
        # тому якщо випдає такий покемон треба змінити його розміри тким чином
        # щоб ширина у всіх відповідала ширині знйдених облич
        if foreground == Image.open('/home/pi/mybot/out/pokemons/1.png') or foreground == Image.open('/home/pi/mybot/out/pokemons/9.png'):
            foreground = foreground.resize((int(w*1.3), int(h*1.3)), Image.ANTIALIAS)
        else:
            foreground = foreground.resize((int(w*1.1), int(h*1.1)), Image.ANTIALIAS)
        # Об'єднуємо два зобрження
        if foreground == foreground.resize((int(w*1.3), int(h*1.3)), Image.ANTIALIAS):
            background.paste(foreground, (x-int(w/10), y-int(h/7)), foreground)
        else:
            background.paste(foreground, (x, y-int(h/10)), foreground)
        # Зберігаємо файл після кожного об'єднання
        background.save('/home/pi/mybot/in/received/photos/' + file_name)
    # збереження файла для відправки користувачу
    background.save('/home/pi/mybot/out/' + file_name)
    return faces_detected


@bot.message_handler(commands=['cputemp'])
def cputemp(message):
    if message.chat.id != admin_id: #перевіряємо право доступу
        bot.reply_to(message, "Sorry.\nThis information available only for admin.")
    else:
        bot.reply_to(message, "Raspberry Pi current CPU temperature is: %s °C \n(high = %s °C, critical = %s °C)" % (
                     format(cpu_temperature(), '.1f'), 82, 85))


@bot.message_handler(commands=['memoryspace'])
def memory(message):
    if message.chat.id != admin_id: #перевіряємо право доступу
        bot.reply_to(message, "Sorry.\nThis information available only for admin.")
    else:
        bot.reply_to(message, memory_space())


# перевірка температури процесора машини на якій запущено код
def cpu_temperature():
    if not hasattr(psutil, "sensors_temperatures"):
        sys.exit("platform not supported")
    temps = psutil.sensors_temperatures()
    if not temps:
        sys.exit("can't read any temperature")
    for name, entries in temps.items():
        for entry in entries:
            return entry.current


# перевірка стану пам'яті машини на якій запущено код
def memory_space():
    disk_usage = psutil.disk_usage('/')
    total = ("Total space: " + format(((((disk_usage.total)/1024)/1024)/1024), '.2f') + " Gb")
    used = ("\nUsed space: " + format(((((disk_usage.used)/1024)/1024)/1024), '.2f') + " Gb " + str(disk_usage.percent) + "%")
    free = ("\nFree space: " + format(((((disk_usage.free)/1024)/1024)/1024), '.2f') + " Gb " + str(100 - (disk_usage.percent)) + "%")
    return total + used + free


# Цикл для постійної роботи бота
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(15)  # <-- Wake up after 15 for prevent crashing
