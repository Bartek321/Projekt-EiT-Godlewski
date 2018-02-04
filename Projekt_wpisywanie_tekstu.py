from clients_engines.audio_provider import get_audio
from clients_engines.dictation_client import DictationClient
import time
from subprocess import check_output
import grpc
import threading
from pydub import AudioSegment
import pyaudio
import wave
from array import array

def thread():
        lastList = []
        iterator = 1

        pasteScript = 'script.vbs'
        backScript = 'script2.vbs'
        dict = { "4" : "", "kropka" : ".", "przecinek" : ",", "wykrzyknik" : "!", "pytajnik" : "?" }    
  
        while True:                             
            while len(Data) <= iterator:            #usypia i czeka na nowe dane
                time.sleep(0.01)
       
            sound1 = AudioSegment(                  #obiekt AudioSegment z nowymi nagranymi danymi
                data=Data[iterator],
                sample_width=2,
                frame_rate=44100,
                channels=1
            )

            iterator += 1                           #inkrementacja, nastepna iteracja dla nowych danych

            results = dc.recognise(method="sync", audio=sound1)         #wyslanie dzwieku do SARMATA
            zmienna = results[0]['transcript']                          #wyodrebnienie samego tlumaczenia
                
            list = zmienna.split()                  #podzial tlumaczenia na pojednycze slowa
            list.append("")
            list1 = []
            indeks = 0

            for index, i in enumerate(list):                #petla sprawdza liste i wykonuje odpowiednie operacje dla slow specjalnych
                list1.append(i)
                if indeks != len(list) - 1 and len(list) > 2:       #wykonuje sie dla wiecej niz 1 slowa
                    if i == "kasuj" and indeks == 0:                #kasuje ostatnie slowo z poprzedniej listy
                        list1.pop(indeks)
                        indeks -= 1
                        for i in range(len(lastList[-2]) + 1):
                            check_output(backScript, shell=True).decode() 
                    elif i == "kasuj":                              #kasuje poprzednie slowo
                        list1.pop(indeks)
                        list1.pop(indeks - 1)
                        indeks -= 2
                    
                    #usuwa jedno slowo jezeli powtorzone zostaly 2 razy slowa kluczowe
                    if (i == "kasuj" and list[index + 1] == "kasuj") or (i == "kropka" and list[index + 1] == "kropka") or (i == "przecinek" and list[index + 1] == "przecinek") or (i == "pytajnik" and list[index + 1] == "pytajnik") or (i == "wykrzyknik" and list[index + 1] == "wykrzyknik") or (i == "akapit" and list[index + 1] == "akapit"):
                        list1.pop(indeks)
                        indeks -= 1
                    elif indeks == 0 and (i == "kropka" or i == "przecinek" or i == "wykrzyknik" or i == "pytajnik"):  #wstawia znak interpunkycjny przed poprzednim slowem z poprzedniej listy
                        check_output(backScript, shell=True).decode() 
                        list1[indeks] = dict[i]
                    elif i == "kropka" or i == "przecinek" or i == "wykrzyknik" or i == "pytajnik":     #wstawia znak interpunkycjny przed poprzednim slowem
                        list1.pop(indeks)
                        list1[indeks - 1] += dict[i]
                        indeks -= 1
                 
                    indeks += 1

            #reaguje na pojedyncze slowo specjalne
            if (len(list) == 2) and (list[0] == "kasuj" or list[0] == "kropka" or list[0] == "przecinek" or list[0] == "wykrzyknik" or list[0] == "pytajnik"):
                check_output(backScript, shell=True).decode()   
                list1[0] = dict[list[0]]
            if len(list) == 2 and list[0] == "kasuj":
                for i in range(len(lastList[-2])):
                    check_output(backScript, shell=True).decode()   
                    
            if len(list) == 2 and list[0] == "akapit":               #reaguje na slowo akapit, wstawia znak nowej linii
                list1[0] = ""
                check_output("echo." + "" + "|clip", shell=True).decode()
                check_output(pasteScript, shell=True).decode()        
        
            if len(list1) < 2:       
                list1.append("") 
              
            zmienna = ' '.join(list1)                       #laczy listy, zapisuje do schowka i wkleja
            check_output("echo|set /p=" + zmienna + "|clip", shell=True).decode()
            check_output(pasteScript, shell=True).decode()

            lastList = list1                    #zapisanie listy
        return

if __name__ == '__main__':
    address = "149.156.121.122:2789"
    dc = DictationClient(address)

    CHUNK = 1000
    FORMAT = pyaudio.paInt16
    RATE = 44100
    RECORD_SECONDS = 50

    p = pyaudio.PyAudio()                   #stworzenie streamu do nagrywania z mikrofonu

    stream = p.open(format=FORMAT,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    Data = [b'']    
    data1 = b''
    SIL = 0
    NSI = 0
    rec = True
    send = True

    t = threading.Thread(target=thread, args=())        #start watku
    t.start()

    for i in range(1, int(RATE / CHUNK * RECORD_SECONDS)):      #petla z nagrywaniem
        data = stream.read(CHUNK)               #zapis pojedynczych fragmentow dzwieku

        if rec == True:             #dodawanie fragmentow do paczki, jezeli nagrywanei jest aktywne
            data1 += data
            print("REC")

        a = array('h', data)

        if max(a) < 5000:           #sprawdzania, czy aplituda jets na odpowiednim poziomie, jezeli nie to inkrementacja zmiennej
            SIL += 1
        else:                       #jezeli jest odpowiednia amplituda aktywacja nagrywania i reset zmiennej 
            SIL = 0
            NSI += 1
            print("voice")
            rec = True
            send = True

        if SIL > 15:                #jezeli przez pewien czs jest cisza - dezaktywacja nagrywania
            rec = False

        if SIL == 120 and send == True and NSI > 10:        #po pewnym czasie ciszy i gdy wielkosc paczki jest odpowiednio duza - wysylanie danych i reset zmiennych
            print("silence")
            SIL = 0
            NSI = 0
            Data.append(data1)
            data1 = b''
            send = False
            T = True

    stream.stop_stream()        #zamkniecie streamu
    stream.close()
    p.terminate()



