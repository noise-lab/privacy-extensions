# Installation

1. Install dependencies

    ```
    # apt-get -y install postgresql-11 python3.7 pipenv postgresql-client libpq-dev
    ```

2. Install Docker

3. Create privext user

    ```
    # adduser privext
    ```

4. Add privext user to docker group

    ```
    # gpasswd -a privext docker
    ```

5. Create privext PostgreSQL user

    ```
    # su - postgres
    $ createuser privext -P
    $ createdb -O privext privext
    ```

6. Clone Git repository

    ```
    # su - privext
    $ git clone git@github.com:noise-lab/privacy-extensions.git
    ```

7. Build Docker containers

    ```
    $ pushd docker/chrome
    $ make docker
    $ popd
    $ pushd docker/firefox
    $ make docker
    $ popd
    ```

# Measurements

* Run `experiments/run.sh` with the corresponding parameters:

    ```
    $ ./experiments/run.sh <logs directory> <database config> <file containing domains> <browser>
    ```

  For example:

    ```
    $ ./experiments/run.sh logs/ experiments/database.ini experiments/tranco_0-1k_99k-100k.txt firefox
    ```
