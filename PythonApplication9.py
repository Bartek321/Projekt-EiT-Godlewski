from clients_engines.audio_provider import get_audio
from clients_engines.dictation_client import DictationClient
import time
from subprocess import check_output
import grpc
import threading

from pydub import AudioSegment

import pyaudio
import wave

if __name__ == '__main__':
    address = "149.156.121.122:2789"
    dc = DictationClient(address)

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"
    wave_filepath = "output.wav"


    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")
    c = threading.Condition()
    o = ''
    def worker(num, m, n):
        global o
        print(n[0])
        print('df: %s' % o)

        sound1 = AudioSegment(
            data=num,
            sample_width=2,
            frame_rate=44100,
            channels=1
        )

        results = dc.recognise(method="streaming", audio=sound1) 
        print ('lol: %s' % results)
        print(len(results))
        for idx, response in enumerate(results):
            if not len(response):
                print("No phrases detected.")
            else:
                print("Transcription:")
                zmienna = "\"{}\"".format(response['transcript'])
                print(zmienna)
                zmienna = zmienna[1:-1]
                print(zmienna)
                if len(zmienna) - len(o) > 0:
                    c.acquire()
                    if len(o) == 0:
                        zmienna = zmienna[len(o):]
                    else:
                        zmienna = zmienna[len(o) + 1:]
                    o = zmienna
                    c.release()
                    print(o)
                
        n[0] += 1
        
        if n[0] % 6 == 0:
            plik = 'script.vbs'
            z = o
            check_output("echo " + z + "|clip", shell=True).decode()
            check_output(plik, shell=True).decode()
            print('lala: %s' % o)
            n[0] = 0
        
        return 
        
    frames = []

    data1 = b''
    n = ['']
    m = [0]

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        data1 += data
        if i % 40 == 0:
            t = threading.Thread(target=worker, args=(data1, n, m ))
            t.start()
            print('dfsdf: %s' % n[0])
      
    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

