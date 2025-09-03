FROM apache/airflow:2.8.0
USER root
RUN apt-get update && \
apt-get install -y docker.io && \
apt-get clean
RUN usermod -aG docker airflow
USER airflow