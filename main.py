from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

roomList = {}

def generateUniqueCode(length):
    while True:
        code = ""
        for i in range(length):
            code += random.choice(ascii_uppercase)
        if code not in roomList:
            break
    return code


@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST": #sever recieve data from user
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)


        if not name:
            return render_template("home.html", error = "Please enter a name.", code = code, name = name)
        if join != False and not code:
            return render_template("home.html", error = "Please enter a room code.", code = code, name = name)

        room = code

        #create room
        if create != False:
            room = generateUniqueCode(4)
            roomList[room] = {"members": 0, "messages": []}
        elif code not in roomList:
            return render_template("home.html", error = "Room does not exist!", code = code, name = name)
    
        #session save data of user even they refresh page
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in roomList:
        return redirect(url_for("home"))
        #If block: is not go to homepage to enter room code and name cannot go to room page

    return render_template("room.html", code = room, messages=roomList[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in roomList:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    roomList[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    if room not in roomList:
        leave_room(room)
        return
    
    #join a room
    join_room(room)
    send({"name": name, "message": "has joined the room."}, to=room)
    roomList[room]["members"] += 1
    print(f"{name} joined room {room}.")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in roomList:
        roomList[room]["members"] -= 1
        #del when last person go out
        if roomList[room]["members"] <= 0:
            del roomList[room]

    send({"name": name, "message": "has left the room."}, to=room)
    print(f"{name} has left the room.")

if __name__ == "__main__":
    socketio.run(app, debug=True)