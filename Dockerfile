FROM sagemath/sagemath:latest
RUN sudo apt-get update && sudo apt-get install -y libpq-dev
COPY requirements.txt .
RUN sage --pip install --upgrade pip && sage --pip install -r requirements.txt
RUN  sudo apt-get update && sudo apt-get install -y --reinstall ca-certificates && sudo update-ca-certificates
EXPOSE 8080
COPY ./ .
RUN sudo chown -R sage:sage utils
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

