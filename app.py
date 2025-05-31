# ... الاستيرادات كما هي

app = Flask(__name__)

# إعدادات الرفع
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ربط قاعدة البيانات من متغير البيئة
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # أفضل من وضع الرابط مباشرة
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ... بقية الكود بدون تغيير