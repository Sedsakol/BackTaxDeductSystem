FROM python:3.9
WORKDIR /BackTaxDeductSystem
COPY requirements-docker.txt /BackTaxDeductSystem/
RUN pip install -r requirements-docker.txt
COPY . /BackTaxDeductSystem/