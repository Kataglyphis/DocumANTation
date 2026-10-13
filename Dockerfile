# nerdctl build . -t pandoc_all
FROM ubuntu:26.04
ENV TZ="Europe/Berlin"
ENV PATH="/root/.local/bin:${PATH}"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y -o Acquire::Retries=20 \
    --no-install-recommends \
    lmodern \
    imagemagick \
    python3-full \
    python3-pip \
    ghostscript \
    locales \
    curl \
    ca-certificates \
    texlive-full \
    less && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Pinned uv installer (reproducible; avoids "curl | sh" pulling a moving target).
ARG UV_VERSION=0.13.0
RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh

# Delete the project metadata after install, or a runtime `uv run` finds it at / and spawns a stray .venv.
COPY pyproject.toml uv.lock /tmp/deps/
RUN uv venv md2pdf && \
    . md2pdf/bin/activate && \
    uv export --frozen --no-dev --no-emit-project --project /tmp/deps -o /tmp/requirements.txt && \
    uv pip install -r /tmp/requirements.txt && \
    rm -rf /tmp/deps /tmp/requirements.txt

ARG PANDOC_VERSION=3.12.1
# SHA256 of the official pandoc .deb releases (verify tamper-free downloads).
ARG PANDOC_SHA256_AMD64=b4217ac7c54067c442f9d4cd38bcd0c184a43f3e7053431a12263a6f92a33ba2
ARG PANDOC_SHA256_ARM64=38f44718c0cb15cb81fc31026bd68c33e8628ca5f7ab15ca86494a7f24f7b8e4
ARG TARGETARCH
RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) sha="$PANDOC_SHA256_AMD64" ;; \
      arm64) sha="$PANDOC_SHA256_ARM64" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fL "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-${TARGETARCH}.deb" -o /tmp/pandoc.deb; \
    echo "${sha}  /tmp/pandoc.deb" | sha256sum -c -; \
    dpkg -i /tmp/pandoc.deb; \
    rm /tmp/pandoc.deb

RUN mkdir -p /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/third_party/awesome-beamer /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/third_party/smile /root/texmf/tex/latex/commonstuff/
RUN texhash

VOLUME ["/md2pdfLib"]
VOLUME ["/data"]

CMD ["/bin/bash", "-c", ". md2pdf/bin/activate && exec /bin/bash"]
