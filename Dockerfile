FROM python:3.9.2
WORKDIR /BackTaxDeductSystem
COPY requirements-docker.txt /BackTaxDeductSystem/
RUN pip install -r requirements-docker.txt --no-cache-dir
COPY . /BackTaxDeductSystem/