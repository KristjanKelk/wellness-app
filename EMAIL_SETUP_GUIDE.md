# 📧 Email Verification Setup Guide

This guide will help you set up email verification for the Wellness Platform using SendGrid.

## 🚀 Quick Setup (Recommended)

Run the automated setup script:

```bash
python setup_email.py
```

The script will guide you through the entire setup process interactively.

## 📋 Manual Setup

If you prefer to configure manually, follow these steps:

### 1. Create SendGrid Account

1. Go to [SendGrid](https://sendgrid.com/free/) and sign up for a free account
2. You'll get 100 free emails per day (40,000 emails for first 30 days)
3. Verify your SendGrid account via email

### 2. Create API Key

1. Log into your SendGrid dashboard
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Choose **Restricted Access**
5. Give it a name like "Wellness Platform"
6. Under **Mail Send**, select **Full Access**
7. Click **Create & View**
8. **Copy the API key** (starts with `SG.`) - you won't see it again!

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Email Configuration (SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key-here
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Frontend URL (where verification links will point)
FRONTEND_URL=http://localhost:8080

# Other required settings
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Update Django Settings

The email settings are already configured in `wellness_project/settings.py`. They will automatically use your environment variables.

### 5. Test Email Configuration

Run the Django shell to test email sending:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test email sending
send_mail(
    subject='Test Email',
    message='If you receive this, email is working!',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-email@example.com'],
    fail_silently=False
)
```

## 🎯 Email Features

### User Registration Flow

1. **User registers** with email and password
2. **Verification email sent** automatically with token
3. **User clicks link** in email (or enters token manually)
4. **Account activated** and welcome email sent

### Email Types

- **📧 Verification Email**: Sent during registration
- **🔄 Resend Verification**: User can request new link
- **👋 Welcome Email**: Sent after successful verification
- **🔐 Password Reset**: For forgotten passwords

### Email Templates

Professional HTML and text templates included:

- `templates/email/verify_email.html` - Verification email (HTML)
- `templates/email/verify_email.txt` - Verification email (text)
- `templates/email/reset_password.html` - Password reset (HTML)
- `templates/email/reset_password.txt` - Password reset (text)

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMAIL_HOST_PASSWORD` | SendGrid API key | - | ✅ |
| `DEFAULT_FROM_EMAIL` | Sender email address | `noreply@wellnessplatform.com` | ✅ |
| `FRONTEND_URL` | Frontend URL for links | - | ✅ |
| `EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS` | Token expiry time | `24` | ❌ |
| `EMAIL_VERIFICATION_COOLDOWN_MINUTES` | Resend cooldown | `5` | ❌ |

### Django Settings

Key settings in `wellness_project/settings.py`:

```python
# Email verification is mandatory
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# Email backend automatically switches to console in development
# if no SMTP credentials are provided
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# Fallback to console backend in development
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## 🔧 Frontend Integration

### API Endpoints

- `POST /api/users/verify-email/` - Verify email with token
- `GET /api/users/verify-email/?token=xxx` - Alternative verification method
- `POST /api/users/resend-verification/` - Resend verification email

### Frontend Components

- `VerifyEmail.vue` - Handles email verification flow
- `VerifyPrompt.vue` - Shows verification reminder

### User Service Methods

```javascript
// Verify email with token
await UserService.verifyEmail(token);

// Resend verification email
await UserService.resendVerificationEmail(email);
```

## 🚨 Troubleshooting

### Common Issues

**"Authentication failed" error:**
- Check that your SendGrid API key is correct
- Ensure the API key has "Mail Send" permissions
- Verify the key starts with `SG.`

**Emails not being received:**
- Check spam/junk folder
- Verify the "from" email address is valid
- Ensure SendGrid account is verified
- Check SendGrid activity dashboard for delivery status

**"Template not found" errors:**
- Verify email templates exist in `templates/email/`
- Check Django template settings
- Templates will fall back to plain text if HTML fails

**Frontend verification not working:**
- Check that `FRONTEND_URL` matches your frontend URL
- Verify API endpoints are accessible
- Check browser console for JavaScript errors

### Debug Mode

In development, if no email credentials are provided, emails will be printed to the console instead of being sent. This is useful for testing.

### SendGrid Dashboard

Monitor email delivery in your SendGrid dashboard:
- **Activity** → See all sent emails and their status
- **Stats** → View delivery metrics
- **Suppressions** → Check for bounced/blocked emails

## 🏗️ Production Deployment

### Domain Authentication

For production, set up domain authentication in SendGrid:

1. Go to **Settings** → **Sender Authentication**
2. Click **Authenticate Your Domain**
3. Follow the DNS configuration steps
4. This improves email deliverability and removes "via sendgrid.net"

### Security Considerations

1. **Environment Variables**: Never commit API keys to version control
2. **HTTPS**: Use HTTPS for production frontend URLs
3. **Rate Limiting**: SendGrid automatically handles rate limiting
4. **From Address**: Use a domain you own for the from address

### Scaling

SendGrid plans:
- **Free**: 100 emails/day
- **Essentials**: $15/month for 40K emails
- **Pro**: $89.95/month for 100K emails

## 📚 Additional Resources

- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Email Best Practices](https://sendgrid.com/blog/email-best-practices/)

## 🆘 Getting Help

If you encounter issues:

1. Check this guide and troubleshooting section
2. Review Django server logs for error messages
3. Check SendGrid activity dashboard
4. Ensure all environment variables are set correctly
5. Test with the provided setup script

For additional support, check the project's main README.md file.