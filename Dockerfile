FROM mambaorg/micromamba:latest

SHELL ["/usr/local/bin/_dockerfile_shell.sh"]

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml

ARG MAMBA_DOCKERFILE_ACTIVATE=1

RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

# Set a working directory owned by the non-root mamba user
WORKDIR /home/$MAMBA_USER/app
COPY --chown=$MAMBA_USER:$MAMBA_USER . .

EXPOSE 5000

CMD ["gunicorn" ,\
    "step_ingestor:app" ,\
    "-b" ,\
    "0.0.0.0:5000" ,\
    "--keyfile" ,\
    "localhost+2-key.pem" ,\
    "--certfile" ,\
    "localhost+2.pem" ]
