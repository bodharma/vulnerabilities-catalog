# vulnerabilities-catalog

### HOW2

1. Install poetry
2. Install poetry env using `poetry install`
3. In cli activate poetry env using `poetry shell`
4. run `make start-rabbit` to start rabbitmq
5. run `make start-mongo` to start mongodb
6. now go to `harvester` and run `poetry run python app.py` (here you might have problem with cve data, as it needs an API key, you can get it [here](https://nvd.nist.gov/developers/request-an-api-key))
7. wait until all data would be downloaded and sent to rabbit mq
8. to verify that data is in rabbitmq go to `http://localhost:15672/` and login with `guest:guest`
9. now you might go to `injector` and run `poetry run python processors/cwe.py` to consume cwe data from rabbitmq and inject it to mongodb

Good to know:
- [ ] rabbit folder
- [ ] config.py
- [ ] poetry.lock
- [ ] pyproject.toml

are moved outside harvester and injector folders, as they are shared between them, so to sync them fast with those folder we use makefile

### TODO
1. Add to injector following processors:
    - [ ] cve
    - [ ] epss
2. Add api endpoint to get data from mongodb
3. More time and resources as this is fully separate project with such requirements



Sources used:
1. https://www.first.org/epss/api
2. https://nvd.nist.gov/developers/vulnerabilities
3. https://cwe.mitre.org/data/downloads.html