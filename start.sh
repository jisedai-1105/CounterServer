#!/bin/bash
#cd /home/user01/jisedai
#source ./jisedaienv/bin/activate

cd /home/user01/jisedai/CounterServer
./../jisedaienv/bin/python main.py &

cd /home/user01/jisedai/CounterServer/web
./../../jisedaienv/bin/python app.py

# サービスファイル
# sudo vim /etc/systemd/system/jisedai_app.service

# 当ファイルを修正したら以下を実行
# sudo systemctl restart jisedai_app.service

# 安全装置をクリア
# sudo systemctl reset-failed jisedai_app.service

# サービスを止めたい場合
# sudo systemctl stop jisedai_app.service

# サービスを起動したい場合
# sudo systemctl start jisedai_app.service

# サービスの状態を確認したい場合
# sudo systemctl status jisedai_app.service

# プロセスを確認したい場合
# ps ax | grep python

# プロセスを終了したい場合
# kill -9 プロセスID