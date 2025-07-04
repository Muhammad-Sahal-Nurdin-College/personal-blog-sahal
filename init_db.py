from app import app
from tables import db, BlogPost, User

with app.app_context():
    # Tambah user dummy (cek dulu biar tidak dobel)
    if not User.query.first():
        user = User(name="Admin", email="admin@example.com", password="admin")
        db.session.add(user)
        db.session.commit()

        # Tambah post dummy
        post = BlogPost(
            title="Hello World",
            subtitle="My First Post",
            date="July 4, 2025",
            body="Ini adalah konten pertama blog Sahal.",
            img_url="https://via.placeholder.com/150",
            author=user
        )
        db.session.add(post)
        db.session.commit()

    print("✅ Dummy user dan post berhasil dibuat.")
