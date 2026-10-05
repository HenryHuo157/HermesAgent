#!/bin/bash
docker exec librechat-mongo mongosh librechat --quiet --eval '
const msgs = db.messages.find({unfinished: false}).sort({createdAt: -1}).limit(3).toArray();
for (const m of msgs) {
  print("=== msg " + m.messageId + " user=" + m.user + " " + m.createdAt);
  if (Array.isArray(m.content)) {
    m.content.forEach((p, i) => {
      const keys = Object.keys(p).join(",");
      let preview = "";
      for (const k of ["text","think"]) {
        if (typeof p[k] === "string") preview += " | " + k + "=" + JSON.stringify(p[k].slice(0, 180));
      }
      print("  [" + i + "] type=" + p.type + " {" + keys + "}" + preview);
    });
  } else {
    print("  content: " + JSON.stringify(m.content).slice(0, 300));
  }
}
' 2>&1 | head -60
