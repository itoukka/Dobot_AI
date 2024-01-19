#Pydobotin ohjaukseen käytetty kirjasto
import pydobot
#Kirjasto jolla saadaan yhteys Dobottiin serial portin kautta
from serial.tools import list_ports

#Käytetään webbikameralla kuvaamiseen sekä kameralla otettuun kuvaan.
import cv2

#Laskuihin käytetty kirjasto
import numpy as np

#Kirjastot joita käytetään Treenatun mallin käyttöön sekä kuvan processointiin.
import keras
from tensorflow import keras
from keras_preprocessing.image import load_img


import os
import time

#Kuvien käsittelyyn
from PIL import Image, ImageTk

#Kirjasto jolla luodaan säikeet. Säikeillä saadan runnattua kahta koodia samanaikaisesti.
import threading

#Käyttöliittymään käytetyt kirjastot               
from tkinter import YES, BOTH
import customtkinter
from customtkinter import *


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

#Määritetään ikkunana koko sekä nimi
root = customtkinter.CTk()
root.title("Tekoäly lajittelija")
root.geometry("800x600")

#Luodaan muuttuja "switch" napille
switch_var = customtkinter.StringVar(value="on")

#Poistetaan errori liittyen Keras kirjastoon ja CPU:n käyttöön
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

#Tällä määrittelemme onko palikka invalid vai valid
obj = None


#Funktiolla kuva muunnetaan kuvasuhteeseen 150x150
def predict_image(model, filename):
    im = load_img(filename)
    im = im.resize((150, 150))
    im = np.expand_dims(im, axis=0)
    im = np.array(im)
    im = im / 255
    prediction = model.predict([im])[0]
    return prediction[0]

#Kuvan prosessointi funktio. 
def process_picture():
    global obj
    print("# Asetetaan kameraa...")
    #avataan kamera.
    s, img = cam.read()
    if s:
        img = cv2.resize(img, (150, 150))
        #Kameralla otettu kuva tallenetaan tällä nimellä
        cv2.imwrite("object_on_conv.jpg", img)
        print("## kuva otettu")
        #Luodaan ennuste käyttäen äsken otettua kuvaa
        output = predict_image(model, "object_on_conv.jpg")
        print("### model output", output)
        #Verrataan ennusteen lukemaa. Jos ennusteen lukema on yli 0.85 se on valid. Jos switch nappi on kohdassa "värilliset" ja palikka on alle 0.85 se on valid. Tällä saamme muutettua
        #ottaako käsi värilliset vai valkoiset. Invalid ja valid termillä ei ole tässä vaiheessa perjaatteessa väliä.
        if output < 0.85:
            if switch_var.get() == "on":
                print("#### object is valid")
                obj = "valid"
            if switch_var.get() == "off":
                print("#### object is invalid")
                obj = "invalid"
        else:
            if switch_var.get() == "off":
                print("valid")
                obj = "valid"
            if switch_var.get() == "on":
                print("invalid")
                obj = "invalid"

    else:
        # Jos kameraan tulee ongelma
        obj = "invalid"

    return obj

#Funktiolla aloitetaan liikuttamaan robottikättä.
def sort_part():
    global obj
    #Liikuteataan palikka kameran alle ja otetaan kuva käyttäen process_picture funktiota.
    device.conveyor_belt_distance(80, 150, 1)
    time.sleep(2)
    obj = process_picture()
    #Jos palikka on "valid" ja switchi on "valkoinen" asennossa se nostaa sen
    if obj == "valid":
        if switch_var.get() == "off":
            #Valkoisen nosto
            device.conveyor_belt_distance(80, 250, 1)
            time.sleep(0.3)
            device.move_to(13, 120, -10, 80)
            time.sleep(0.3)
            device.move_to(13, 120, 50, 80)
            time.sleep(0.3)
            device.move_to(226, 7, 81, 6)
            time.sleep(0.3)
            device.move_to(226, 7, -4, 6)
            device.suck(True)
            time.sleep(0.3)
            device.move_to(226, 7, 81, 6)
            time.sleep(0.3)
            device.move_to(13, 230, 50, 80)
            time.sleep(0.3)
            device.move_to(13, 230, 0, 80)
            time.sleep(0.3)
            device.suck(False)
            time.sleep(0.3)
            device.move_to(13, 120, -10, 80)
        else:
            #värillinen nosto
            #Muuten robotti nostaa värillisen palikan. Liikeradoissa on erona korkeudet josta palikka nostetaan ja lasketaan.
            device.conveyor_belt_distance(80, 250, 1)
            time.sleep(0.3)
            device.move_to(13, 120, -10, 80)
            time.sleep(0.3)
            device.move_to(13, 120, 50, 80)
            time.sleep(0.3)
            device.move_to(226, 7, 81, 6)
            time.sleep(0.3)
            device.move_to(226, 7, 20, 6)
            device.suck(True)
            time.sleep(0.3)
            device.move_to(226, 7, 81, 6)
            time.sleep(0.3)
            device.move_to(13, 230, 60, 80)
            time.sleep(0.3)
            device.move_to(13, 230, 0, 80)
            time.sleep(0.3)
            device.suck(False)
            time.sleep(0.3)
            device.move_to(13, 120, -10, 80)
    #esim. Jos switchi on asennossa "valkoinen" ja värillinen palikka tunnistetaan, se ohitetaan ja annetaan kulkea liukuhihnan loppuun. 
    else:
        device.conveyor_belt_distance(80, 600, 1)

#CV2 Kirjastoa käyttäen saamme haltuun webbikameran
cam = cv2.VideoCapture(0)

#Funktio jolla saamme live kameran käyttöliittymäämme.
def videoLoop():
    global root
    #Luodaan kameralle "Label" johon se liittetään.
    vidLabel = customtkinter.CTkLabel(root, text="")
    vidLabel.pack()
    #While loopilla samme kuvan päivitettyä käyttöliittymään
    while True:
        #Kuva pitää ensin käsitellä, jotta se voidaan päivittää käyttöliittymään ilman, että päivitykset näkyvät räpsähdellen.
        ret, frame = cam.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(frame)
        vidLabel.configure(image=frame)
        vidLabel.image = frame


#Funktio jota käytämme koodin aloittamiseen.
def start_sort_part_thread():
    global robot_thread
    #Luodaan säike robottikädelle
    robot_thread = threading.Thread(target=sort_part, args=())
    #Aina kun "Aloitus" nappi painaa pitää tarkistaa, ettei koodi luo uuttaa säikettä. Ylimääräiset säikeet veisivät resursseja.
    if robot_thread and robot_thread.is_alive():
        print("Previous thread is still running. Waiting for it to finish...")
        robot_thread.join() # Odota vanhan säikeen lopettamista
    #Aloita uusi säike.
    robot_thread.start()

#funktio switchi napille.
def on_switch_change(*args):
    switch_value = switch_var.get()
    #Päivitetään käyttöliittymään mikä asento on kyseessä
    switchi.configure(text="Värillinen")
    print("Switch state:", switch_value)
    if switch_value == "off":
        print("Switch is OFF")
        switchi.configure(text="Valkoinen")

#avataan portit dobottia varten ja listataan ne.
av_ports = list_ports.comports()
port = av_ports[1].device
print(f'available ports:  {[x.device for x in av_ports]}')

#Määritellään dobotti portille
device = pydobot.Dobot(port=port)

#Määritellään treenattu malli joka on tallennettu koneelle.
model = keras.models.load_model('valid_vs_invalid_model.h5', compile=False)

#Määritellään kameralle oma säike.
camera_thread = threading.Thread(target=videoLoop, args=())


#Aloitetaan kamera säike
camera_thread.start()

#Frame on osa käyttöliittymää johon voi liittää osia. Tämä helpottaa komponenttien järjestelyä.
frame = CTkFrame(root)
frame.pack(expand=YES, fill=BOTH)

#Luodaan oma frame myös napeille jotta saadaan ne samaan paikkaan vierekkäin.
buttons_frame = CTkFrame(frame)
buttons_frame.pack(side=TOP)  # Placed at the top

#Määritellään nappien koko
button_width = 200
button_height = 150

#Määritellään switch napin koko
switch_button_height = 50
switch_button_width = 100


#Lisätään nappi käyttöliittymään ja asetetaan sille arvot, sekä komento joka alkaa painaessa. Painaessa nappia se tarkistaa onko säike olemassa, tuhoaa sen ja luo uuden.
Aloitus_nappi = customtkinter.CTkButton(buttons_frame, text="Aloita", command=start_sort_part_thread, height=button_height, width=button_width)
Aloitus_nappi.pack(side=LEFT, padx=20)

#Switch nappi lisätään käyttöliittymään ja asetetaan sille arvot. Komento switch napille muuttaa arvoa joka määrittää onko kyseessä valkoisen vai värillisen napin nosto.
switchi = customtkinter.CTkSwitch(buttons_frame, text="Värillinen", variable=switch_var, onvalue="on", offvalue="off", command=on_switch_change, switch_height=switch_button_height, switch_width=switch_button_width)
switchi.pack(side=LEFT, padx=20)




# Kameralle tehty "Label" johon saadaan asetettua live kamera kuva.
vidLabel = customtkinter.CTkLabel(frame, text="")
vidLabel.pack()
root.mainloop()