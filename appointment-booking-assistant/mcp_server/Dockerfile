FROM --platform=$BUILDPLATFORM python:3.11@sha256:6f4ad35576ea868518b5621c31595bf5a56b9b0c333f18118c868543c7f7cf40
WORKDIR /app
COPY appointment_server_http.py /app/
RUN pip install fastmcp==2.11.3
ENTRYPOINT [ "python" ]
