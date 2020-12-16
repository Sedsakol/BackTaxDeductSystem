FROM python:3.9
WORKDIR /BackTaxDeductSystem
COPY requirements.txt /BackTaxDeductSystem/
RUN pip install -r requirements.txt
COPY BackTaxDeductSystem/ /BackTaxDeductSystem/