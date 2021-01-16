FROM python:3.8
RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN apt-get update
RUN apt-get install -y libspatialindex-dev libspatialindex-c5 libspatialindex5 vim firefox-esr
RUN pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir  -r requirements.txt
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz
RUN tar -x geckodriver -zf geckodriver-v0.24.0-linux64.tar.gz -O > /usr/bin/geckodriver
RUN chmod +x /usr/bin/geckodriver
RUN rm geckodriver-v0.24.0-linux64.tar.gz
COPY . .