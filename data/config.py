from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = list(map(int, env.list("ADMINS")))
IP = env.str("ip", "localhost")
OPENAI_API_KEY = env.str("OPENAI_API_KEY")
PRESENTON_URL = env.str("PRESENTON_URL", "http://presenton:80")
