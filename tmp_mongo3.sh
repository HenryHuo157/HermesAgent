#!/bin/bash
docker exec librechat-mongo mongosh LibreChat --quiet --eval '
const msgs = db.messages.find({}).sort({createdAt: -1}).limit(4).toArray();
for (const m of msgs) {
  print("=== " + m.messageId + " | unfinished=" + m.unfinished + " | " + m.createdAt + " | text=" + JSON.stringify((m.text||"").slice(0,60)));
  if (Array.isArray(m.content)) {
    m.content.forEach((p, i) => {
      let preview = "";
      for (const k of ["text","think"]) {
        if (typeof p[k] === "string") preview += " | " + k + "=" + JSON.stringify(p[k].slice(0, 160));
      }
      print("  [" + i + "] type=" + p.type + preview);
    });
  }
}
' 2>&1 | head -80
