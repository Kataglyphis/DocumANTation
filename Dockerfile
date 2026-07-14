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

# Pinned uv installer (reproducible; avoids "curl | sh" pulling a moving target).
ARG UV_VERSION=0.11.3
RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh

# Install the pinned runtime dependencies from the lockfile into the md2pdf venv.
# We export the lock to a requirements file and pip-install it, then delete the
# project metadata so it does NOT linger at / — otherwise runtime `uv run`
# (used by the build scripts) would discover it and spawn a stray .venv instead
# of using this md2pdf venv. The project itself runs from the mounted
# /md2pdfLib volume and is never installed (see [tool.uv] package = false).
COPY pyproject.toml uv.lock /tmp/deps/
RUN uv venv md2pdf && \
    . md2pdf/bin/activate && \
    uv export --frozen --no-dev --no-emit-project --project /tmp/deps -o /tmp/requirements.txt && \
    uv pip install -r /tmp/requirements.txt && \
    rm -rf /tmp/deps /tmp/requirements.txt

ARG PANDOC_VERSION=3.9.0.2
# SHA256 of the official pandoc .deb releases (verify tamper-free downloads).
ARG PANDOC_SHA256_AMD64=ce4ac48f48aa7eadc1f5dbdf3449a1739f188ecb8c5421c5adc070fe7479e567
ARG PANDOC_SHA256_ARM64=2e77b311be7d1c3b40b5475c6cd5bd44ba02d7d9683e3eecb3324baebf16e4d8
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
ADD md2pdfLib/presentation/template/latex/awesome-beamer /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/presentation/template/latex/smile /root/texmf/tex/latex/commonstuff/
RUN texhash

VOLUME ["/md2pdfLib"]
VOLUME ["/data"]

CMD ["/bin/bash", "-c", ". md2pdf/bin/activate && exec /bin/bash"]
