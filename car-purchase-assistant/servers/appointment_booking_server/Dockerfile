FROM --platform=$BUILDPLATFORM python:3.11@sha256:6f4ad35576ea868518b5621c31595bf5a56b9b0c333f18118c868543c7f7cf40
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
