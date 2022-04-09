# Slide-view

Biomedical project

## Setup

- On project initialisation, clone the repository using

```sh
git clone https://github.com/parthjetani/Slide-view.git
```

> _Note:_ This needs to be done only once

## Create and activate virtual environment

Create virtual environment

```sh
python -m venv venv
```

After creating a virtual environment (optional), activate it by running

For windows, activate it this way

```sh
venv/Scripts/activate
```

For other operating system like Linux and MacOS, use

```sh
source venv/bin/activate
```

## Installing project dependencies

To install the project dependencies, use

```sh
pip install -r requirements.txt
```

> _Note:_ Create .env file inside project directory

> _Note:_ And Copy the content of env file into .env file and fill the information

## Run script to get extracted data

For windows, activate it this way

```sh
python .\manage.py makemigrations
python .\manage.py migrate
python .\manage.py runserver
```

For other operating system like Linux and MacOS, use

```sh
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```