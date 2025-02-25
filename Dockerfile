# Dockerfile
# docker build . -t pandoc_all
# WINDOWS: docker run -it --rm -v ${PWD}/md2pdfLib:/md2pdfLib -v ${PWD}/data:/data --name mypandoc -h mypandoc pandoc_all
# LINUX: docker run -it --rm -v $(pwd)/md2pdfLib:/md2pdfLib -v $(pwd)/data:/data --name mypandoc -h mypandoc pandoc_all

FROM ubuntu:24.04
ENV TZ="Europe/Berlin" 

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get -y install sudo && \
    apt-get install -y -o Acquire::Retries=20 \
    --no-install-recommends \
    lmodern \
    imagemagick \
    unzip \
    python3-full \
    pip \
    ghostscript \
    locales \
    joe \
    vim \
    nano \
    emacs \
    curl \
    wget \
    ca-certificates \
    texlive-full \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-lang-german \
    texlive-pstricks \
    texlive-fonts-extra \
    less && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# for styling our code snippets
RUN python3 -m venv md2pdf && \
    . md2pdf/bin/activate && \
    pip3 install Pygments

# install a specific Pandoc version for amd64 or arm64 platform
# i want to use it on my schlaptop and my himbeerkuchen (raspberrypi)
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "amd64" ]; then \
    curl -L https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-1-amd64.deb \
    -o /tmp/pandoc.deb && \
    dpkg -i /tmp/pandoc.deb && \
    rm /tmp/pandoc.deb; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
    curl -L https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-1-arm64.deb \
    -o /tmp/pandoc.deb && \
    dpkg -i /tmp/pandoc.deb && \
    rm /tmp/pandoc.deb; \
    fi


# install fonts
ADD Roboto.zip /usr/local/share/texmf
# make outr custom themes globally available
RUN mkdir -p /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/presentation/template/latex/awesome-beamer /root/texmf/tex/latex/commonstuff/
ADD md2pdfLib/presentation/template/latex/smile /root/texmf/tex/latex/commonstuff/
RUN texhash
# RUN mktexlsr

# neccessary file for generating pdf (scripts, templates, ... etc.)
VOLUME  ["/md2pdfLib"]
# connect to your local directory with *.md files
VOLUME  ["/data"]

# Activate the virtual environment and start the application
ENTRYPOINT ["sh", "-c", ". md2pdf/bin/activate && exec /bin/bash"]
