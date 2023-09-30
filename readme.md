# Component Lifetime Data Project

This project provides a system to store, manage, and analyze the lifetime data of components related to storm surge barriers. The project is centered around a FastAPI application that exposes endpoints for various CRUD operations, enabling users to capture details of component lifetimes, insert new component data, fetch lifetime intervals, among other tasks. The primary data storage solution is a PostgreSQL database, which is easily manageable using DBeaver.

## Introduction

Storm surge barriers play a pivotal role in protecting low-lying regions from potential floods due to rising sea levels and frequent storm surges. To ensure their reliability, it's crucial to closely monitor the lifetime and reliability of individual components. This project serves as a comprehensive database system that catalogs component lifetime data, thereby aiding in the understanding of the overall reliability behavior of storm surge barriers over time. Using the FastAPI framework, we provide a robust and user-friendly API to seamlessly interact with this database.

## Setting Up Development Environment

### Creating a Python Virtual Environment

1. Open your terminal and navigate to the project directory.
2. Run the command to generate a virtual environment named `venv`:
    ```bash
    python3 -m venv venv
    ```

3. Activate the virtual environment:
    - **Windows**:
        ```bash
        .\\venv\\Scripts\\Activate
        ```

    - **macOS and Linux**:
        ```bash
        source venv/bin/activate
        ```

### Installing Required Packages

1. A `requirements.txt` file should contain all essential packages, such as:
    ```
    fastapi
    uvicorn
    sqlalchemy
    python-dotenv
    ```

2. Install these packages using the command:
    ```bash
    pip install -r requirements.txt
    ```

## Running the FastAPI application

1. FastAPI is a state-of-the-art web framework built on Starlette and Pydantic, allowing swift and effective API creation.
2. Uvicorn serves as the ASGI server, acting as the bridge between the FastAPI application and external requests.
3. Launch the FastAPI application using:

    ```bash
    uvicorn your_component_lifetime_app:app --reload
    ```

   Replace `your_component_lifetime_app` with your application file's name (excluding the `.py`).
4. Access the application at `http://127.0.0.1:8000`.

## Generating a Database

### Installing and Setting up DBeaver

1. Fetch DBeaver from [the official website](https://dbeaver.io/).
2. After installation, initiate DBeaver.
3. Navigate to `Database` in the menu, and select `New Database Connection`.
4. Choose `PostgreSQL` and enter your database credentials.

### Setting up a Local PostgreSQL Server in DBeaver

1. Within DBeaver, right-click on `Databases` located in the `Database Navigator`.
2. Navigate to `Create` -> `Database`.
3. Name your new database `componentLifetimeData`.
4. Modify other properties if needed, and click `OK`.

### Running the Database Initialization Script

1. Configure your `.env` file with the proper database details.
2. Open a terminal in the project's root directory.
3. Activate the Python virtual environment:
    - **Windows**:
        ```bash
        .\\venv\\Scripts\\Activate
        ```

    - **macOS and Linux**:
        ```bash
        source venv/bin/activate
        ```

4. Execute the database initialization script:
    ```bash
    python create_database.py
    ```

This action will structure the tables in the `componentLifetimeData` database based on the pre-defined models.

## Incorporating Records to the Database

For bulk data insertion:

1. Prepare a JSON file with the required records. Each entry should adhere to this structure:

    ```json
    {
        "StartDate": "YYYY-MM-DD",
        "StartTime": "HH:MM:SS",
        "EndDate": "YYYY-MM-DD",
        "EndTime": "HH:MM:SS"
    }
    ```

2. Use the supplied API endpoints (or tools like `curl` or Postman) to transmit records to the server. If needed, account for rate limits and segment your data.

For easy conversion from Excel to JSON, consider the following online utility: [https://tableconvert.com/excel-to-json](https://tableconvert.com/excel-to-json).


### Inserting Initial Lifetime Records for Components

As we began observing the components' lifetimes on 20 May 2010, it's essential to initialize each component's record with this start date. Although we don't possess information on the exact lifetimes of these components before this date, we make the working assumption that their observations effectively began from this point.

To set the initial start date for each object in the database:
```sql
INSERT INTO public."ObjectLifetime" ("ID", "ObjectCodeID", "StartDate")
SELECT gen_random_uuid(), "ID", '2010-05-20'
FROM public."ObjectCode";


## Alembic for Database Migrations

Alembic is a database migration tool for SQLAlchemy, the ORM (Object Relational Mapper) that we are using in our project. It helps manage database schema changes by providing a way to define and track schema changes using "migration scripts." Alembic is especially useful when collaborating with others or when deploying updates to a live environment, as it ensures consistent database states across different environments.

### Setting Up Alembic

1. First, make sure you've already created and activated your virtual environment as outlined above.
2. Install Alembic by running:
    ```bash
    pip install alembic
    ```

3. Next, initialize Alembic within your project:
    ```bash
    alembic init alembic
    ```

   This command will generate an `alembic` directory at your project root with configuration files and a `versions` folder.

4. Modify `alembic.ini` and adjust the following line:
    ```ini
    sqlalchemy.url = driver://user:password@localhost/dbname
    ```

   Replace the placeholder values (`driver`, `user`, `password`, `localhost`, `dbname`) with the appropriate connection string for your PostgreSQL database.

5. In `alembic/env.py`, adjust the target metadata:
    ```python
    from your_component_lifetime_app.models import Base  # Import the base from your SQLAlchemy models
    target_metadata = Base.metadata
    ```

### Generating and Running Migrations

1. Whenever you modify the database models in your FastAPI application, you can auto-generate migration scripts:

    ```bash
    alembic revision --autogenerate -m "Short description of changes"
    ```

    This command will produce a new script in the `alembic/versions` directory.

2. To apply the migrations and update the database schema:
    ```bash
    alembic upgrade head
    ```

3. If you need to revert a migration:
    ```bash
    alembic downgrade -1
    ```

    This command will undo the most recent migration.

### Additional Resources

For more comprehensive details on Alembic, refer to the [official documentation](https://alembic.sqlalchemy.org/en/latest/index.html).
