import tkinter as tk
import tkinter.filedialog as fd
import speech_recognition as sr

def openfile():
    fpath = fd.askopenfilename()
    r = sr.Recognizer()
    with sr.AudioFile(fpath) as source:
        audio = r.record(source)
    text = r.recognize_google(audio, language='ja-JP')
    print(text)
        


root = tk.Tk()
root.geometry("300x400")

lbl = tk.Label(text="開く")
bt = tk.Button(text="open", command = openfile)


lbl.pack()
bt.pack()
tk.mainloop()
