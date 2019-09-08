FROM python:3-slim
ADD blurbot.py /
RUN pip install requests pillow pyTelegramBotAPI
CMD [ "python", "./blurbot.py" ]
