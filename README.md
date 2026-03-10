# paddle-ocr

## pyenv install (mac)

brew install pyenv

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc

echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc

echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# 적용
source ~/.zshrc

## Python 3.10 설치 및 PaddleOCR용 환경 세팅 (mac)

## Python 3.10 설치

pyenv install 3.10.14

## 프로젝트 폴더에서 버전 고정

cd your-project

pyenv local 3.10.14

## 가상환경 생성

python -m venv .venv

source .venv/bin/activate

## PaddleOCR 설치

pip install --upgrade pip

pip install paddlepaddle

pip install paddleocr opencv-python


## pyenv install (ubuntu)

### 의존성 패키지 설치 (필수)
sudo apt update

sudo apt install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev git

curl https://pyenv.run | bash

### 쉘 설정 추가

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc

echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc

echo 'eval "$(pyenv init -)"' >> ~/.bashrc

### 적용

source ~/.bashrc


## Python 3.10 설치 및 PaddleOCR용 환경 세팅(ubuntu)

### Python 3.10 설치

pyenv install 3.10.14

### 프로젝트 폴더에서 버전 고정

cd your-project

pyenv local 3.10.14

### 가상환경 생성

python -m venv .venv

source .venv/bin/activate

#### PaddleOCR 설치

pip install --upgrade pip

pip install paddlepaddle

pip install paddleocr opencv-python
