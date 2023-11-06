FROM python:3.11.4
COPY . .
RUN pip install .
CMD ["python", "-m uvicorn main:app --reload "]
