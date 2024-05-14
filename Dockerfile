# Dockerfile
# docker build . -t pandoc_all
# WINDOWS: docker run -it --rm -v ${PWD}:/data --name mypandoc -h mypandoc pandoc_all
# LINUX: docker run -it --rm -v $(pwd):/data --name mypandoc -h mypandoc pandoc_all
# docker start -ai mypandoc
FROM ubuntu:22.04
ENV TZ="Europe/Berlin" 

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update -y && \
	apt-get upgrade -y && \
	apt-get -y install sudo && \
    apt-get install -y -o Acquire::Retries=20 \
                     --no-install-recommends \
	  texlive-full \
      texlive-latex-recommended \
      texlive-latex-extra \
      texlive-fonts-recommended \
      texlive-lang-german \
      texlive-pstricks \
      texlive-fonts-extra \
	  lmodern \
      imagemagick \
      unzip \
      python3 \
      ghostscript \
      locales \
      joe \
      vim \
	  nano \
	  emacs \
      curl \
      wget \
      ca-certificates \
      less && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# install a specific Pandoc version for amd64 or arm64 platform
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "amd64" ]; then \
      curl -L https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-1-amd64.deb \
        -o /tmp/pandoc.deb && \
      dpkg -i /tmp/pandoc.deb && \
      rm /tmp/pandoc.deb; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
      curl -L https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-1-arm64.deb \
        -o /tmp/pandoc.deb && \
      dpkg -i /tmp/pandoc.deb && \
      rm /tmp/pandoc.deb; \
    fi
   

# install fonts
# (unfortunately, we cannot provide the fonts file)
ADD Roboto.zip /usr/local/share/texmf
RUN texhash 

# /data volume
# connect to your local directory with *.md files
# when executing docker run:
# - docker run -v $(pwd):/data 
# - docker run -v $(pwd):/data:z   (:z option necessary for RHEL, Fedora)
VOLUME  ["/data"]

# start command
ENTRYPOINT ["/bin/bash"]
