#!/bin/bash
set -e
cd /home/admin/.hermes/skills/research/trend-vs-portfolio
sudo -u admin python3 /home/admin/.hermes/skills/procurement/procurement-manager/scripts/make_report.py --json examples/運動水瓶-VS報告示範.json --outdir /srv/hermes-share/採購報告 --prefix 趨勢VS報告
rm -f "/srv/hermes-share/採購報告/趨勢VS報告-運動水瓶（歐美爆款 VS 示範）.html" "/srv/hermes-share/採購報告/趨勢VS報告-運動水瓶（歐美爆款 VS 示範）.pptx"
ls /srv/hermes-share/採購報告/
echo CLEAN-DONE
