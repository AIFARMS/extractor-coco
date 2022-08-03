FROM python:3.8

ARG VERSION="unknown"
ARG BUILDNUMBER="unknown"
ARG GITSHA1="unknown"

# environemnt variables
ENV VERSION=${VERSION} \
    BUILDNUMBER=${BUILDNUMBER} \
    GITSHA1=${GITSHA1}

WORKDIR /extractor

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY *.py extractor_info.json ./
CMD ["python3", "extractor.py"]
