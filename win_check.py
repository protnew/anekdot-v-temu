modules = ['fastapi','uvicorn','sklearn','numpy','pydantic','gtts','openai','faster_whisper','pyaudio','speech_recognition','tkinter']
for m in modules:
    try:
        __import__(m)
        print(f'{m}: OK')
    except ImportError as e:
        print(f'{m}: MISSING ({e})')
