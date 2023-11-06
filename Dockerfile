FROM python:3.11.4
COPY . .
RUN pip install .
EXPOSE 8000
CMD ["python", "-m uvicorn main:app --reload --port 8000"]
