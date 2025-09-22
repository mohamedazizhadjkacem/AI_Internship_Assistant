# AI Internship Assistant 🚀

A Streamlit web application that helps you find and track internship opportunities by scraping LinkedIn and providing intelligent notifications.

## Features

- 🔍 **LinkedIn Job Scraping**: Automatically search for internships on LinkedIn
- 📊 **Dashboard**: Track and manage your internship applications
- 🔄 **Continuous Search**: Background monitoring for new opportunities
- 📱 **Telegram Notifications**: Get notified instantly when new internships are found
- 📝 **Application Tracking**: Keep track of application status and notes
- 👥 **User Management**: Multi-user support with secure authentication

## Setup Instructions

### Prerequisites

- Python 3.8+
- A Supabase account (for database)
- A Telegram bot (optional, for notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI_Internship_Assistant.git
   cd AI_Internship_Assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the template secrets file
   copy .streamlit\secrets.toml.template .streamlit\secrets.toml
   ```

4. **Configure your secrets**
   
   Edit `.streamlit/secrets.toml` with your actual values:
   ```toml
   [SUPABASE]
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-supabase-anon-key-here"
   ```

5. **Set up Supabase Database**
   
   Create these tables in your Supabase project:
   
   ```sql
   -- Users table
   CREATE TABLE users (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     email VARCHAR UNIQUE NOT NULL,
     username VARCHAR NOT NULL,
     telegram_bot_token VARCHAR,
     telegram_chat_id VARCHAR,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Internships table
   CREATE TABLE internships (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     user_id UUID REFERENCES users(id),
     job_title VARCHAR NOT NULL,
     company_name VARCHAR NOT NULL,
     application_link VARCHAR,
     source_site VARCHAR DEFAULT 'LinkedIn',
     status VARCHAR DEFAULT 'new',
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

6. **Set up Telegram Bot (Optional)**
   
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Get your bot token and chat ID
   - Add them to your secrets.toml or user profile

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

1. **Register/Login**: Create an account or login
2. **Search for Internships**: Use the scraper to find opportunities
3. **Track Applications**: Manage your application pipeline
4. **Set up Continuous Search**: Get notified about new opportunities
5. **Configure Notifications**: Set up Telegram alerts

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Your Supabase anon key | Yes |

## Security Notes

- Never commit your `.streamlit/secrets.toml` file
- Use environment variables in production
- Keep your Supabase keys secure
- Use service role key for database operations that require elevated permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

If you encounter any issues, please create an issue on GitHub with:
- Steps to reproduce
- Error messages
- Your environment details