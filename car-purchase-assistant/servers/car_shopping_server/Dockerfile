FROM python:3.11-slim@sha256:0b23cfb7425d065008b778022a17b1551c82f8b4866ee5a7a200084b7e2eafbf
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
EXPOSE 10002
ENTRYPOINT [ "python", "car_shopping_server.py" ]
CMD [ "--host", "0.0.0.0" ]
