# Technical test about currency conversion API

## Purpose

This repository is a project following Clean Architecture, done with Django and PostgreSQL, PEP8 styling.  

Its purpose is to give a simplified API to convert the value of a given currency to its target currency.


## How to setup the project

Prerequisites: Docker + Docker Compose (install the desktop app or the docker engine https://docs.docker.com/get-started/)

Copy .env.example to .env

then start the project with `docker compose up -d` 


## Commands

Tests : `docker compose exec app pytest`

Linter : `docker compose exec app ruff check .` 

Formatter : `docker compose exec app ruff format --check .`
