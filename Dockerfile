# Dockerfile
# nerdctl build . -t pandoc_all
FROM ubuntu:26.04
ENV TZ="Europe/Berlin"
ENV PATH="/root/.local/bin:${PATH}"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get -y install sudo && \
    apt-get install -y -o Acquire::Retries=20 \
    --no-install-recommends \
    lmodern \
    imagemagick \
    python3-full \
    python3-pip \
    ghostscript \
    locales \
    curl \
    wget \
    ca-certificates \
    texlive-full \
    less && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

RUN uv venv md2pdf && \
    . md2pdf/bin/activate && \
    uv pip install Pygments

ARG PANDOC_VERSION=3.9.0.2
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "amd64" ]; then \
    curl -L "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-amd64.deb" \
    -o /tmp/pandoc.deb && \
    dpkg -i /tmp/pandoc.deb && \
    rm /tmp/pandoc.deb; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
    curl -L "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-arm64.deb" \
    -o /tmp/pandoc.deb && \
    dpkg -i /tmp/pandoc.deb && \
    rm /tmp/pandoc.deb; \
    fi

RUN mkdir -p /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/presentation/template/latex/awesome-beamer /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/presentation/template/latex/smile /root/texmf/tex/latex/commonstuff/
RUN texhash

VOLUME ["/md2pdfLib"]
VOLUME ["/data"]

CMD ["/bin/bash", "-c", ". md2pdf/bin/activate && exec /bin/bash"]
