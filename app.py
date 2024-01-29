import time
import redis
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, Boolean, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from threading import Thread


Base = declarative_base()

app = Flask(__name__)


class UserActive(Base):
    __tablename__ = "users_active"
    userid = Column(String, primary_key=True)
    active = Column(Boolean, default=True)
    username = Column(String)


redis_client = redis.Redis(host="localhost", port=6379, db=0)

redis_client.config_set('maxmemory', '100mb')

redis_client.config_set('maxmemory-policy', 'allkeys-lru')

DATABASE_URL = "postgresql://postgres:12345@localhost/chat-app-user-db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def mark_inactive_users():
    while True:
        user_keys = redis_client.keys("user:*:lastActive")
        print(user_keys)
        for key in user_keys:
            print(key)
            user_id = key.decode("utf-8").split(":")[1]
            last_active_timestamp = int(redis_client.get(key))
            time_difference = time.time() - (last_active_timestamp / 1000)
            print(time_difference)
            print(f"user_id is : {user_id}")
            if time_difference > 100:
                new_session = Session()
                try:
                    user = (
                        new_session.query(UserActive)
                        .filter(UserActive.userid == user_id)
                        .first()
                    )
                    print(f"user: {user}")
                    if user:
                        user.active = False
                        new_session.commit()
                        print(f"User {user_id} marked as inactive.")
                except Exception as e:
                    new_session.rollback()
                    print(f"Error marking user {user_id} as inactive:", e)
                finally:
                    new_session.close()
        time.sleep(60)


@app.route("/user/user_activity", methods=["GET"])
def get_user_activity():
    username = request.args.get("username")

    if not username:
        return jsonify({"error": "Username parameter is missing"}), 400

    user = session.query(UserActive).filter(UserActive.username == username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"username": user.username, "active": user.active})


# @app.route('/update-last-active', methods=['POST'])
# def update_last_active():
#     data = request.json
#     user_id = data.get('userId')
#     timestamp = int(time.time() * 1000)
#     redis_client.set(f'user:{user_id}:lastActive', timestamp)
#     user = session.query(UserActive).filter(UserActive.userid == user_id).first()
#     user.active = True
#     session.commit()
#     # print(f"User {user_id} marked as active.")

#     return 'Last active time updated successfully.', 200


@app.route("/update-last-active", methods=["POST"])
def update_last_active():
    data = request.json
    user_id = data.get("userId")
    timestamp = int(time.time() * 1000)
    redis_client.set(f"user:{user_id}:lastActive", timestamp)

    new_session = Session()
    try:
        user = (
            new_session.query(UserActive).filter(UserActive.userid == user_id).first()
        )
        user.active = True
        new_session.commit()
        print(f"Last active time updated successfully for {user_id}.")

    except Exception as e:
        new_session.rollback()
        raise e
    finally:
        new_session.close()

    return "Last active time updated successfully.", 200


@app.route("/user/last_active", methods=["GET"])
def get_last_active_time():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID parameter is missing"}), 400

    last_active_timestamp = redis_client.get(f"user:{user_id}:lastActive")

    if not last_active_timestamp:
        return jsonify({"error": "User not found or never active"}), 404

    return jsonify({"user_id": user_id, "last_active_timestamp": int(last_active_timestamp)})


@app.route("/")
def start_heartbeat():
    heartbeat_thread = Thread(target=mark_inactive_users)
    heartbeat_thread.start()
    return "Heartbeat mechanism started."


if __name__ == "__main__":
    app.run(port=5006, debug=True)
