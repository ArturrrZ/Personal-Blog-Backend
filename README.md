# Backend API - README

## Overview
This is a Django REST Framework (DRF) backend that supports a social platform with user authentication, post creation, subscription plans, and payment processing using Stripe. The authentication system uses JWT (JSON Web Tokens) for secure user access.

## Features
- **User Authentication**
  - User registration and login/logout with JWT authentication.
  - Token refresh mechanism for access token renewal.
- **User Profiles**
  - View user profiles.
  - Subscribe to creators.
- **Posts Management**
  - Create, edit, and delete posts.
  - Like and report posts.
- **Subscription System**
  - Users can subscribe to content creators.
  - Creators can register and manage their subscription plans.
  - Stripe integration for payment processing.
- **Stripe Integration**
  - Subscription-based payments using Stripe.
  - Automatic subscription handling and cancellations.

## Technologies Used
- **Django** (Python web framework)
- **Django REST Framework (DRF)**
- **JWT Authentication (djangorestframework-simplejwt)**
- **Stripe API for payments**
   ```

## Environment Variables
Create a `.env` file in the root directory and set the following:
```
SECRET_KEY=<your-secret-key>
DEBUG=True  # Set to False in production
DATABASE_URL=<your-database-url>
STRIPE_SECRET_KEY=<your-stripe-secret-key>
```

## API Endpoints

### Authentication
- **Register**: `POST /api/auth/register/`
- **Login**: `POST /api/auth/login/`
- **Logout**: `GET /api/auth/logout/`
- **Token Refresh**: `POST /api/auth/token/refresh/`
- **Check Authentication**: `GET /api/auth/check/`

### User & Profiles
- **Get Profile**: `GET /api/profile/{username}/`
- **Become a Creator**: `POST /api/creator/`
- **View Creator Dashboard**: `GET /api/creator/`

### Posts
- **Create Post**: `POST /api/posts/`
- **Edit Post**: `PUT /api/posts/{id}/`
- **Delete Post**: `DELETE /api/posts/{id}/`
- **Like/Unlike Post**: `PUT /api/posts/{id}/like/`
- **Report Post**: `POST /api/posts/{id}/report/`

### Subscriptions
- **Subscribe to Creator**: `POST /api/subscriptions/`
- **View Subscriptions**: `GET /api/subscriptions/`
- **Cancel Subscription**: `POST /api/subscriptions/cancel/`

### Stripe Payments
- **Create Checkout Session**: `POST /api/stripe/checkout/`
- **Stripe Webhook**: `POST /api/stripe/webhook/`
- **Success Page**: `GET /api/success/`
- **Cancel Page**: `GET /api/cancel/`

## Usage
1. Register a new user via `/api/auth/register/`
2. Log in and receive JWT tokens.
3. Use the access token in the `Authorization` header (`Bearer <token>`) for protected routes.
4. Create or subscribe to content.
5. Use Stripe checkout for payments.

## Notes
- Ensure you have a Stripe account and set up the necessary API keys.
- For production, configure secure settings for cookies and HTTPS enforcement.
- Use PostgreSQL for a more robust database solution.
- Redis and Celery are used for background task processing (e.g., sending emails, processing payments).


