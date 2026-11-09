FROM pals-reliability-network-guard-base:b27f1d8
USER root
RUN apt-get update && apt-get install -y --no-install-recommends nftables && rm -rf /var/lib/apt/lists/*
COPY guard.py budget_proxy.py /opt/pals-local/
ENTRYPOINT ["python", "/opt/pals-local/guard.py"]
