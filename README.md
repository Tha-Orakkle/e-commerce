# E-commerce Platform Backend

A multi-vendor e-commerce backend built with Django + Django REST Framework.  
Supports shops, products, carts, orders, payments (Paystack), and asynchronous processing with Celery + Redis.

---

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation-development)
- [API Documentation](#api-documentation)
- [Environment variables](#environment-variables-example)
- [Response](#response)
- [Testing](#testing)
- [Usage](#usage)
- [Concurrency strategy](#concurrency-strategy)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- User auth & roles (shop owners/staff, customers)
- Orders & inventory management with concurrency control
- Shopping cart support
- Payment integration with [Paystack](https://paystack.com)
- Asynchronous tasks with Celery + Redis
- Swagger/OpenAPI documentation
- Unit tests for key functionality
- CI/CD pipeline using GitHub Actions

---

## Tech Stack
- Python 3.10+  
- Django  
- Django REST Framework  
- Celery (task queue)  
- Redis (broker / cache)  
- MySQL / PostgreSQL (configurable)  
- Swagger / drf-spectacular (API docs)  
- GitHub Actions (CI/CD)

---

## Installation (development)

1. Clone the repo:
```bash
git clone https://github.com/Tha-Orakkle/e-commerce.git
cd e-commerce
```

2. Create & activate a venv:
```bash
python3 -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate.bat # Windows
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Copy `.env-sample` → `.env` and fill values (see below).

5. Run migrations:
```bash
python manage.py migrate
```
6. Create a superuser:
```bash
python manage.py createsuperuser
```
Enter the required details when prompted.

7. Start local services:
* Redis server:
```bash
redis-server
```
* Django
```bash
python manage.py runserver
```
8. Start Celery worker and beat (in separate terminals):
```bash
# worker
celery -A core worker --loglevel=info

# beat
celery -A core beat --loglevel=info
```

---

## API Documentation
Interactive API docs are available at `/api/docs/` (Swagger UI) and `/api/redoc/` (Redoc).

---

## Environment variables (example)
Your `.env` should include at least:
```ini
SECRET_KEY=...
DEBUG=True
DB_NAME=ecommerce_db
DB_USER=root
DB_HOST=localhost
DB_PASSWORD=password
DB_PORT=3306
PAYSTACK_SECRET_KEY=...
EMAIL_PORT=587
EMAIL_HOST_USER="sample@gmail.com"
EMAIL_HOST_PASSWORD="password"
```
For a full list of environment variables, see `.env-sample`.

---

## Response
All API responses follow a consistent structure:

* ### success response
```json
{
  "status": "success",
  "message": "string",
  "data": {
    "id": 123,
    ...
  }
}
// When there is no data, the data field won't be present
```

* ### paginated response
```json
{
  "status": "success",
  "message": "string",
  "data": {
    "count": 6,  // Total number of items
    "next": "string" | null,  // URL to the next page of results, or null
    "previous": "string" | null,  // URL to the previous page
    "results": [...]  // List of items for the current page
  }
}

```

* ### error response
```json
{
  "status": "error",
  "code": "string",  // A string code representing the error type
  "message": "string",  // Error message
  "errors": {} | null  // Any errors encountered during the request
}
```

---

## Testing
Run tests with:
```bash
pytest
```

## Usage
- Use the provided API endpoints to manage shops, products, carts, orders, and user accounts.
- Refer to the Swagger documentation for detailed information on each endpoint, including request and response formats.

## Concurrency strategy
- Uses pessimistic locking (`transaction.atomic` + `select_for_update`) to ensure safe concurrent updates to orders and inventory.




## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes. Ensure that your code adheres to the existing style and includes appropriate tests.


## License
