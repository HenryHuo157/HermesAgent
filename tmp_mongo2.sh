#!/bin/bash
docker exec librechat-mongo mongosh librechat --quiet --eval 'db.messages.countDocuments({})' 2>&1
docker exec librechat-mongo mongosh librechat --quiet --eval 'db.messages.find({}, {messageId:1, createdAt:1, unfinished:1}).sort({createdAt:-1}).limit(5).toArray()' 2>&1 | head -40
