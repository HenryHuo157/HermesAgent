#!/bin/bash
docker exec librechat-mongo mongosh LibreChat --quiet --eval '
const m = db.messages.find({}).sort({createdAt: -1}).limit(1).toArray()[0];
print("createdAt:", m.createdAt, "unfinished:", m.unfinished);
if (Array.isArray(m.content)) {
  m.content.forEach((p, i) => {
    let preview = "";
    for (const k of ["text","think"]) {
      if (typeof p[k] === "string") preview += "\n      " + k + "=" + JSON.stringify(p[k].slice(0, 220));
    }
    print("  [" + i + "] type=" + p.type + preview);
  });
} else {
  print("content:", JSON.stringify(m.content).slice(0, 500));
}
'
