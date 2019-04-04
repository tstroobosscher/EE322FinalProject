
PWD=$(shell pwd)

TARGET=main.py

HRTF_FILES=$(PWD)/full
DRYSPEECH=$(PWD)/dryspeech.wav

all:
	pyinstaller --onefile $(TARGET)
	cp -fpr $(HRTF_FILES) $(PWD)/dist/
	cp -fpr $(DRYSPEECH) $(PWD)/dist/
