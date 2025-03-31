# PDF Manipulator

A modern web application for PDF manipulation, offering features like converting images to PDF, merging PDFs, and reordering PDF pages.

## Features

- Convert Images to PDF
- Merge Multiple PDFs
- Reorder PDF Pages
- User Authentication
- Subscription-based Access
- Modern, Responsive UI

## Tech Stack

- Backend: Python/Flask
- Database: PostgreSQL
- Authentication: Flask-Login
- Payment Processing: Stripe
- Frontend: Bootstrap 5, Font Awesome
- PDF Processing: PyPDF2, Pillow

## Prerequisites

- Python 3.7 or higher
- PostgreSQL
- Stripe Account
- Virtual Environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdf-manipulator.git
cd pdf-manipulator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://username:password@localhost:5432/pdfmanipulator
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Development

Run the development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

### Heroku Deployment

1. Create a Heroku account and install the Heroku CLI

2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

4. Configure environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set STRIPE_PUBLIC_KEY=your-stripe-public-key
heroku config:set STRIPE_SECRET_KEY=your-stripe-secret-key
```

5. Deploy the application:
```bash
git push heroku main
```

6. Run database migrations:
```bash
heroku run flask db upgrade
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t pdf-manipulator .
```

2. Run the container:
```bash
docker run -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://username:password@host:5432/pdfmanipulator \
  -e STRIPE_PUBLIC_KEY=your-stripe-public-key \
  -e STRIPE_SECRET_KEY=your-stripe-secret-key \
  pdf-manipulator
```

## Subscription Plans

### Free Plan
- Up to 16MB file size
- 5 files per operation
- 50 operations per month

### Pro Plan ($9.99/month)
- Up to 50MB file size
- 20 files per operation
- 500 operations per month

### Enterprise Plan ($29.99/month)
- Up to 100MB file size
- 100 files per operation
- 2000 operations per month

## Security

- All passwords are hashed using secure algorithms
- File uploads are validated and sanitized
- HTTPS is enforced in production
- Regular security updates and patches

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. # pdfmanipog
